# ElevenLabs Language Switcher Agent

A multilingual voice assistant that dynamically switches between languages using ElevenLabs TTS and LiveKit's voice agents.

## Overview

**Language Switcher Agent** - A voice-enabled assistant that can seamlessly switch between multiple languages during a conversation, demonstrating dynamic TTS and STT configuration.

## Features

- **Dynamic Language Switching**: Change languages mid-conversation without restarting
- **Synchronized STT/TTS**: Both speech recognition and synthesis switch together
- **Multiple Language Support**: English, Spanish, French, German, and Italian
- **Native Pronunciation**: Each language uses ElevenLabs' native language models
- **Contextual Greetings**: Language-specific welcome messages after switching
- **Voice-Enabled**: Built using LiveKit's voice capabilities with support for:
  - Speech-to-Text (STT) using Deepgram (multilingual)
  - Large Language Model (LLM) using OpenAI GPT-4o
  - Text-to-Speech (TTS) using ElevenLabs Turbo v2.5
  - Voice Activity Detection (VAD) using Silero

## How It Works

1. User connects and hears a greeting in English
2. User can ask the agent to switch to any supported language
3. The agent updates both TTS and STT language settings dynamically
4. A confirmation message is spoken in the new language
5. All subsequent conversation happens in the selected language
6. User can switch languages again at any time during the conversation

## Prerequisites

- Python 3.10+
- `livekit-agents`>=1.0
- LiveKit account and credentials
- API keys for:
  - OpenAI (for LLM capabilities)
  - Deepgram (for multilingual speech-to-text)
  - ElevenLabs (for multilingual text-to-speech)

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
   ELEVENLABS_API_KEY=your_elevenlabs_key
   ```

## Running the Agent

```bash
python elevenlabs_change_language.py dev
```

The agent will start in English. Try saying:
- "Switch to Spanish"
- "Can you speak French?"
- "Let's talk in German"
- "Change to Italian"

## Architecture Details

### Language Configuration

The agent maintains mappings for:
- **Language codes**: Standard two-letter codes (en, es, fr, de, it)
- **Language names**: Human-readable names for user feedback
- **Deepgram codes**: Some languages use region-specific codes (e.g., fr-CA for French)
- **Greetings**: Native language welcome messages

### Dynamic Updates

Language switching involves:
1. **TTS Update**: `self.tts.update_options(language=language_code)`
2. **STT Update**: `self.stt.update_options(language=deepgram_language)`
3. **State tracking**: Current language stored for duplicate prevention
4. **Confirmation**: Native language greeting confirms the switch

### Function Tools

Each language has a dedicated function tool:
- `switch_to_english()`
- `switch_to_spanish()`
- `switch_to_french()`
- `switch_to_german()`
- `switch_to_italian()`

This approach allows the LLM to understand natural language requests like "habla español" or "parlez-vous français?"

## Supported Languages

| Language | Code | Deepgram Code | Example Phrase |
|----------|------|---------------|----------------|
| English | en | en | "Hello! How can I help you?" |
| Spanish | es | es | "¡Hola! ¿Cómo puedo ayudarte?" |
| French | fr | fr-CA | "Bonjour! Comment puis-je vous aider?" |
| German | de | de | "Hallo! Wie kann ich Ihnen helfen?" |
| Italian | it | it | "Ciao! Come posso aiutarti?" |

## Possible Customizations

1. **Add More Languages**: Extend the language mappings and add corresponding function tools
2. **Voice Selection**: Use different ElevenLabs voices for different languages
3. **Regional Variants**: Add support for regional dialects (e.g., Mexican Spanish, British English)
4. **Language Detection**: Implement automatic language detection from user speech
5. **Model Selection**: Use different ElevenLabs models for specific language pairs

## Extra Notes

- **ElevenLabs Model**: Uses `eleven_turbo_v2_5` which supports multiple languages
- **Deepgram Model**: Uses `nova-2-general` with language-specific parameters
- **Language Persistence**: Current language is maintained throughout the session

## Example Conversation

```
Agent: "Hi there! I can speak in multiple languages..."
User: "Can you speak Spanish?"
Agent: "¡Hola! Ahora estoy hablando en español. ¿Cómo puedo ayudarte hoy?"
User: "¿Cuál es el clima?"
Agent: [Responds in Spanish about the weather]
User: "Now switch to French"
Agent: "Bonjour! Je parle maintenant en français. Comment puis-je vous aider aujourd'hui?"
```