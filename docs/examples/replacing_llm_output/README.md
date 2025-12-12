---
title: LLM Output Replacement
category: pipeline-llm
tags: [deepseek, groq, deepgram, openai]
difficulty: intermediate
description: Replaces Deepseek thinking tags with custom messages for TTS
demonstrates:
  - Groq integration with Deepseek model
  - Real-time stream processing
  - Text replacement in LLM output
  - Custom llm_node for output manipulation
  - Handling model-specific output formats
---

This example shows how to replace Deepseek thinking tags (`<think>` and `</think>`) with custom messages before sending to TTS. This prevents the TTS engine from reading out the model's internal thinking process.

## Prerequisites

- Add a `.env` in this directory with your LiveKit and API credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  GROQ_API_KEY=your_groq_api_key
  DEEPGRAM_API_KEY=your_deepgram_api_key
  OPENAI_API_KEY=your_openai_api_key
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero,openai,deepgram]" python-dotenv
  ```

## Load environment, logging, and define an AgentServer

Set up dotenv, logging, and initialize the AgentServer.

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession
from livekit.plugins import openai, deepgram, silero

load_dotenv()

logger = logging.getLogger("replacing-llm-output")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Define the agent with custom llm_node

Create an agent that uses a custom `llm_node` to intercept and process the LLM output stream. The agent stores its own LLM instance and overrides the `llm_node` method to filter out thinking tags.

```python
class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful agent."
        )
        self._llm = openai.LLM.with_groq(model="deepseek-r1-distill-llama-70b")

    async def on_enter(self):
        self.session.generate_reply()
```

## Implement the stream processing llm_node

Override the `llm_node` method to intercept the LLM stream. Process each chunk, replacing `<think>` with nothing and `</think>` with a transition phrase.

```python
    async def llm_node(self, chat_ctx, tools, model_settings=None):
        async def process_stream():
            async with self._llm.chat(chat_ctx=chat_ctx, tools=tools, tool_choice=None) as stream:
                async for chunk in stream:
                    if chunk is None:
                        continue

                    content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
                    if content is None:
                        yield chunk
                        continue

                    processed_content = content.replace("<think>", "").replace("</think>", "Okay, I'm ready to respond.")
                    print(f"Original: {content}, Processed: {processed_content}")

                    if processed_content != content:
                        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content'):
                            chunk.delta.content = processed_content
                        else:
                            chunk = processed_content

                    yield chunk

        return process_stream()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process to reduce connection latency.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define the rtc session entrypoint

Create the session with Deepgram STT, OpenAI TTS, and prewarmed VAD. The LLM is handled internally by the agent's custom `llm_node`.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=deepgram.STT(),
        tts=openai.TTS(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=SimpleAgent(), room=ctx.room)
    await ctx.connect()
```

## Run the server

Start the agent server with the CLI runner.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```bash
python replacing_llm_output.py console
```

## How it works

1. The agent uses Groq's API with the Deepseek model which produces `<think>` tags during reasoning.
2. The custom `llm_node` intercepts the streaming LLM output before it reaches TTS.
3. Thinking tags are stripped or replaced with a transition phrase ("Okay, I'm ready to respond.").
4. The processed stream is passed to TTS, which only speaks the actual response.
5. This pattern can be adapted to filter any model-specific output formatting.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession
from livekit.plugins import openai, deepgram, silero

load_dotenv()

logger = logging.getLogger("replacing-llm-output")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful agent."
        )
        self._llm = openai.LLM.with_groq(model="deepseek-r1-distill-llama-70b")

    async def on_enter(self):
        self.session.generate_reply()

    async def llm_node(self, chat_ctx, tools, model_settings=None):
        async def process_stream():
            async with self._llm.chat(chat_ctx=chat_ctx, tools=tools, tool_choice=None) as stream:
                async for chunk in stream:
                    if chunk is None:
                        continue

                    content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
                    if content is None:
                        yield chunk
                        continue

                    processed_content = content.replace("<think>", "").replace("</think>", "Okay, I'm ready to respond.")
                    print(f"Original: {content}, Processed: {processed_content}")

                    if processed_content != content:
                        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content'):
                            chunk.delta.content = processed_content
                        else:
                            chunk = processed_content

                    yield chunk

        return process_stream()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=deepgram.STT(),
        tts=openai.TTS(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=SimpleAgent(), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
