---
title: SIP Lifecycle Management Agent
category: telephony
tags: [telephony, sip, deepgram, openai, elevenlabs]
difficulty: advanced
description: Advanced SIP agent demonstrating complete call lifecycle management
demonstrates:
  - SIP participant management and addition
  - Call status tracking and event handling
  - Room management and deletion
  - Participant attribute monitoring
  - Call lifecycle event handlers
  - Function tools for call operations
---

This example demonstrates advanced SIP (Session Initiation Protocol) call management. The agent can add new SIP participants to a call, track call status changes, list participants, and cleanly end calls. It monitors SIP-specific participant attributes like call status, trunk information, and phone numbers.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials and SIP trunk ID:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  SIP_TRUNK_ID=your_sip_trunk_id
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero,deepgram,openai,elevenlabs]" python-dotenv
  ```

## Set up logging and create the AgentServer

Load environment variables and configure logging. Create an AgentServer to manage the agent lifecycle.

```python
import asyncio
import logging
import os
import uuid
from dotenv import load_dotenv
from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess, cli, Agent, inference, RunContext, function_tool
from livekit import rtc
from livekit import api
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("sip-lifecycle-agent")
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

## Define the SIP Lifecycle Agent with function tools

The agent stores a reference to the job context to access the LiveKit API. Function tools allow the agent to add SIP participants, end calls, and list participants based on user voice commands.

```python
class SIPLifecycleAgent(Agent):
    def __init__(self, job_context=None) -> None:
        self.job_context = job_context
        super().__init__(
            instructions="""
                You are a helpful assistant demonstrating SIP call lifecycle management.
                You can add SIP participants and end the call when requested.
            """,
        )

    @function_tool
    async def add_sip_participant(self, context: RunContext, phone_number: str):
        """Add a SIP participant to the current call."""
        if not self.job_context:
            logger.error("No job context available")
            await self.session.say("I'm sorry, I can't add participants at this time.")
            return None, "Failed to add SIP participant: No job context available"

        room_name = self.job_context.room.name
        identity = f"sip_{uuid.uuid4().hex[:8]}"
        sip_trunk_id = os.environ.get('SIP_TRUNK_ID')

        try:
            response = await self.job_context.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    sip_trunk_id=sip_trunk_id,
                    sip_call_to=phone_number,
                    room_name=room_name,
                    participant_identity=identity,
                    participant_name=f"SIP Participant {phone_number}",
                    krisp_enabled=True
                )
            )
            return None, f"Added SIP participant {phone_number} to the call."
        except Exception as e:
            logger.error(f"Error adding SIP participant: {e}")
            await self.session.say(f"I'm sorry, I couldn't add {phone_number} to the call.")
            return None, f"Failed to add SIP participant: {e}"

    @function_tool
    async def end_call(self, context: RunContext):
        """End the current call by deleting the room."""
        if not self.job_context:
            return None, "Failed to end call: No job context available"

        room_name = self.job_context.room.name
        try:
            await context.session.generate_reply(
                instructions="Thank you for your time. I'll be ending this call now. Goodbye!"
            )
            await self.job_context.api.room.delete_room(
                api.DeleteRoomRequest(room=room_name)
            )
            return None, "Call ended successfully."
        except Exception as e:
            return None, f"Failed to end call: {e}"

    @function_tool
    async def log_participants(self, context: RunContext):
        """Log all participants in the current room."""
        if not self.job_context:
            return None, "Failed to list participants: No job context available"

        room_name = self.job_context.room.name
        try:
            response = await self.job_context.api.room.list_participants(
                api.ListParticipantsRequest(room=room_name)
            )
            participants = response.participants
            await self.session.say(f"There are {len(participants)} participants in this call.")
            return None, f"Listed {len(participants)} participants in the room."
        except Exception as e:
            return None, f"Failed to list participants: {e}"

    async def on_enter(self):
        self.session.generate_reply()
```

## Define the RTC session entrypoint with event handlers

