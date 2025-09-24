# Uninterruptable Agent

A voice assistant that demonstrates non-interruptible speech behavior using LiveKit's voice agents, useful for delivering information without interruption.

## Overview

**Uninterruptable Agent** - A voice-enabled assistant configured to complete its responses without being interrupted by user speech, demonstrating the `allow_interruptions=False` configuration option.

## Features

- **Simple Configuration**: Single parameter controls interruption behavior
- **Voice-Enabled**: Built using LiveKit's voice capabilities with support for:
  - Speech-to-Text (STT) using Deepgram
  - Large Language Model (LLM) using OpenAI GPT-4o
  - Text-to-Speech (TTS) using OpenAI
  - Voice Activity Detection (VAD) disabled during agent speech

## How It Works

1. User connects to the LiveKit room
2. Agent automatically starts speaking a long test message
3. User attempts to interrupt by speaking
4. Agent continues speaking without stopping
5. Only after the agent finishes can the user's input be processed
6. Subsequent responses are also uninterruptible

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
python uninterruptable.py dev
```

The agent will immediately start speaking a long message. Try interrupting to observe the non-interruptible behavior.

## Architecture Details

### Key Configuration

The critical setting that makes this agent uninterruptible:

```python
Agent(
    instructions="...",
    stt=deepgram.STT(),
    llm=openai.LLM(model="gpt-4o"),
    tts=openai.TTS(),
    allow_interruptions=False  # This prevents interruptions
)
```

### Behavior Comparison

| Setting | User Speaks While Agent Talks | Result |
|---------|------------------------------|---------|
| `allow_interruptions=True` (default) | Agent stops mid-sentence | User input processed immediately |
| `allow_interruptions=False` | Agent continues speaking | User input queued until agent finishes |

### Testing Approach

The agent automatically generates a long response on entry to facilitate testing:
```python
self.session.generate_reply(user_input="Say something somewhat long and boring so I can test if you're interruptable.")
```

## Use Cases

### When to Use Uninterruptible Agents

1. **Legal Disclaimers**: Must be read in full without interruption
2. **Emergency Instructions**: Critical safety information
3. **Tutorial Steps**: Sequential instructions that shouldn't be skipped
4. **Terms and Conditions**: Required complete playback


## Implementation Patterns

### Selective Non-Interruption

```python
# Make only critical messages uninterruptible
async def say_critical(self, message: str):
    self.allow_interruptions = False
    await self.session.say(message)
    self.allow_interruptions = True
```

## Important Considerations

- **User Experience**: Non-interruptible agents can be frustrating if overused
- **Message Length**: Keep uninterruptible segments reasonably short
- **Clear Indication**: Consider informing users when interruption is disabled
- **Fallback Options**: Provide alternative ways to skip or pause if needed

## Example Interaction

```
Agent: [Starts long message] "I'm going to tell you a very long and detailed story about..."
User: "Stop!" [Agent continues]
Agent: "...and that's why the chicken crossed the road. The moral of the story is..."
User: "Hey, wait!" [Agent still continues]
Agent: "...patience is a virtue." [Finally finishes]
User: "Finally! Can you hear me now?"
Agent: "Yes, I can hear you now. How can I help?"
```