"""
---
title: Smart Turn Detection
category: integrations
tags: [turn_detection, end_of_turn, smart_turn, onnx, custom_model]
difficulty: intermediate
description: Use a Smart Turn end-of-turn model as the turn detector in an AgentSession.
demonstrates:
  - Passing your own turn detector to AgentSession through turn_handling
  - Loading a Smart Turn ONNX model with the smart-turn-livekit plugin
  - Reading end-of-turn probability from the detector's on_prediction callback
  - Loading the detector once in prewarm so the graph is shared across jobs
  - Setting min_silence_duration on Silero VAD so predictions are actually requested
---
"""
import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
)
from livekit.plugins import silero
from smart_turn_livekit import Prediction, SmartTurnDetector

load_dotenv()

logger = logging.getLogger("smart-turn-detection")
logger.setLevel(logging.INFO)

server = AgentServer()


def log_prediction(pred: Prediction) -> None:
    """Print every end-of-turn decision, so the model is visible in the console."""
    verdict = "complete" if pred.complete else "incomplete"
    logger.info(
        f"end of turn {pred.probability:.1%} -> {verdict} "
        f"(threshold {pred.threshold:.2f}, {pred.inference_s * 1000:.0f} ms)"
    )


def prewarm(proc: JobProcess):
    # LiveKit will not request a prediction until the VAD has seen
    # min_silence_duration + 50 ms of silence, so this is a floor rather than a
    # ceiling: 0.25 is the lowest legal value and therefore the fastest.
    proc.userdata["vad"] = silero.VAD.load(min_silence_duration=0.25)

    # Loaded once per worker process, not once per call. The model is fetched
    # from Hugging Face on first use and cached; it is an int8 ONNX graph that
    # runs on CPU, so there is nothing to schedule on a GPU.
    proc.userdata["turn_detector"] = SmartTurnDetector(
        model="smart-turn-v3",
        on_prediction=log_prediction,
    )


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=inference.TTS(
            model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        vad=ctx.proc.userdata["vad"],
        turn_handling={
            "turn_detection": ctx.proc.userdata["turn_detector"],
            # The prediction picks which of these two waits applies: a confident
            # "finished" gets min_delay, anything below the model's threshold
            # gets max_delay. The detector never ends the turn by itself.
            "endpointing": {"min_delay": 0.3, "max_delay": 2.5},
        },
    )

    agent = Agent(
        instructions=(
            "You are a helpful agent. Keep replies to two sentences at most, and "
            "end with a short question so there are turns to detect."
        )
    )

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