Create the AgentSession with models configured. After starting the session, set up event handlers to monitor participant connections and attribute changes. These handlers log SIP-specific information like call status and phone numbers.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="elevenlabs/eleven_multilingual_v2"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = SIPLifecycleAgent(job_context=ctx)

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

    def on_participant_connected_handler(participant: rtc.RemoteParticipant):
        asyncio.create_task(async_on_participant_connected(participant))

    async def async_on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"New participant connected: {participant.identity}")

        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            if participant.attributes:
                call_status = participant.attributes.get('sip.callStatus', 'Unknown')
                phone_number = participant.attributes.get('sip.phoneNumber', 'Unknown')
                logger.info(f"SIP Call Status: {call_status}, Phone: {phone_number}")

        await agent.session.say(f"Welcome, {participant.name or participant.identity}!")

    ctx.room.on("participant_connected", on_participant_connected_handler)
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
python sip_lifecycle.py console
```

For testing with real SIP calls, use dev mode:

```bash
python sip_lifecycle.py dev
```

## How it works

1. The agent initializes with function tools for SIP operations.
2. When a new participant joins, the event handler logs their SIP attributes (call status, phone number, trunk ID).
3. Users can ask the agent to add participants by phone number—the agent uses the LiveKit SIP API to dial out.
4. The agent tracks call status changes (dialing, ringing, active, hangup) via attribute change events.
5. Users can end the call, which triggers a goodbye message and room deletion.

## Full example

```python
import asyncio
import logging
import os
import uuid
from dotenv import load_dotenv
from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess, cli, Agent, inference, RunContext, function_tool
from livekit import rtc
from livekit import api
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("sip-lifecycle-agent")
logger.setLevel(logging.INFO)

