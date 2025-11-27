# Model Battleground Demo

The model battleground is a multi‑agent LiveKit experience that lets you compare three different voice stacks side‑by‑side. A single dashboard shows how each agent performs (STT, LLM, TTS latency) while you talk, and you can dispatch or disconnect agents in real time.

## Repo layout

| Directory | Description |
| --- | --- |
| `battleground-agent` | Agent 1 – baseline stack (AssemblyAI + GPT‑4.1‑mini + Inworld TTS) and the dispatch RPC used to spawn other agents. |
| `battleground-agent-2` | Agent 2 – alternative stack A (Deepgram + Gemini + Cartesia) that mirrors the same metrics/transcript RPCs. |
| `battleground-agent-3` | Agent 3 – alternative stack B (Deepgram + Moonshot + Rime) with identical RPC contracts. |
| `frontend` | Next.js dashboard that renders three agent cards with live metrics, transcripts, and dispatch controls. |

Each directory has its own README with further details and setup instructions.

## Quick start

1. **Prepare LiveKit**
   - Create (or reuse) a LiveKit Cloud project.
   - Collect `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET`.
   - Ensure Agent Dispatch is enabled.

2. **Run the agents**

   ```bash
   # Agent 1 (baseline)
   cd model-battleground/battleground-agent
   uv sync
   cp .env.example .env.local
   uv run python src/agent.py download-files
   uv run python src/agent.py dev

   # Agent 2 (alt stack A)
   cd ../battleground-agent-2
   uv sync
   cp .env.example .env.local
   uv run python src/agent.py download-files
   uv run python src/agent.py dev

   # Agent 3 (alt stack B)
   cd ../battleground-agent-3
   uv sync
   cp .env.example .env.local
   uv run python src/agent.py download-files
   uv run python src/agent.py dev
   ```

   Make sure each worker is registered under the names referenced by the frontend (e.g., `devday-battleground-agent-2` and `devday-battleground-agent-3` for Agents 2 and 3).

3. **Launch the dashboard**

   ```bash
   cd ../frontend
   pnpm install
   cp .env.example .env.local
   pnpm dev
   ```

   Open http://localhost:3000 and click **Start call** to join a LiveKit room with Agent 1.

4. **Dispatch and compare**
   - Use the UI to dispatch Agents 2 and 3 via the **Dispatch Agent** buttons.
   - Speak continuously; watch STT / LLM / TTS bars update for each agent.
   - Inspect transcript differences and connection state per column.

## How data flows

1. All agents run an `AgentSession` with their own STT/LLM/TTS configuration.
2. On `metrics_collected` and `UserInputTranscribedEvent`, workers normalize the timing values and emit RPCs:
   - `model_battleground.agent.metrics`
   - `model_battleground.agent.status`
   - `model_battleground.agent.transcript`
3. The frontend registers RPC handlers on the room and updates:
   - `agentMetrics` – driving the bar charts,
   - `agentStatuses` – powering the “connected” pips and dispatch spinners,
   - `messagesByAgent` – transcript columns for each card.
4. Clicking **Dispatch Agent** calls `model_battleground.agent.dispatch` on Agent 1, which uses the LiveKit Agent Dispatch API to bring the requested worker into the room.

## Customization ideas

- Swap any agent’s STT/LLM/TTS models to compare your own providers; keep the RPC payloads stable and the dashboard will continue to work.
- Add new metrics (e.g., quality scores, cost per minute) to the RPC payloads and surface them in `AgentCard`.
- Integrate a logging / analytics backend by mirroring the metrics events to your own observability stack.***
