"""
Simple example agent that plays a pre-recorded greeting when user connects.
"""
import logging
import wave
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero
from livekit import rtc

logger = logging.getLogger("example-agent")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# File name to play
GREETING_FILE = Path(__file__).parent / "recordings" / "greeting.wav"

class ExampleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful assistant. The user has already heard a greeting, so just help them with their questions",
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="inworld/inworld-tts-1:Ashley",
            vad=silero.VAD.load()
        )
    
    async def on_enter(self):
        # If you want, you can add some delays here
        if GREETING_FILE.exists():
            await self._play_greeting()
        else:
            await self.session.say("Looks like there's no greeting recorded yet. Please record a greeting first.")
    
    async def _play_greeting(self):
        with wave.open(str(GREETING_FILE), 'rb') as wav_file:
            num_channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            frames = wav_file.readframes(wav_file.getnframes())
            num_frames = wav_file.getnframes()

        audio_frame = rtc.AudioFrame(
            data=frames,
            sample_rate=sample_rate,
            num_channels=num_channels,
            samples_per_channel=num_frames
        )

        async def audio_generator():
            yield audio_frame

        # allow_interruptions is blocking the user from interrupting agent while it's playing the greeting recording
        await self.session.say("", audio=audio_generator(), allow_interruptions=False)

async def entrypoint(ctx: JobContext):
    session = AgentSession()
    await session.start(agent=ExampleAgent(), room=ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

