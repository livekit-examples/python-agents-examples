# Call Moderation Demo

@call-moderation is a multi-agent LiveKit experience that pairs a chatty rideshare driver with a silent compliance officer. The driver (Esteban) handles inbound rider calls, while the moderation agent shadows the conversation, matches it against LiveRide’s policy guidelines, and notifies the frontend whenever it detects a violation.

## Repository layout

| Directory | Description |
| --- | --- |
| `driver-agent` | Voice agent that greets riders, collects the destination, and dispatches the moderator into the same room. |
| `moderation-agent` | No-audio compliance worker that listens to the driver’s audio, applies `guidelines.md`, and emits RPC alerts. |
| `frontend` | Next.js 15 UI (“Hail Ride Dispatch”) that joins the room, talks to the driver, and surfaces moderation warnings. |

Each folder has its own README with deeper setup notes and customization tips.

## Quick start

1. **Prep LiveKit credentials**
   - Create (or reuse) a LiveKit Cloud project.
   - Grab `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET`.

2. **Run the moderation stack**

   ```bash
   # Driver agent
   cd call-moderation/driver-agent
   uv sync
   cp .env.example .env.local
   uv run python src/agent.py download-files
   uv run python src/agent.py dev
   ```

   The driver automatically dispatches `devday-moderation-agent`, so ensure that worker is deployed under that name (either in another terminal locally or on LiveKit Cloud).

3. **Launch the frontend**

   ```bash
   cd ../frontend
   pnpm install
   cp .env.example .env.local
   pnpm dev
   ```

   Browse to http://localhost:3000 and select **Contact Driver**. The UI fetches connection details, joins the LiveKit room, and unlocks the mic.

4. **Talk + observe**
   - Chat with Esteban; he will insist on hearing your destination before pickup.
   - The moderation agent listens in; if you violate `guidelines.md` (threats, discrimination, asking for a destination before pickup, etc.) it sends a `moderation.show_violation` RPC.
   - The frontend displays the warning banner with severity + description so dispatchers can intervene.

## How the pieces talk

1. Frontend requests a token from `/api/connection-details`, including the configured agent name.
2. LiveKit spawns the driver agent into the room. Once it starts, the driver invokes the Agent Dispatch API to summon the moderator.
3. The moderator subscribes only to the driver’s audio (based on dispatch metadata) and pushes violation events via RPC.
4. `SessionView` listens for those RPCs and updates UI state immediately

## Deployment notes

- Both Python workers ship with Dockerfiles and can be run on LiveKit Cloud’s managed infrastructure.
- The frontend only needs `LIVEKIT_*` env vars and HTTPS; branding + agent names live in `app-config.ts`.
- If you rename either agent, update `MODERATION_AGENT_NAME` in `driver-agent/src/agent.py` and `APP_CONFIG_DEFAULTS.agentName` in the frontend.

## Next steps

- Replace `src/guidelines.md` with your own policy doc and extend the violation payload schema.
- Wire a pager, ticketing system, or webhook inside `report_guideline_violation` if you need automated enforcement.
