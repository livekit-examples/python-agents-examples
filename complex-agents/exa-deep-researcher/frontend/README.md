# Exa Deep Researcher Frontend

This is a web interface for the [Exa Deep Researcher](../) agent built with [LiveKit Agents](https://docs.livekit.io/agents). It provides a real-time voice interface with visual research progress tracking using the [LiveKit JavaScript SDK](https://github.com/livekit/client-sdk-js).

This template is built with Next.js and is free for you to use or modify as you see fit.

## Features

- Real-time voice interaction with the research agent
- Visual research progress timeline
- Live streaming of research notes and citations
- Daily statistics tracking (results, sources, domains)
- Responsive split-view interface
- Light/dark theme support

## Getting started

> [!TIP]
> Make sure you have the Python agent running first before starting the frontend. See the [main README](../) for agent setup instructions.

1. Install dependencies:

   ```bash
   pnpm install
   ```

2. Configure environment variables in `.env.local` (copy from `.env.example` if you don't have one):

   ```bash
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your_api_key
   LIVEKIT_API_SECRET=your_api_secret
   
   # Optional - Environment (for dev/prod separation)
   DEV=1                    # Set DEV to any value to use dev agent name (exa-deep-researcher-dev)
   ```

   > [!NOTE]
   > **Dev/Prod Separation**: Set `DEV` to any value to match your Python agent's environment. This ensures both frontend and agent use the same agent name (`exa-deep-researcher-dev` for dev, `exa-deep-researcher` for prod).

3. Run the development server:

   ```bash
   pnpm dev
   ```

4. Open http://localhost:3000 in your browser

> [!NOTE]
> The frontend expects the Python agent to be running and will connect to it automatically when you click "Connect to Room".

## How It Works

1. User clicks "Connect to Room" to connect to the agent
2. The agent greets the user and is ready to accept research requests
3. User gives a voice command like "Research quantum computing breakthroughs"
4. The frontend receives real-time updates via RPC:
   - Status updates showing research phase and progress
   - Research notes as the agent discovers information
   - Citations with clickable links
5. When research completes, the full report is available on disk

## Contributing

This template is open source and we welcome contributions! Please open a PR or issue through GitHub, and don't forget to join us in the [LiveKit Community Slack](https://livekit.io/join-slack)!
