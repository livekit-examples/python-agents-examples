# Transcriber Agent

A speech-to-text logging agent that transcribes user speech and saves it to a file using LiveKit's voice agents.

## Overview

**Transcriber Agent** - A voice-enabled agent that listens to user speech, transcribes it using Deepgram STT, and logs all transcriptions with timestamps to a local file.

## Features

- **Real-time Transcription**: Converts speech to text as users speak
- **Persistent Logging**: Saves all transcriptions to `user_speech_log.txt` with timestamps
- **Voice-Enabled**: Built using LiveKit's voice capabilities with support for:
  - Speech-to-Text (STT) using Deepgram
  - Minimal agent configuration without LLM or TTS
- **Event-Based Processing**: Uses the `user_input_transcribed` event for efficient transcript handling
- **Automatic Timestamping**: Each transcription entry includes date and time

## How It Works

1. User connects to the LiveKit room
2. Agent starts listening for speech input
3. Deepgram STT processes the audio stream in real-time
4. When a final transcript is ready, it triggers the `user_input_transcribed` event
5. The transcript is appended to `user_speech_log.txt` with a timestamp
6. The process continues for all subsequent speech

## Prerequisites

- Python 3.10+
- `livekit-agents`>=1.0
- LiveKit account and credentials
- API keys for:
  - Deepgram (for speech-to-text)

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
   DEEPGRAM_API_KEY=your_deepgram_key
   ```

## Running the Agent

```bash
python transcriber.py console
```

The agent will start listening for speech and logging transcriptions to `user_speech_log.txt` in the current directory.

## Architecture Details

### Main Components

- **AgentSession**: Manages the agent lifecycle and event handling
- **user_input_transcribed Event**: Fired when Deepgram completes a transcription
- **Transcript Object**: Contains the transcript text and finality status

### Log File Format

Transcriptions are saved in the following format:
```
[2024-01-15 14:30:45] Hello, this is my first transcription
[2024-01-15 14:30:52] Testing the speech to text functionality
```

### Minimal Agent Configuration

This agent uses a minimal configuration without LLM or TTS:
```python
Agent(
    instructions="You are a helpful assistant that transcribes user speech to text.",
    stt=deepgram.STT()
)
```