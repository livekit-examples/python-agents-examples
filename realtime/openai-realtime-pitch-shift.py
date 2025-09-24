"""
---
title: Realtime Audio Pitch Shifting
category: realtime
tags: [audio_processing, pitch_shift, librosa, realtime_audio_output_node]
difficulty: advanced
description: OpenAI Realtime agent with real-time audio pitch shifting
demonstrates:
  - Custom realtime_audio_output_node override
  - Audio stream processing with librosa
  - Pitch shifting by semitones
  - AudioByteStream for buffering
  - Frame-by-frame audio transformation
  - NumPy audio data manipulation
---
"""

import librosa
import numpy as np
from typing import AsyncIterable
from dotenv import load_dotenv
from pathlib import Path
from livekit import agents, rtc
from livekit.agents import utils
from livekit.agents.voice import AgentSession, Agent, room_io, ModelSettings
from livekit.plugins import (
    openai,
    silero
)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class Assistant(Agent):
    def __init__(self, *, pitch_shift_semitones: float = -4.0) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant.")
        self.pitch_shift_semitones = pitch_shift_semitones

    async def realtime_audio_output_node(
        self, audio: AsyncIterable[rtc.AudioFrame], model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        return self._process_audio_stream(
            Agent.default.realtime_audio_output_node(self, audio, model_settings)
        )

    async def _process_audio_stream(
        self, audio: AsyncIterable[rtc.AudioFrame]
    ) -> AsyncIterable[rtc.AudioFrame]:
        stream: utils.audio.AudioByteStream | None = None
        async for frame in audio:
            if stream is None:
                stream = utils.audio.AudioByteStream(
                    sample_rate=frame.sample_rate,
                    num_channels=frame.num_channels,
                    samples_per_channel=frame.sample_rate // 4,
                )
            for f in stream.push(frame.data):
                yield self._process_audio(f)

        for f in stream.flush():
            yield self._process_audio(f)

    def _process_audio(self, frame: rtc.AudioFrame) -> rtc.AudioFrame:
        audio_data = np.frombuffer(frame.data, dtype=np.int16)

        shifted = librosa.effects.pitch_shift(
            audio_data.astype(np.float32) / np.iinfo(np.int16).max,
            sr=frame.sample_rate,
            n_steps=self.pitch_shift_semitones,
        )
        shifted = (shifted * np.iinfo(np.int16).max).astype(np.int16)
        return rtc.AudioFrame(
            data=shifted.tobytes(),
            sample_rate=frame.sample_rate,
            num_channels=frame.num_channels,
            samples_per_channel=shifted.shape[-1],
        )

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(),
        vad=silero.VAD.load()
    )

    await session.start(
        room=ctx.room,
        agent=Assistant()
    )

    await session.generate_reply()


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))