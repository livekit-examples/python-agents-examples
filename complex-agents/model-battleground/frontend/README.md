# Model Battleground Frontend

This Next.js app is the **model battleground dashboard**. It connects to a LiveKit room, talks to Agent 1, and visualizes three different voice stacks (Agents 1–3) side‑by‑side with live latency charts, status indicators, and transcripts.

## Highlights

- **Three‑column comparison view** – `SessionView` renders one `AgentCard` per worker (Agent 1, 2, 3) with:
  - live STT / LLM / TTS latency bars,
  - streaming transcripts,
  - connection state, and
  - a “Dispatch Agent” button for the secondary stacks.
- **RPC‑driven metrics** – listens for `model_battleground.agent.metrics`, `model_battleground.agent.status`, and `model_battleground.agent.transcript` RPCs, then updates UI state per agent.
- **Dynamic identity mapping** – maintains a `participant_identity → agent_id` map so transcripts and metrics are always attributed to the right card even if identities shift.
- **Optimized subscriptions** – only subscribes to media tracks from the highlighted agent’s participant(s) so bandwidth and CPU stay focused on the model you’re inspecting.

## Prerequisites

- Node.js 20+
- [pnpm 9](https://pnpm.io/)
- LiveKit project credentials with Agent Dispatch enabled
- All three backend workers running (`battleground-agent`, `battleground-agent-2`, `battleground-agent-3`)

## Setup

1. Install dependencies:

   ```bash
   pnpm install
   ```

2. Configure environment:

   ```bash
   cp .env.example .env.local
   # then set LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
   ```

3. Start the dev server:

   ```bash
   pnpm dev
   ```

4. In separate terminals, run the agents (at minimum Agent 1; Agents 2/3 can be dispatched on demand):

   ```bash
   # Agent 1
   cd ../battleground-agent
   uv run python src/agent.py dev

   # Agent 2
   cd ../battleground-agent-2
   uv run python src/agent.py dev

   # Agent 3
   cd ../battleground-agent-3
   uv run python src/agent.py dev
   ```

5. Open http://localhost:3000, click **Start call**, and begin speaking; the dashboard will show metrics as soon as agents emit RPCs.

## How the dashboard works

- `AGENT_CARD_DEFINITIONS` in `components/app/session-view.tsx` encodes:
  - internal ids (`agent-1`, `agent-2`, `agent-3`),
  - display names,
  - dispatch target names (e.g. `devday-battleground-agent-2`),
  - initial metric placeholders, and
  - any known participant identities.
- When the room connects:
  - `SessionView` registers RPC handlers for:
    - `model_battleground.agent.metrics` → updates `agentMetrics` and marks the agent as connected.
    - `model_battleground.agent.status` → toggles the “connected” pill and updates `identityToAgentId`.
    - `model_battleground.agent.transcript` → appends/updates per‑agent transcript logs.
  - Transcripts from the LiveKit components (`useChatMessages`) are merged with the per‑agent logs so each card gets the right combination of system + user messages.
- Dispatching:
  - Clicking “Dispatch Agent” on Agents 2 or 3 calls `dispatchAgent`, which sends a `model_battleground.agent.dispatch` RPC to Agent 1 along with the target `agent_name`.
  - On success, the dashboard marks the target agent as active and starts expecting metrics/status/transcripts for it.
- Subscription control:
  - A background effect recalculates which remote participants belong to the highlighted or active agent and toggles track subscription via `RemoteTrackPublication.setSubscribed`.

## Key files

- `components/app/session-view.tsx` – core three‑card layout, RPC handlers, dispatch logic, and subscription management.
- `components/app/agent-card.tsx` – presentational component for metrics, messages, and dispatch state.
- `components/livekit/agent-control-bar/*` – mic + chat controls, shared with other demos.
- `hooks/useChatMessages.ts` – pulls transcript events from LiveKit’s React components.

## Build & deploy

```bash
pnpm build
pnpm start
```

Serve over HTTPS so browsers grant mic access, and set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` in your hosting environment. Make sure the agent names in LiveKit Cloud match the dispatch targets defined in `AGENT_CARD_DEFINITIONS`.

## Troubleshooting

- **Metrics don’t show up** – verify each agent emits the `model_battleground.agent.metrics` RPC (check worker logs) and that the browser registered handlers after the room connected.
- **Dispatch fails** – ensure Agent 1 is running and has the `model_battleground.agent.dispatch` RPC wired to the LiveKit Agent Dispatch API; also confirm the `agent_name` strings match the workers’ `agent_name`/`name` settings.
- **Wrong transcripts under a card** – check `participantIdentities` in `AGENT_CARD_DEFINITIONS` or watch the `identityToAgentId` mapping; adjust the identity hints if your agent identities differ.*** End Patch  ***!
