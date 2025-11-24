"""
---
title: Recording Studio Agent
category: basics
tags: [audio, recording, tts, playback, voice-switching, openai, deepgram]
difficulty: intermediate
description: A recording studio agent that can switch voices, record audio, and manage recordings.
demonstrates:
  - Overriding the tts_node to intercept audio frames
  - Saving audio frames to WAV files with metadata
  - Playing back recorded audio with function tools
  - Switching TTS voices dynamically
  - Managing recordings directory with metadata
---
"""
import logging
import wave
import json
from pathlib import Path
from typing import AsyncIterable, Optional
from datetime import datetime
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, ModelSettings, inference
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import silero
from livekit import rtc

logger = logging.getLogger("recording-studio-agent")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')
# Check the available voices in the LiveKit inference documentation:
# For example, here: https://docs.livekit.io/agents/models/tts/inference/cartesia/
AVAILABLE_VOICES = [
    {
        "name": "Blake",
        "description": "Energetic American adult male",
        "model": "cartesia/sonic-3:a167e0f3-df7e-4d52-a9c3-f949145efdab"
    },
    {
        "name": "Daniela",
        "description": "Calm and trusting Mexican female",
        "model": "cartesia/sonic-3:5c5ad5e7-1020-476b-8b91-fdcbe9cc313c"
    },
    {
        "name": "Jacqueline",
        "description": "Confident, young American adult female",
        "model": "cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
    },
    {
        "name": "Robyn",
        "description": "Neutral, mature Australian female",
        "model": "cartesia/sonic-3:f31cc6a7-c1e8-4764-980c-60a361443dd1"
    },
    {
        "name": "Alice",
        "description": "Clear and engaging, friendly British woman",
        "model": "elevenlabs/eleven_turbo_v2_5:Xb7hH8MSUJpSbSDYk0k2"
    },
    {
        "name": "Ashley",
        "description": "Warm, natural American female",
        "model": "inworld/inworld-tts-1:Ashley"
    },
    # Add more if needed
]

class RecordingStudioAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a recording studio assistant. You help users record audio with different voices.
                
                Workflow:
                1. User can ask to see available voices - use change_voice() without parameters
                2. User can switch voice - use change_voice(voice_name)
                3. User can see all recordings - use list_recordings()
                4. User can record text - use record_text(text) with ONLY the exact text to record
                5. User can play recordings - use play_recording() for latest or play_recording(filename) for specific
                
                IMPORTANT: When recording, pass ONLY the exact text the user wants recorded.
            """,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="elevenlabs/eleven_turbo_v2_5:Xb7hH8MSUJpSbSDYk0k2",
            vad=silero.VAD.load()
        )
        
        self.is_recording = False
        self.audio_buffer = []
        self.sample_rate = None
        self.num_channels = None
        self.recordings_dir = Path(__file__).parent / "recordings"
        self.recordings_dir.mkdir(exist_ok=True)
        self.current_voice = AVAILABLE_VOICES[4]
        self.last_recording = None
        self.last_recording_text = None
        self._should_greet = False
    
    @function_tool
    async def change_voice(self, context: RunContext, voice_name: Optional[str] = None):
        """Change the TTS voice or list available voices."""
        if voice_name is None:
            voices_list = [f"{v['name']} - {v['description']}" for v in AVAILABLE_VOICES]
            return f"Available voices:\n" + "\n".join(voices_list) + f"\n\nCurrent voice: {self.current_voice['name']}"
        
        voice_info = next((v for v in AVAILABLE_VOICES if v['name'].lower() == voice_name.lower()), None)
        if voice_info is None:
            available = ", ".join([v['name'] for v in AVAILABLE_VOICES])
            return f"Voice '{voice_name}' not found. Available: {available}"
        
        logger.info(f"Switching to voice: {voice_info['name']}")
        
        new_agent = RecordingStudioAgent()
        new_agent.current_voice = voice_info
        new_agent._tts = inference.TTS.from_model_string(voice_info['model'])
        new_agent.recordings_dir = self.recordings_dir
        new_agent.last_recording = self.last_recording
        new_agent.last_recording_text = self.last_recording_text
        new_agent._should_greet = True
        
        return new_agent
    
    @function_tool
    async def list_recordings(self, context: RunContext):
        """List all recordings with their metadata."""
        recordings = []
        for wav_file in sorted(self.recordings_dir.glob("*.wav")):
            meta_file = wav_file.with_suffix(".json")
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                    voice_display = meta.get('voice_name', meta.get('voice', 'unknown'))
                    recordings.append(f"{wav_file.name}: \"{meta['text']}\" (voice: {voice_display})")
        
        if not recordings:
            return None, "No recordings found yet."
        
        return None, f"Recordings:\n" + "\n".join(recordings)
    
    @function_tool
    async def record_text(self, context: RunContext, text: str):
        """Record the given text as audio and save it to a file."""
        logger.info(f"Recording text: {text}")
        
        await self.session.say("Recording now.")
        
        self.is_recording = True
        self.audio_buffer = []
        self.sample_rate = None
        self.num_channels = None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.last_recording = f"recording_{timestamp}.wav"
        self.last_recording_text = text
        
        await self.session.say(text)
        self.is_recording = False
        
        return None, f"Done! Saved as {self.last_recording}"
    
    @function_tool
    async def play_recording(self, context: RunContext, filename: Optional[str] = None):
        """Play back a recorded audio file."""
        if filename is None:
            if self.last_recording is None:
                return None, "No recent recording. Use list_recordings to see available files."
            filename = self.last_recording
        
        recording_path = self.recordings_dir / filename
        if not recording_path.exists():
            return None, f"Recording '{filename}' not found. Use list_recordings to see available files."
        
        with wave.open(str(recording_path), 'rb') as wav_file:
            num_channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            frames = wav_file.readframes(wav_file.getnframes())
            num_frames = wav_file.getnframes()
            
            duration = num_frames / sample_rate
            logger.info(f"Playing {filename}: {duration:.2f}s")

        audio_frame = rtc.AudioFrame(
            data=frames,
            sample_rate=sample_rate,
            num_channels=num_channels,
            samples_per_channel=num_frames
        )

        async def audio_generator():
            yield audio_frame

        await self.session.say("Here's the recording", audio=audio_generator())
        return None, f"Played {filename}"
    
    async def tts_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        async def process_and_record_audio():
            audio_stream = Agent.default.tts_node(self, text, model_settings)
            
            async for frame in audio_stream:
                if self.is_recording:
                    if self.sample_rate is None:
                        self.sample_rate = frame.sample_rate
                        self.num_channels = frame.num_channels
                        logger.info(f"Recording audio: {self.sample_rate}Hz, {self.num_channels}ch")
                    
                    self.audio_buffer.append(bytes(frame.data))
                
                yield frame
            
            if self.is_recording and self.audio_buffer:
                await self._save_recording()
        
        return process_and_record_audio()
    
    async def _save_recording(self):
        if not self.audio_buffer or self.sample_rate is None or self.last_recording is None:
            return
        
        audio_data = b''.join(self.audio_buffer)
        bytes_per_sample = 2
        bytes_per_frame = bytes_per_sample * self.num_channels
        num_frames = len(audio_data) // bytes_per_frame
        
        recording_path = self.recordings_dir / self.last_recording
        
        with wave.open(str(recording_path), 'wb') as wav_file:
            wav_file.setnchannels(self.num_channels)
            wav_file.setsampwidth(bytes_per_sample)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data)
        
        meta_path = recording_path.with_suffix(".json")
        with open(meta_path, 'w') as f:
            json.dump({
                "filename": self.last_recording,
                "timestamp": datetime.now().isoformat(),
                "voice_name": self.current_voice['name'],
                "voice_description": self.current_voice['description'],
                "duration": num_frames / self.sample_rate,
                "sample_rate": self.sample_rate,
                "channels": self.num_channels,
                "text": self.last_recording_text or ""
            }, f, indent=2)
        
        logger.info(f"Saved {self.last_recording}: {num_frames / self.sample_rate:.2f}s")
    
    async def on_enter(self):
        if self._should_greet:
            await self.session.say(f"Voice changed to {self.current_voice['name']}. How does this sound?")
        else:
            await self.session.say("Welcome to the recording studio! I can help you record audio with different voices.")

async def entrypoint(ctx: JobContext):
    session = AgentSession()
    
    await session.start(
        agent=RecordingStudioAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

