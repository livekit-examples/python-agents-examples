---
title: NPC Character State Tracking
category: state-management
tags: [state-management, deepgram, openai, cartesia]
difficulty: advanced
description: Advanced NPC system with dynamic rapport tracking and conversation state management
demonstrates:
  - Complex character state tracking with rapport system
  - Multi-agent conversation flows and switching
  - Topic-based conversation management
  - Dynamic response variation based on relationship state
  - Agent inheritance patterns for character consistency
  - Session data persistence across interactions
---

This example creates an immersive NPC (non-player character) named Brenna, an innkeeper at "The Winking Stoat" tavern. The agent tracks rapport with the user—being curt and unhelpful at low rapport, but warm and informative when trust is earned. It demonstrates state management, agent inheritance patterns, and dynamic response variation based on relationship state.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero,deepgram,openai,cartesia]" python-dotenv pydantic
  ```

## Set up logging and create the AgentServer

Load environment variables and configure logging. Create an AgentServer to manage the agent lifecycle.

```python
import logging
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import List, Annotated
from enum import Enum
from pydantic import Field

from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess, cli, Agent, inference, function_tool
from livekit.plugins import silero
from livekit import api

load_dotenv()
logger = logging.getLogger("npc-flow")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process. This runs before any sessions start and stores the VAD instance in `proc.userdata` so it can be reused.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define the NPC data model

Use a dataclass to store the NPC's state: rapport score and visited topics. This data persists across the conversation via `session.userdata`.

```python
@dataclass
class NPCData:
    """Stores NPC conversation state and rapport score."""
    rapport: int = 0
    topics_visited: List[str] = field(default_factory=list)
```

## Create a base agent class for shared functionality

The base agent handles common setup like storing the job context and provides the rapport adjustment tool. This pattern allows multiple agent variants to share functionality.

```python
class BaseAgent(Agent):
    """Base agent class handling common setup and job context."""
    def __init__(self, job_context: JobContext, instructions: str) -> None:
        self.job_context = job_context
        super().__init__(instructions=instructions)

    @function_tool
    async def adjust_rapport(self, delta: int) -> int:
        """
        Adjust the NPC's rapport score by delta and return the new score.
        A score of -100 is the lowest, and means they will tell you to leave.
        A score of 100 is the highest, and means they will be very friendly.
        """
        data: NPCData = self.session.userdata
        data.rapport += delta
        logger.info(f"Rapport adjusted by {delta}. New rapport: {data.rapport}")
        return data.rapport
```

## Define the NPC agent with topic-based interactions

The NPC agent includes rich character instructions and function tools for discussing different topics. The response tone varies based on the current rapport score—low rapport gets brief, curt responses while high rapport unlocks friendlier, more detailed information.

```python
class NPCAgent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions=(
                "You are Brenna, the innkeeper of The Winking Stoat—a creaky old tavern. "
                "You speak like a person: distracted if busy, skeptical if unsure, warm only when it's earned. "
                "If rapport is low, you're short and unhelpful. If rapport is high, you share secrets and warnings."
            )
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply()

    class NPCTopic(str, Enum):
        LEGENDS = "local_legends"
        JOBS = "jobs_around_town"
        SALE = "for_sale"
        IMPORTANT = "important_info"

    @function_tool
    async def choose_topic(
        self,
        topic: Annotated[NPCTopic, Field(description="Which topic do you want to ask the NPC about?")]
    ) -> None:
        """Choose a topic to ask the NPC about."""
        data: NPCData = self.session.userdata
        data.topics_visited.append(topic.value)
        # Route to appropriate handler based on topic
        if topic == self.NPCTopic.LEGENDS:
            await self.share_legend()
        elif topic == self.NPCTopic.JOBS:
            await self.describe_jobs()
        # ... etc

    @function_tool
    async def share_legend(self) -> None:
        """Share a local legend with the user, with detail and tone based on rapport."""
        data: NPCData = self.session.userdata
        if data.rapport < 3:
            await self.session.generate_reply(user_input="Share a well known legend, but keep it very brief.")
        else:
            await self.session.generate_reply(user_input="Share a rare legend, like you would with a friend.")
```

## Define the RTC session entrypoint

