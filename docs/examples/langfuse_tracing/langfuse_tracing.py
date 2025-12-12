import base64
import logging
import os
from dotenv import load_dotenv

from livekit.agents import JobContext, JobProcess, cli, Agent, AgentSession, AgentServer, inference, RunContext, function_tool, metrics
from livekit.agents.telemetry import set_tracer_provider
from livekit.agents.voice import MetricsCollectedEvent
from livekit.plugins import openai,silero

logger = logging.getLogger("langfuse-trace-example")
load_dotenv()

def setup_langfuse(host: str | None = None, public_key: str | None = None, secret_key: str | None = None):
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
    host = host or os.getenv("LANGFUSE_HOST")

    if not public_key or not secret_key or not host:
        logger.warning("LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_HOST must be set for tracing")
        return

    langfuse_auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{host.rstrip('/')}/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {langfuse_auth}"

    trace_provider = TracerProvider()
    trace_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    set_tracer_provider(trace_provider)

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    setup_langfuse()

server.setup_fnc = prewarm

@function_tool
async def lookup_weather(context: RunContext, location: str) -> str:
    """Called when the user asks for weather related information.

    Args:
        location: The location they are asking for
    """

    logger.info(f"Looking up weather for {location}")

    return "sunny with a temperature of 70 degrees."


class Kelly(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="Your name is Kelly.",
            stt=inference.STT(model="deepgram/nova-3-general"),
            llm=inference.LLM(model="openai/gpt-4.1-mini"),
            tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
            tools=[lookup_weather],
        )

    async def on_enter(self):
        logger.info("Kelly is entering the session")
        self.session.generate_reply()

    @function_tool
    async def transfer_to_alloy(self) -> Agent:
        """Transfer the call to Alloy."""
        logger.info("Transferring the call to Alloy")
        return Alloy()


class Alloy(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="Your name is Alloy.",
            llm=openai.realtime.RealtimeModel(voice="alloy"),
            tools=[lookup_weather],
        )

    async def on_enter(self):
        logger.info("Alloy is entering the session")
        self.session.generate_reply()

    @function_tool
    async def transfer_to_kelly(self) -> Agent:
        """Transfer the call to Kelly."""

        logger.info("Transferring the call to Kelly")
        return Kelly()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(vad=ctx.proc.userdata["vad"])

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        logger.info(f"Metrics collected: {ev.metrics}")

    await session.start(agent=Kelly(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
