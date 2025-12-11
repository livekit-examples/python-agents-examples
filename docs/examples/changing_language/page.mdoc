---
title: ElevenLabs Change Language
category: pipeline-tts
tags: [pipeline-tts, elevenlabs, deepgram, openai]
difficulty: intermediate
description: Shows how to use the ElevenLabs TTS model to change the language of the agent.
demonstrates:
  - Using the update_options() method to change the language of STT and TTS
  - Allowing agents to self-update their own options using function tools
  - Accessing session STT/TTS from within an agent
---

This example demonstrates how to build a multilingual voice agent that can switch between languages mid-call by updating ElevenLabs TTS and Deepgram STT on the fly. The agent greets callers in English, switches to Spanish, French, German, or Italian when asked, and replies with a native greeting in the new language.

## Prerequisites

- Add a `.env` in this directory with your LiveKit and provider credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  DEEPGRAM_API_KEY=your_deepgram_key
  ELEVENLABS_API_KEY=your_elevenlabs_key
  ```
- Install dependencies:
  ```bash
  pip install python-dotenv "livekit-agents[silero,deepgram,elevenlabs]"
  ```

## Load environment, logging, and define an AgentServer

Start by loading your environment variables and setting up logging. Define an `AgentServer` which wraps your application and handles the worker lifecycle.

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference, function_tool
from livekit.plugins import deepgram, elevenlabs, silero

load_dotenv()

logger = logging.getLogger("language-switcher")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process using the `setup_fnc`.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define the language-switcher agent

Create a lightweight agent with instructions and language configuration maps. The agent tracks the current language and has lookup tables for language names, Deepgram codes, and native greetings.

```python
class LanguageSwitcherAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                You can switch to a different language if asked.
                Don't use any unpronouncable characters.
            """
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
```

## Switch languages dynamically

Use a helper method to update both STT and TTS pipelines via the session. The agent accesses `self.session.tts` and `self.session.stt` to call `update_options()` and then confirms the switch with a greeting in the target language.

```python
    async def on_enter(self):
        await self.session.say("Hi there! I can speak in multiple languages including Spanish, French, German, and Italian. Just ask me to switch to any of these languages. How can I help you today?")

    async def _switch_language(self, language_code: str) -> None:
        """Helper method to switch the language"""
        if language_code == self.current_language:
            await self.session.say(f"I'm already speaking in {self.language_names[language_code]}.")
            return

        # Access TTS and STT from the session
        if self.session.tts is not None:
            self.session.tts.update_options(language=language_code)

        if self.session.stt is not None:
            deepgram_language = self.deepgram_language_codes.get(language_code, language_code)
            self.session.stt.update_options(language=deepgram_language)

        self.current_language = language_code

        await self.session.say(self.greetings[language_code])
```

## Expose function tools for each language

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

## Define the RTC session entrypoint

Create an `AgentSession` with Deepgram STT, ElevenLabs TTS, and inference-based LLM. The STT and TTS are configured with English as the default language.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=deepgram.STT(model="nova-2-general", language="en"),
        llm=inference.LLM(model="openai/gpt-4o"),
        tts=elevenlabs.TTS(model="eleven_turbo_v2_5", language="en"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=LanguageSwitcherAgent(), room=ctx.room)
    await ctx.connect()
```

## Run the server

```python
if __name__ == "__main__":
    cli.run_app(server)
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
2. A function tool routes to `_switch_language()`, which updates both TTS and STT via `update_options()`.
3. The agent tracks the current language to avoid redundant switches.
4. A native greeting confirms the change, and the rest of the conversation stays in the selected language until switched again.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference, function_tool
from livekit.plugins import deepgram, elevenlabs, silero

load_dotenv()

logger = logging.getLogger("language-switcher")
logger.setLevel(logging.INFO)


class LanguageSwitcherAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                You can switch to a different language if asked.
                Don't use any unpronouncable characters.
            """
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
        await self.session.say("Hi there! I can speak in multiple languages including Spanish, French, German, and Italian. Just ask me to switch to any of these languages. How can I help you today?")

    async def _switch_language(self, language_code: str) -> None:
        """Helper method to switch the language"""
        if language_code == self.current_language:
            await self.session.say(f"I'm already speaking in {self.language_names[language_code]}.")
            return

        # Access TTS and STT from the session
        if self.session.tts is not None:
            self.session.tts.update_options(language=language_code)

        if self.session.stt is not None:
            deepgram_language = self.deepgram_language_codes.get(language_code, language_code)
            self.session.stt.update_options(language=deepgram_language)

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


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=deepgram.STT(model="nova-2-general", language="en"),
        llm=inference.LLM(model="openai/gpt-4o"),
        tts=elevenlabs.TTS(model="eleven_turbo_v2_5", language="en"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=LanguageSwitcherAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
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
