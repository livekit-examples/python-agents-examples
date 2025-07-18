# Vision Agent

A multimodal voice assistant with vision capabilities that can see and discuss what users show through their camera using LiveKit's voice agents.

## Overview

**VisionAgent** - A voice-enabled AI assistant that combines speech interaction with computer vision, allowing users to show objects, documents, or scenes through their camera and have natural conversations about what the agent sees.

## Features

- **Computer Vision Integration**: Processes video frames from user's camera in real-time
- **Multimodal Conversation**: Combines visual context with voice interaction
- **Automatic Frame Capture**: Buffers the latest video frame when users speak
- **Multi-Track Support**: Handles video streams from remote participants
- **Voice-Enabled**: Built using LiveKit's voice capabilities with support for:
  - Speech-to-Text (STT) using Deepgram
  - Large Language Model (LLM) using X.AI's Grok-2-Vision model
  - Text-to-Speech (TTS) using Rime
  - Voice Activity Detection (VAD) using Silero
- **Modern Web Interface**: Next.js frontend with video sharing capabilities

## How It Works

1. User connects to the LiveKit room through the web interface
2. User enables their camera to share video with the agent
3. The agent subscribes to the user's video track automatically
4. When the user speaks, the agent captures the current video frame
5. The captured frame is added to the conversation context along with the transcribed speech
6. Grok-2-Vision processes both the visual and textual input
7. The agent responds with voice, able to describe and discuss what it sees
8. Users can show different objects or scenes and ask questions about them

## Prerequisites

- Python 3.10+
- `livekit-agents`>=1.0
- LiveKit account and credentials
- API keys for:
  - X.AI (for Grok-2-Vision model access)
  - Deepgram (for speech-to-text)
  - Rime (for text-to-speech)
- Node.js and pnpm (for the frontend)

## Installation

1. Clone the repository

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the parent directory with your API credentials:
   ```
   LIVEKIT_URL=your_livekit_url
   LIVEKIT_API_KEY=your_api_key
   LIVEKIT_API_SECRET=your_api_secret
   XAI_API_KEY=your_xai_key
   DEEPGRAM_API_KEY=your_deepgram_key
   RIME_API_KEY=your_rime_key
   ```

## Running the Agent

1. Start the agent:
   ```bash
   python agent.py dev
   ```

2. In a separate terminal, navigate to the frontend directory and start the Next.js app:
   ```bash
   cd agent-vision-frontend
   pnpm install
   pnpm dev
   ```

The application will be available at `http://localhost:3000`. Enable your camera when prompted to start showing things to the agent.

## Architecture Details

### Main Classes

- **VisionAgent**: Core agent class that handles both voice and vision inputs
- **Video Stream Management**: Automatically subscribes to video tracks from participants
- **Frame Buffering**: Stores the latest video frame for processing when user speaks

### Vision Processing Flow

1. User's video track is detected when they join or publish video
2. Agent creates a VideoStream to receive frames
3. Latest frame is continuously buffered as video streams
4. When user completes their turn (stops speaking), the current frame is captured
5. Frame is added as ImageContent to the chat message
6. Grok-2-Vision processes the multimodal input (text + image)
7. Agent generates a response based on both visual and conversational context

### Frontend Features

- Video input support with camera selection
- Screen sharing capabilities
- Chat interface for text input (optional)
- Real-time transcription display
- Modern, responsive UI with dark mode support

### Multimodal Context

The agent maintains conversation context that includes:
- User's spoken/typed messages
- Captured video frames at the moment of each user utterance
- Agent's responses
- Full conversation history with visual context

## Customization

1. **Change Vision Model**: Replace Grok-2-Vision with other multimodal LLMs like GPT-4o or Claude 3
2. **Modify Frame Capture Logic**: Adjust when frames are captured (e.g., continuous vs. on-demand)
3. **Add Visual Analysis Tools**: Integrate specialized vision APIs for OCR, object detection, etc.
4. **Enhance Agent Instructions**: Update the prompt to specialize in specific visual tasks