class SIPLifecycleAgent(Agent):
    def __init__(self, job_context=None) -> None:
        self.job_context = job_context
        super().__init__(
            instructions="""
                You are a helpful assistant demonstrating SIP call lifecycle management.
                You can add SIP participants and end the call when requested.
            """,
        )

    @function_tool
    async def add_sip_participant(self, context: RunContext, phone_number: str):
        """
        Add a SIP participant to the current call.

        Args:
            context: The call context
            phone_number: The phone number to call
        """
        if not self.job_context:
            logger.error("No job context available")
            await self.session.say("I'm sorry, I can't add participants at this time.")
            return None, "Failed to add SIP participant: No job context available"

        room_name = self.job_context.room.name

        identity = f"sip_{uuid.uuid4().hex[:8]}"

        sip_trunk_id = os.environ.get('SIP_TRUNK_ID')

        logger.info(f"Adding SIP participant with phone number {phone_number} to room {room_name}")

        try:
            response = await self.job_context.api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    sip_trunk_id=sip_trunk_id,
                    sip_call_to=phone_number,
                    room_name=room_name,
                    participant_identity=identity,
                    participant_name=f"SIP Participant {phone_number}",
                    krisp_enabled=True
                )
            )

            logger.info(f"Successfully added SIP participant: {response}")
            return None, f"Added SIP participant {phone_number} to the call."

        except Exception as e:
            logger.error(f"Error adding SIP participant: {e}")
            await self.session.say(f"I'm sorry, I couldn't add {phone_number} to the call.")
            return None, f"Failed to add SIP participant: {e}"

    @function_tool
    async def end_call(self, context: RunContext):
        """
        End the current call by deleting the room.
        """
        if not self.job_context:
            logger.error("No job context available")
            await self.session.say("I'm sorry, I can't end the call at this time.")
            return None, "Failed to end call: No job context available"

        room_name = self.job_context.room.name
        logger.info(f"Ending call by deleting room {room_name}")

        try:
            await context.session.generate_reply(
                instructions="Thank you for your time. I'll be ending this call now. Goodbye!"
            )
            await self.job_context.api.room.delete_room(
                api.DeleteRoomRequest(room=room_name)
            )

            logger.info(f"Successfully deleted room {room_name}")
            return None, "Call ended successfully."

        except Exception as e:
            logger.error(f"Error ending call: {e}")
            return None, f"Failed to end call: {e}"

    @function_tool
    async def log_participants(self, context: RunContext):
        """
        Log all participants in the current room.
        """
        if not self.job_context:
            logger.error("No job context available")
            await self.session.say("I'm sorry, I can't list participants at this time.")
            return None, "Failed to list participants: No job context available"

        room_name = self.job_context.room.name
        logger.info(f"Logging participants in room {room_name}")

        try:
            response = await self.job_context.api.room.list_participants(
                api.ListParticipantsRequest(room=room_name)
            )

            participants = response.participants
            participant_info = []

            for p in participants:
                participant_info.append({
                    "identity": p.identity,
                    "name": p.name,
                    "state": p.state,
                    "is_publisher": p.is_publisher
                })

            logger.info(f"Participants in room {room_name}: {participant_info}")

            await self.session.say(f"There are {len(participants)} participants in this call.")

            return None, f"Listed {len(participants)} participants in the room."

        except Exception as e:
            logger.error(f"Error listing participants: {e}")
            return None, f"Failed to list participants: {e}"

    async def on_enter(self):
        self.session.generate_reply()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="elevenlabs/eleven_multilingual_v2"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = SIPLifecycleAgent(job_context=ctx)

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

    def on_participant_connected_handler(participant: rtc.RemoteParticipant):
        asyncio.create_task(async_on_participant_connected(participant))

    def on_participant_attributes_changed_handler(changed_attributes: dict, participant: rtc.Participant):
        asyncio.create_task(async_on_participant_attributes_changed(changed_attributes, participant))

    async def async_on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"New participant connected: {participant.identity}")

        # Check if this is a SIP participant and log call status
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            logger.info(f"SIP participant connected: {participant.identity}")

            # Log SIP attributes
            if participant.attributes:
                call_id = participant.attributes.get('sip.callID', 'Unknown')
                call_status = participant.attributes.get('sip.callStatus', 'Unknown')
                phone_number = participant.attributes.get('sip.phoneNumber', 'Unknown')
                trunk_id = participant.attributes.get('sip.trunkID', 'Unknown')
                trunk_phone = participant.attributes.get('sip.trunkPhoneNumber', 'Unknown')

                logger.info(f"SIP Call ID: {call_id}")
                logger.info(f"SIP Call Status: {call_status}")
                logger.info(f"SIP Phone Number: {phone_number}")
                logger.info(f"SIP Trunk ID: {trunk_id}")
                logger.info(f"SIP Trunk Phone Number: {trunk_phone}")

                # Log specific call status information
                if call_status == 'active':
                    logger.info("Call is active and connected")
                elif call_status == 'automation':
                    logger.info("Call is connected and dialing DTMF numbers")
                elif call_status == 'dialing':
                    logger.info("Call is dialing and waiting to be picked up")
                elif call_status == 'hangup':
                    logger.info("Call has been ended by a participant")
                elif call_status == 'ringing':
                    logger.info("Inbound call is ringing for the caller")

        await agent.session.say(f"Welcome, {participant.name or participant.identity}! I can help you add a participant to this call or end the call.")

    async def async_on_participant_attributes_changed(changed_attributes: dict, participant: rtc.Participant):
        logger.info(f"Participant {participant.identity} attributes changed: {changed_attributes}")

        # Check if this is a SIP participant and if call status has changed
        if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            # Check if sip.callStatus is in the changed attributes
            if 'sip.callStatus' in changed_attributes:
                call_status = changed_attributes['sip.callStatus']
                logger.info(f"SIP Call Status updated: {call_status}")

                # Log specific call status information
                if call_status == 'active':
                    logger.info("Call is now active and connected")
                elif call_status == 'automation':
                    logger.info("Call is now connected and dialing DTMF numbers")
                elif call_status == 'dialing':
                    logger.info("Call is now dialing and waiting to be picked up")
                elif call_status == 'hangup':
                    logger.info("Call has been ended by a participant")
                elif call_status == 'ringing':
                    logger.info("Inbound call is now ringing for the caller")

    ctx.room.on("participant_connected", on_participant_connected_handler)
    ctx.room.on("participant_attributes_changed", on_participant_attributes_changed_handler)

if __name__ == "__main__":
    cli.run_app(server)
```
