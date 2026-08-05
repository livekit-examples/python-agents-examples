import logging
import os

from dotenv import load_dotenv

import noveum_trace
from noveum_trace.integrations.livekit import setup_livekit_tracing
from livekit.agents import JobContext, JobProcess, cli, Agent, AgentSession, AgentServer, inference, RunContext, function_tool
from livekit.plugins import silero

logger = logging.getLogger("noveum-trace-example")
load_dotenv()


def setup_noveum(project: str | None = None, api_key: str | None = None):
    api_key = api_key or os.getenv("NOVEUM_API_KEY")
    project = project or os.getenv("NOVEUM_PROJECT", "livekit-agent-example")

    if not api_key:
        logger.warning("NOVEUM_API_KEY must be set for tracing")
        return

    noveum_trace.init(project=project, api_key=api_key)


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    setup_noveum()


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


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(vad=ctx.proc.userdata["vad"])

    setup_livekit_tracing(session, record=True, trace_name_prefix="livekit-example")

    await session.start(agent=Kelly(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
