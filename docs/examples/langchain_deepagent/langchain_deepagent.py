"""
---
title: LangChain Deep Agent
category: integrations
tags: [langchain, openai, deepagents]
difficulty: intermediate
description: Shows how to use a LangChain deep agent with planning and subagents in a LiveKit voice agent.
demonstrates:
  - Using create_deep_agent from the deepagents library
  - Delegating work to a subagent for weather research
  - Using built-in planning (write_todos)
  - Using a custom llm_node to stream only AI responses and filter tool messages
---

Latency note: The LLMAdapter uses LangGraph's streaming mode to minimise time-to-first-token, but care should be taken when porting LangChain workflows that were not originally designed for voice use cases. 
"""
from dotenv import load_dotenv
from deepagents import create_deep_agent
from langchain.tools import tool
from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    llm,
)
from livekit.plugins import langchain, silero

load_dotenv()

ASSISTANT_INSTRUCTIONS = """You are a trip planning voice assistant.
When the user asks you to plan a trip, you should:
1. Use write_todos to break the planning into steps.
2. Delegate weather research to the weather_researcher subagent using the task tool.
3. Summarize the plan back to the user.

Your spoken responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols."""


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city.

    Args:
        city: The name of the city to get weather for.
    """
    # Stub implementation - replace with a real weather API call
    return f"The weather in {city} is sunny and 72 degrees Fahrenheit."


@tool
def get_attractions(city: str) -> str:
    """Get popular tourist attractions for a given city.

    Args:
        city: The name of the city to get attractions for.
    """
    # Stub implementation - replace with a real attractions API call
    attractions = {
        "paris": "Eiffel Tower, Louvre Museum, Notre-Dame Cathedral, Champs-Elysees",
        "london": "Big Ben, Tower of London, British Museum, Buckingham Palace",
        "tokyo": "Shibuya Crossing, Senso-ji Temple, Tokyo Tower, Meiji Shrine",
    }
    result = attractions.get(city.lower(), "Various local landmarks and cultural sites")
    return f"Popular attractions in {city}: {result}"


_agent_graph = create_deep_agent(
    model=ChatOpenAI(model="gpt-4.1-mini", temperature=0.7),
    tools=[get_attractions],
    system_prompt=ASSISTANT_INSTRUCTIONS,
    subagents=[
        {
            "name": "weather_researcher",
            "description": "Looks up the current weather for a city. Delegate to this subagent when you need weather information for trip planning.",
            "system_prompt": "You are a weather research assistant. Use the get_weather tool to look up weather for the requested city and return a brief summary.",
            "tools": [get_weather],
        },
    ],
)


class DeepAgentVoice(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=ASSISTANT_INSTRUCTIONS)

    async def llm_node(self, chat_ctx, tools, model_settings=None):
        """Stream from the deep agent graph, yielding only AIMessage chunks.

        Deep agents use many built-in tools (todos, subagents) and
        the llm_node is used to avoid tool results being spoken."""
        state = langchain.LLMAdapter(graph=_agent_graph).chat(
            chat_ctx=chat_ctx, tools=[]
        )
        lc_messages = state._chat_ctx_to_state()

        async for chunk, _metadata in _agent_graph.astream(
            lc_messages, stream_mode="messages"
        ):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                yield llm.ChatChunk(
                    id=chunk.id or "",
                    delta=llm.ChoiceDelta(
                        role="assistant", content=chunk.content
                    ),
                )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=langchain.LLMAdapter(graph=_agent_graph),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(agent=DeepAgentVoice(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
