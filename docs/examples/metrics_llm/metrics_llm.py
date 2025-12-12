"""
---
title: LLM Metrics
category: metrics
tags: [metrics, deepgram, openai, cartesia]
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
