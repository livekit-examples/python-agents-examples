---
title: Recording Agent
category: egress
tags: [recording]
difficulty: intermediate
description: Shows how to create an agent that can record the input to a room and save it to a file.
demonstrates:
  - Using egress to record the input to a room
---

This example shows how to create an agent that can record the input to a room and save it to a file.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" python-dotenv
  ```

## Run it

```bash
python recording_agent.py console
```

## How it works

- Using egress to record the input to a room

## Full example

```python
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit import api
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import silero

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

logger = logging.getLogger("recording-agent")
logger.setLevel(logging.INFO)

class RecordingAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """,
            stt=inference.STT(
                model="assemblyai/universal-streaming",
                language="en"
            ),
            llm=inference.LLM(
                model="openai/gpt-5-mini",
                provider="openai",
            ),
            tts=inference.TTS(
                model="cartesia/sonic-3",
                voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
            ),
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    file_contents = ""
    with open("/path/to/credentials.json", "r") as f:
      file_contents = f.read()

    req = api.RoomCompositeEgressRequest(
        room_name="my-room",
        layout="speaker",
        preset=api.EncodingOptionsPreset.H264_720P_30,
        audio_only=False,
        segment_outputs=[api.SegmentedFileOutput(
            filename_prefix="my-output",
            playlist_name="my-playlist.m3u8",
            live_playlist_name="my-live-playlist.m3u8",
            segment_duration=5,
            gcp=api.GCPUpload(
                credentials=file_contents,
                bucket="<my-bucket>",
            ),
        )],
    )
    lkapi = api.LiveKitAPI()
    res = await lkapi.egress.start_room_composite_egress(req)
    session = AgentSession()

    await session.start(
        agent=RecordingAgent(),
        room=ctx.room
    )

    await lkapi.aclose()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
