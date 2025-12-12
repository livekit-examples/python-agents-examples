---
title: TTS Metrics
category: metrics
tags: [metrics, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to use the TTS metrics to log metrics to the console.
demonstrates:
  - Using the TTS metrics to log metrics to the console.
  - This includes:
    - TTFB
    - Duration
    - Audio Duration
    - Cancelled
    - Characters Count
    - Streamed
    - Speech ID
    - Error
---

This example shows you how to watch text-to-speech performance metrics in real time. Each time the agent speaks, the TTS plugin emits metrics (TTFB, duration, audio length, etc.) that are displayed as a Rich table.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install python-dotenv rich "livekit-agents[silero]"
  ```

## Load environment, logging, and define an AgentServer

Initialize dotenv, logging, a Rich console for the metrics table, and the AgentServer.

```python
import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference
from livekit.agents.metrics import TTSMetrics
from livekit.plugins import silero
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime

load_dotenv()

logger = logging.getLogger("metrics-tts")
logger.setLevel(logging.INFO)

console = Console()

server = AgentServer()
```

## Define a lightweight agent and TTS metrics display function

Keep the Agent class minimal with instructions and an entry greeting. Define an async function to display TTS metrics as a Rich table.

```python
class TTSMetricsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful agent."
        )

    async def on_enter(self):
        self.session.generate_reply()

async def display_tts_metrics(metrics: TTSMetrics):
    table = Table(
        title="[bold blue]TTS Metrics Report[/bold blue]",
        box=box.ROUNDED,
        highlight=True,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Metric", style="bold green")
    table.add_column("Value", style="yellow")

    timestamp = datetime.fromtimestamp(metrics.timestamp).strftime('%Y-%m-%d %H:%M:%S')

    table.add_row("Type", str(metrics.type))
    table.add_row("Label", str(metrics.label))
    table.add_row("Request ID", str(metrics.request_id))
    table.add_row("Timestamp", timestamp)
    table.add_row("TTFB", f"[white]{metrics.ttfb:.4f}[/white]s")
    table.add_row("Duration", f"[white]{metrics.duration:.4f}[/white]s")
    table.add_row("Audio Duration", f"[white]{metrics.audio_duration:.4f}[/white]s")
    table.add_row("Cancelled", "✓" if metrics.cancelled else "✗")
    table.add_row("Characters Count", str(metrics.characters_count))
    table.add_row("Streamed", "✓" if metrics.streamed else "✗")
    table.add_row("Speech ID", str(metrics.speech_id))
    table.add_row("Error", str(metrics.error))

    console.print("\n")
    console.print(table)
    console.print("\n")
```

## Prewarm VAD for faster connections

Preload the VAD model once per process. This runs before any sessions start and stores the VAD instance in `proc.userdata`.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define the rtc session with TTS metrics hook

Create an rtc session entrypoint that creates the TTS instance, hooks into its `metrics_collected` event, and starts the agent session.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    tts_instance = inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc")

    def on_tts_metrics(metrics: TTSMetrics):
        asyncio.create_task(display_tts_metrics(metrics))

    tts_instance.on("metrics_collected", on_tts_metrics)

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=tts_instance,
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=TTSMetricsAgent(), room=ctx.room)
    await ctx.connect()
```

## Run the server

The `cli.run_app()` function starts the agent server and manages the worker lifecycle.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```bash
python metrics_tts.py console
```

## How it works

1. The VAD model is prewarmed once per process for faster connections.
2. The TTS instance is created and its `metrics_collected` event handler is attached.
3. When the agent speaks, the TTS plugin emits metrics including TTFB, duration, and audio length.
4. An async handler formats the metrics (latency, durations, character counts) into a Rich table.
5. Because the handler runs in a background task, the call flow is not blocked.

## Full example

```python
import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference
from livekit.agents.metrics import TTSMetrics
from livekit.plugins import silero
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime

load_dotenv()

logger = logging.getLogger("metrics-tts")
logger.setLevel(logging.INFO)

console = Console()

class TTSMetricsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful agent."
        )

    async def on_enter(self):
        self.session.generate_reply()

async def display_tts_metrics(metrics: TTSMetrics):
    table = Table(
        title="[bold blue]TTS Metrics Report[/bold blue]",
        box=box.ROUNDED,
        highlight=True,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Metric", style="bold green")
    table.add_column("Value", style="yellow")

    timestamp = datetime.fromtimestamp(metrics.timestamp).strftime('%Y-%m-%d %H:%M:%S')

    table.add_row("Type", str(metrics.type))
    table.add_row("Label", str(metrics.label))
    table.add_row("Request ID", str(metrics.request_id))
    table.add_row("Timestamp", timestamp)
    table.add_row("TTFB", f"[white]{metrics.ttfb:.4f}[/white]s")
    table.add_row("Duration", f"[white]{metrics.duration:.4f}[/white]s")
    table.add_row("Audio Duration", f"[white]{metrics.audio_duration:.4f}[/white]s")
    table.add_row("Cancelled", "✓" if metrics.cancelled else "✗")
    table.add_row("Characters Count", str(metrics.characters_count))
    table.add_row("Streamed", "✓" if metrics.streamed else "✗")
    table.add_row("Speech ID", str(metrics.speech_id))
    table.add_row("Error", str(metrics.error))

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

    tts_instance = inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc")

    def on_tts_metrics(metrics: TTSMetrics):
        asyncio.create_task(display_tts_metrics(metrics))

    tts_instance.on("metrics_collected", on_tts_metrics)

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=tts_instance,
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=TTSMetricsAgent(), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
