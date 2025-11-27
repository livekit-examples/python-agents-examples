# LiveKit Drive-Thru Demo

This folder contains the complete @drive-thru experience showcased at Dev Day: a LiveKit-powered voice agent that takes orders like a McDonald’s attendant plus a Next.js dashboard that shows the cart in real time.

## Repository layout

| Directory | Description |
| --- | --- |
| `drive-thru-agent` | Python worker that runs the Kelly drive-thru persona, exposes ordering tools, and sends checkout RPCs when the user says “that’s it.” |
| `frontend` | Next.js 15 app that boots a LiveKit room, streams audio from the browser, and renders the animated order board + controls. |

Each directory has its own README with deeper instructions on setup, architecture, and customization.

## Quick start

1. **Configure LiveKit**
   - Create or reuse a LiveKit Cloud project.
   - Grab `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET`.
   - Ensure the drive-thru agent name in `drive-thru-agent/livekit.toml` matches the worker you spin up in Cloud.

2. **Run the agent**

   ```bash
   cd drive-thru/drive-thru-agent
   uv sync
   cp .env.example .env.local  # or create manually with your credentials
   uv run python src/agent.py download-files
   uv run python src/agent.py dev
   ```

   The `README.md` in that folder explains the menu database, toolset, and how to swap models.

3. **Run the frontend**

   ```bash
   cd ../frontend
   pnpm install
   cp .env.example .env.local  # ensure LiveKit env vars match the agent
   pnpm dev
   ```

   Visit http://localhost:3000 and click “Start Drive Thru.” The React app joins the same LiveKit room, streams mic audio, and polls the agent’s `get_order_state` RPC so the order board updates every second.

4. **End-to-end flow**
   - Speak to the agent through the browser mic.
   - Watch combo/happy/regular items animate in the order column.
   - Say “that’s all,” then the agent calls `complete_order`, pushing a `show_checkout` RPC to the UI so it shows the total and closes the loop.

## Deployment notes

- The Python worker is production-ready (Dockerfile included) and can be deployed on LiveKit Cloud using `lk agent deploy`
- The Next.js app only needs `LIVEKIT_*` env vars plus an HTTPS origin so browsers grant mic access.
- Keep your agent and frontend synced on agent ID—if you rename the worker in Cloud, update `app-config.ts`.

## Where to go next

- Want menu persistence? Replace `FakeDB` and `OrderState` with your POS or inventory system.
- Want kiosks or in-store signage? Use the `OrderStatus` component as a drop-in widget; it only needs a LiveKit room + the `get_order_state` RPC.
- Need multiple agents? Copy `drive-thru-agent`, adjust prompts and menu, then point a new frontend (or the same one) at the different `agentName`.
