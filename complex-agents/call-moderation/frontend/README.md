# Call Moderation Frontend

This Next.js 15 app is the rider-facing “dispatch console” used in the @call-moderation demo. It joins a LiveKit room, connects to the **driver agent** (`devday-driver-agent`), listens for RPC alerts from the **moderation agent**, and renders a mobile-like interface to demo realtime moderation and rider notification.

<img width="1218" height="998" alt="Screenshot 2025-11-18 at 9 23 21 AM" src="https://github.com/user-attachments/assets/008d984f-3190-49a3-aef2-02b198b48d93" />

## Highlights

- **Live session** – timer, driver profile, rating summary, and mic controls that sit on top of the LiveKit audio session.
- **Safety alerts** – the moderation worker calls `moderation.show_violation`; `SessionView` registers that RPC and surfaces the severity + description in a prominent warning card.
- **Agent-aware tokens** – the `/api/connection-details` route accepts the configured `agentName`, bakes it into the LiveKit access token, and ensures the driver agent auto-joins each new room.

## Prerequisites

- Node.js 20+
- [pnpm 9](https://pnpm.io/)
- Running instances of both backend workers (`../driver-agent` and `../moderation-agent`)
- LiveKit Cloud (or self-hosted) credentials with Agent Dispatch enabled

## Local setup

1. Install dependencies:

   ```bash
   pnpm install
   ```

2. Configure LiveKit credentials:

   ```bash
   cp .env.example .env.local
   # then edit LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET
   ```

3. Start the dev server:

   ```bash
   pnpm dev
   ```

4. In another terminal, run the driver agent (`uv run python src/agent.py dev` inside `../driver-agent`). It will automatically dispatch the moderation agent.

5. Visit http://localhost:3000, click **Contact Driver**, and listen for Esteban plus any violations the moderator reports.

## Connection flow

- `app-config.ts` holds UI branding plus the `agentName` (`devday-driver-agent`). Update it if you rename the worker.
- `hooks/useConnectionDetails` issues a `POST` to `/api/connection-details`, which mints a short-lived token and includes the agent name inside `RoomConfiguration`.
- The browser joins the LiveKit room, un-mutes the mic, and the driver agent receives a matching dispatch.
- The moderation agent sends RPC payloads to `moderation.show_violation`; `SessionView` parses the JSON and shows the alert via `SafetyAlertCard`.

## Key files

- `components/app/session-view.tsx` – core layout, timer, driver card, RPC handling for violations.
- `components/livekit/agent-control-bar` – shared mic toggle logic with LiveKit’s hooks.
- `app/api/connection-details/route.ts` – server route that issues LiveKit tokens and passes along the agent configuration.
- `hooks/useChatMessages.ts` – hydrates the transcript view from LiveKit component events.

## Build & deploy

```bash
pnpm build
pnpm start
```

Deploy behind HTTPS so browsers grant microphone access, and remember to set `LIVEKIT_*` env vars plus any branding overrides through `app-config.ts`.

## Troubleshooting

- **No moderation alerts?** Make sure the moderation agent is deployed as `devday-moderation-agent` and that the driver’s `_dispatch_moderation_agent` succeeds (check worker logs).
- **Agent never joins?** Confirm `/api/connection-details` receives an `agentName` in `room_config.agents[0].agent_name`; this comes straight from `app-config`.
- **Mic stuck muted?** Browsers block autoplay + mic until the user interacts. Keep `isPreConnectBufferEnabled` off (already false) and verify permissions in the browser UI.
