# LiveKit Drive-Thru Agent

This directory contains the Python worker that powers the Dev Day drive-thru demo. The agent plays the role of **Kelly**, a McDonald’s-style attendant who guides customers through their order over voice. It is implemented with [LiveKit Agents for Python](https://github.com/livekit/agents) and runs on LiveKit Cloud so it can be paired with the matching web frontend in `../frontend`.

## What the agent does

- Streams real-time audio between the customer and the assistant, using AssemblyAI for STT, GPT-4.1 for reasoning, and Cartesia Sonic for TTS (configured in `src/agent.py`).
- Models a realistic menu through `FakeDB`, exposes combo/happy/regular-order tools, and enforces each item’s required options before submitting tool calls.
- Keeps a running `OrderState`, exposes `list_order_items`, `remove_order_item`, and `complete_order` tools, and pushes checkout info back to the UI through LiveKit RPCs.
- Adds ambient speaker noise (`bg_noise.mp3`) and multilingual turn detection to keep the conversation snappy and realistic.

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) for dependency management
- A LiveKit project with API credentials and an agent slot

## Setup

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Create `.env.local` with your LiveKit credentials:

   ```bash
   LIVEKIT_URL=wss://<your-project>.livekit.cloud
   LIVEKIT_API_KEY=...
   LIVEKIT_API_SECRET=...
   ```

   You can use `lk cloud auth && lk app env -w -d .env.local` to populate the file from the CLI.

3. Download the required VAD and turn-detection models (only once):

   ```bash
   uv run python src/agent.py download-files
   ```

## Running the worker

Use the mode that matches how you are testing:

```bash
# Talk to the agent in your terminal
uv run python src/agent.py console

# Run with a LiveKit room so the frontend can join
uv run python src/agent.py dev

# Production entrypoint (same as dev but with worker-friendly defaults)
uv run python src/agent.py start
```

When the agent starts in `dev`/`start`, it registers itself under the `agent_name` defined in `livekit.toml`. The frontend expects to find that agent when it asks LiveKit Cloud to join a room.

## Order toolset

All ordering logic lives inside `DriveThruAgent`:

- `order_combo_meal`, `order_happy_meal`, and `order_regular_item` validate menu IDs, enforce drink/sauce sizing, and push the structured payload into `OrderState`.
- `remove_order_item` and `list_order_items` let the model inspect and edit the cart.
- `complete_order` calculates the total and issues a `show_checkout` RPC to every participant so the UI can show a “drive to the next window” screen.

The `FakeDB` implementation inside `src/database.py` is intentionally verbose so you can see how to encode calories, prices, and availability flags. Replace these calls with your real catalog or a remote API when you productionize the agent.

## Frontend integration

`entrypoint` wires up a background `BackgroundAudioPlayer`, registers a `get_order_state` RPC handler, and boots an `AgentSession` with:

- `silero.VAD` and the multilingual turn detector to keep the mic responsive.
- AssemblyAI streaming STT, GPT-4.1, and Cartesia Sonic 2 for the voice.
- `max_tool_steps=10` so the LLM can chain multiple edits in a single turn if needed.

The React app polls `get_order_state` every second and listens for the `show_checkout` RPC. As soon as customers say “that’s all,” the frontend transitions into the checkout view.

## Testing

The `tests` folder contains pytest examples that exercise the order logic. Run them with:

```bash
uv run pytest
```
