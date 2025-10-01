"""
---
title: TTS Metrics
category: metrics
tags: [metrics, openai, assemblyai]
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
"""
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.metrics import TTSMetrics
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.room_io import RoomInputOptions
from livekit.plugins import silero
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime

logger = logging.getLogger("metrics-tts")
logger.setLevel(logging.INFO)

console = Console()

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class TTSMetricsAgent(Agent):
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

        def sync_wrapper(metrics: TTSMetrics):
            asyncio.create_task(self.on_metrics_collected(metrics))

        self.tts.on("metrics_collected", sync_wrapper)

    async def on_metrics_collected(self, metrics: TTSMetrics) -> None:
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


async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=TTSMetricsAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint)
    )