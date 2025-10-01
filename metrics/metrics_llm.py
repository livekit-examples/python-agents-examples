"""
---
title: LLM Metrics
category: metrics
tags: [metrics, openai, deepgram]
difficulty: beginner
description: Shows how to use the LLM metrics to log metrics to the console for all of the different LLM models.
demonstrates:
  - Using the LLM metrics to log metrics to the console.
    - This includes:
        - Type
        - Label
        - Request ID
        - Timestamp
        - Duration
        - Time to First Token
        - Cancelled
        - Completion Tokens
        - Prompt Tokens
        - Total Tokens
        - Tokens/Second
---
"""
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.metrics import LLMMetrics
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.room_io import RoomInputOptions
from livekit.plugins import deepgram, openai, silero
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime

logger = logging.getLogger("metrics-llm")
logger.setLevel(logging.INFO)

console = Console()

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class LLMMetricsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            vad=silero.VAD.load()
        )

        def sync_wrapper(metrics: LLMMetrics):
            asyncio.create_task(self.on_metrics_collected(metrics))

        self.llm.on("metrics_collected", sync_wrapper)

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


async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=LLMMetricsAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint)
    )