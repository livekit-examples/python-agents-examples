# Call Moderation – Driver Agent

This directory contains the LiveRide **driver** persona that kicks off every call in the call-moderation demo. Esteban (the driver) chats with the rider, insists on knowing the destination before pickup, and automatically dispatches a separate moderation agent that shadows the conversation.

## What this worker does

- Boots an `AgentSession` with AssemblyAI streaming STT, GPT‑4.1‑mini for reasoning, Cartesia Sonic‑3 for voice, Silero VAD, and multilingual turn detection for snappy barge-in handling (`src/agent.py`).
- Applies LiveKit’s background voice cancellation so the rider hears clear audio even from a noisy street.
- Uses `preemptive_generation` so the LLM can start speaking as soon as it has enough context.
- Immediately dispatches the moderation worker (`devday-moderation-agent`) via the LiveKit Agent Dispatch API, passing along the driver’s participant identity so the moderator knows whose audio to monitor.
- Collects usage metrics via `UsageCollector` and logs a summary when the worker shuts down.

## Requirements

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) or another PEP 517 runner for dependencies
- LiveKit Cloud project or self-hosted LiveKit server with API key/secret
- Access to the models configured in `AgentSession` (AssemblyAI, OpenAI, Cartesia)

## Setup

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Copy `.env.example` to `.env.local` and set your LiveKit credentials:

   ```bash
   LIVEKIT_URL=wss://<your-project>.livekit.cloud
   LIVEKIT_API_KEY=...
   LIVEKIT_API_SECRET=...
   ```

   Use `lk cloud auth && lk app env -w -d .env.local` if you prefer the CLI helper.

3. (First run only) Download the VAD/turn-detection assets:

   ```bash
   uv run python src/agent.py download-files
   ```

## Running the driver

Pick the entrypoint that matches your workflow:

```bash
# Talk to Esteban in your terminal
uv run python src/agent.py console

# Launch the worker so web clients can join via LiveKit
uv run python src/agent.py dev

# Production-style start (same agent, wrapped for worker pools)
uv run python src/agent.py start
```

The worker registers itself as `devday-driver-agent` (see `cli.run_app(...)`). Make sure that name matches whatever your frontend or dispatch API expects.

## Moderation hand-off

- `MODERATION_AGENT_NAME` is set to `devday-moderation-agent`. The driver uses the LiveKit REST API (`LiveKitAPI.agent_dispatch.create_dispatch`) to invoke that worker into the same room.
- The driver attaches the target participant identity to the dispatch metadata so the moderator can selectively subscribe to the driver’s track.
- If dispatching fails the driver logs the error but continues serving the rider.

## Observability

- `UsageCollector` records LLM/STT/TTS token usage from `metrics_collected` events.
- Structured fields (`ctx.log_context_fields`) add the room name to every log line.
- Shutdown callbacks close the LiveKit REST client and emit a usage summary.

## Testing

Basic pytest scaffolding lives under `tests/`. Run them with:

```bash
uv run pytest
```

## Customization ideas

- Update `Assistant.instructions` if you want a different persona or playbook.
- Swap `MODERATION_AGENT_NAME` to dispatch a different coaching or compliance agent.
- Edit the model choices inside `AgentSession` to try faster/cheaper models or LiveKit’s Realtime API.
- Extend `_dispatch_moderation_agent` to include more metadata (trip ID, rider ID, etc.) that the moderator can use for routing.
