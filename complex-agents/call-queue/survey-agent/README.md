# Call Queue – Survey Agent

This worker is the “post-call surveyor” for the Call Queue experience. When a dispatcher connects to a caller, this agent asks five ride-sharing focused CSAT questions in order, records every answer, and updates the room metadata so the dashboard can display real-time progress.

## Highlights

- Uses AssemblyAI streaming STT, GPT‑4.1‑mini, and Cartesia Sonic‑3 for a natural back-and-forth voice survey (`AgentSession` config in `src/agent.py`).
- Follows a fixed sequence of questions (`SURVEY_QUESTIONS`) and enforces that the LLM records each answer via the `record_survey_response` function tool.
- Pushes structured results to LiveKit room metadata through the REST API, which the frontend polls to show “questions answered” progress bars per room.
- Logs per-session usage stats (tokens, duration) via `metrics.UsageCollector`.

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (or another PEP 517 runner)
- A LiveKit Cloud project (or self-hosted deployment) with API credentials
- Access to the STT/LLM/TTS models referenced above

## Setup

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Copy `.env.example` to `.env.local` and fill in LiveKit credentials:

   ```bash
   LIVEKIT_URL=wss://<your-project>.livekit.cloud
   LIVEKIT_API_KEY=...
   LIVEKIT_API_SECRET=...
   ```

3. Download voice assets (first run only):

   ```bash
   uv run python src/agent.py download-files
   ```

## Running

```bash
# Talk to the survey agent in your terminal
uv run python src/agent.py console

# Start a worker that joins LiveKit rooms (used by the UI)
uv run python src/agent.py dev

# Production entrypoint
uv run python src/agent.py start
```

The worker registers as `devday-survey-agent` (see `cli.run_app`). Keep this in sync with the frontend’s `app-config.ts`.

## How response logging works

1. The agent instructions lay out each survey question and remind the LLM to call `record_survey_response` after every answer.
2. `record_survey_response` validates the `question_id`, normalizes the answer, and stores it in `SurveyUserdata.responses`.
3. `SurveyUserdata.record_response` rebuilds the room metadata JSON:
   - Includes `survey.total`, `survey.answered`, and a chronological list of responses (question text, summary, timestamp).
   - Uses `LiveKitAPI.room.update_room_metadata(...)` so anyone polling the REST API sees progress immediately.
4. The frontend’s `/api/rooms` endpoint decodes that metadata and renders the progress indicator in the queue.

## Customization ideas

- Swap the `SURVEY_QUESTIONS` tuple for your own script or load it from a CMS.
- Extend the metadata payload with rider IDs, ticket numbers, or sentiment labels.
- Replace GPT‑4.1‑mini / Sonic‑3 with the models your org prefers
- Hook `SurveyUserdata` up to an external datastore instead of (or in addition to) LiveKit metadata if you need durable storage.

## Tests

Basic pytest scaffolding is available under `tests/`. Run them with:

```bash
uv run pytest
```
