# Model Battleground – Agent 2 (Alt Stack A)

This worker hosts **Agent 2** in the model battleground demo. It runs a different vendor stack from Agent 1 (Deepgram + Gemini + Cartesia), but uses the same RPC contracts so the React dashboard can compare latency and behavior side‑by‑side.

## Model stack

Configured in `src/agent.py`:

- **STT** – `deepgram/nova-3`.
- **LLM** – `google/gemini-2.5-flash-lite`.
- **TTS** – `cartesia/sonic-3` with a specific voice ID.
- **Turn-taking** – `MultilingualModel` + Silero VAD.
- **Noise** – LiveKit background voice cancellation (`BVC`), configured via `RoomInputOptions`.

All timings are normalized against a 1‑second budget for STT, LLM, and TTS (see `STT_NORMALIZATION_SECONDS`, `LLM_NORMALIZATION_SECONDS`, `TTS_NORMALIZATION_SECONDS`).

## RPC contracts

Like the other battleground workers, Agent 2 uses `livekit_ext.rpc` to expose three RPC methods that send data *out* to any interested frontend:

- `model_battleground.agent.metrics` → emits `AgentMetricsPayload` (STT/LLM/TTS labels, percent‑of‑budget value, and raw latency in ms).
- `model_battleground.agent.status` → emits `AgentStatusPayload` when the agent joins/leaves, so the UI can toggle its “connected” pill.
- `model_battleground.agent.transcript` → emits `AgentTranscriptPayload` for user utterances, letting the dashboard show agent‑specific transcript chips.

Each payload contains:

- `agent_id = "agent-2"`.
- `participant_identity` – the LiveKit identity of this agent participant.
- A stable `message_id` for transcript updates so the frontend can upsert “final” messages over “partial” ones.

Note: this worker does **not** implement the dispatch RPC; Agent 1 is responsible for dispatching Agents 2 and 3 via the LiveKit Agent Dispatch API.

## Setup

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Create `.env.local` with LiveKit credentials:

   ```bash
   LIVEKIT_URL=wss://<your-project>.livekit.cloud
   LIVEKIT_API_KEY=...
   LIVEKIT_API_SECRET=...
   ```

3. Download VAD/turn detection models on first run:

   ```bash
   uv run python src/agent.py download-files
   ```

## Running

```bash
# Local console test
uv run python src/agent.py console

# Room-connected worker (dispatched by Agent 1)
uv run python src/agent.py dev

# Production entrypoint
uv run python src/agent.py start
```

When registered as `devday-battleground-agent-2`, the frontend can dispatch this worker by calling `model_battleground.agent.dispatch` on Agent 1 with `agent_name: "devday-battleground-agent-2"`.

## Metrics and error handling

- `UsageCollector` aggregates usage across STT/LLM/TTS and logs a summary at shutdown.
- `_send_metrics_snapshot` and `_send_agent_status`:
  - Iterate remote participants and send to the first participant that understands the RPC.
  - Treat `UNSUPPORTED_METHOD` as non-fatal, so non-dashboard clients don’t break the agent.
  - Guard against network failures with structured logging.

## Customization ideas

- Swap the Deepgram / Gemini / Cartesia models for any LiveKit‑supported STT/LLM/TTS combination.
- Adjust normalization budgets per stage if you want the charts to highlight different latency targets.