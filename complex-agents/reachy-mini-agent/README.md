# Reachy Mini LiveKit Agent

A LiveKit agent system for controlling a Reachy Mini robot with vision capabilities. The agent can see through the robot's camera and control the robot's movements, including face detection and tracking.

## Overview

This project consists of two main components:

1. **Agent Backend** (`agent.py`) - A LiveKit agent that:
   - Uses Grok-2 Vision to see what the robot's camera sees
   - Provides a "look at me" function tool that triggers the robot to detect and look at faces
   - Communicates with the robot via RPC methods

2. **Reachy Client** (`reachy_client.py`) - A client that:
   - Connects the Reachy Mini robot to a LiveKit room
   - Streams video and audio from the robot's camera and microphone
   - Implements face detection using OpenCV
   - Provides RPC methods for the agent to control the robot

## Features

- **Vision-Enabled Agent**: Uses Grok-2 Vision to see through the robot's camera
- **Face Detection**: Automatically detects faces in the camera feed
- **Robot Control**: Agent can trigger the robot to look at detected faces
- **Real-time Streaming**: Streams video and audio from robot to LiveKit room
- **RPC Communication**: Bidirectional communication between agent and robot

## Prerequisites

- Python 3.10+
- Reachy Mini robot with daemon running
- LiveKit server (cloud or self-hosted)
- API keys for:
  - X.AI (for Grok-2-Vision model access)
  - Deepgram (for speech-to-text)
  - Rime (for text-to-speech)
  - LiveKit (for room access)

## Installation

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Create a `.env` file in the parent directory (`complex-agents/`) with your API credentials:
   ```env
   LIVEKIT_URL=your_livekit_url
   LIVEKIT_API_KEY=your_api_key
   LIVEKIT_API_SECRET=your_api_secret
   XAI_API_KEY=your_xai_key
   DEEPGRAM_API_KEY=your_deepgram_key
   RIME_API_KEY=your_rime_key
   ```

## Running

### 1. Start the Reachy Mini Daemon

Make sure the Reachy Mini daemon is running:
```bash
reachy-mini-daemon
```

### 2. Start the Reachy Client

In one terminal, start the client that connects the robot to LiveKit:
```bash
python reachy_client.py
```

The client will:
- Connect to the LiveKit room
- Stream video and audio from the robot
- Register RPC methods for robot control

### 3. Start the Agent

In another terminal, start the agent:
```bash
python agent.py dev
```

The agent will:
- Connect to the LiveKit room
- Subscribe to the robot's video stream
- Process video frames with Grok-2 Vision
- Provide voice interaction capabilities

## Usage

Once both the client and agent are running:

1. **Voice Interaction**: Speak to the agent through the LiveKit room
2. **Vision**: The agent can see what the robot's camera sees
3. **Control**: Ask the agent to "look at me" and it will trigger the robot to detect and look at your face

### Example Interaction

- User: "Can you look at me?"
- Agent: (calls `look_at_me` function tool)
- Robot: Detects face and moves head to look at the person

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Agent     │◄────────┤  LiveKit     │────────►│   Reachy    │
│  (Grok)    │  RPC    │    Room      │  Video/ │   Client    │
│             │         │              │  Audio  │             │
└─────────────┘         └──────────────┘         └─────────────┘
                                                         │
                                                         ▼
                                                   ┌─────────────┐
                                                   │   Reachy    │
                                                   │    Mini     │
                                                   │   Robot     │
                                                   └─────────────┘
```

## RPC Methods

### `robot.look_at_me`

Triggered by the agent to make the robot look at the person in front of it.

**Request**: Empty JSON object `{}`

**Response**:
```json
{
  "status": "success",
  "message": "Robot is now looking at you!"
}
```

or

```json
{
  "status": "error",
  "message": "No face detected. Please make sure you're visible to the camera."
}
```

## Function Tools

### `look_at_me`

A function tool available to the agent that triggers the robot to detect and look at faces.

## Configuration

### Environment Variables

- `LIVEKIT_URL`: LiveKit server URL
- `LIVEKIT_API_KEY`: LiveKit API key
- `LIVEKIT_API_SECRET`: LiveKit API secret
- `LIVEKIT_ROOM_NAME`: Room name (default: "reachy-mini-room")
- `LIVEKIT_PARTICIPANT_NAME`: Participant name for robot (default: "reachy-mini")
- `XAI_API_KEY`: X.AI API key for Grok-2 Vision
- `DEEPGRAM_API_KEY`: Deepgram API key for STT
- `RIME_API_KEY`: Rime API key for TTS

## Troubleshooting

### Robot not connecting

- Ensure the Reachy Mini daemon is running
- Check that the robot is powered on and connected
- Verify media backend is set correctly

### Face detection not working

- Ensure you're visible to the camera
- Check that OpenCV's Haar cascade file is available
- Verify camera is working: `reachy_mini.media.get_frame()` should return frames

### Video/Audio not streaming

- Check LiveKit room connection
- Verify tracks are published correctly
- Check network connectivity

## Development

### Project Structure

```
reachy-mini-agent/
├── agent.py           # LiveKit agent with Grok vision
├── reachy_client.py   # Reachy Mini LiveKit client
├── pyproject.toml     # Project dependencies
└── README.md          # This file
```

## License

See the main repository license.

