---
title: ElevenLabs Change Language
category: pipeline-tts
tags: [pipeline-tts, openai, deepgram]
difficulty: intermediate
description: Shows how to use the ElevenLabs TTS model to change the language of the agent.
demonstrates:
  - Using the `tts.update_options` method to change the language of the agent.
  - Allowing agents to self-update their own options using function tools.
---

In this example you will build a multilingual voice agent that can switch between languages mid-call by updating ElevenLabs TTS and Deepgram STT on the fly. The agent greets callers in English, switches to Spanish, French, German, or Italian when asked, and replies with a native greeting in the new language.

## Prerequisites

- Python 3.10+ and `livekit-agents`>=1.0
- A `.env` at the repo root with:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  OPENAI_API_KEY=your_openai_key
  DEEPGRAM_API_KEY=your_deepgram_key
  ELEVENLABS_API_KEY=your_elevenlabs_key
  ```
- Install dependencies in one line:
  ```bash
  pip install python-dotenv "livekit-agents[deepgram,elevenlabs,openai]"
  ```

## Load configuration and logging

Initialize logging and load your `.env` so STT, TTS, and LLM plugins can find their keys.

```python
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference, function_tool
from livekit.plugins import deepgram, openai, elevenlabs, silero

logger = logging.getLogger("language-switcher")
logger.setLevel(logging.INFO)

load_dotenv()
```

## Define the language-switcher agent

Start with English STT/TTS plus GPT-4o, and give the agent short instructions about switching languages.

```python
class LanguageSwitcherAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                You can switch to a different language if asked.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(
                model="nova-2-general",
                language="en"
            ),
            llm=openai.LLM(model="gpt-4o"),
            tts=elevenlabs.TTS(
                model="eleven_turbo_v2_5",
                language="en"
            ),
            vad=silero.VAD.load()
        )
        self.current_language = "en"
```

## Map supported languages and greetings

Track friendly names, Deepgram language codes, and native greetings so you can update both TTS and STT together.

```python
        self.language_names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian"
        }

        self.deepgram_language_codes = {
            "en": "en",
            "es": "es",
            "fr": "fr-CA",
            "de": "de",
            "it": "it"
        }

        self.greetings = {
            "en": "Hello! I'm now speaking in English. How can I help you today?",
            "es": "¡Hola! Ahora estoy hablando en español. ¿Cómo puedo ayudarte hoy?",
            "fr": "Bonjour! Je parle maintenant en français. Comment puis-je vous aider aujourd'hui?",
            "de": "Hallo! Ich spreche jetzt Deutsch. Wie kann ich Ihnen heute helfen?",
            "it": "Ciao! Ora sto parlando in italiano. Come posso aiutarti oggi?"
        }
```

## Switch languages dynamically

Use a helper to update both audio pipelines and confirm with a greeting in the target language.

```python
    async def on_enter(self):
        await self.session.say("Hi there! I can speak in multiple languages including Spanish, French, German, and Italian. Just ask me to switch to any of these languages. How can I help you today?")

    async def _switch_language(self, language_code: str) -> None:
        """Helper method to switch the language"""
        if language_code == self.current_language:
            await self.session.say(f"I'm already speaking in {self.language_names[language_code]}.")
            return

        if self.tts is not None:
            self.tts.update_options(language=language_code)

        if self.stt is not None:
            deepgram_language = self.deepgram_language_codes.get(language_code, language_code)
            self.stt.update_options(language=deepgram_language)

        self.current_language = language_code

        await self.session.say(self.greetings[language_code])
```

## Expose tool calls for each language

Function tools give the LLM explicit hooks to change the language when the user asks.

```python
    @function_tool
    async def switch_to_english(self):
        """Switch to speaking English"""
        await self._switch_language("en")

    @function_tool
    async def switch_to_spanish(self):
        """Switch to speaking Spanish"""
        await self._switch_language("es")

    @function_tool
    async def switch_to_french(self):
        """Switch to speaking French"""
        await self._switch_language("fr")

    @function_tool
    async def switch_to_german(self):
        """Switch to speaking German"""
        await self._switch_language("de")

    @function_tool
    async def switch_to_italian(self):
        """Switch to speaking Italian"""
        await self._switch_language("it")
