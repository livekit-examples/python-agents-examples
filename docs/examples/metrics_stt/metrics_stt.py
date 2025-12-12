"""
---
title: STT Metrics
category: metrics
tags: [metrics, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to use the STT metrics to log metrics to the console.
demonstrates:
  - Using the STT metrics to log metrics to the console.
  - This includes:
    - Type
    - Label
    - Request ID
    - Timestamp
    - Duration
    - Speech ID
    - Error
---
"""

import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, inference, AgentServer, cli
from livekit.agents.metrics import STTMetrics, EOUMetrics
from livekit.plugins import silero
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime

load_dotenv()

logger = logging.getLogger("metrics-stt")
logger.setLevel(logging.INFO)

console = Console()

class STTMetricsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """
        )

    async def on_enter(self):
        def stt_wrapper(metrics: STTMetrics):
            asyncio.create_task(self.on_stt_metrics_collected(metrics))

        def eou_wrapper(metrics: EOUMetrics):
            asyncio.create_task(self.on_eou_metrics_collected(metrics))

        self.session.stt.on("metrics_collected", stt_wrapper)
        self.session.stt.on("eou_metrics_collected", eou_wrapper)
        self.session.generate_reply()

    async def on_stt_metrics_collected(self, metrics: STTMetrics) -> None:
        table = Table(
            title="[bold blue]STT Metrics Report[/bold blue]",
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
        table.add_row("Speech ID", str(metrics.speech_id))
        table.add_row("Error", str(metrics.error))
        table.add_row("Streamed", "✓" if metrics.streamed else "✗")
        table.add_row("Audio Duration", f"[white]{metrics.audio_duration:.4f}[/white]s")

        console.print("\n")
        console.print(table)
        console.print("\n")

    async def on_eou_metrics_collected(self, metrics: EOUMetrics) -> None:
        table = Table(
            title="[bold blue]End of Utterance Metrics Report[/bold blue]",
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
        table.add_row("Timestamp", timestamp)
        table.add_row("End of Utterance Delay", f"[white]{metrics.end_of_utterance_delay:.4f}[/white]s")
        table.add_row("Transcription Delay", f"[white]{metrics.transcription_delay:.4f}[/white]s")
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

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = STTMetricsAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
