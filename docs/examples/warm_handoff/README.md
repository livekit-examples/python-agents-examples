---
title: Warm Handoff Agent
category: telephony
tags: [call-transfer, warm-handoff, sip, agent-to-human, function-tools, deepgram, openai, elevenlabs]
difficulty: intermediate
description: Agent demonstrating warm handoff functionality to transfer calls to human agents
demonstrates:
  - Call transfer to human agents via SIP
  - Warm handoff implementation patterns
  - SIP participant creation and management
  - Function tools for call operations
  - Multi-participant call handling
  - Professional call transfer announcements
---

This example demonstrates a warm handoff agent that can transfer calls to human agents via SIP. The agent uses a function tool to initiate the transfer and creates a SIP participant to connect the caller with a human.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  SIP_TRUNK_ID=your_sip_trunk_id
  DEEPGRAM_API_KEY=your_deepgram_key
  OPENAI_API_KEY=your_openai_key
  ELEVENLABS_API_KEY=your_elevenlabs_key
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" python-dotenv livekit-plugins-deepgram livekit-plugins-openai livekit-plugins-elevenlabs
  ```

## Load environment and create the AgentServer

Import the necessary modules, load environment variables, and create an AgentServer.

```python
import asyncio
import os
import uuid
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, RunContext, function_tool
from livekit import rtc
from livekit import api
from livekit.plugins import deepgram, openai, silero, elevenlabs

load_dotenv()

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process to reduce connection latency.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define the warm handoff agent

Create an Agent that stores the job context for API access. The agent includes STT/LLM/TTS/VAD configuration and a function tool for call transfers.

```python
class WarmHandoffAgent(Agent):
    def __init__(self, job_context=None, vad=None) -> None:
        self.job_context = job_context
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. You're helping me test ... yourself ... since you're the AI agent.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=elevenlabs.TTS(encoding="pcm_44100", model="eleven_multilingual_v2"),
            vad=vad
        )

    async def on_enter(self):
        self.session.generate_reply()
```

## Implement the transfer call function tool

The transfer tool creates a new SIP participant to dial the human agent. It uses the LiveKit API to initiate the outbound call and add them to the same room.

```python
@function_tool
async def transfer_call(self, context: RunContext, phone_number: str):
    """
    Transfer the current call to a human agent at the specified phone number.
    """
    if not self.job_context:
        await self.session.say("I'm sorry, I can't transfer the call at this time.")
        return None, "Failed to transfer call: No job context available"

    room_name = os.environ.get('LIVEKIT_ROOM_NAME', self.job_context.room.name)
    identity = f"transfer_{uuid.uuid4().hex[:8]}"
    sip_trunk_id = os.environ.get('SIP_TRUNK_ID')

    response = await self.job_context.api.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            sip_trunk_id=sip_trunk_id,
            sip_call_to=phone_number,
            room_name=room_name,
            participant_identity=identity,
            participant_name="Human Agent",
            krisp_enabled=True
        )
    )

    await self.session.say("I'm transferring you to a human agent now. Please hold while we connect you.")
    return None, f"I've transferred you to a human agent at {phone_number}."
```

## Create the RTC session entrypoint

Start the session and set up participant event handlers to greet new callers automatically.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession()
    agent = WarmHandoffAgent(job_context=ctx, vad=ctx.proc.userdata["vad"])

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

    def on_participant_connected_handler(participant: rtc.RemoteParticipant):
        asyncio.create_task(async_on_participant_connected(participant))

    async def async_on_participant_connected(participant: rtc.RemoteParticipant):
        await agent.session.say("Hi there! Is there anything I can help you with?")

    for participant in ctx.room.remote_participants.values():
        asyncio.create_task(async_on_participant_connected(participant))

    ctx.room.on("participant_connected", on_participant_connected_handler)
```

## Run it

```console
python warm_handoff.py console
```

## How it works

1. The agent answers calls and greets participants as they join.
2. When the user asks to speak with a human, the LLM calls `transfer_call`.
3. The function creates a SIP participant to dial the specified phone number.
4. The human agent joins the same room, enabling a warm handoff.
5. Krisp noise cancellation is enabled for the SIP participant.

## Full example

```python
import asyncio
import os
import uuid
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, RunContext, function_tool
from livekit import rtc
from livekit import api
from livekit.plugins import deepgram, openai, silero, elevenlabs

load_dotenv()

class WarmHandoffAgent(Agent):
    def __init__(self, job_context=None, vad=None) -> None:
        self.job_context = job_context
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. You're helping me test ... yourself ... since you're the AI agent.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=elevenlabs.TTS(
                encoding="pcm_44100",
                model="eleven_multilingual_v2"
            ),
            vad=vad
        )

    @function_tool
    async def transfer_call(self, context: RunContext, phone_number: str):
        """
        Transfer the current call to a human agent at the specified phone number.

        Args:
            context: The call context
            phone_number: The phone number to transfer the call to
        """
        if not self.job_context:
            await self.session.say("I'm sorry, I can't transfer the call at this time.")
            return None, "Failed to transfer call: No job context available"

        room_name = os.environ.get('LIVEKIT_ROOM_NAME', self.job_context.room.name)
        identity = f"transfer_{uuid.uuid4().hex[:8]}"

        livekit_url = os.environ.get('LIVEKIT_URL')
        livekit_api_key = os.environ.get('LIVEKIT_API_KEY')
        livekit_api_secret = os.environ.get('LIVEKIT_API_SECRET')
        sip_trunk_id = os.environ.get('SIP_TRUNK_ID')

        try:
            print(f"Transferring call to {phone_number}")

            if self.job_context and hasattr(self.job_context, 'api'):
                response = await self.job_context.api.sip.create_sip_participant(
                    api.CreateSIPParticipantRequest(
                        sip_trunk_id=sip_trunk_id,
                        sip_call_to=phone_number,
                        room_name=room_name,
                        participant_identity=identity,
                        participant_name="Human Agent",
                        krisp_enabled=True
                    )
                )
            else:
                livekit_api = api.LiveKitAPI(
                    url=livekit_url,
                    api_key=livekit_api_key,
                    api_secret=livekit_api_secret
                )

                response = await livekit_api.sip.create_sip_participant(
                    api.CreateSIPParticipantRequest(
                        sip_trunk_id=sip_trunk_id,
                        sip_call_to=phone_number,
                        room_name=room_name,
                        participant_identity=identity,
                        participant_name="Human Agent",
                        krisp_enabled=True
                    )
                )

                await livekit_api.aclose()

            await self.session.say(f"I'm transferring you to a human agent now. Please hold while we connect you.")

            return None, f"I've transferred you to a human agent at {phone_number}. Please hold while we connect you."

        except Exception as e:
            print(f"Error transferring call: {e}")
            await self.session.say(f"I'm sorry, I couldn't transfer the call at this time.")
            return None, f"Failed to transfer call: {e}"

    async def on_enter(self):
        self.session.generate_reply()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession()
    agent = WarmHandoffAgent(job_context=ctx, vad=ctx.proc.userdata["vad"])

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

    def on_participant_connected_handler(participant: rtc.RemoteParticipant):
        asyncio.create_task(async_on_participant_connected(participant))

    async def async_on_participant_connected(participant: rtc.RemoteParticipant):
        await agent.session.say(f"Hi there! Is there anything I can help you with?")

    for participant in ctx.room.remote_participants.values():
        asyncio.create_task(async_on_participant_connected(participant))

    ctx.room.on("participant_connected", on_participant_connected_handler)

if __name__ == "__main__":
    cli.run_app(server)
```
