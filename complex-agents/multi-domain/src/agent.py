import asyncio
import json
import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    room_io,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# How long the agent waits for the user to return before shutting down
IDLE_TIMEOUT_SECONDS = 300  # 5 minutes


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are a helpful voice AI assistant. The user is interacting "
                "with you via voice, even if you perceive the conversation as text.\n"
                "You eagerly assist users with their questions by providing "
                "information from your extensive knowledge.\n"
                "Your responses are concise, to the point, and without any complex "
                "formatting or punctuation including emojis, asterisks, or other symbols.\n"
                "You are curious, friendly, and have a sense of humor.\n\n"
                "The user may disconnect and reconnect at any time (they might be "
                "navigating between different pages or domains). When they reconnect, "
                "continue the conversation naturally without re-introducing yourself. "
                "You remember everything from earlier in the conversation."
            ),
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="multi-domain-agent")
async def my_agent(ctx: JobContext):
    metadata = json.loads(ctx.job.metadata or "{}")
    user_id = metadata.get("user_id", "unknown")

    ctx.log_context_fields = {
        "room": ctx.room.name,
        "user_id": user_id,
    }

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="multi"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            # Keep the agent in the room when the user disconnects,
            # so they can reconnect and resume the conversation.
            close_on_disconnect=False,
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    await ctx.connect()

    # Idle timeout: shut down the agent if the user doesn't return
    idle_task: asyncio.Task | None = None

    async def _idle_shutdown():
        logger.info(f"User left, waiting {IDLE_TIMEOUT_SECONDS}s for reconnect...")
        await asyncio.sleep(IDLE_TIMEOUT_SECONDS)
        logger.info("Idle timeout reached, shutting down session.")
        session.shutdown()

    @ctx.room.on("participant_disconnected")
    def on_participant_left(participant: rtc.RemoteParticipant):
        nonlocal idle_task
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD:
            idle_task = asyncio.create_task(_idle_shutdown())

    @ctx.room.on("participant_connected")
    def on_participant_joined(participant: rtc.RemoteParticipant):
        nonlocal idle_task
        if (
            participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD
            and idle_task
            and not idle_task.done()
        ):
            idle_task.cancel()
            idle_task = None
            logger.info("User reconnected, cancelled idle timeout.")


if __name__ == "__main__":
    cli.run_app(server)
