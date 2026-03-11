"""
---
title: LangChain Integration
category: integrations
tags: [langchain, openai]
difficulty: beginner
description: Shows how to use LangGraph to integrate LangChain with LiveKit.
demonstrates:
  - Using LangGraph StateGraph to build a conversational workflow
  - Using langchain.LLMAdapter to connect a LangGraph workflow to a LiveKit agent
  - Using ChatOpenAI from langchain_openai as the LLM provider
---

Latency note: The LLMAdapter uses LangGraph's streaming mode to minimise time-to-first-token, but care should be taken when porting LangChain workflows that were not originally designed for voice use cases. 
"""
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, add_messages
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
)
from livekit.plugins import langchain, silero
from typing_extensions import TypedDict

load_dotenv()

ASSISTANT_INSTRUCTIONS = """You are a helpful voice AI assistant. The user is interacting with you via voice, even if you perceive the conversation as text.
You eagerly assist users with their questions by providing information from your extensive knowledge.
Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
You are curious, friendly, and have a sense of humor."""


class AgentState(TypedDict):
    """State for the LangGraph agent"""

    messages: Annotated[list, add_messages]


def _create_langgraph_workflow():
    """Build a simple LangGraph state graph: messages in -> LLM -> messages out."""
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.7)

    def call_model(state: AgentState):
        messages = [SystemMessage(content=ASSISTANT_INSTRUCTIONS)] + state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}

    builder = StateGraph(AgentState)
    builder.add_node("model", call_model)
    builder.add_edge(START, "model")
    builder.add_edge("model", END)

    return builder.compile()


_langgraph_app = _create_langgraph_workflow()

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=langchain.LLMAdapter(graph=_langgraph_app),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(agent=Agent(instructions=ASSISTANT_INSTRUCTIONS), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
