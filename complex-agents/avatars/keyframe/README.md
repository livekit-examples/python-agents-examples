<a href="https://livekit.io/">
  <img src="./.github/assets/livekit-mark.png" alt="LiveKit logo" width="100" height="100">
</a>

# Keyframe Avatars x LiveKit Demo

A demo app showcasing emotionally expressive, real-time avatar interactions powered by [Keyframe](https://keyframelabs.com/) avatars and [LiveKit Agents](https://github.com/livekit/agents). Two AI personas, Cosmo and Lyra, demonstrate emotion rendering driven by LiveKit function calls across two conversation scenarios.

The demo has two phases:

1. **Emotion showcase** — Cosmo responds to prompts (sad haiku, dad joke, insults) with matching facial expressions, demonstrating Keyframe's emotion rendering triggered by LLM tool calls.
2. **Acme Airlines support** — Lyra, a customer support agent, handles a trip cancellation scenario with empathy. She looks up bookings, modifies flights and hotels, and expresses appropriate emotions throughout.

## Project structure

This is a monorepo with two apps:

- **`agent/`** — Python voice AI agent built with LiveKit Agents SDK
- **`frontend/`** — Next.js React app with LiveKit Agents UI components

```
keyframe-demo/
├── .env.local              # Shared credentials (symlinked into agent/ and frontend/)
├── ARCHITECTURE.md         # Detailed architecture docs
├── agent/
│   ├── src/agent.py        # CosmoAgent + AcmeAirlinesAgent
│   ├── tests/test_agent.py # Behavioral tests
│   ├── pyproject.toml
│   └── Dockerfile
└── frontend/
    ├── app/                # Next.js pages + token API route
    ├── components/
    │   ├── agents-ui/      # LiveKit Agents UI (shadcn-style)
    │   └── app/            # Booking card, view controller, welcome view
    ├── hooks/
    │   └── useAgentEvents.ts
    └── package.json
```

## Pipeline

| Component | Provider | Model |
|-----------|----------|-------|
| STT | LiveKit Inference | `deepgram/nova-3` (multilingual) |
| LLM | LiveKit Inference | `openai/gpt-4.1-mini` |
| TTS | LiveKit Inference | `elevenlabs/eleven_turbo_v2_5` |
| Avatar | Keyframe | `public:cosmo_persona-1.5-live` |
| VAD | Silero | (prewarmed) |
| Turn detection | LiveKit | Multilingual model |

## Using coding agents

This project is designed to work with coding agents like [Claude Code](https://claude.com/product/claude-code), [Cursor](https://www.cursor.com/), and [Codex](https://openai.com/codex/).

For your convenience, LiveKit offers both a CLI and an [MCP server](https://docs.livekit.io/reference/developer-tools/docs-mcp/) that can be used to browse and search its documentation. The [LiveKit CLI](https://docs.livekit.io/intro/basics/cli/) (`lk docs`) works with any coding agent that can run shell commands. Install it for your platform:

**macOS:**

```console
brew install livekit-cli
```

**Linux:**

```console
curl -sSL https://get.livekit.io/cli | bash
```

**Windows:**

```console
winget install LiveKit.LiveKitCLI
```

The `lk docs` subcommand requires version 2.15.0 or higher. Check your version with `lk --version` and update if needed. Once installed, your coding agent can search and browse LiveKit documentation directly from the terminal:

```console
lk docs search "voice agents"
lk docs get-page /agents/start/voice-ai-quickstart
```

See the [Using coding agents](https://docs.livekit.io/intro/coding-agents/) guide for more details, including MCP server setup.

The project includes a complete [AGENTS.md](AGENTS.md) file for these assistants. You can modify this file to suit your needs. To learn more about this file, see [https://agents.md](https://agents.md).

## Dev setup

### Prerequisites

- Python 3.10+ with [uv](https://docs.astral.sh/uv/) package manager
- Node.js 18+ with [pnpm](https://pnpm.io/) package manager
- A [LiveKit Cloud](https://cloud.livekit.io/) account
- A [Keyframe](https://platform.keyframelabs.com) API key

### Environment variables

Copy the `.env.example` to `.env.local` at the repo root:

```bash
cp .env.example .env.local
```

Then fill in the required values:

| Variable | Source |
|----------|--------|
| `LIVEKIT_URL` | [LiveKit Cloud](https://cloud.livekit.io/) project |
| `LIVEKIT_API_KEY` | LiveKit Cloud project |
| `LIVEKIT_API_SECRET` | LiveKit Cloud project |
| `KEYFRAME_API_KEY` | [Keyframe Platform](https://platform.keyframelabs.com) |

You can load the LiveKit variables automatically using the [LiveKit CLI](https://docs.livekit.io/intro/basics/cli/):

```bash
lk cloud auth
lk app env -w -d .env.local
```

You'll still need to add `KEYFRAME_API_KEY` manually.

The `.env.local` file at the root is symlinked into both `agent/` and `frontend/`.

### Install dependencies

```bash
# Agent (Python)
cd agent && uv sync

# Frontend (Next.js)
cd frontend && pnpm install
```

## Run the demo

Before your first run, download required models ([Silero VAD](https://docs.livekit.io/agents/logic/turns/vad/) and the [LiveKit turn detector](https://docs.livekit.io/agents/logic/turns/turn-detector/)):

```console
cd agent
uv run python src/agent.py download-files
```

Then start both the agent and the frontend:

```bash
# Terminal 1: Start the agent
cd agent
uv run python src/agent.py dev

# Terminal 2: Start the frontend
cd frontend
pnpm dev
```

Open http://localhost:3000 and click "Talk to Cosmo".

You can also speak to the agent directly in your terminal (without the frontend):

```console
cd agent
uv run python src/agent.py console
```

## Tests

The agent includes behavioral tests covering both demo scenarios. Run them from the `agent/` directory:

```console
cd agent
uv run pytest
```

Tests cover emotion triggers, agent handoffs, booking operations, empathy behavior, persona RPC events, and session startup ordering.

## Deploying to production

The agent includes a working `Dockerfile`. To deploy it to LiveKit Cloud or another environment, see the [deploying to production](https://docs.livekit.io/deploy/agents/) guide.

## Self-hosted LiveKit

You can also self-host LiveKit instead of using LiveKit Cloud. See the [self-hosting](https://docs.livekit.io/transport/self-hosting/local/) guide for more information. If you choose to self-host, you'll need to use [model plugins](https://docs.livekit.io/agents/models/#plugins) instead of LiveKit Inference and will need to remove the [LiveKit Cloud noise cancellation](https://docs.livekit.io/transport/media/noise-cancellation/) plugin.
