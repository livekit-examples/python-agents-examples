"""
---
title: Warm Handoff Agent
category: telephony
tags: [call-transfer, warm-handoff, sip, agent-to-human, function-tools]
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
"""

import asyncio
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit import rtc
from livekit import api
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import deepgram, openai, silero, elevenlabs

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class WarmHandoffAgent(Agent):
    def __init__(self, job_context=None) -> None:
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
            vad=silero.VAD.load()
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
            
        # Get room name from environment variable
        room_name = os.environ.get('LIVEKIT_ROOM_NAME', self.job_context.room.name)
        
        # Generate a unique identity for the SIP participant
        identity = f"transfer_{uuid.uuid4().hex[:8]}"
        
        # Create LiveKit API client
        livekit_url = os.environ.get('LIVEKIT_URL')
        livekit_api_key = os.environ.get('LIVEKIT_API_KEY')
        livekit_api_secret = os.environ.get('LIVEKIT_API_SECRET')
        sip_trunk_id = os.environ.get('SIP_TRUNK_ID')
        
        try:
            print(f"Transferring call to {phone_number}")
            
            # Using the API from the job context if available
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
                # Fallback to creating our own API client
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
        # Generate initial greeting
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    session = AgentSession()
    agent = WarmHandoffAgent(job_context=ctx)

    await session.start(
        agent=agent,
        room=ctx.room
    )

    def on_participant_connected_handler(participant: rtc.RemoteParticipant):
        asyncio.create_task(async_on_participant_connected(participant))
        
    async def async_on_participant_connected(participant: rtc.RemoteParticipant):
        await agent.session.say(f"Hi there! Is there anything I can help you with?")

    # Handle existing participants
    for participant in ctx.room.remote_participants.values():
        asyncio.create_task(async_on_participant_connected(participant))
    
    # Set up listener for new participants
    ctx.room.on("participant_connected", on_participant_connected_handler)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))