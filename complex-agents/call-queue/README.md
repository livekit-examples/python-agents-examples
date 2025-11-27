# Call Queue Demo

This demo showcases how LiveKit Agents can power a lightweight call center workflow: a dispatcher dashboard lists every active survey room, while a voice agent interviews callers and pushes their answers back into LiveKit metadata in real time.

## Repo layout

| Directory | Description |
| --- | --- |
| `survey-agent` | Post-call survey worker (voice agent) that asks five scripted questions and records results via a tool call. |
| `frontend` | Next.js dashboard with queue cards, survey-progress visualizations, and a full-featured LiveKit session view. |

Each folder includes a README with setup tips and architecture details.

## Quick start

1. **Prep LiveKit credentials**
   - Create (or reuse) a LiveKit Cloud project.
   - Copy the `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` into both the agent and frontend `.env.local` files.

2. **Run the survey worker**

   ```bash
   cd call-queue/survey-agent
   uv sync
   cp .env.example .env.local
   uv run python src/agent.py download-files
   uv run python src/agent.py dev
   ```

   The agent registers as `devday-survey-agent` by default; keep this name aligned with the frontend config.

3. **Launch the dashboard**

   ```bash
   cd ../frontend
   pnpm install
   cp .env.example .env.local  # reuse the same LIVEKIT_* values
   pnpm dev
   ```

   Visit http://localhost:3000 to load the queue. When new rooms appear, click the headset icon to join the call and continue the survey.

## How it works

1. The survey agent greets callers, follows the script in `SURVEY_QUESTIONS`, and calls `record_survey_response` after every answer. That tool updates room metadata with totals and timestamps.
2. The frontend polls `/api/rooms`, which wraps LiveKit’s Room Service API and JSON-decodes the metadata into `survey.total` / `survey.answered`.
3. Queue cards surface caller info, SIP participants, duration, and progress. If no rooms exist, the UI invites dispatchers to place outbound calls instead.
4. When a dispatcher starts a call, the frontend POSTs to `/api/connection-details`, embeds `agentName="devday-survey-agent"` in the token, and hands the room to the LiveKit Agent session view with chat + mic controls.

## Customization ideas

- Update `SURVEY_QUESTIONS` or load copy from an external CMS to support different campaigns!
