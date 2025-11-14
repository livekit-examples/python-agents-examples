# Shopify Voice Shopper

Shopify Voice Shopper is a demo project that combines a [LiveKit](https://livekit.io/) voice agent with a small Next.js frontend. The Python agent (`shopify.py`) connects to Shopify stores through the public MCP endpoint on every shop using the Agent MCP client and responds to users via voice. The `shopify-voice-frontend` directory contains a web UI and Chrome extension for talking with the agent.

## Repository layout

```
├── shopify.py                # LiveKit agent that talks to Shopify via MCP
├── shopify-voice-frontend/   # Next.js frontend and browser extension
└── requirements.txt          # Python dependencies
```

## How it works

1. **Python Agent (`shopify.py`)**
   - Implements a `LiveKit Agent` that can search and switch Shopify stores using MCP.
   - Supports functions for sending URLs back to the browser and for switching the active shop.
   - Uses Deepgram for speech‑to‑text, Cartesia for text‑to‑speech, and OpenAI for LLM responses.
   - The agent starts a LiveKit room and communicates with the frontend via RPC calls.

2. **Frontend (`shopify-voice-frontend`)**
   - A Next.js application that renders the chat UI and handles transcription display.
   - Also includes a Chrome extension (`extension/`) which opens the UI in a side panel and forwards navigation requests from the agent.
   - `app/api/connection-details/route.ts` generates LiveKit connection tokens for the browser client. Shouldn't need to touch this!

The agent sends `client.navigate` RPC messages with URLs. The frontend receives these and forwards them to the extension, which then opens the page in the user’s browser.

## Setup

### Requirements

- Python 3.10+
- Node.js and `pnpm`

### Python agent

1. Install dependencies
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   The `livekit-agents` dependency is installed from the latest `main` branch
   on GitHub rather than PyPI.
2. Configure environment variables
   - `SHOPIFY_MCP_URL` – URL of the Shopify MCP server for your store.
   - `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` – credentials for your LiveKit project.
   - Any additional keys required by the plugins (OpenAI, Deepgram, etc.).
3. Run the agent
   ```bash
   python shopify.py dev
   ```

### Frontend & Chrome extension

1. Copy `.env.example` to `.env.local` inside `shopify-voice-frontend` and fill in your LiveKit credentials.
2. Install dependencies and start the dev server
   ```bash
   cd shopify-voice-frontend
   pnpm install
   pnpm dev
   ```
   Open <http://localhost:3000> to view the UI.
3. To use the Chrome extension, load `shopify-voice-frontend/extension` as an unpacked extension in Chrome. The extension expects the Next.js app to be running at `http://localhost:3000`.

For production you can run `pnpm build` which exports the site to `out/`. Update the extension’s `popup.html` to point to your hosted files or packaged assets.

## Usage

Start the Python agent and open the web UI (or Chrome extension). Press **Start conversation** to connect. The agent will speak responses, display transcriptions, and can navigate your browser to product pages via voice commands. The shop context that it will start with is Snow Devil (naturally) but you can ask it to change to any other shopify URL and it will let you shop there instead!

## License

This project is provided as a demonstration of LiveKit Agents + Shopify MCP and is offered under the MIT license.