"""
---
title: VAD Metrics
category: metrics
tags: [metrics, openai, assemblyai]
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
"""
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, vad
from livekit.agents.metrics import VADMetrics
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.room_io import RoomInputOptions
from livekit.plugins import silero
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime

logger = logging.getLogger("metrics-vad")
logger.setLevel(logging.INFO)

console = Console()

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class VADMetricsAgent(Agent):
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

        def sync_wrapper(event: vad.VADEvent):
            asyncio.create_task(self.on_vad_event(event))

        self.vad.on("metrics_collected", sync_wrapper)

    async def on_vad_event(self, event: vad.VADEvent):
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


async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=VADMetricsAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint)
    )