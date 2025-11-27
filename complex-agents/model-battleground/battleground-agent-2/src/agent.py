import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Final

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    UserInputTranscribedEvent,
    WorkerOptions,
    cli,
    inference,
    metrics,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.rtc.rpc import RpcError
from livekit_ext import install_extensions
from livekit_ext.rpc import RPC, rpc_call

logger = logging.getLogger("agent")

load_dotenv(".env.local")

AGENT_ID: Final = "agent-2"
DEFAULT_STT_LABEL: Final = "STT (deepgram/nova-3)"
DEFAULT_LLM_LABEL: Final = "LLM (google/gemini-2.5-flash-lite)"
DEFAULT_TTS_LABEL: Final = "TTS (cartesia/sonic-3)"
STT_NORMALIZATION_SECONDS: Final = 1.0
LLM_NORMALIZATION_SECONDS: Final = 1.0
TTS_NORMALIZATION_SECONDS: Final = 1.0


@dataclass
class MetricDatum:
    label: str
    value: float
    latency_ms: float


@dataclass
class AgentMetricsPayload:
    agent_id: str
    stt: MetricDatum
    llm: MetricDatum
    tts: MetricDatum
    ts: float
    participant_identity: str | None
    id: str | None = None


@dataclass
class AgentTranscriptPayload:
    agent_id: str
    message_id: str
    text: str
    is_final: bool
    ts: float
    participant_identity: str | None
    speaker_id: str | None = None


