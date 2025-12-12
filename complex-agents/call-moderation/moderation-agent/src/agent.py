from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    ModelSettings,
    RoomInputOptions,
    RoomIO,
    WorkerOptions,
    cli,
    function_tool,
    inference,
    metrics,
)
from livekit.agents.voice import RunContext
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")


GUIDELINES_PATH = Path(__file__).with_name("guidelines.md")


def _load_guidelines() -> str:
    try:
        return GUIDELINES_PATH.read_text(encoding="utf-8").strip()
    except OSError as exc:
        logger.warning("Unable to load moderation guidelines: %s", exc)
        return "Guidelines unavailable. Default to the strictest interpretation of respectful conduct."


GUIDELINES_TEXT = _load_guidelines()
VIOLATION_RPC_METHOD = "moderation.show_violation"

BASE_INSTRUCTIONS = (
    "You are a very strict moderation agent. You must actively monitor every utterance for safety or policy violations."
)

MODERATION_DIRECTIVE = (
    "You must actively monitor every utterance for safety or policy violations. "
    "When you observe content that violates LiveRide community standards, immediately call the `report_guideline_violation` tool "
    "with the category, severity (low|moderate|high), and a short summary. You do not need to respond to the user."
    "You are here to moderate, and to call tools to report violations. You do not need to respond to the user."
    "If you notice anyone ask about destination before pickup, immediately call the `report_guideline_violation` tool with the category 'destination_before_pickup' and severity 'high'."
)

ASSISTANT_INSTRUCTIONS = (
    f"{BASE_INSTRUCTIONS}\n\n{MODERATION_DIRECTIVE}\n\nLiveRide community guidelines (verbatim):\n{GUIDELINES_TEXT}"
)


@dataclass
class ModerationUserdata:
    room: rtc.Room | None = None
    target_identity: str | None = None

    async def notify_violation(self, violation: dict[str, Any]) -> None:
        room = self.room
        if room is None:
            logger.warning("violation RPC skipped: room unavailable")
            return

        local_participant = getattr(room, "local_participant", None)
        if local_participant is None:
            logger.warning("violation RPC skipped: local participant unavailable")
            return

        payload = {
            "category": violation.get("category"),
            "severity": violation.get("severity"),
            "description": violation.get("description"),
            "excerpt": violation.get("excerpt"),
            "timestamp": violation.get("timestamp"),
        }

        participants = list(getattr(room, "remote_participants", {}).values())
        if not participants:
            logger.debug("violation RPC skipped: no remote participants to notify")
            return

        delivered = False

        for participant in participants:
            identity = getattr(participant, "identity", None)
            if not identity:
                continue
            kind = getattr(participant, "kind", None)
            # Only notify non-agent participants
            if kind == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
                continue
            try:
                await local_participant.perform_rpc(
                    destination_identity=identity,
                    method=VIOLATION_RPC_METHOD,
                    payload=json.dumps(payload),
                )
                delivered = True
            except Exception:
                logger.exception(
                    "failed to emit violation RPC",
                    extra={"destination_identity": identity, "method": VIOLATION_RPC_METHOD},
                )
            finally:
                if delivered:
                    break

        if not delivered:
            logger.debug(
                "violation RPC skipped: no non-agent participants available",
                extra={"target_identity": self.target_identity},
            )


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=ASSISTANT_INSTRUCTIONS)

    async def tts_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ) -> AsyncIterable[rtc.AudioFrame]:
        # We just pass here because we don't want to use TTS
        pass

    @function_tool()
    async def report_guideline_violation(
        self,
        ctx: RunContext[ModerationUserdata],
        violation_category: str,
        description: str,
        transcript_excerpt: str | None = None,
        severity: str = "moderate",
    ) -> str:
        """Report guideline infractions to connected participants."""

        userdata = ctx.userdata
        if userdata is None:
            return "Moderation context unavailable; notification was not delivered."

        normalized_category = violation_category.strip() or "unspecified"
        normalized_severity = (severity or "moderate").strip().lower()
        if normalized_severity not in {"low", "moderate", "high"}:
            normalized_severity = "moderate"

        event: dict[str, Any] = {
            "timestamp": time.time(),
            "category": normalized_category,
            "severity": normalized_severity,
            "description": description.strip(),
            "guideline_source": GUIDELINES_PATH.name,
        }
        if transcript_excerpt:
            event["excerpt"] = transcript_excerpt.strip()

        await userdata.notify_violation(event)
        return f"Notified participants of {normalized_category} infraction ({normalized_severity})."



