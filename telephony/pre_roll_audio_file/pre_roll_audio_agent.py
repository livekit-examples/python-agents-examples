"""
LiveKit Voice Agent Example: Law Office Reception with Pre-roll Audio and Office Hours Logic

This example demonstrates a voice AI agent that acts as a law office receptionist with the following features:

1. Pre-roll Audio: Plays a pre-recorded audio file when the agent first enters the session
2. Office Hours Logic: Automatically switches between two modes based on current time:
   - Office Open (8 AM - 5 PM): Full interactive agent with STT, LLM, and TTS capabilities
   - Office Closed (outside 8 AM - 5 PM): Plays background audio loop (closed.mp3) continuously for N seconds, then hangup call then hangs up
3. Voice Agent: Uses OpenAI's GPT-4o-mini for natural language processing
4. Audio Processing: Supports both pre-synthesized audio playback and real-time TTS generation

The agent greets callers during office hours and provides a professional law office experience,
while offering appropriate messaging when the office is closed.
"""

import logging
import asyncio
from typing import AsyncIterable
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    NOT_GIVEN,
    Agent,
    AgentFalseInterruptionEvent,
    AgentSession,
    BackgroundAudioPlayer,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RoomOutputOptions,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.agents.utils.codecs import AudioStreamDecoder
from livekit.plugins import deepgram, openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# uncomment to enable Krisp background voice/noise cancellation
# from livekit.plugins import noise_cancellation

logger = logging.getLogger("basic-agent")

load_dotenv()

audio_path = Path(__file__).parent
audio_file = f"{audio_path}/pre_roll_audio.mp3"
closed_audio_file =  f"{audio_path}/closed.mp3"


async def load_audio_file(file_path: str) -> AsyncIterable[rtc.AudioFrame]:
    """Load an audio file and convert it to AudioFrames"""
    # Check if file exists before attempting to load
    if not Path(file_path).exists():
        logger.error("Audio file could not be loaded: %s", file_path)
        logger.error("File path: %s", Path(file_path).absolute())
        logger.error("File name: %s", Path(file_path).name)
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    logger.info("Loading audio file: %s", file_path)
    decoder = AudioStreamDecoder(sample_rate=48000, num_channels=1)
    
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(4096):
                decoder.push(chunk)
            decoder.end_input()
        
        async for frame in decoder:
            yield frame
    except Exception as e:
        logger.error("Error loading audio file %s: %s", file_path, e)
        raise

class MyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
            You are a reception for the law office of Dewey, Cheatham & Howe. 
            You would interact with users via voice. With that in mind keep your responses concise and to the point. 
            Do not use emojis, asterisks, markdown, or other special characters in your responses. You are curious and friendly, and have a sense of humor.
            """
        )

    async def on_enter(self):
        try:
            audio_frames = load_audio_file(audio_file)
            await self.session.say(".", audio=audio_frames, allow_interruptions=False)
            await asyncio.sleep(3)
        except FileNotFoundError as e:
            logger.error("Pre-roll audio file not found, continuing without audio: %s", e)
        except Exception as e:
            logger.error("Error loading pre-roll audio file: %s", e)

        # Generate a reply
        await self.session.say("Hello, thank you for calling. I am Pat. How can I help you today?")

   
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # each log entry will include these fields
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # If current time is between 8am and 5pm, call entrypoint_office_open
    if datetime.now().hour >= 8 and datetime.now().hour <= 17:
    #if True: # for Open Office Hours
    #if False: # for Closed Office Hours
        await entrypoint_office_open(ctx)
    else:
        await entrypoint_office_closed(ctx)

async def entrypoint_office_closed(ctx: JobContext):
    """Play background audio when office is closed"""
    logger.info("Office is closed, playing background audio")
    
    # Check if closed audio file exists
    if not Path(closed_audio_file).exists():
        logger.error("Closed office audio file could not be loaded: %s", closed_audio_file)
        logger.error("File path: %s", Path(closed_audio_file).absolute())
        logger.error("File name: %s", Path(closed_audio_file).name)
        logger.error("Cannot play background audio, hanging up call")
        await ctx.delete_room()
        return
    
    # Connect to the room first
    await ctx.connect()
    
    # Create background audio player with the closed audio file looped
    background_audio = BackgroundAudioPlayer(
        ambient_sound=closed_audio_file
    )
    
    try:
        # Start the background audio player
        await background_audio.start(room=ctx.room, agent_session=None)
        logger.info("Successfully started background audio: %s", closed_audio_file)
        
        # Keep the audio playing for N seconds then hang up
        start_time = datetime.now()
        while True:
            # after 10 seconds hangup call
            if (datetime.now() - start_time).seconds >= 10:
                await background_audio.aclose()
                await ctx.delete_room()
                return

            await asyncio.sleep(1)
            
    except FileNotFoundError as e:
        logger.error("Background audio file not found during playback: %s", e)
        logger.error("File path: %s", Path(closed_audio_file).absolute())
        logger.error("File name: %s", Path(closed_audio_file).name)
    except Exception as e:
        logger.error("Error in office closed mode: %s", e)
    finally:
        # Clean up the background audio player
        try:
            await background_audio.aclose()
        except Exception as e:
            logger.error("Error closing background audio player: %s", e)


async def entrypoint_office_open(ctx: JobContext):
    
    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        # any combination of STT, LLM, TTS, or realtime API can be used
        #llm=openai.LLM(model="gpt-4o-mini"),
        llm=openai.LLM(model="gpt-4o-mini"),
        stt=deepgram.STT(model="nova-3", language="multi"),
        tts=openai.TTS(voice="ash"),
        # allow the LLM to generate a response while waiting for the end of turn
        preemptive_generation=True,
        # use LiveKit's turn detection model
        turn_detection=MultilingualModel(),
    )

    # log metrics as they are emitted, and total usage after session is over
    usage_collector = metrics.UsageCollector()

    # sometimes background noise could interrupt the agent session, these are considered false positive interruptions
    # when it's detected, you may resume the agent's speech
    @session.on("agent_false_interruption")
    def _on_agent_false_interruption(ev: AgentFalseInterruptionEvent):
        logger.info("false positive interruption, resuming")
        session.generate_reply(instructions=ev.extra_instructions or NOT_GIVEN)

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info("Usage: %s", summary)

    # shutdown callbacks are triggered when the session is over
    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=MyAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # uncomment to enable Krisp BVC noise cancellation
            # noise_cancellation=noise_cancellation.BVC(),
        ),
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))