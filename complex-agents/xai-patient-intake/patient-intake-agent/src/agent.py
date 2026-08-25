"""Compose and run the xAI patient-intake agent."""

from __future__ import annotations

import logging
from datetime import datetime

from dotenv import load_dotenv
from livekit.agents import (
    AgentServer,
    AgentSession,
    JobContext,
    TurnHandlingOptions,
    cli,
    inference,
    room_io,
)
from livekit.plugins import ai_coustics

from clinic import open_clinic
from reception import PatientIntakeAgent
from visit import Visit

logger = logging.getLogger("xai-patient-intake")

server = AgentServer()


async def on_session_end(ctx: JobContext) -> None:
    """Log which models the finished call used, and how much."""
    try:
        report = ctx.make_session_report()
    except RuntimeError as error:
        if "no AgentSession" not in str(error):
            logger.error("no usage report for this call: %s", error)
        return

    logger.info(
        "call finished",
        extra={
            "models": [usage.model for usage in report.model_usage or []],
            "usage": report.model_usage,
        },
    )


@server.rtc_session(
    agent_name="xai-patient-intake",
    on_session_end=on_session_end,
)
async def patient_intake(ctx: JobContext) -> None:
    ctx.log_context_fields = {"room": ctx.room.name}
    clinic = open_clinic(datetime.now())
    session = AgentSession[Visit](
        userdata=Visit(clinic=clinic),
        stt=inference.STT(model="xai/stt-1", language="en"),
        llm=inference.LLM(
            model="xai/grok-4.3",
            extra_kwargs={
                # A front desk answers from the chart in front of it; no thinking budget needed.
                "reasoning_effort": "none",
                "temperature": 0.3,
                "max_completion_tokens": 600,
                "parallel_tool_calls": False,
            },
        ),
        tts=inference.TTS(model="xai/tts-1", voice="carina"),
        expressive=True,
        vad=inference.VAD(),
        max_tool_steps=5,
        # Dynamic endpointing gives hesitant, incomplete speech time to continue. Both delays
        # sit well above the defaults (mode="fixed", min_delay=0.3, max_delay=2.5 under the
        # audio turn detector) and are the reason this agent feels less snappy than a
        # latency-optimized demo. That is the trade we want here: patients pause mid-sentence
        # to find a date, a medication name, or the word for a symptom, and clipping them
        # costs a whole turn to repair.
        #
        # If perceived lag is ever the complaint, min_delay is the first knob to lower. Dynamic
        # mode only adapts *upward* from the floor, so 1.2 is charged to every caller including
        # the fluent ones, while max_delay is only ever paid by someone still talking.
        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(),
            endpointing={"mode": "dynamic", "min_delay": 1.2, "max_delay": 4.0},
        ),
    )
    await session.start(
        agent=PatientIntakeAgent(clinic=clinic),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_S
                ),
            ),
        ),
    )
    await ctx.connect()


if __name__ == "__main__":
    load_dotenv(".env.local")
    cli.run_app(server)