def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    moderation_userdata = ModerationUserdata()
    moderation_userdata.room = ctx.room

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1"),
        tts=inference.TTS(model="NO_TTS_USED"),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
        userdata=moderation_userdata,
    )

    usage_collector = metrics.UsageCollector()
    assistant = Assistant()

    room_io = RoomIO(session, room=ctx.room)
    await room_io.start()

    def _parse_target_identity() -> str | None:
        metadata = getattr(ctx.job, "metadata", "")
        if not metadata:
            return None
        try:
            payload = json.loads(metadata)
        except json.JSONDecodeError:
            logger.warning("invalid dispatch metadata for moderation agent")
            return None

        if isinstance(payload, dict):
            identity = payload.get("target_identity")
            if isinstance(identity, str) and identity.strip():
                return identity.strip()
        return None

    def _is_agent_participant(participant: rtc.RemoteParticipant | None) -> bool:
        if participant is None:
            return False
        return getattr(participant, "kind", None) == rtc.ParticipantKind.PARTICIPANT_KIND_AGENT

    def _find_agent_participant(identity: str | None = None):
        for participant in ctx.room.remote_participants.values():
            if not _is_agent_participant(participant):
                continue
            if identity and getattr(participant, "identity", None) != identity:
                continue
            return participant
        return None

    def _apply_participant_subscription(participant: rtc.RemoteParticipant | None) -> None:
        if participant is None:
            return
        should_subscribe = (
            moderation_userdata.target_identity is not None
            and participant.identity == moderation_userdata.target_identity
            and _is_agent_participant(participant)
        )
        track_publications = getattr(participant, "track_publications", {})
        for publication in track_publications.values():
            if getattr(publication, "kind", None) != rtc.TrackKind.KIND_AUDIO:
                continue
            try:
                publication.set_subscribed(should_subscribe)
            except Exception:
                logger.exception(
                    "failed to update subscription for participant %s",
                    getattr(participant, "identity", "<unknown>"),
                )

    def _apply_subscription_filters():
        for participant in ctx.room.remote_participants.values():
            _apply_participant_subscription(participant)

    def _set_target_identity(identity: str | None):
        moderation_userdata.target_identity = identity
        if identity:
            room_io.set_participant(identity)
            logger.info("moderation agent now monitoring %s", identity)
        else:
            room_io.unset_participant()
            logger.info("cleared moderation participant target")
        _apply_subscription_filters()

    async def _wait_for_agent(identity: str | None, timeout: float = 10.0):
        try:
            return await asyncio.wait_for(
                ctx.wait_for_participant(
                    identity=identity,
                    kind=rtc.ParticipantKind.PARTICIPANT_KIND_AGENT,
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            return None
        except Exception:
            logger.exception("error while waiting for agent participant")
            return None

    async def _select_initial_target():
        participant = None
        target_identity = _parse_target_identity()
        if target_identity:
            participant = _find_agent_participant(target_identity)
            if participant is None:
                participant = await _wait_for_agent(target_identity)
                if participant is None:
                    logger.warning(
                        "target identity '%s' not found; falling back to first agent participant",
                        target_identity,
                    )
        if participant is None:
            participant = _find_agent_participant()
            if participant is None:
                participant = await _wait_for_agent(None)
        if participant is None:
            logger.warning("unable to determine a participant for moderation monitoring")
            return

        identity = getattr(participant, "identity", None)
        if not identity:
            logger.warning("participant missing identity; cannot set moderation target")
            return

        _set_target_identity(identity)

    @ctx.room.on("participant_connected")
    def _on_participant_connected(participant: rtc.RemoteParticipant):
        if moderation_userdata.target_identity is None and _is_agent_participant(participant):
            identity = getattr(participant, "identity", None)
            if identity:
                _set_target_identity(identity)
                return
        _apply_participant_subscription(participant)

    @ctx.room.on("participant_disconnected")
    def _on_participant_disconnected(participant: rtc.RemoteParticipant):
        identity = getattr(participant, "identity", None)
        if identity and identity == moderation_userdata.target_identity:
            _set_target_identity(None)
            asyncio.create_task(_select_initial_target())
        else:
            _apply_subscription_filters()

    @ctx.room.on("track_published")
    def _on_track_published(
        publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
    ):
        _apply_participant_subscription(participant)

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

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

    await ctx.connect()
    await _select_initial_target()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="devday-moderation-agent", prewarm_fnc=prewarm))