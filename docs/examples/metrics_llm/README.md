---
title: LLM Metrics
category: metrics
tags: [metrics, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to use the LLM metrics to log metrics to the console for all of the different LLM models.
demonstrates:
  - Using the LLM metrics to log metrics to the console
  - Inspecting fields like type, label, request ID, timestamps, duration,
    time to first token, cancellation, token counts, and throughput
---

This example shows how to capture token and latency metrics emitted by the LLM pipeline and print them as a Rich table whenever the agent responds. It's a quick way to see prompt/response token counts and time-to-first-token during a live call.

## Prerequisites

- Add a `.env` in this directory with your LiveKit and OpenAI credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  OPENAI_API_KEY=your_openai_key
  ```
- Install dependencies:
  ```bash
  pip install python-dotenv rich "livekit-agents[silero]"
  ```

## Load configuration and logging

Set up dotenv, a logger, and a Rich console for the metrics table.

```python
import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, inference, AgentServer, cli
from livekit.agents.metrics import LLMMetrics
from livekit.plugins import silero
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime

load_dotenv()

logger = logging.getLogger("metrics-llm")
logger.setLevel(logging.INFO)

console = Console()

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process to reduce connection latency.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Create the metrics-enabled agent

Keep the agent lightweight with just instructions. In `on_enter`, attach an `on("metrics_collected")` listener to the session's LLM so every response triggers your metrics handler.

```python
class LLMMetricsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """
        )

    async def on_enter(self):
        def sync_wrapper(metrics: LLMMetrics):
            asyncio.create_task(self.on_metrics_collected(metrics))

        self.session.llm.on("metrics_collected", sync_wrapper)
        self.session.generate_reply()
```

## Render metrics with Rich

When metrics arrive, format them into a table with timestamps, TTFT, durations, and token counts.

```python
    async def on_metrics_collected(self, metrics: LLMMetrics) -> None:
        table = Table(
            title="[bold blue]LLM Metrics Report[/bold blue]",
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
        table.add_row("Duration", f"[white]{metrics.duration:.4f}[/white]s")
        table.add_row("Time to First Token", f"[white]{metrics.ttft:.4f}[/white]s")
        table.add_row("Cancelled", "✓" if metrics.cancelled else "✗")
        table.add_row("Completion Tokens", str(metrics.completion_tokens))
        table.add_row("Prompt Tokens", str(metrics.prompt_tokens))
        table.add_row("Total Tokens", str(metrics.total_tokens))
        table.add_row("Tokens/Second", f"{metrics.tokens_per_second:.2f}")

        console.print("\n")
        console.print(table)
        console.print("\n")
```

## Set up the session

Configure the AgentSession with STT, LLM, TTS, and prewarmed VAD. The LLM's metrics events will be captured by the listener attached in `on_enter`.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = LLMMetricsAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()
```

## Run the server

Start the agent server with the CLI.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```console
python metrics_llm.py console
```

## How it works

1. The agent runs with standard STT/LLM/TTS and Silero VAD.
2. The LLM emits `metrics_collected` after each generation.
3. A wrapper in `on_enter` schedules `on_metrics_collected` so you can await inside it.
4. Rich renders the metrics in a readable table showing latency and token stats.

## Full example

```python
import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, inference, AgentServer, cli
from livekit.agents.metrics import LLMMetrics
from livekit.plugins import silero
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime

load_dotenv()

logger = logging.getLogger("metrics-llm")
logger.setLevel(logging.INFO)

console = Console()

class LLMMetricsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """
        )

    async def on_enter(self):
        def sync_wrapper(metrics: LLMMetrics):
            asyncio.create_task(self.on_metrics_collected(metrics))

        self.session.llm.on("metrics_collected", sync_wrapper)
        self.session.generate_reply()

    async def on_metrics_collected(self, metrics: LLMMetrics) -> None:
        table = Table(
            title="[bold blue]LLM Metrics Report[/bold blue]",
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
        table.add_row("Duration", f"[white]{metrics.duration:.4f}[/white]s")
        table.add_row("Time to First Token", f"[white]{metrics.ttft:.4f}[/white]s")
        table.add_row("Cancelled", "✓" if metrics.cancelled else "✗")
        table.add_row("Completion Tokens", str(metrics.completion_tokens))
        table.add_row("Prompt Tokens", str(metrics.prompt_tokens))
        table.add_row("Total Tokens", str(metrics.total_tokens))
        table.add_row("Tokens/Second", f"{metrics.tokens_per_second:.2f}")

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

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = LLMMetricsAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