Create the AgentSession with STT, LLM, TTS, and VAD configured. Initialize the session userdata with an empty NPCData instance to track state.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession[NPCData](
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    session.userdata = NPCData()

    await session.start(agent=NPCAgent(job_context=ctx), room=ctx.room)
    await ctx.connect()
```

## Run the server

The `cli.run_app()` function starts the agent server, manages the worker lifecycle, and processes incoming jobs.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

Run the agent using the `console` command for local testing:

```bash
python state_tracking.py console
```

To test with a real LiveKit room, use dev mode:

```bash
python state_tracking.py dev
```

## How it works

1. The session initializes with `NPCData` storing rapport (0) and visited topics.
2. When users interact, the NPC's `adjust_rapport` tool modifies the rapport score.
3. Topic-based functions check rapport before responding—low rapport means brief, unhelpful answers.
4. High rapport unlocks detailed information, secrets, and friendly conversation.
5. The `NPCSummaryAgent` can end conversations gracefully and clean up the room.

## Full example

```python
import logging
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import List, Annotated
from enum import Enum
from pydantic import Field

from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess, cli, Agent, inference, function_tool
from livekit.plugins import silero
from livekit import api

# Load environment and configure logger
load_dotenv()
logger = logging.getLogger("npc-flow")
logger.setLevel(logging.INFO)

@dataclass
class NPCData:
    """Stores NPC conversation state and rapport score."""
    rapport: int = 0
    topics_visited: List[str] = field(default_factory=list)

class BaseAgent(Agent):
    """Base agent class handling common setup and job context."""
    def __init__(self, job_context: JobContext, instructions: str) -> None:
        self.job_context = job_context
        super().__init__(instructions=instructions)

    @function_tool
    async def adjust_rapport(self, delta: int) -> int:
        """
        Adjust the NPC's rapport score by delta and return the new score.
        A score of -100 is the lowest, and means they will tell you to leave.
        A score of 100 is the highest, and means they will be very friendly.
        """
        data: NPCData = self.session.userdata
        data.rapport += delta
        logger.info(f"Rapport adjusted by {delta}. New rapport: {data.rapport}")
        return data.rapport

class NPCAgent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions=(
                "You are Brenna, the innkeeper of The Winking Stoat—a creaky old tavern tucked off the village square. "
                "You are not an assistant. You don't explain things like a tour guide or offer summaries. You speak like a person: distracted if busy, skeptical if unsure, warm only when it's earned. "
                "You've run this place for years. You know every local by voice, you spot liars on their first word, and you remember who paid their tab. "
                "Speak casually, like someone wiping down a mug while half-listening. Use contractions, drop words sometimes, let your speech trail off if you're thinking. "
                "You're not a quest-giver. You'll talk if someone's interesting—but you've got little patience for fools or questions with obvious answers. "
                "If rapport is low, you're short, distracted, maybe even rude. If rapport is high, you might offer a hot meal, a warning, or something you heard in confidence. "
                "Your memory is long. You might reference a strange traveler last week, the sound of wolves last night, or the time someone pissed in the hearth. "
                "You don't explain yourself. You live here. This is your inn. Speak like you're part of this world, and always stay in character."
            )
        )

    async def on_enter(self) -> None:
        await self.session.generate_reply()

    class NPCTopic(str, Enum):
        LEGENDS = "local_legends"
        JOBS = "jobs_around_town"
        SALE = "for_sale"
        IMPORTANT = "important_info"

    @function_tool
    async def choose_topic(
        self,
        topic: Annotated[
            NPCTopic,
            Field(description="Which topic do you want to ask the NPC about?")
        ]
    ) -> None:
        """
        Choose a topic to ask the NPC about.

        Args:
            topic: The topic to discuss (must be one of the defined enum values)
        """
        data: NPCData = self.session.userdata
        data.topics_visited.append(topic.value)
        if topic == self.NPCTopic.LEGENDS:
            await self.share_legend()
        elif topic == self.NPCTopic.JOBS:
            await self.describe_jobs()
        elif topic == self.NPCTopic.SALE:
            await self.list_items_for_sale()
        else:
            await self.share_important_info()

    @function_tool
    async def share_legend(self) -> None:
        """Share a local legend with the user, with detail and tone based on rapport."""
        data: NPCData = self.session.userdata
        if data.rapport < 3:
            await self.session.generate_reply(user_input="Share a well known legend, but keep it very brief.")
        else:
            await self.session.generate_reply(user_input="Share a rare legend, like you would with a friend.")

    @function_tool
    async def describe_jobs(self) -> None:
        """Describe jobs around town, with detail and tone based on rapport."""
        data: NPCData = self.session.userdata
        if data.rapport < 3:
            await self.session.generate_reply(user_input="Describe jobs around town, but be vague and not very helpful.")
        else:
            await self.session.generate_reply(user_input="Describe jobs around town, and offer helpful details as you would to a friend.")

    @function_tool
    async def list_items_for_sale(self) -> None:
        """List items for sale, with detail and tone based on rapport."""
        data: NPCData = self.session.userdata
        if data.rapport < 3:
            await self.session.generate_reply(user_input="List only the most basic items for sale, and be a little curt.")
        else:
            await self.session.generate_reply(user_input="List all items for sale, and be friendly and welcoming.")

    @function_tool
    async def share_important_info(self) -> None:
        """Share important info, with detail and tone based on rapport."""
        data: NPCData = self.session.userdata
        if data.rapport < 3:
            await self.session.generate_reply(user_input="Give an unhelpful or generic answer to 'is there anything important I should know?'")
        else:
            await self.session.generate_reply(user_input="Share a local secret or warning that only a friend would get.")

    @function_tool
    async def return_to_main(self) -> Agent:
        """
        Return to the main NPC conversation.
        """
        return NPCAgent(job_context=self.job_context)


class NPCSummaryAgent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="NPC thanks the traveler and ends the conversation."
        )

    async def on_enter(self) -> None:
        data: NPCData = self.session.userdata
        await self.session.say(
            f"Thank you for your company! Our rapport is now {data.rapport}. Safe travels!"
        )
        logger.info("NPC conversation ended, closing session.")
        await self.session.aclose()
        try:
            await self.job_context.api.room.delete_room(
                api.DeleteRoomRequest(room=self.job_context.room.name)
            )
        except Exception as e:
            logger.error(f"Error deleting room: {e}")

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession[NPCData](
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    session.userdata = NPCData()

    await session.start(agent=NPCAgent(job_context=ctx), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
