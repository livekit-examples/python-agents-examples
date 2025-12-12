import json
import logging

from dotenv import load_dotenv
from livekit import api
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    inference,
    metrics,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

MODERATION_AGENT_NAME = "devday-moderation-agent"


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are an LiveRide driver who is insistent on not picking up the passenger unless they tell you the destination before you start the trip.""",
        )

    async def on_enter(self):
        await self.session.generate_reply(
            instructions="Greet the user by asking if it's Shayne. Don't say anything else in the greeting until the user responds.",
        )

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    lk_api = api.LiveKitAPI()

    async def _close_livekit_api():
        await lk_api.aclose()

    ctx.add_shutdown_callback(_close_livekit_api)

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="228fca29-3a0a-435c-8728-5cb483251068"
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    async def _dispatch_moderation_agent():
        claims = ctx.token_claims()
        target_identity = getattr(claims, "identity", None) or getattr(
            ctx.room.local_participant, "identity", None
        )

        metadata = None
        if target_identity:
            metadata = json.dumps({"target_identity": target_identity})

        try:
            dispatch = await lk_api.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(
                    agent_name=MODERATION_AGENT_NAME,
                    room=ctx.room.name,
                    metadata=metadata,
                )
            )
            dispatch_id = getattr(dispatch, "id", None) or getattr(
                dispatch, "dispatch", None
            )
            logger.info(
                "dispatched moderation agent",
                extra={
                    "agent_name": MODERATION_AGENT_NAME,
                    "dispatch_id": dispatch_id,
                    "target_identity": target_identity,
                },
            )
        except Exception:
            logger.exception(
                "failed to dispatch moderation agent",
                extra={"agent_name": MODERATION_AGENT_NAME, "target_identity": target_identity},
            )

    await _dispatch_moderation_agent()

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="devday-driver-agent", prewarm_fnc=prewarm))
