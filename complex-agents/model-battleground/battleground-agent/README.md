# Model Battleground – Agent 1 (Baseline)

This worker hosts **Agent 1**, the baseline voice assistant in the model battleground demo. It uses a single model stack (AssemblyAI + GPT‑4.1‑mini + Inworld TTS), publishes real‑time metrics and transcripts over LiveKit RPC, and exposes a dispatch endpoint the frontend uses to spin up the other agents.

## Role in the battleground

- Acts as the **always‑on** worker: when a room is created, this is the agent that joins by default.
- Exposes `model_battleground.agent.dispatch`, so the React dashboard can ask it to launch the other agents (`devday-battleground-agent-2` and `devday-battleground-agent-3`) into the same room via the Agent Dispatch API.
- Streams normalized performance metrics for STT, LLM, and TTS as `model_battleground.agent.metrics` RPC payloads so the UI can render per‑agent latency bars.
- Emits connection state via `model_battleground.agent.status` and incremental user transcript snippets via `model_battleground.agent.transcript`, which the frontend uses to route chat bubbles to the correct column.

## Model stack

Configured in `src/agent.py`:

- **STT** – `assemblyai/universal-streaming` (English), tracked via `EOUMetrics.transcription_delay`.
- **LLM** – `openai/gpt-4.1-mini`.
- **TTS** – `inworld/inworld-tts-1-max`.
- **Turn-taking** – `MultilingualModel` + Silero VAD for fast barge‑in.
- **Noise** – LiveKit background voice cancellation (`BVC`).

The low‑latency expectations for each stage are encoded as:

- `STT_NORMALIZATION_SECONDS` = 0.5
- `LLM_NORMALIZATION_SECONDS` = 1.0
- `TTS_NORMALIZATION_SECONDS` = 0.5

These bounds are used to convert raw seconds into a 0–100 “percent of budget used” value for the UI.

## RPC payloads

Agent 1 uses the `livekit_ext.rpc` helper to install three RPC “methods” on itself:

- `emit_metrics(payload: AgentMetricsPayload)` → sent to any participant that has registered `model_battleground.agent.metrics`.
- `emit_status(payload: AgentStatusPayload)` → sent when the agent joins/leaves so the UI can mark the card as connected.
- `emit_transcript(payload: AgentTranscriptPayload)` → sent on `UserInputTranscribedEvent` so the dashboard sees interim/final user utterances.

Each payload includes:

- `agent_id` – `"agent-1"` for this worker.
- `participant_identity` – the LiveKit identity for the agent participant.
- Per‑stage labels + latencies (`MetricDatum`), plus transcript metadata (`message_id`, `is_final`, `speaker_id`, `ts`).

## Dispatch endpoint

`entrypoint` constructs a single `LiveKitAPI` client and implements `_handle_dispatch_rpc`, which:

- Accepts a JSON payload with `agent_name` (e.g. `devday-battleground-agent-2`) and optional `metadata` from the frontend.
- Calls `agent_dispatch.create_dispatch` to bring the requested agent into the existing room.
- Returns `{ success: true }` or `{ success: false, error }` back to the caller over RPC.

The React app calls this by performing an RPC to `model_battleground.agent.dispatch` on the Agent 1 participant.

## Setup

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Create `.env.local` with your LiveKit credentials:

   ```bash
   LIVEKIT_URL=wss://<your-project>.livekit.cloud
   LIVEKIT_API_KEY=...
   LIVEKIT_API_SECRET=...
   ```

3. Download VAD + turn detector models (first run):

   ```bash
   uv run python src/agent.py download-files
   ```

## Running

Use the usual LiveKit Agents commands:

```bash
# Talk to Agent 1 in your terminal
uv run python src/agent.py console

# Run as a room-connected worker (used by the dashboard)
uv run python src/agent.py dev

# Production entrypoint
uv run python src/agent.py start
```

`cli.run_app` registers this worker as the primary battleground agent. The frontend assumes Agent 1 is present and will use it to dispatch Agents 2 and 3.

## Metrics & logging

- `UsageCollector` subscribes to `metrics_collected` events and logs aggregate usage when the worker shuts down.
- `_send_metrics_snapshot` and `_send_agent_status` are careful to:
  - Only broadcast to participants that actually implement the corresponding RPC.
  - Log and swallow `UNSUPPORTED_METHOD` errors so non-dashboard clients don’t break the agent.