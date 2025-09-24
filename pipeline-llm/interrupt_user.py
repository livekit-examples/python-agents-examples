"""
---
title: Interrupt User
category: pipeline-llm
tags: [pipeline-llm, openai, deepgram]
difficulty: intermediate
description: Shows how to interrupt the user if they've spoken too much.
demonstrates:
  - Using the `session.say` method to interrupt the user.
  - Using the `allow_interruptions` parameter to prevent the user from interrupting the agent.
  - Once the agent has spoken, it will allow the user to interrupt again.
---
"""
# This agent keeps track of the number of sentences the user has spoken
# and interrupts them if they've said a certain number of sentences.
# We use session.say() to interrupt the user, and set allow_interruptions=False
# on that specific call to prevent the user from interrupting the agent.
# After the agent has spoken, allow_interruptions is once again True so the agent
# can listen for the user's response.

import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, deepgram, silero
from livekit.agents.llm import ChatContext, ChatMessage
import re
import asyncio

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("interrupt-user")
logger.setLevel(logging.INFO)

def count_sentences(text):
    """Count the number of sentences in text"""
    sentences = re.findall(r'[^.!?]+[.!?](?:\s|$)', text)
    return len(sentences)

async def entrypoint(ctx: JobContext):
    session = AgentSession()
    agent = Agent(
        instructions="You are a helpful agent that politely interrupts users when they talk too much.",
        stt=deepgram.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
        vad=silero.VAD.load()
    )
    
    async def handle_interruption(context):
        await agent.update_chat_ctx(context)
        session.say("Sorry, can I pause you there?", allow_interruptions=False)
        await session.generate_reply(allow_interruptions=False)
    
    transcript_buffer = ""
    max_sentences = 3
    
    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        nonlocal transcript_buffer
        
        if transcript.is_final:
            logger.info(f"Received final transcript: {transcript.transcript}")
            return
            
        transcript_buffer += " " + transcript.transcript
        transcript_buffer = transcript_buffer.strip()
        
        logger.info(f"Buffer: {transcript_buffer}")
        
        sentence_count = count_sentences(transcript_buffer)
        logger.info(f"Sentence count: {sentence_count}")
        
        if sentence_count >= max_sentences:
            logger.info("Interrupting user...")
            
            interruption_ctx = ChatContext([
                ChatMessage(
                    type="message",
                    role="system",
                    content=["You are an agent that politely interrupts users who speak too much. Create a brief response that acknowledges what they've said so far, then redirects to get more focused information."]
                ),
                ChatMessage(type="message", role="user", content=[f"User has been speaking and said: {transcript_buffer}"])
            ])
            
            asyncio.create_task(handle_interruption(interruption_ctx))
            transcript_buffer = ""
    
    @session.on("session_start")
    def on_session_start():
        nonlocal transcript_buffer
        transcript_buffer = ""
        session.generate_reply()
    
    await session.start(agent=agent, room=ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))