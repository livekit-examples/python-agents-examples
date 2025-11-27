# Model Battleground – Agent 3 (Alt Stack B)

This worker hosts **Agent 3** in the model battleground demo. It runs yet another vendor stack (Deepgram + Moonshot + Rime), allowing you to compare three end‑to‑end voice pipelines in a single LiveKit room.

## Model stack

Defined in `src/agent.py`:

- **STT** – `deepgram/nova-3-general`.
- **LLM** – `moonshotai/kimi-k2-instruct`.
- **TTS** – `rime/arcana`.
- **Turn-taking** – `MultilingualModel` + Silero VAD.
- **Noise** – LiveKit `BVC` noise cancellation.

Latency budgets:

- `STT_NORMALIZATION_SECONDS` = 1.0
- `LLM_NORMALIZATION_SECONDS` = 1.0
- `TTS_NORMALIZATION_SECONDS` = 1.0

The worker converts raw durations into 0–100 “percent of budget” values that the UI renders as horizontal bar charts.

## RPC integration

Agent 3 uses the same outgoing RPC shape as Agent 2:

- `model_battleground.agent.metrics` – `AgentMetricsPayload` with `agent_id = "agent-3"`.
- `model_battleground.agent.status` – `AgentStatusPayload` when the participant connects/disconnects.
- `model_battleground.agent.transcript` – `AgentTranscriptPayload` for user‑authored text.

Every payload carries:

- `agent_id` and the agent’s `participant_identity`, so the frontend can map LiveKit identities back to the correct card.
- Stable `message_id`s that allow the dashboard to upsert final transcripts and keep ordering consistent.

This worker does not expose the dispatch RPC; it is meant to be **dispatched by Agent 1** when requested from the UI.

## Setup

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Create `.env.local` and set LiveKit credentials:

   ```bash
   LIVEKIT_URL=wss://<your-project>.livekit.cloud
   LIVEKIT_API_KEY=...
   LIVEKIT_API_SECRET=...
   ```

3. Download VAD + turn‑detection assets:

   ```bash
   uv run python src/agent.py download-files
   ```

## Running

```bash
# Local console interaction
uv run python src/agent.py console

# Room-connected worker (spawned by Agent 1)
uv run python src/agent.py dev

# Production entrypoint
uv run python src/agent.py start
```

Register this worker as `devday-battleground-agent-3` so the frontend can dispatch it by name via `model_battleground.agent.dispatch`.

## Metrics & behavior

- Uses `UsageCollector` to aggregate token usage and logs a summary on shutdown.
- `_send_metrics_snapshot` and `_send_agent_status`:
  - Wait for at least one remote participant before sending status.
  - Walk the participant list and send to the first one that supports the method, treating `UNSUPPORTED_METHOD` as a soft failure.
  - Catch and log unexpected errors instead of bubbling them into the main agent loop.