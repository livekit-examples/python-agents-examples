# TTS Provider Comparison Agent

A voice assistant that allows real-time switching between different Text-to-Speech providers to compare voice quality, latency, and characteristics using LiveKit's voice agents.

## Overview

**TTS Comparison Agent** - A voice-enabled assistant that dynamically switches between multiple TTS providers (Rime, ElevenLabs, Cartesia, and PlayAI) during a conversation, allowing direct comparison of different voice synthesis technologies.

## Features

- **Multiple TTS Providers**: Compare 4 different TTS services in one session
- **Dynamic Provider Switching**: Change voices mid-conversation via agent transfer
- **Consistent Sample Rate**: All providers use 44.1kHz for fair comparison
- **Provider Awareness**: Agent knows which TTS it's using and can discuss differences
- **Voice-Enabled**: Built using LiveKit's voice capabilities with support for:
  - Speech-to-Text (STT) using Deepgram
  - Large Language Model (LLM) using OpenAI GPT-4o
  - Text-to-Speech (TTS) using multiple providers
  - Voice Activity Detection (VAD) using Silero

## TTS Providers included in this comparison

### 1. Rime
- **Model**: MistV2
- **Voice**: Abbie
- **Sample Rate**: 44.1kHz
- **Characteristics**: Natural conversational voice

### 2. ElevenLabs
- **Model**: Eleven Multilingual V2
- **Sample Rate**: Default (provider-managed)
- **Characteristics**: High-quality multilingual support

### 3. Cartesia
- **Model**: Sonic Preview
- **Voice**: Custom voice ID
- **Sample Rate**: 44.1kHz
- **Characteristics**: Fast, low-latency synthesis

### 4. PlayAI
- **Model**: PlayDialog
- **Voice**: Custom cloned voice
- **Sample Rate**: 44.1kHz
- **Characteristics**: Voice cloning capabilities

## How It Works

1. Session starts with the Rime TTS provider
2. Agent introduces itself using the current voice
3. User can request to switch providers (e.g., "Switch to ElevenLabs")
4. Agent transfers to a new agent instance with the requested TTS
5. New agent greets the user with the new voice
6. Process repeats for any provider comparison

## Prerequisites

- Python 3.10+
- `livekit-agents`>=1.0
- LiveKit account and credentials
- API keys for:
  - OpenAI (for LLM capabilities)
  - Deepgram (for speech-to-text)
  - Rime (for Rime TTS)
  - ElevenLabs (for ElevenLabs TTS)
  - Cartesia (for Cartesia TTS)
  - PlayAI (for PlayAI TTS)

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
   RIME_API_KEY=your_rime_key
   ELEVENLABS_API_KEY=your_elevenlabs_key
   CARTESIA_API_KEY=your_cartesia_key
   PLAYAI_API_KEY=your_playai_key
   ```

## Running the Agent

```bash
python tts_comparison.py dev
```

Try these commands to switch between providers:
- "Switch to ElevenLabs"
- "Use the Cartesia voice"
- "Let me hear PlayAI"
- "Go back to Rime"

## Architecture Details

### Agent Transfer Pattern

Each TTS provider has its own agent class:
- `RimeAgent`
- `ElevenLabsAgent`
- `CartesiaAgent`
- `PlayAIAgent`

Switching providers involves:
1. Function tool detects switch request
2. Returns new agent instance
3. Session transfers to new agent
4. `on_enter()` method provides audio confirmation

### Sample Rate Consistency

All providers are configured to use 44.1kHz sample rate (where configurable) to ensure fair comparison. This prevents audio quality differences due to sample rate mismatches.

### Provider Configuration

Each agent maintains its own TTS configuration:
```python
tts=rime.TTS(
    sample_rate=44100,
    model="mistv2",
    speaker="abbie"
)
```

## Comparison Criteria

When testing different providers, consider:

1. **Voice Quality**: Naturalness, clarity, pronunciation
2. **Latency**: Time from request to first audio
3. **Expressiveness**: Emotion and intonation range
4. **Language Support**: Accent and multilingual capabilities
5. **Consistency**: Voice stability across utterances
6. **Cost**: Per-character or per-second pricing

## Example Conversation

```
Agent (Rime): "Hello! I'm now using the Rime TTS voice. How does it sound?"
User: "It sounds good. Can I hear ElevenLabs?"
Agent (ElevenLabs): "Hello! I'm now using the ElevenLabs TTS voice. What do you think of how I sound?"
User: "Very natural! Now try Cartesia"
Agent (Cartesia): "Hello! I'm now using the Cartesia TTS voice. How do I sound to you?"
User: "Fast response! What about PlayAI?"
Agent (PlayAI): "Hello! I'm now using the PlayAI TTS voice. What are your thoughts on how I sound?"
```