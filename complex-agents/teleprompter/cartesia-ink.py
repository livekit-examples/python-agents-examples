"""
---
title: Teleprompter Transcription Agent
category: complex-agents
tags: [rpc_transcript, cartesia_stt, user_input_transcribed, frontend_communication]
difficulty: intermediate
description: Real-time teleprompter that sends transcriptions to frontend via RPC
demonstrates:
  - Cartesia STT for transcription
  - RPC method registration for status checks
  - Event handler for final transcriptions
  - Async RPC calls to send transcripts
  - Frontend communication pattern
  - Real-time transcript streaming
---
"""

# Teleprompter agent that transcribes user speech and sends it to frontend via RPC

import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import cartesia

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / '.env')

async def entrypoint(ctx: JobContext):
    await ctx.connect()
    session = AgentSession()

    # Register RPC method for frontend to retrieve transcript data
    @ctx.room.local_participant.register_rpc_method("get_transcript_status")
    async def get_transcript_status(data):
        # This can be called by frontend to check connection
        return {"status": "connected"}

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            # Send transcript to frontend via RPC
            
            async def send_transcript():
                try:
                    # Get remote participants
                    remote_participants = list(ctx.room.remote_participants.values())
                    if not remote_participants:
                        print("No remote participants found to send transcript")
                        return
                    
                    # Send to the first remote participant (the frontend)
                    client_participant = remote_participants[0]
                    
                    # Perform RPC call to frontend with transcript data
                    await ctx.room.local_participant.perform_rpc(
                        destination_identity=client_participant.identity,
                        method="receive_transcript",
                        payload=json.dumps({
                            "transcript": transcript.transcript,
                            "timestamp": getattr(transcript, 'timestamp', None)
                        })
                    )
                    print(f"Sent transcript to frontend ({client_participant.identity}): {transcript.transcript}")
                except Exception as e:
                    print(f"Error sending transcript via RPC: {e}")
            
            # Create task to run async function
            asyncio.create_task(send_transcript())

    await session.start(
        agent=Agent(
            instructions="You are a teleprompter assistant that transcribes user speech. Focus on accurate real-time transcription.",
            stt="assemblyai/universal-streaming"
        ),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
