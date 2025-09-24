## Overview

**Keyword Detection Agent** - A voice-enabled agent that monitors user speech for predefined keywords and logs when they are detected.

## Features

- **Real-time Keyword Detection**: Monitors speech for specific keywords as users talk
- **Custom STT Pipeline**: Intercepts the speech-to-text pipeline to detect keywords
- **Logging System**: Logs detected keywords with proper formatting
- **Voice-Enabled**: Built using voice capabilities with support for:
  - Speech-to-Text (STT) using Deepgram
  - Large Language Model (LLM) using OpenAI
  - Text-to-Speech (TTS) using OpenAI
  - Voice Activity Detection (VAD) using Silero

## How It Works

1. User connects to the LiveKit room
2. Agent greets the user and starts a conversation
3. As the user speaks, the custom STT pipeline monitors for keywords
4. When keywords like "Shane", "hello", "thanks", or "bye" are detected, they are logged
5. The agent continues normal conversation while monitoring in the background
6. All speech continues to be processed by the LLM for responses

## Prerequisites

- Python 3.10+
- `livekit-agents`>=1.0
- LiveKit account and credentials
- API keys for:
  - OpenAI (for LLM and TTS capabilities)
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
   OPENAI_API_KEY=your_openai_key
   DEEPGRAM_API_KEY=your_deepgram_key
   ```

## Running the Agent

```bash
python keyword_detection.py console
```

The agent will start a conversation and monitor for keywords in the background. Try using words like "hello", "thanks", or "bye" in your speech and watch them come up in logging.

## Architecture Details

### Main Classes

- **KeywordDetectionAgent**: Custom agent class that extends the base Agent with keyword detection
- **stt_node**: Overridden method that intercepts the STT pipeline to monitor for keywords

### Keyword Detection Pipeline

The agent overrides the `stt_node` method to create a custom processing pipeline:
1. Receives the parent STT stream
2. Monitors final transcripts for keywords
3. Logs detected keywords
4. Passes all events through unchanged for normal processing

### Current Keywords

The agent monitors for these keywords (case-insensitive):
- "Shane"
- "hello"
- "thanks"
- "bye"

### Logging Output

When keywords are detected, you'll see log messages like:
```
INFO:keyword-detection:Keyword detected: 'hello'
INFO:keyword-detection:Keyword detected: 'thanks'
```