# Recording Studio Agent

Voice recording studio with multiple TTS voices, recording management, and playback.

## Quick Start

```bash
# 1. Install
uv sync

# 2. Setup .env in parent directory
# Get credentials from: https://cloud.livekit.io/projects/p_/settings/keys
cat > ../.env << EOF
LIVEKIT_URL=https://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
EOF

# 3. Run
uv run agent.py console              # Recoding Studio
uv run example-agent.py console      # Example (plays greeting)
```

## Usage

**Main agent:**

- "What voices do you have?"
- "Switch to Ashley"
- "Record this: Hello from the studio"
- "Show me all recordings"
- "Play the last recording"

**Example agent:**

- Plays `recordings/greeting.wav` on connect
