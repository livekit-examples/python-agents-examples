"""
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
"""
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai, elevenlabs, silero

logger = logging.getLogger("language-switcher")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

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