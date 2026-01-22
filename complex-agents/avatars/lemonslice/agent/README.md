# LemonSlice salary negotiation coach

This agent creates an interactive salary negotiation practice experience using [LemonSlice](https://www.lemonslice.com/) avatars with LiveKit Agents. Users can practice asking for a raise with three different boss personalities, and get real-time coaching feedback.

## Setup

### Environment variables

Create a `.env.local` file in this directory with the following variables:

```bash
# LiveKit Configuration (also used for inference API)
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=wss://your-project.livekit.cloud

LEMONSLICE_API_KEY=your_lemonslice_api_key
```

### Dependencies

Install dependencies using uv:

```bash
uv sync
```

This will install:
- `livekit-agents` (>=1.3.12)
- `livekit-plugins-lemonslice` (>=1.3.12)
- `python-dotenv`
- `pyyaml`

### Running the agent

Start the agent worker in development mode:

```bash
uv run lemonslice-agent.py dev
```

## Features

### Three boss personalities

Each boss has a unique voice, avatar, and negotiation style:

- **Easy (The Encourager)**: Supportive and open to discussion. Uses warm, encouraging body language and a friendly voice.
- **Medium (The Skeptic)**: Questions everything and pushes back on numbers. Professional and measured in tone.
- **Hard (The Busy Executive)**: Impatient and time-constrained. Direct and dismissive with confident body language.

### Dual-mode operation

- **Roleplay mode**: Practice negotiating with the selected boss personality
- **Coaching mode**: Get real-time feedback on your performance by asking "How am I doing?"

### Session management

- 3-minute practice sessions with automatic timer
- Session ends with a summary after time expires
- Tracks coaching requests and negotiation phases

### Models and services

- **Speech-to-Text**: Deepgram Nova 3 (via LiveKit inference API)
- **Language Model**: Google Gemini 2.5 Flash (via LiveKit inference API)
- **Text-to-Speech**: Cartesia Sonic 3 (via LiveKit inference API)
- **Avatar**: LemonSlice animated avatars with personality-specific movement prompts

## How it works

1. User selects a boss personality in the frontend (easy, medium, or hard)
2. Agent receives boss type via participant attributes
3. Agent creates appropriate `BaseBossAgent` subclass with personality-specific:
   - Instructions loaded from YAML prompt files
   - Cartesia voice ID
   - LemonSlice avatar image and movement prompt
4. `AgentSession` starts with the selected boss agent
5. LemonSlice `AvatarSession` publishes synchronized audio + video tracks
6. Boss agent greets user and begins roleplay
7. User can trigger coaching mode via function tool `how_am_i_doing()`
8. Agent switches modes by updating instructions dynamically
9. After 3 minutes, session automatically ends with a farewell message

## Architecture

### Agent classes

- `BaseBossAgent`: Base class with coaching functionality and mode switching
  - `EasyBossAgent`: The Encourager personality
  - `MediumBossAgent`: The Skeptic personality
  - `HardBossAgent`: The Busy Executive personality

### Function tools

- `how_am_i_doing()`: Switches from roleplay to coaching mode
- `return_to_roleplay()`: Returns from coaching back to boss roleplay
