---
title: Large Context Window LLM
category: pipeline-llm
tags: [gemini_2_flash, large_context, book_analysis, war_and_peace]
difficulty: intermediate
description: Agent using Gemini 2.0 Flash to analyze War and Peace with large context window
demonstrates:
  - Loading large text files into LLM context
  - Google Gemini 2.0 Flash model for large contexts
  - Book analysis and discussion capabilities
  - Direct text quotation from context
  - Custom TTS instructions for literary tone
---

In this recipe you will load a full novel into the LLM context and discuss it with the caller. Gemini 2.0 Flash handles the long prompt; the agent quotes passages on request.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" python-dotenv
  ```

## Load configuration and logging

Load environment variables and set up logging.

```python
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, cli, Agent, AgentSession, AgentServer, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("google_llm")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Read the book into memory

Load the War and Peace text from `lib/war_and_peace.txt` so it can be embedded directly into the prompt.

```python
book_path = Path(__file__).parent / "lib" / "war_and_peace.txt"
try:
    with open(book_path, "r", encoding="utf-8") as f:
        war_and_peace_text = f.read()
except FileNotFoundError:
    logger.error(f"Could not find book at {book_path}")
    war_and_peace_text = "War and Peace text not found."
```

## Prewarm VAD and Define Entrypoint

We preload the VAD model. Inside the session, we configure the `AgentSession` with Deepgram STT, Gemini LLM (for large context), and OpenAI TTS (with custom instructions for tone).

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=deepgram.STT(),
        llm=google.LLM(model="gemini-2.5-flash"),
        tts=openai.TTS(instructions="You are a literary discussion assistant with a pleasant voice. Speak in a natural, conversational tone that conveys enthusiasm for literature."),
        vad=ctx.proc.userdata["vad"],
    )
    
    agent = Agent(
        instructions=f"""
            You are a War and Peace book club assistant. You help users discuss and understand Leo Tolstoy's novel "War and Peace."

            You can answer questions about the plot, characters, themes, historical context, and literary analysis of the book.

            Here is the complete text of the book that you can reference:

            {war_and_peace_text}

            Be concise but informative in your responses. If asked about specific passages, quote directly from the text.
        """,
    )
    # ...
```

## Start the session

Greet the user and start the session.

```python
    @session.on("session_start")
    def on_session_start():
        session.generate_reply("Welcome to the War and Peace book club! I'm here to discuss Leo Tolstoy's epic novel with you. What would you like to talk about?")

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```bash
python large_context.py console
```

## How it works

- The entire novel is embedded into the prompt at startup.
- Gemini 2.0 Flash handles the large context and can quote passages directly.
- Deepgram STT captures user questions; the LLM responds with literary analysis; TTS speaks in a friendly tone.
- Silero VAD manages turn-taking between user and agent.

## Full example

```python
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, cli, Agent, AgentSession, AgentServer, inference
from livekit.plugins import openai, google, deepgram, silero

load_dotenv()

logger = logging.getLogger("google_llm")
logger.setLevel(logging.INFO)

# Load book text once
book_path = Path(__file__).parent / "lib" / "war_and_peace.txt"
try:
    with open(book_path, "r", encoding="utf-8") as f:
        war_and_peace_text = f.read()
except FileNotFoundError:
    logger.error(f"Could not find book at {book_path}")
    war_and_peace_text = "War and Peace text not found."

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=deepgram.STT(),
        llm=google.LLM(model="gemini-2.0-flash"),
        tts=openai.TTS(instructions="You are a literary discussion assistant with a pleasant voice. Speak in a natural, conversational tone that conveys enthusiasm for literature."),
        vad=ctx.proc.userdata["vad"],
    )
    
    agent = Agent(
        instructions=f"""
            You are a War and Peace book club assistant. You help users discuss and understand Leo Tolstoy's novel "War and Peace."

            You can answer questions about the plot, characters, themes, historical context, and literary analysis of the book.

            Here is the complete text of the book that you can reference:

            {war_and_peace_text}

            Be concise but informative in your responses. If asked about specific passages, quote directly from the text.
        """,
    )
    
    @session.on("session_start")
    def on_session_start():
        session.generate_reply("Welcome to the War and Peace book club! I'm here to discuss Leo Tolstoy's epic novel with you. What would you like to talk about?")

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
