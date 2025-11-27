# LiveKit Drive-Thru Frontend

This Next.js 15 app is the visual half of the Dev Day drive-thru demo. It connects to LiveKit, joins the same room as the Python agent in `../drive-thru-agent`, and renders a modern order-status board so customers can watch menu items being added in real time.

![App screenshot](/.github/assets/frontend-screenshot.jpeg)

## Highlights

- **Voice-first session flow** – customers click “Start Drive Thru,” grant mic access, and the UI handles the LiveKit room lifecycle, pre-connect buffering, and device errors for them.
- **Live order ticker** – `components/order-status.tsx` polls the agent’s `get_order_state` RPC and animates combo/happy/regular items as they enter the cart. When the agent calls `complete_order`, the view transitions into a checkout/thank-you screen.
- **Agent-aware controls** – the custom `AgentControlBar` exposes mic/camera/screen-share toggles, chat input (if supported), and device selectors powered by the LiveKit React SDK.
- **Drive-thru specific framing** – welcome copy, toasts, and the running total card in `SessionView` keep the experience on-theme for a fast-food kiosk or speaker box.

## Prerequisites

- Node.js 20+
- [pnpm 9](https://pnpm.io/) (or adapt the commands to npm/yarn)
- The Python worker running in `../drive-thru-agent` (start it with `uv run python src/agent.py dev`)
- A LiveKit project with API key/secret and an accessible server URL

## Local setup

1. Install dependencies:

   ```bash
   pnpm install
   ```

2. Create `.env.local` and add your LiveKit credentials:

   ```bash
   LIVEKIT_API_KEY=...
   LIVEKIT_API_SECRET=...
   LIVEKIT_URL=wss://<your-project>.livekit.cloud
   ```

   The `app/api/connection-details` route uses these values to mint short-lived room tokens and is the default endpoint consumed by the React hooks.

3. Run the development server:

   ```bash
   pnpm dev
   ```

4. Open http://localhost:3000, click “Start Drive Thru,” and begin speaking once the microphone indicator lights up. Keep the agent running so the UI has someone to talk to.

## How LiveKit connections work

- `hooks/useConnectionDetails` fetches token + server info from `/api/connection-details`. Override the endpoint by setting `NEXT_PUBLIC_CONN_DETAILS_ENDPOINT` if you host that API elsewhere.
- `app/api/connection-details/route.ts` uses `livekit-server-sdk` to mint tokens scoped to random rooms and participants. Lock this down in production by enforcing auth or a fixed room.
- `app-config.ts` stores the agent name (`agentName`) and UI affordances consumed by `components/app.tsx` and the control bar.

## Key files

- `components/app.tsx` – bootstraps the LiveKit `Room`, handles auto-reconnect, and wraps everything in `RoomContext`.
- `components/session-view.tsx` – renders both the connect screen and the active session layout, including the running total strip.
- `components/order-status.tsx` – interfaces with the agent’s RPCs, animates menu items, and exposes a callback used for the running total snapshot.
- `components/livekit/agent-control-bar/*` – mic/camera toggles, device menus, and optional chat support powered by LiveKit’s React helpers.
- `app/api/connection-details/route.ts` – server-side token minting.

## Build & deploy

```bash
# Production build
pnpm build

# Start the compiled app (uses PORT=3000 by default)
pnpm start
```

Because the API route issues LiveKit tokens, be sure to set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` wherever you deploy. If you front this UI with LiveKit Cloud Sandbox, you can also populate `sandboxId`/`agentName` inside `app-config.ts` to match your deployed agent.

## Troubleshooting tips

- If the connect button stays disabled, ensure the browser can reach `/api/connection-details` and your `.env.local` is loaded (restart `pnpm dev` after edits).
- The UI polls the agent every second; if items never appear, verify that the Python worker registered the `get_order_state` RPC without throwing in its logs.
- For local HTTPS or cross-origin setups, update `getOrigin`/`getAppConfig` in `lib/utils.ts` so the frontend fetches config from the right domain.
