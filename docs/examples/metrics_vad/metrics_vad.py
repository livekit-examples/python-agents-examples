"""
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
"""
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
