import logging
import os

from dotenv import load_dotenv

import noveum_trace
from noveum_trace.integrations.livekit import (
    LiveKitLLMWrapper,
    LiveKitSTTWrapper,
    LiveKitTTSWrapper,
    extract_job_context,
    setup_livekit_tracing,
)
from livekit.agents import JobContext, JobProcess, cli, Agent, AgentSession, AgentServer, RunContext, function_tool
from livekit.plugins import cartesia, deepgram, openai, silero

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
            tools=[lookup_weather],
        )

    async def on_enter(self):
        logger.info("Kelly is entering the session")
        self.session.generate_reply()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    job_context = await extract_job_context(ctx)
    session_id = ctx.job.id

    traced_stt = LiveKitSTTWrapper(
        stt=deepgram.STT(model="nova-3", language="en-US"),
        session_id=session_id,
        job_context=job_context,
    )
    traced_llm = LiveKitLLMWrapper(
        llm=openai.LLM(model="gpt-4.1-mini"),
        session_id=session_id,
        job_context=job_context,
    )
    traced_tts = LiveKitTTSWrapper(
        tts=cartesia.TTS(model="sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        session_id=session_id,
        job_context=job_context,
    )

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=traced_stt,
        llm=traced_llm,
        tts=traced_tts,
    )

    setup_livekit_tracing(session, record=True, trace_name_prefix="livekit-example")

    await session.start(agent=Kelly(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