```

## Start the session

Launch the language-switcher agent and connect it to your LiveKit room.

```python
async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=LanguageSwitcherAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

## Run it

```bash
python elevenlabs_change_language.py console
```

Try saying:
- "Switch to Spanish"
- "Can you speak French?"
- "Let's talk in German"
- "Change to Italian"

## Supported languages

| Language | Code | Deepgram Code | Example Phrase |
|----------|------|---------------|----------------|
| English | en | en | "Hello! How can I help you?" |
| Spanish | es | es | "¡Hola! ¿Cómo puedo ayudarte?" |
| French | fr | fr-CA | "Bonjour! Comment puis-je vous aider?" |
| German | de | de | "Hallo! Wie kann ich Ihnen helfen?" |
| Italian | it | it | "Ciao! Come posso aiutarti?" |

## How it works

1. The agent greets in English and waits for a language change request.
2. A function tool routes to `_switch_language`, which updates both TTS and STT via `update_options`.
3. The agent tracks the current language to avoid redundant switches.
4. A native greeting confirms the change, and the rest of the conversation stays in the selected language until switched again.

## Complete example

```python
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference, function_tool
from livekit.plugins import deepgram, openai, elevenlabs, silero

logger = logging.getLogger("language-switcher")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

class LanguageSwitcherAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                You can switch to a different language if asked.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(
                model="nova-2-general",
                language="en"
            ),
            llm=openai.LLM(model="gpt-4o"),
            tts=elevenlabs.TTS(
                model="eleven_turbo_v2_5",
                language="en"
            ),
            vad=silero.VAD.load()
        )
        self.current_language = "en"

        self.language_names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian"
        }

        self.deepgram_language_codes = {
            "en": "en",
            "es": "es",
            "fr": "fr-CA",
            "de": "de",
            "it": "it"
        }

        self.greetings = {
            "en": "Hello! I'm now speaking in English. How can I help you today?",
            "es": "¡Hola! Ahora estoy hablando en español. ¿Cómo puedo ayudarte hoy?",
            "fr": "Bonjour! Je parle maintenant en français. Comment puis-je vous aider aujourd'hui?",
            "de": "Hallo! Ich spreche jetzt Deutsch. Wie kann ich Ihnen heute helfen?",
            "it": "Ciao! Ora sto parlando in italiano. Come posso aiutarti oggi?"
        }

    async def on_enter(self):
        await self.session.say(f"Hi there! I can speak in multiple languages including Spanish, French, German, and Italian. Just ask me to switch to any of these languages. How can I help you today?")

    async def _switch_language(self, language_code: str) -> None:
        """Helper method to switch the language"""
        if language_code == self.current_language:
            await self.session.say(f"I'm already speaking in {self.language_names[language_code]}.")
            return

        if self.tts is not None:
            self.tts.update_options(language=language_code)

        if self.stt is not None:
            deepgram_language = self.deepgram_language_codes.get(language_code, language_code)
            self.stt.update_options(language=deepgram_language)

        self.current_language = language_code

        await self.session.say(self.greetings[language_code])

    @function_tool
    async def switch_to_english(self):
        """Switch to speaking English"""
        await self._switch_language("en")

    @function_tool
    async def switch_to_spanish(self):
        """Switch to speaking Spanish"""
        await self._switch_language("es")

    @function_tool
    async def switch_to_french(self):
        """Switch to speaking French"""
        await self._switch_language("fr")

    @function_tool
    async def switch_to_german(self):
        """Switch to speaking German"""
        await self._switch_language("de")

    @function_tool
    async def switch_to_italian(self):
        """Switch to speaking Italian"""
        await self._switch_language("it")


async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=LanguageSwitcherAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

## Example conversation

```
Agent: "Hi there! I can speak in multiple languages..."
User: "Can you speak Spanish?"
Agent: "¡Hola! Ahora estoy hablando en español. ¿Cómo puedo ayudarte hoy?"
User: "¿Cuál es el clima?"
Agent: [Responds in Spanish about the weather]
User: "Now switch to French"
Agent: "Bonjour! Je parle maintenant en français. Comment puis-je vous aider aujourd'hui?"
```
