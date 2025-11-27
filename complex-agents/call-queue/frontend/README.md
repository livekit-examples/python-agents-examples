# Call Queue Frontend

This Next.js 15 app is the dispatcher console for the Survey Queue example. It polls LiveKit for open rooms, and shows how far each post-call survey has progressed, and lets a human jump into any call to finish the questionnaire with the `devday-survey-agent`.

## Highlights

- **Live queue dashboard** – `useRoomQueue` polls `/api/rooms` every second, which in turn calls the LiveKit Room Service API. Metadata written by the survey agent feeds the “questions answered” progress pills inside each card.
- **Room-aware start button** – Selecting a call launches the real-time session UI, mints a LiveKit token via `/api/connection-details`, and ensures the `devday-survey-agent` joins automatically (thanks to the `agentName` from `app-config.ts`).

## Prerequisites

- Node.js 20+
- [pnpm 9](https://pnpm.io/)
- LiveKit project credentials with Room Service + Agent Dispatch access
- The survey agent running locally or on LiveKit Cloud (`../survey-agent`)

## Setup

1. Install dependencies:

   ```bash
   pnpm install
   ```

2. Configure environment variables:

   ```bash
   cp .env.example .env.local
   # then set LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
   ```

   The same credentials are used for both token minting and the Room Service API client.

3. Start the dev server:

   ```bash
   pnpm dev
   ```

4. In another terminal, run the survey agent (`uv run python src/agent.py dev`) so there’s someone on the other end of each call.

5. Open http://localhost:3000, wait for rooms to appear in the queue, and click the headset icon to join a survey.

## Connection & queue flow

1. `app-config.ts` defines branding plus the agent ID (`agentName: "devday-survey-agent"`).
2. When you “Start call,” `session-provider` posts that config to `/api/connection-details`. The route adds the agent to `RoomConfiguration` before minting a participant token, so LiveKit automatically co-locates you with the survey worker.
3. Separately, `/api/rooms` uses `RoomServiceClient` to list rooms + participants. Room metadata is JSON-decoded so UI components can read survey totals, answered count, and timestamps.
4. `CallQueueView` merges all of this into queue cards. Once you connect, `SessionView` takes over with the transcript, mic/agent meters, and control bar.

## Key files

- `components/app/call-queue-view.tsx` – queue cards, survey progress UI, phone modal, error/empty states.
- `components/app/session-view.tsx` – active-call layout, transcript overlay, LiveKit control bar, pre-connect messaging.
- `app/api/rooms/route.ts` – server-side polling proxy around `RoomServiceClient`.
- `app/api/connection-details/route.ts` – mints LiveKit tokens that include the survey agent.
- `hooks/useRoomQueue.ts` – polling hook with abort + backoff logic.

## Build & deploy

```bash
pnpm build
pnpm start
```

Serve the app over HTTPS so browsers grant microphone access. Set the same `LIVEKIT_*` variables in your hosting environment, and update `app-config.ts` if you rename the survey agent or want different branding.