@dataclass
class AgentStatusPayload:
    agent_id: str
    connected: bool
    ts: float
    participant_identity: str | None


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant. The user is interacting with you via voice, even if you perceive the conversation as text.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
            You are curious, friendly, and have a sense of humor.""",
        )
        install_extensions(self, RPC())

    @rpc_call("model_battleground.agent.metrics", model=AgentMetricsPayload)
    async def emit_metrics(self, payload: AgentMetricsPayload) -> str:
        logger.debug("sent agent metrics payload", extra={"payload": payload})
        return "ok"

    @rpc_call("model_battleground.agent.status", model=AgentStatusPayload)
    async def emit_status(self, payload: AgentStatusPayload) -> str:
        logger.debug("sent agent status payload", extra={"payload": payload})
        return "ok"

    @rpc_call("model_battleground.agent.transcript", model=AgentTranscriptPayload)
    async def emit_transcript(self, payload: AgentTranscriptPayload) -> str:
        logger.debug("sent agent transcript payload", extra={"payload": payload})
        return "ok"

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3"),
        llm=inference.LLM(model="google/gemini-2.5-flash-lite"),
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    usage_collector = metrics.UsageCollector()
    assistant = Assistant()
    metric_state = {
        "stt": MetricDatum(label=DEFAULT_STT_LABEL, value=0.0, latency_ms=0.0),
        "llm": MetricDatum(label=DEFAULT_LLM_LABEL, value=0.0, latency_ms=0.0),
        "tts": MetricDatum(label=DEFAULT_TTS_LABEL, value=0.0, latency_ms=0.0),
    }
    def _normalize_duration(seconds: float, *, limit: float) -> float:
        if limit <= 0:
            return 0.0
        scaled = max(0.0, seconds) / limit * 100.0
        return max(0.0, min(100.0, scaled))

    def _update_metric_snapshot(agent_metric: metrics.AgentMetrics) -> bool:
        if isinstance(agent_metric, metrics.EOUMetrics):
            delay = max(0.0, getattr(agent_metric, "transcription_delay", 0.0))
            metric_state["stt"] = MetricDatum(
                label=DEFAULT_STT_LABEL,
                value=_normalize_duration(delay, limit=STT_NORMALIZATION_SECONDS),
                latency_ms=delay * 1000.0,
            )
            return True
        if isinstance(agent_metric, metrics.LLMMetrics):
            ttft = max(0.0, agent_metric.ttft or 0.0)
            metric_state["llm"] = MetricDatum(
                label=DEFAULT_LLM_LABEL,
                value=_normalize_duration(ttft, limit=LLM_NORMALIZATION_SECONDS),
                latency_ms=ttft * 1000.0,
            )
            return True
        if isinstance(agent_metric, metrics.TTSMetrics):
            ttfb = max(0.0, agent_metric.ttfb or 0.0)
            metric_state["tts"] = MetricDatum(
                label=DEFAULT_TTS_LABEL,
                value=_normalize_duration(ttfb, limit=TTS_NORMALIZATION_SECONDS),
                latency_ms=ttfb * 1000.0,
            )
            return True
        return False

    def _build_payload() -> AgentMetricsPayload:
        return AgentMetricsPayload(
            agent_id=AGENT_ID,
            stt=metric_state["stt"],
            llm=metric_state["llm"],
            tts=metric_state["tts"],
            ts=time.time(),
            participant_identity=getattr(ctx.room.local_participant, "identity", None),
        )

    def _build_status_payload(*, connected: bool) -> AgentStatusPayload:
        return AgentStatusPayload(
            agent_id=AGENT_ID,
            connected=connected,
            ts=time.time(),
            participant_identity=getattr(ctx.room.local_participant, "identity", None),
        )

    def _build_transcript_payload(ev: UserInputTranscribedEvent) -> AgentTranscriptPayload:
        return AgentTranscriptPayload(
            agent_id=AGENT_ID,
            message_id=f"{AGENT_ID}-{uuid.uuid4().hex}",
            text=ev.transcript,
            is_final=ev.is_final,
            ts=time.time(),
            participant_identity=getattr(ctx.room.local_participant, "identity", None),
            speaker_id=ev.speaker_id,
        )

    def _send_metrics_snapshot(snapshot: AgentMetricsPayload) -> None:
        async def _broadcast_snapshot():
            helper = getattr(assistant.helpers, "rpc", None)
            if helper is None:
                return
            participants = list(ctx.room.remote_participants.values())
            if not participants:
                return
            for participant in participants:
                try:
                    helper.set_default_identity(participant.identity)
                    await assistant.emit_metrics(snapshot)
                    return
                except RpcError as exc:
                    if exc.code == RpcError.ErrorCode.UNSUPPORTED_METHOD:
                        continue
                    logger.exception(
                        "failed to emit agent metrics",
                        extra={"identity": participant.identity},
                        exc_info=exc,
                    )
                    return
                except Exception as exc:
                    logger.exception(
                        "unexpected failure while emitting agent metrics",
                        extra={"identity": participant.identity},
                        exc_info=exc,
                    )
                    return

        task = asyncio.create_task(_broadcast_snapshot())

        def _log_result(future: asyncio.Task):
            if future.cancelled():
                return
            exc = future.exception()
            if exc:
                logger.exception("failed to emit agent metrics", exc_info=exc)

        task.add_done_callback(_log_result)

    def _send_agent_status(*, connected: bool) -> None:
        async def _broadcast_status():
            helper = getattr(assistant.helpers, "rpc", None)
            if helper is None:
                logger.debug("rpc helper not installed; skipping agent status broadcast")
                return

            payload = _build_status_payload(connected=connected)
            loop = asyncio.get_running_loop()
            deadline = loop.time() + 5.0

            while True:
                participants = list(ctx.room.remote_participants.values())
                if not participants:
                    if loop.time() >= deadline:
                        logger.debug("timed out waiting for participants to send agent status")
                        return
                    await asyncio.sleep(0.2)
                    continue

                for participant in participants:
                    try:
                        helper.set_default_identity(participant.identity)
                        await assistant.emit_status(payload)
                        logger.debug(
                            "emitted agent status",
                            extra={"identity": participant.identity, "payload": payload},
                        )
                        return
                    except RpcError as exc:
                        if exc.code == RpcError.ErrorCode.UNSUPPORTED_METHOD:
                            logger.debug(
                                "participant does not support agent status rpc",
                                extra={"identity": participant.identity},
                            )
                            continue
                        logger.exception(
                            "failed to emit agent status",
                            extra={"identity": participant.identity},
                            exc_info=exc,
                        )
                        return
                    except Exception as exc:
                        logger.exception(
                            "unexpected failure while emitting agent status",
                            extra={"identity": participant.identity},
                            exc_info=exc,
                        )
                        return

                logger.debug("no participants accepted agent status rpc payload")
                return

        task = asyncio.create_task(_broadcast_status())

        def _log_result(future: asyncio.Task):
            if future.cancelled():
                return
            exc = future.exception()
            if exc:
                logger.exception("failed to emit agent status", exc_info=exc)

        task.add_done_callback(_log_result)

    def _send_agent_transcript(ev: UserInputTranscribedEvent) -> None:
        if not ev.is_final:
            return

        payload = _build_transcript_payload(ev)

        async def _broadcast_transcript():
            helper = getattr(assistant.helpers, "rpc", None)
            if helper is None:
                logger.debug("rpc helper not installed; skipping agent transcript broadcast")
                return

            participants = list(ctx.room.remote_participants.values())
            if not participants:
                logger.debug("no remote participants available for transcript broadcast")
                return

            for participant in participants:
                try:
                    helper.set_default_identity(participant.identity)
                    await assistant.emit_transcript(payload)
                    logger.debug(
                        "emitted agent transcript",
                        extra={"identity": participant.identity, "payload": payload},
                    )
                    return
                except RpcError as exc:
                    if exc.code == RpcError.ErrorCode.UNSUPPORTED_METHOD:
                        logger.debug(
                            "participant does not support agent transcript rpc",
                            extra={"identity": participant.identity},
                        )
                        continue
                    logger.exception(
                        "failed to emit agent transcript",
                        extra={"identity": participant.identity},
                        exc_info=exc,
                    )
                    return
                except Exception as exc:
                    logger.exception(
                        "unexpected failure while emitting agent transcript",
                        extra={"identity": participant.identity},
                        exc_info=exc,
                    )
                    return

            logger.debug("no participants accepted agent transcript rpc payload")

        task = asyncio.create_task(_broadcast_transcript())

        def _log_result(future: asyncio.Task):
            if future.cancelled():
                return
            exc = future.exception()
            if exc:
                logger.exception("failed to emit agent transcript", exc_info=exc)

        task.add_done_callback(_log_result)

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)
        if _update_metric_snapshot(ev.metrics):
            snapshot = _build_payload()
            _send_metrics_snapshot(snapshot)

    @session.on("user_input_transcribed")
    def _on_user_input_transcribed(ev: UserInputTranscribedEvent):
        _send_agent_transcript(ev)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=assistant,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    _send_agent_status(connected=True)

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="devday-battleground-agent-2", prewarm_fnc=prewarm))
