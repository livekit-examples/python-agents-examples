---
title: Noveum Tracing
category: metrics
tags: [metrics, openai, deepgram, cartesia]
difficulty: intermediate
description: Shows how to use Noveum Trace, a community-maintained integration, to trace the agent session.
demonstrates:
  - Using setup_livekit_tracing to trace an AgentSession with Noveum Trace.
  - Wrapping STT/TTS/LLM providers for per-utterance audio and per-call LLM capture.
  - Configuring record=False for privacy-sensitive deployments.
---

This example shows how to trace a LiveKit agent session with
[Noveum Trace](https://github.com/Noveum/noveum-trace), a community-maintained
observability integration. It captures AgentSession events, STT/TTS/LLM data, tool
calls, conversation history, and (optionally) audio, and exports them to
[Noveum](https://noveum.ai).

## Prerequisites

- Add a `.env` in this directory with your LiveKit, Noveum, and provider credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  NOVEUM_API_KEY=your_noveum_api_key
  DEEPGRAM_API_KEY=your_deepgram_api_key
  OPENAI_API_KEY=your_openai_api_key
  CARTESIA_API_KEY=your_cartesia_api_key
  ```
- Install dependencies:
  ```bash
  pip install "noveum-trace[livekit]" "livekit-agents[silero]" livekit-plugins-deepgram livekit-plugins-openai livekit-plugins-cartesia python-dotenv
  ```

## Run it

```bash
python noveum_tracing.py console
```

## How it works

- `noveum_trace.init()` configures the Noveum project and API key.
- `LiveKitSTTWrapper`, `LiveKitTTSWrapper`, and `LiveKitLLMWrapper` wrap the
  STT/TTS/LLM providers passed to `AgentSession`; the STT/TTS wrappers capture
  per-utterance audio and transcripts, and the LLM wrapper captures full chat
  context, response text, token usage, and timing per call.
- `setup_livekit_tracing(session, record=True, trace_name_prefix="livekit-example")`
  attaches session-level tracing; every turn, session event, and tool call is
  exported as a trace, and `record=True` uploads the full conversation audio at
  session end.
- **Privacy note:** `record=True` captures full conversation audio, and the
  STT/TTS wrappers capture per-utterance audio. Pass `record=False` and skip the
  wrappers for privacy-sensitive deployments; text/transcript capture is likewise
  configurable.

## Compatibility

Requires Python 3.10+ and `livekit-agents >= 1.0`. Tested with released
`noveum-trace` 1.5.21. Noveum Trace is maintained by
[Noveum](https://github.com/Noveum) (community integration, not officially part of
LiveKit) — see the [integration docs](https://noveum.ai/en/docs/integration-examples/livekit/overview),
[GitHub repository](https://github.com/Noveum/noveum-trace), and
[PyPI package](https://pypi.org/project/noveum-trace/).

## Full example

```python
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
```
