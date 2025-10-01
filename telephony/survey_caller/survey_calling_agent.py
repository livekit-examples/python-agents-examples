"""
---
title: Survey Calling Agent
category: telephony
tags: [surveys, data-collection, csv-handling, automated-calling, metadata-processing]
difficulty: intermediate
description: Automated survey calling agent with CSV data management and response recording
demonstrates:
  - Survey data collection via phone calls
  - CSV file integration for response tracking
  - Metadata-based call configuration
  - Automated room deletion after completion
  - Function tools for survey response recording
  - Professional survey caller persona
---
"""

import logging
import os
import asyncio
import pandas as pd
import json
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import openai, silero, deepgram
from livekit.api import DeleteRoomRequest

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / '.env')

logger = logging.getLogger("calling-agent")
logger.setLevel(logging.INFO)

csv_file_path = Path(__file__).parent / "survey_data.csv"

class SurveyAgent(Agent):
    def __init__(self, question="Do you prefer chocolate or vanilla ice cream?", context=None, job_context=None) -> None:
        self.survey_question = question
        self.context = context or {}
        self.job_context = job_context
        self.survey_answer = None
        self.phone_number = self.context.get("phone_number", "unknown")
        # Adjust for 0-based indexing since row_index from metadata is 1-based
        self.row_index = self.context.get("row_index", 1)  # Default to 1 if not provided

        instructions = f"""
            You are conducting a brief phone survey. Your goal is to ask the following question:
            '{self.survey_question}'

            Be polite and professional. Introduce yourself as a survey caller named "Sam", ask the question,
            and thank them for their time. Keep the call brief and focused on getting their answer.
            Don't ask any follow-up questions.

            Note: When you have an answer to the question, use the `record_survey_answer` function
            to persist what the user said.
        """

        super().__init__(
            instructions=instructions,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            vad=silero.VAD.load()
        )

    @function_tool
    async def record_survey_answer(self, context: RunContext, answer: str):
        logger.info(f"Survey answer recorded: {answer}")
        logger.info(f"Row index: {self.row_index}")
        self.survey_answer = answer

        df = pd.read_csv(csv_file_path, dtype=str)
        logger.info(f"CSV contents before update: {df.head()}")

        df.loc[self.row_index - 1, 'Answer'] = answer
        df.loc[self.row_index - 1, 'Status'] = 'Completed'
        logger.info(f"CSV contents after update: {df.head()}")
        df.to_csv(csv_file_path, index=False)

        await asyncio.sleep(5)
        await self.job_context.api.room.delete_room(DeleteRoomRequest(
            room=self.job_context.room.name
        ))

        return None, f"[Call ended]"

async def entrypoint(ctx: JobContext):
    metadata_json = ctx.job.metadata
    logger.info(f"Received metadata: {metadata_json}")

    metadata = json.loads(metadata_json)
    phone_number = metadata.get("phone_number", "unknown")
    row_index = metadata.get("row_index", 1)
    question = metadata.get("question", "Do you prefer chocolate or vanilla ice cream?")

    logger.info(f"Parsed metadata - phone_number: {phone_number}, row_index: {row_index}, question: {question}")

    context = {
        "phone_number": phone_number,
        "row_index": row_index
    }

    session = AgentSession()
    agent = SurveyAgent(question=question, context=context, job_context=ctx)

    await session.start(
        agent=agent,
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="survey-agent"))