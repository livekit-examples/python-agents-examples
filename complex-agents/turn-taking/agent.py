"""
---
title: Turn-Taking Detection Agent
category: complex-agents
tags: [eou_probability, turn_detection, gladia_stt, multilingual, rpc_eou_updates]
difficulty: advanced
description: Agent that exposes end-of-utterance probability for turn-taking research
demonstrates:
  - Custom turn detector wrapper exposing EOU probability
  - Real-time EOU probability RPC updates to frontend
  - Multilingual STT with Gladia
  - Percentage formatting for tiny probabilities
  - Session userdata for RPC communication
  - STT event processing for transcript logging
---
"""

import logging
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import AsyncIterable, Optional
from dataclasses import dataclass
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero, gladia
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("turn-taking")
logger.setLevel(logging.INFO)

@dataclass
class TurnTakingUserData:
    ctx: JobContext
    session: AgentSession = None

class CustomTurnDetector:
    """Wrapper around MultilingualModel that exposes EOU probability"""

    def __init__(self, userdata: TurnTakingUserData = None):
        self._model = MultilingualModel()
        self.last_eou_probability = None
        self.userdata = userdata

    def unlikely_threshold(self, language: str | None) -> float | None:
        return self._model.unlikely_threshold(language)

    def supports_language(self, language: str | None) -> bool:
        return self._model.supports_language(language)

    async def predict_end_of_turn(self, chat_ctx: llm.ChatContext) -> float:
        probability = await self._model.predict_end_of_turn(chat_ctx)
        self.last_eou_probability = probability

        percentage = probability * 100

        if percentage < 0.001:
            formatted_percentage = f"{percentage:.3f}%"
        else:
            formatted_percentage = f"{percentage:.3f}%"

        print(f"EOU Probability: {formatted_percentage}")

        await self._send_eou_to_frontend(probability)

        return probability

    async def _send_eou_to_frontend(self, probability: float) -> None:
        """Send EOU probability to frontend via RPC"""
        if not self.userdata or not self.userdata.ctx:
            logger.warning("No userdata or context available to send EOU RPC")
            return

        try:
            room = self.userdata.ctx.room
            if not room:
                logger.warning("No room available to send EOU RPC")
                return

            remote_participants = list(room.remote_participants.values())
            if not remote_participants:
                logger.warning("No remote participants found to send EOU RPC")
                return

            client_participant = remote_participants[0]

            payload = {
                "eou_probability": probability,
                "percentage": probability * 100
            }

            await room.local_participant.perform_rpc(
                destination_identity=client_participant.identity,
                method="client.eou_update",
                payload=json.dumps(payload)
            )
            logger.debug(f"Sent EOU RPC to frontend: {probability:.4f}")
        except Exception as e:
            logger.error(f"Failed to send EOU RPC to frontend: {e}")

class SimpleAgent(Agent):
    def __init__(self, userdata: TurnTakingUserData) -> None:
        self.custom_turn_detector = CustomTurnDetector(userdata)
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            vad=silero.VAD.load(),
            turn_detection=self.custom_turn_detector
        )

    async def on_enter(self):
        self.session.generate_reply(user_input="Greet the user warmly.")

    def get_last_eou_probability(self) -> float | None:
        """Get the last calculated EOU probability"""
        return self.custom_turn_detector.last_eou_probability

    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        parent_stream = super().stt_node(text, model_settings)

        async def process_stream():
            async for event in parent_stream:
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text
                    print(transcript)

                yield event

        return process_stream()

async def entrypoint(ctx: JobContext):
    userdata = TurnTakingUserData(ctx=ctx)

    session = AgentSession[TurnTakingUserData](
        userdata=userdata,
        vad=silero.VAD.load(),
        stt=gladia.STT(
            languages=["en", "fr", "de", "pt", "zh", "ja", "ko", "id", "ru", "nl", "tr", "es", "it"]
        ),
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
        turn_detection=CustomTurnDetector(userdata),
    )

    userdata.session = session

    agent = SimpleAgent(userdata)

    await session.start(agent=agent, room=ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
