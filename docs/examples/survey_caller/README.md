---
title: Survey Calling Agent
category: telephony
tags: [surveys, data-collection, csv-handling, automated-calling, metadata-processing, deepgram, openai, cartesia]
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

This example demonstrates an automated survey calling agent that collects responses via phone calls, stores them in a CSV file, and cleans up the room after completion. The agent reads survey configuration from job metadata and uses function tools to record answers.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" python-dotenv pandas
  ```

## Load environment and define the AgentServer

Import the necessary modules, load environment variables, and create an AgentServer. The CSV file path is defined relative to the script location.

```python
import logging
import asyncio
import pandas as pd
import json
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, RunContext, function_tool
from livekit.plugins import silero
from livekit.api import DeleteRoomRequest

load_dotenv()

logger = logging.getLogger("calling-agent")
logger.setLevel(logging.INFO)

csv_file_path = Path(__file__).parent / "survey_data.csv"

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process to reduce connection latency. The VAD instance is stored in `proc.userdata` for reuse across sessions.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define the survey agent

Create a lightweight Agent that only contains instructions and a function tool. The survey question is passed dynamically and included in the instructions. The `record_survey_answer` tool saves the response to CSV and deletes the room after completion.

```python
class SurveyAgent(Agent):
    def __init__(self, question="Do you prefer chocolate or vanilla ice cream?", context=None, job_context=None) -> None:
        self.survey_question = question
        self.context = context or {}
        self.job_context = job_context
        self.survey_answer = None
        self.phone_number = self.context.get("phone_number", "unknown")
        self.row_index = self.context.get("row_index", 1)

        instructions = f"""
            You are conducting a brief phone survey. Your goal is to ask the following question:
            '{self.survey_question}'

            Be polite and professional. Introduce yourself as a survey caller named "Sam", ask the question,
            and thank them for their time. Keep the call brief and focused on getting their answer.
            Don't ask any follow-up questions.

            Note: When you have an answer to the question, use the `record_survey_answer` function
            to persist what the user said.
        """

        super().__init__(instructions=instructions)

    @function_tool
    async def record_survey_answer(self, context: RunContext, answer: str):
        logger.info(f"Survey answer recorded: {answer}")
        self.survey_answer = answer

        df = pd.read_csv(csv_file_path, dtype=str)
        df.loc[self.row_index - 1, 'Answer'] = answer
        df.loc[self.row_index - 1, 'Status'] = 'Completed'
        df.to_csv(csv_file_path, index=False)

        await asyncio.sleep(5)
        await self.job_context.api.room.delete_room(DeleteRoomRequest(
            room=self.job_context.room.name
        ))

        return None, f"[Call ended]"
```

## Create the RTC session entrypoint

Parse survey configuration from job metadata, create an AgentSession with STT/LLM/TTS/VAD, and start the session. The `ctx.connect()` call binds the room after session startup.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    metadata_json = ctx.job.metadata
    metadata = json.loads(metadata_json)
    phone_number = metadata.get("phone_number", "unknown")
    row_index = metadata.get("row_index", 1)
    question = metadata.get("question", "Do you prefer chocolate or vanilla ice cream?")

    context = {
        "phone_number": phone_number,
        "row_index": row_index
    }

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = SurveyAgent(question=question, context=context, job_context=ctx)

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()
```

## Run the server

The `cli.run_app()` function starts the agent server and manages the worker lifecycle.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```console
python survey_calling_agent.py console
```

## How it works

1. Job metadata contains the survey question, phone number, and CSV row index.
2. The agent introduces itself as "Sam" and asks the configured question.
3. When the user responds, the agent calls `record_survey_answer` to save the response.
4. The function tool updates the CSV file with the answer and status.
5. After a brief delay, the room is automatically deleted to clean up resources.

## Full example

```python
import logging
import asyncio
import pandas as pd
import json
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, RunContext, function_tool
from livekit.plugins import silero
from livekit.api import DeleteRoomRequest

load_dotenv()

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
        self.row_index = self.context.get("row_index", 1)

        instructions = f"""
            You are conducting a brief phone survey. Your goal is to ask the following question:
            '{self.survey_question}'

            Be polite and professional. Introduce yourself as a survey caller named "Sam", ask the question,
            and thank them for their time. Keep the call brief and focused on getting their answer.
            Don't ask any follow-up questions.

            Note: When you have an answer to the question, use the `record_survey_answer` function
            to persist what the user said.
        """

        super().__init__(instructions=instructions)

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

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

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

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = SurveyAgent(question=question, context=context, job_context=ctx)

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
