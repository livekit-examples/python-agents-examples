# Call Moderation – Compliance Agent

This worker is the “LiveRide moderation desk.” Whenever a driver agent spins up, it dispatches this companion process so it can silently monitor the conversation, enforce the community guidelines in `src/guidelines.md`, and issue RPC alerts to the frontend when something crosses the line.

## Responsibilities

- Listens to a single target participant (the driver) using selective subscription logic so that it's monitoring the driver rather than the caller.
- Uses AssemblyAI streaming STT and GPT‑4.1 with a **no‑TTS** session. The agent never speaks—it only reasons about transcripts.
- Loads the LiveRide guidelines at startup and injects them directly into the prompt so the LLM can cite categories when it spots a violation.
- Exposes a dedicated `report_guideline_violation` tool (see `Assistant` class). When the LLM calls it, the worker formats the event and sends a `moderation.show_violation` RPC to the rider UI.
- Accepts dispatch metadata (`target_identity`) from the driver so it immediately knows which participant to follow, but falls back to the first agent participant if no metadata is provided.

## Requirements

- Python 3.9+
- [uv](https://github.com/astral-sh/uv)
- LiveKit Cloud project or compatible self-hosted deployment

## Setup

```bash
uv sync
cp .env.example .env.local  # then add LIVEKIT_URL/API_KEY/API_SECRET
uv run python src/agent.py download-files  # downloads VAD & turn detector
```

## Running

Use the same commands as other LiveKit agents:

```bash
# Manual test run
uv run python src/agent.py console

# Room-connected worker
uv run python src/agent.py dev

# Production entrypoint
uv run python src/agent.py start
```

When packaged with `cli.run_app` the worker registers as `devday-moderation-agent`. Keep the name aligned with `MODERATION_AGENT_NAME` in the driver agent.

## How the moderation flow works

1. `prewarm` loads the Silero VAD once per worker process so each job starts quickly.
2. `entrypoint` creates a `ModerationUserdata` object that stores the active room and the identity being monitored.
3. `RoomIO` mirrors the driver's audio stream into the LLM, while helper functions update which track is subscribed based on dispatch metadata.
4. Whenever the LLM calls `report_guideline_violation`, `userdata.notify_violation` finds a non-agent participant (the rider UI) and sends a JSON payload through `moderation.show_violation`.
5. The frontend shows a safety banner (see `components/app/session-view.tsx`), but the call stays live so humans can intervene.

## Customization ideas

- Update `guidelines.md` to match your brand policy; the README auto-loads whatever content you place there.
- Expand the tool schema so violations include structured severity enums, rider IDs, or ticket numbers.
- Wire additional RPCs (like `moderation.end_call`) if you need to actually terminate sessions.