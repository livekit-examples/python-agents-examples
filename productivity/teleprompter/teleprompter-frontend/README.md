<a href="https://livekit.io/">
  <img src="./.github/assets/livekit-mark.png" alt="LiveKit logo" width="100" height="100">
</a>

# Next.js Transcription Frontend

<p>
  <a href="https://cloud.livekit.io/projects/p_/sandbox"><strong>Deploy a sandbox app</strong></a>
  •
  <a href="https://docs.livekit.io/agents/overview/">LiveKit Agents Docs</a>
  •
  <a href="https://livekit.io/cloud">LiveKit Cloud</a>
  •
  <a href="https://blog.livekit.io/">Blog</a>
</p>

A basic example of a speech transcription frontend using LiveKit.

## Dev Setup

Clone the repository and install dependencies to a virtual environment:

```console
cd transcription-frontend
pnpm install
```

Set up the environment by copying `.env.example` to `.env.local` and filling in the required values:

- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `NEXT_PUBLIC_LIVEKIT_URL`

You can also do this automatically using the LiveKit CLI:

```console
lk app env --write
```

Run the app:

```console
pnpm dev
```

This app requires a transcription agent to communicate with. You can use one of our example agents in [livekit-examples](https://github.com/livekit-examples/), or create your own following one of the [transcription guice](https://docs.livekit.io/agents/voice-agent/transcriptions/#overview).
