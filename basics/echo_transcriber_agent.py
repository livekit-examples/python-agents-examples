"""
---
title: Echo Transcriber Agent
category: basics
tags: [echo, transcriber, deepgram, silero]
difficulty: beginner
description: Shows how to create an agent that can transcribe audio and echo it back.
demonstrates:
  - Transcribing audio
  - Echoing audio back that's stored in a buffer
---
"""
import logging
import asyncio
from pathlib import Path
from typing import AsyncIterable, Optional
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession, room_io
from livekit.agents.vad import VADEventType
from livekit.plugins import silero, noise_cancellation

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("echo-transcriber")
logger.setLevel(logging.INFO)

class EchoTranscriberAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are an echo transcriber that listens and repeats audio.",
            stt="assemblyai/universal-streaming",
            vad=None,
            allow_interruptions=False
        )
        
        # We'll set these after initialization
        self.audio_source = None
        self.echo_track = None
        self.ctx = None
        self.audio_buffer = []
        self.custom_vad = silero.VAD.load(
            min_speech_duration=0.2,
            min_silence_duration=0.6,
        )
        self.vad_stream = self.custom_vad.stream()
        self.is_speaking = False
        self.is_echoing = False
        self.audio_format_set = False
    
    async def on_enter(self):
        # Override to prevent default TTS greeting
        pass
    
    def set_context(self, ctx: JobContext):
        self.ctx = ctx
    
    async def setup_audio_output(self):
        if self.audio_format_set:
            return
            
        self.audio_source = rtc.AudioSource(sample_rate=48000, num_channels=1)
        self.echo_track = rtc.LocalAudioTrack.create_audio_track("echo", self.audio_source)
        await self.ctx.room.local_participant.publish_track(
            self.echo_track,
            rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE),
        )
        self.audio_format_set = True
    
    async def stt_node(self, audio: AsyncIterable[rtc.AudioFrame], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[str]]:
        """Intercept audio frames before STT processing"""
        
        async def audio_with_buffer():
            """Pass through audio while processing with VAD and buffering"""
            first_frame = True
            async for frame in audio:
                if first_frame:
                    await self.setup_audio_output()
                    first_frame = False
                
                if not self.is_echoing:
                    self.vad_stream.push_frame(frame)
                    
                    self.audio_buffer.append(frame)
                    
                    if len(self.audio_buffer) > 1000:
                        self.audio_buffer.pop(0)
                
                yield frame
        
        return super().stt_node(audio_with_buffer(), model_settings)

async def entrypoint(ctx: JobContext):
    await ctx.room.local_participant.set_attributes({"lk.agent.state": "listening"})
    
    session = AgentSession()
    agent = EchoTranscriberAgent()
    agent.set_context(ctx)
    
    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            logger.info(f"Transcribed: {transcript.transcript}")
    
    async def process_vad():
        """Process VAD events"""
        async for vad_event in agent.vad_stream:
            if agent.is_echoing:
                continue
                
            if vad_event.type == VADEventType.START_OF_SPEECH:
                agent.is_speaking = True
                logger.info("VAD: Start of speech detected")
                # Keep only recent frames (last 100 frames ~1 second)
                if len(agent.audio_buffer) > 100:
                    agent.audio_buffer = agent.audio_buffer[-100:]
                    
            elif vad_event.type == VADEventType.END_OF_SPEECH:
                agent.is_speaking = False
                agent.is_echoing = True
                buffer_size = len(agent.audio_buffer)
                logger.info(f"VAD: End of speech, echoing {buffer_size} frames")
                
                # Set state to speaking
                await ctx.room.local_participant.set_attributes({"lk.agent.state": "speaking"})
                
                # Copy buffer to avoid modification during playback
                frames_to_play = agent.audio_buffer.copy()
                agent.audio_buffer.clear()
                
                # Play back all buffered audio
                if agent.audio_source:
                    for frame in frames_to_play:
                        await agent.audio_source.capture_frame(frame)
                else:
                    logger.error("Audio source not initialized yet")
                
                agent.is_echoing = False
                logger.info("Finished echoing")
                
                await ctx.room.local_participant.set_attributes({"lk.agent.state": "listening"})
    
    # Start VAD processing
    vad_task = asyncio.create_task(process_vad())
    
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=room_io.RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
            audio_sample_rate=48000,
            audio_num_channels=1,
        )
    )
    
    # Keep VAD task running
    await vad_task

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))