---
title: VAD Metrics
category: metrics
tags: [metrics, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to use the VAD metrics to log metrics to the console.
demonstrates:
  - Using the VAD metrics to log metrics to the console.
  - This includes:
    - Idle Time
    - Inference Duration Total
    - Inference Count
    - Speech ID
    - Error
---

This example shows you how to log voice-activity-detection (VAD) metrics during a call. Each time the Silero VAD processes speech, it emits idle time and inference timing data that you render with Rich.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install rich "livekit-agents[silero]" python-dotenv
  ```

## Load environment, logging, and define an AgentServer

Set up dotenv, logging, a Rich console for the VAD reports, and initialize the AgentServer.

```python
import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, vad
from livekit.plugins import silero
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime

load_dotenv()

logger = logging.getLogger("metrics-vad")
logger.setLevel(logging.INFO)

console = Console()

server = AgentServer()
```

## Define a lightweight agent and VAD metrics display function

Keep the Agent class minimal with just instructions. Define an async function to display VAD metrics as a Rich table.

```python
class VADMetricsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful agent."
        )

async def display_vad_metrics(event: vad.VADEvent):
    table = Table(
        title="[bold blue]VAD Event Metrics Report[/bold blue]",
        box=box.ROUNDED,
        highlight=True,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Metric", style="bold green")
    table.add_column("Value", style="yellow")

    timestamp = datetime.fromtimestamp(event.timestamp).strftime('%Y-%m-%d %H:%M:%S')

    table.add_row("Type", str(event.type))
    table.add_row("Timestamp", timestamp)
    table.add_row("Idle Time", f"[white]{event.idle_time:.4f}[/white]s")
    table.add_row("Inference Duration Total", f"[white]{event.inference_duration_total:.4f}[/white]s")
    table.add_row("Inference Count", str(event.inference_count))
    table.add_row("Speech ID", str(event.speech_id))
    table.add_row("Error", str(event.error))

    console.print("\n")
    console.print(table)
    console.print("\n")
```

## Prewarm VAD for faster connections

Preload the VAD model once per process. This runs before any sessions start and stores the VAD instance in `proc.userdata` so it can be reused, cutting down on connection latency.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define the rtc session with VAD metrics hook

Create an rtc session entrypoint that retrieves the prewarmed VAD, hooks into its `metrics_collected` event, and starts the agent session with STT/LLM/TTS configuration.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    vad_instance = ctx.proc.userdata["vad"]

    def on_vad_event(event: vad.VADEvent):
        asyncio.create_task(display_vad_metrics(event))

    vad_instance.on("metrics_collected", on_vad_event)

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=vad_instance,
        preemptive_generation=True,
    )

    await session.start(agent=VADMetricsAgent(), room=ctx.room)
    await ctx.connect()
```

## Run the server

The `cli.run_app()` function starts the agent server. It manages the worker lifecycle, connects to LiveKit, and processes incoming jobs.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```bash
python metrics_vad.py console
```

## How it works

1. The VAD model is prewarmed once per process for faster connections.
2. When the rtc session starts, the `metrics_collected` event handler is attached to the VAD.
3. Silero VAD detects speech and emits metrics events with idle time, inference duration, and count.
4. A background task formats and prints the metrics as a Rich table.
5. Because the handler is async, it does not block ongoing audio processing.

## Full example

```python
import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, vad
from livekit.plugins import silero
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime

load_dotenv()

logger = logging.getLogger("metrics-vad")
logger.setLevel(logging.INFO)

console = Console()

class VADMetricsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful agent."
        )

async def display_vad_metrics(event: vad.VADEvent):
    table = Table(
        title="[bold blue]VAD Event Metrics Report[/bold blue]",
        box=box.ROUNDED,
        highlight=True,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Metric", style="bold green")
    table.add_column("Value", style="yellow")

    timestamp = datetime.fromtimestamp(event.timestamp).strftime('%Y-%m-%d %H:%M:%S')

    table.add_row("Type", str(event.type))
    table.add_row("Timestamp", timestamp)
    table.add_row("Idle Time", f"[white]{event.idle_time:.4f}[/white]s")
    table.add_row("Inference Duration Total", f"[white]{event.inference_duration_total:.4f}[/white]s")
    table.add_row("Inference Count", str(event.inference_count))
    table.add_row("Speech ID", str(event.speech_id))
    table.add_row("Error", str(event.error))

    console.print("\n")
    console.print(table)
    console.print("\n")

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    vad_instance = ctx.proc.userdata["vad"]

    def on_vad_event(event: vad.VADEvent):
        asyncio.create_task(display_vad_metrics(event))

    vad_instance.on("metrics_collected", on_vad_event)

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=vad_instance,
        preemptive_generation=True,
    )

    await session.start(agent=VADMetricsAgent(), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
