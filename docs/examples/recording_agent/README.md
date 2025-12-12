---
title: Recording Agent
category: egress
tags: [recording, deepgram, openai, cartesia]
difficulty: intermediate
description: Shows how to create an agent that can record the input to a room and save it to a file.
demonstrates:
  - Using egress to record the input to a room
---

This example shows how to start a voice agent and kick off a LiveKit egress recording for the room. Media is saved to a segmented playlist in cloud storage while the agent runs.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" python-dotenv livekit-api
  ```
- A cloud bucket and credentials JSON for egress (GCP in this example)

## Load environment, logging, and define an AgentServer

Load environment variables, set up logging, and initialize the AgentServer.

```python
import logging
from dotenv import load_dotenv
from livekit import api
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("recording-agent")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Define a lightweight agent

Create an agent with simple instructions that greets on entry.

```python
class RecordingAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """
        )

    async def on_enter(self):
        self.session.generate_reply()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process to reduce connection latency.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Start room composite egress and agent session

Before starting the agent, configure a `RoomCompositeEgressRequest` pointing to your bucket. Read your GCP credentials JSON into the request and set segment output options.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

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

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=RecordingAgent(), room=ctx.room)
    await ctx.connect()

    await lkapi.aclose()
```

## Run the server

Start the agent server with the CLI runner.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```bash
python recording_agent.py console
```

## How it works

1. The VAD is prewarmed once per process for faster connections.
2. Egress starts a composite recording of the room (audio/video).
3. Output is segmented and uploaded to your bucket with playlists.
4. The agent runs concurrently, greeting and conversing while recording continues.
5. The API client is closed after the session/egress setup.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit import api
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("recording-agent")
logger.setLevel(logging.INFO)

class RecordingAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """
        )

    async def on_enter(self):
        self.session.generate_reply()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

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

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=RecordingAgent(), room=ctx.room)
    await ctx.connect()

    await lkapi.aclose()

if __name__ == "__main__":
    cli.run_app(server)
```
