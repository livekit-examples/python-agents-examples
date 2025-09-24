"""
---
title: Diarization
category: pipeline-stt
tags: [pipeline-stt, openai, deepgram]
difficulty: intermediate
description: Shows how to use the Speechmatics STT model with diarization.
demonstrates:
  - Using the Speechmatics STT model with diarization.
  - Allow speakers to label themselves when they're speaking using function tools.
  - Using the `stt_node` method to override the default STT node and add custom logic to detect speaker changes.
---
"""
from pathlib import Path
from dotenv import load_dotenv
from typing import AsyncIterable, Optional
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession, ModelSettings, RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import openai, silero, speechmatics
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("speechmatics-stt")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

@dataclass
class SpeechmaticsUserData:
    """UserData class to store speaker names mapping"""
    ctx: JobContext
    session: AgentSession = None
    speaker_names: dict[str, str] = field(default_factory=dict)

class DiarizationAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. Transcripts will come in with speaker IDs, they'll be in pieces but that's okay.
                Just have a natural conversation with the user. You can also help set names for different speakers to make conversations more personal.
            """,
            stt = speechmatics.STT(
                transcription_config=speechmatics.types.TranscriptionConfig(
                    operating_point="enhanced",
                    enable_partials=True,
                    language="en",
                    output_locale="en-US",
                    diarization="speaker",
                ),
                audio_settings=speechmatics.types.AudioSettings(
                    encoding="pcm_s16le",
                    sample_rate=16000,
                )
            ),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )

    @function_tool
    async def set_speaker_name(self, context: RunContext[SpeechmaticsUserData], speaker_id: str, name: str):
        """
        Set a name for a speaker ID. This will replace the speaker ID in future transcripts.

        Args:
            speaker_id: The speaker ID (e.g., "S1", "S2")
            name: The name to assign to this speaker
        """
        if context.userdata:
            context.userdata.speaker_names[speaker_id] = name
            logger.info(f"Set speaker {speaker_id} to name: {name}")
            return f"I'll now refer to speaker {speaker_id} as {name}."
        return "Error: Could not set speaker name."

    @function_tool
    async def get_speaker_names(self, context: RunContext[SpeechmaticsUserData]):
        """
        Get all current speaker name mappings.
        """
        if context.userdata and context.userdata.speaker_names:
            names_list = [f"{speaker_id}: {name}" for speaker_id, name in context.userdata.speaker_names.items()]
            return f"Current speaker names: {', '.join(names_list)}"
        return "No speaker names have been set yet."

    @function_tool
    async def clear_speaker_names(self, context: RunContext[SpeechmaticsUserData]):
        """
        Clear all speaker name mappings.
        """
        if context.userdata:
            context.userdata.speaker_names.clear()
            logger.info("Cleared all speaker names")
            return "All speaker names have been cleared."
        return "Error: Could not clear speaker names."

    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        parent_stream = super().stt_node(text, model_settings)

        async def process_stream():
            current_speaker_id = None
            async for event in parent_stream:
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text
                    speaker_id = event.alternatives[0].speaker_id
                    changed_speaker = (current_speaker_id != speaker_id)
                    if changed_speaker:
                        logger.info(f"starting speaker: {speaker_id}")
                        current_speaker_id = speaker_id

                        speaker_name = speaker_id
                        if hasattr(self, 'session') and self.session and self.session.userdata:
                            speaker_name = self.session.userdata.speaker_names.get(speaker_id, speaker_id)

                        modified_transcript = f"{speaker_name}: {transcript}"
                        event.alternatives[0].text = modified_transcript

                yield event

        return process_stream()

    async def on_enter(self):
        await self.session.say(f"Hi there! Is there anything I can help you with?")

async def entrypoint(ctx: JobContext):
    userdata = SpeechmaticsUserData(ctx=ctx)

    session = AgentSession[SpeechmaticsUserData](
        userdata=userdata
    )

    userdata.session = session

    await session.start(
        agent=DiarizationAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))