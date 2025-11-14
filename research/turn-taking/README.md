# Turn-Taking Agent

A voice agent that demonstrates advanced turn-taking detection with real-time End-of-Utterance (EOU) probability visualization using LiveKit's voice agents.

## Overview

**Turn-Taking Agent** - A multilingual voice assistant that uses advanced turn detection to determine when a user has finished speaking, displaying real-time EOU probability percentages to show how the AI predicts conversation turns.

## Features

- **Advanced Turn Detection**: Uses multilingual turn detection model to predict when users finish speaking
- **Real-time EOU Visualization**: Displays End-of-Utterance probability percentage in the frontend
- **Multilingual Support**: Handles 13 languages including English, French, German, Portuguese, Chinese, Japanese, Korean, Indonesian, Russian, Dutch, Turkish, Spanish, and Italian
- **RPC Communication**: Sends EOU probability updates to frontend in real-time
- **Voice-Enabled**: Built using LiveKit's voice capabilities with support for:
  - Speech-to-Text (STT) using Gladia (multilingual)
  - Large Language Model (LLM) using OpenAI GPT-4o-mini
  - Text-to-Speech (TTS) using OpenAI
  - Voice Activity Detection (VAD) using Silero
- **Visual Feedback**: Bar visualizer and transcription view in the frontend

## How It Works

1. User connects to the LiveKit room through the web interface
2. The agent greets the user and starts listening
3. As the user speaks, Gladia STT transcribes in multiple languages
4. The turn detection model continuously calculates EOU probability
5. EOU probability is sent to the frontend via RPC and displayed as a percentage
6. When EOU probability is high enough, the agent knows the user has finished speaking
7. The agent generates and speaks a response using OpenAI's LLM and TTS
8. The cycle continues with real-time visualization of turn-taking predictions

## Prerequisites

- Python 3.10+
- `livekit-agents`>=1.0
- LiveKit account and credentials
- API keys for:
  - OpenAI (for LLM and TTS capabilities)
  - Gladia (for multilingual speech-to-text)
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
   OPENAI_API_KEY=your_openai_key
   GLADIA_API_KEY=your_gladia_key
   ```

## Running the Agent

1. Start the agent:
   ```bash
   python agent.py dev
   ```

2. In a separate terminal, navigate to the frontend directory and start the Next.js app:
   ```bash
   cd turn-taking-frontend
   pnpm install
   pnpm dev
   ```

The application will be available at `http://localhost:3000`. Connect to start conversing with the agent while watching real-time turn-taking predictions.

## Architecture Details

### Main Classes

- **CustomTurnDetector**: Wrapper around MultilingualModel that exposes EOU probability and sends it to frontend
- **SimpleAgent**: Main agent class that handles conversation with custom turn detection
- **TurnTakingUserData**: Stores session context and references


### Frontend Integration

- Next.js app with real-time EOU probability display
- Registers RPC handler for `client.eou_update` method
- Shows transcription view and audio visualizer
- Updates EOU percentage dynamically as user speaks

### RPC Communication

The agent sends EOU updates with the following payload:
```json
{
  "eou_probability": 0.875,
  "percentage": 87.5
}
```