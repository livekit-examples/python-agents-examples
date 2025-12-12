from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv
from livekit import api
from livekit.agents import (
    Agent,
    AgentSession,
    AgentTask,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    function_tool,
    inference,
    metrics,
)
from livekit.agents.voice import RunContext
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("survey_agent")

load_dotenv(".env.local")


@dataclass(frozen=True)
class SurveyQuestion:
    id: str
    prompt: str


SURVEY_QUESTIONS: tuple[SurveyQuestion, ...] = (
    SurveyQuestion(
        id="ride_frequency",
        prompt="How many times per week do you typically request a rideshare with us?",
    ),
    SurveyQuestion(
        id="recent_rating",
        prompt="On a scale from 1 to 5, how would you rate your most recent rideshare",
    ),
    SurveyQuestion(
        id="favorite_feature",
        prompt="What is your favorite feature of the service right now?",
    ),
    SurveyQuestion(
        id="improvement",
        prompt="What is one thing we could improve before your next rideshare",
    ),
    SurveyQuestion(
        id="refer_friend",
        prompt="Would you recommend us to a friend, and why or why not?",
    ),
)

QUESTION_GUIDE = "\n".join(f"- {q.id}: {q.prompt}" for q in SURVEY_QUESTIONS)

ASSISTANT_INSTRUCTIONS = f"""
You are a friendly post-call survey agent for LiveRide.
Ask each of the following questions one at a time and in order.
After the caller answers each question, immediately call `record_survey_response` with the matching `question_id` and a concise summary of their answer.
Do not skip or combine questions. Keep the conversation upbeat and brief, and avoid enumerated lists when speaking.
Once all questions are answered and recorded, thank the caller, let them know the survey is complete, and end the call.

Survey questions:\n{QUESTION_GUIDE}
""".strip()


@dataclass
class SurveyUserdata:
    livekit_api: api.LiveKitAPI
    room_name: str
    metadata_cache: str | None = None
    metadata_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    responses: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._question_lookup = {q.id: q for q in SURVEY_QUESTIONS}

    async def record_response(self, question_id: str, answer: str) -> bool:
        question = self._question_lookup.get(question_id)
        if question is None:
            raise ValueError(
                f"Unknown question_id '{question_id}'. Use the IDs listed in the system instructions."
            )

        normalized_answer = answer.strip()
        if not normalized_answer:
            raise ValueError("Survey answer cannot be empty.")

        async with self.metadata_lock:
            timestamp = time.time()
            self.responses[question_id] = {
                "question_id": question.id,
                "question": question.prompt,
                "answer": normalized_answer,
                "timestamp": timestamp,
            }
            metadata_payload = self._build_metadata_payload(timestamp)
            await self.livekit_api.room.update_room_metadata(
                api.UpdateRoomMetadataRequest(room=self.room_name, metadata=metadata_payload)
            )
            return len(self.responses) >= len(SURVEY_QUESTIONS)

    def _build_metadata_payload(self, timestamp: float) -> str:
        cache = self.metadata_cache
        if cache:
            try:
                base = json.loads(cache)
                if not isinstance(base, dict):
                    base = {"previous_metadata": cache}
            except json.JSONDecodeError:
                base = {"previous_metadata": cache}
        else:
            base = {}

        responses = [
            self.responses[q.id]
            for q in SURVEY_QUESTIONS
            if q.id in self.responses
        ]

        base["survey"] = {
            "total": len(SURVEY_QUESTIONS),
            "answered": len(self.responses),
            "responses": responses,
            "last_updated_epoch": timestamp,
        }

        metadata = json.dumps(base)
        self.metadata_cache = metadata
        return metadata


class SurveyQuestionTask(AgentTask[None]):
    def __init__(self, question: SurveyQuestion, *, is_last: bool) -> None:
        self.question = question
        self._is_last = is_last
        super().__init__(
            instructions=(
                f"Conduct the survey for question_id '{question.id}'. "
                "Ask it conversationally, listen for the caller's answer, then call "
                f"`record_survey_response` with question_id '{question.id}' and a concise summary. "
                "Do not move on to other topics or questions."
            ),
        )

    async def on_enter(self):
        await self.session.generate_reply(
            instructions=f"Ask this question: {self.question.prompt}"
        )

    @function_tool()
    async def record_survey_response(
        self,
        ctx: RunContext[SurveyUserdata],
        question_id: str,
        answer_summary: str,
    ) -> str:
        """Record a caller's answer to a survey question."""
        userdata = ctx.userdata
        if userdata is None:
            return "Survey context unavailable."

        if question_id != self.question.id:
            return f"Use the expected question_id '{self.question.id}'."

        try:
            completed = await userdata.record_response(question_id, answer_summary)
        except ValueError as exc:
            return str(exc)

        self.complete(None)
        if completed and self._is_last:
            return "Recorded the final answer. Thank the caller and end the survey."

        return "Recorded the answer. Acknowledge and continue."


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=ASSISTANT_INSTRUCTIONS)

    async def on_enter(self):
        await self.session.generate_reply(
            instructions="Greet the caller and explain you'll ask a short survey in order."
        )

        for idx, question in enumerate(SURVEY_QUESTIONS):
            task = SurveyQuestionTask(question, is_last=idx == len(SURVEY_QUESTIONS) - 1)
            await task

        await self.session.generate_reply(
            instructions="Thank the caller, confirm the survey is complete, and end the call."
        )
        self.session.shutdown()




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

    survey_userdata = SurveyUserdata(
        livekit_api=lk_api,
        room_name=ctx.room.name,
        metadata_cache=getattr(ctx.room, "metadata", None),
    )

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
        userdata=survey_userdata,
    )

    usage_collector = metrics.UsageCollector()
    assistant = Assistant()

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


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="devday-survey-agent", prewarm_fnc=prewarm))
