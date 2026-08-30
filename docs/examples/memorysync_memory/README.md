---
title: MemorySync Long-Term Memory
category: integrations
tags: [memory, memorysync, deepgram, openai, cartesia]
difficulty: beginner
description: Gives the agent long-term memory with MemorySync, so it remembers callers across calls.
demonstrates:
  - Injecting recalled memories each turn under a hard latency budget
  - Capturing both user and assistant turns as durable memories
  - Adding a memory search tool the LLM can call on demand
---

This example gives a voice agent long-term memory backed by [MemorySync](https://memorysync.io). Tell the agent something, hang up, call back — it remembers.

Voice is the one surface where memory latency is *audible*, so the integration is built around a hard rule: recalled context is injected in `on_user_turn_completed` under a strict time budget (default 1.2 s). If the memory service is slow, the agent replies without memories — the conversation is never stalled. A background prefetch warms the next turn's recall, so the steady-state cost is close to zero.

## Prerequisites

- Add a `.env` in this directory with your LiveKit and MemorySync credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  MEMORYSYNC_API_KEY=your_memorysync_api_key
  ```
  Get a MemorySync API key at [app.memorysync.io](https://app.memorysync.io) (Settings → API Keys).
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" python-dotenv livekit-memorysync
  ```

## Run it

```bash
python memorysync_memory.py console
```

Say "My name is Alex and my favorite color is teal", exit, then start a new console session — the agent recalls both facts.

## How it works

- `memory.on_user_turn(turn_ctx, new_message)` runs inside `on_user_turn_completed` and injects a compact block of relevant memories for this turn only (it is not persisted into the LLM context, avoiding context bloat and double-learning).
- `memory.attach(session)` subscribes to `conversation_item_added` and stores both user and assistant turns as they finalize, with deterministic idempotency seeds so retries and reconnects never create duplicates. Interrupted assistant turns are stored with `interrupted: true` metadata.
- `create_memory_search_tool(memory)` gives the LLM an explicit search tool for questions like "what did I tell you last week?". Errors come back to the model as readable strings, never exceptions.
- Memory outages, quota limits, and dead networks all degrade to "no memories this turn" — the call itself is never affected.

With speech-to-speech realtime models, prefer the memory search tool over per-turn injection: `on_user_turn_completed` still fires, but injection can land after the model has started speaking.
