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

A voice agent has to decide, at every pause, whether the caller has finished speaking or is only thinking. `AgentSession` does not restrict you to the built-in detector: `turn_handling["turn_detection"]` accepts any object implementing the streaming turn-detector protocol, so you can run a model of your own.

This example runs [Smart Turn](https://github.com/pipecat-ai/smart-turn), an open end-of-turn model, through the `smart-turn-livekit` plugin. The plugin loads any Smart Turn ONNX graph and adapts it to that protocol, so swapping the model is a one-line change. Every decision is printed to the console, which is the point of the example: you can watch the model hesitate.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" smart-turn-livekit python-dotenv
  ```

The model is downloaded from Hugging Face on first use and cached. It is an int8 ONNX graph of a few megabytes and runs on CPU.

## Load environment, logging, and define an AgentServer

```python
import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent, AgentServer, AgentSession, JobContext, JobProcess, cli, inference,
)
from livekit.plugins import silero
from smart_turn_livekit import Prediction, SmartTurnDetector

load_dotenv()

logger = logging.getLogger("smart-turn-detection")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Log every end-of-turn decision

The detector calls `on_prediction` with the probability, the threshold it was compared against, and how long inference took. Printing it is the cheapest way to see the model working.

```python
def log_prediction(pred: Prediction) -> None:
    """Print every end-of-turn decision, so the model is visible in the console."""
    verdict = "complete" if pred.complete else "incomplete"
    logger.info(
        f"end of turn {pred.probability:.1%} -> {verdict} "
        f"(threshold {pred.threshold:.2f}, {pred.inference_s * 1000:.0f} ms)"
    )
```

## Load the VAD and the detector once, in prewarm

Both are reused across jobs, so neither belongs in the entrypoint.

The VAD setting matters. LiveKit will not ask the detector for a prediction until the VAD reports `min_silence_duration + 50 ms` of silence, so this value is a floor on how quickly a turn can end, not a ceiling. Silero's default is 0.55; 0.25 is the lowest legal value and therefore the fastest.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load(min_silence_duration=0.25)

    proc.userdata["turn_detector"] = SmartTurnDetector(
        model="smart-turn-v3",
        on_prediction=log_prediction,
    )


server.setup_fnc = prewarm
```

## Wire the detector into the session

`turn_handling["turn_detection"]` takes the detector object directly — no registration, no subclassing.

Note what the prediction is used for: it does not end the turn. It selects which of the two endpointing delays applies — a confident "finished" waits `min_delay`, anything below the model's threshold waits `max_delay`. A wrong prediction costs a slightly wrong pause, not an interruption.

```python
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
```

## Running the example

```bash
python smart_turn_detection.py dev
```

Connect with any LiveKit frontend, speak, and pause in the middle of a sentence. The console prints a line per decision:

```
end of turn 1.2%  -> incomplete (threshold 0.50, 55 ms)
end of turn 94.5% -> complete   (threshold 0.50, 58 ms)
```

A low probability mid-sentence means the agent waits instead of cutting in.

## Choosing a model

`model=` selects which Smart Turn graph the plugin loads:

| model | notes |
|---|---|
| `smart-turn-v3` | upstream weights, covering a range of languages — the default here |
| `smart-turn-v3-fp32` | the same weights at full precision |
| `smart-turn-tamil-tiny` | example of a fine-tune trained for a single language |

Pass `model_path=` instead to load your own `.onnx` file. Fine-tuning Smart Turn for a language the upstream weights do not cover is the usual reason to reach for this — the plugin loads the result the same way, and nothing else in the agent changes.

- Plugin: https://github.com/santhosh-005/smart-turn-livekit
- Upstream model: https://github.com/pipecat-ai/smart-turn
