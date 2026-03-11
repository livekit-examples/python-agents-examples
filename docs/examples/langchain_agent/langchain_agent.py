"""
---
title: LangChain Agent
category: integrations
tags: [langchain, openai]
difficulty: beginner
description: Shows how to use a LangChain agent with tools in a LiveKit voice agent.
demonstrates:
  - Using create_agent from langchain.agents to build a tool-calling agent
  - Defining LangChain tools with the @tool decorator
  - Using a custom llm_node to stream only AI responses and filter tool messages
---

Latency note: The LLMAdapter uses LangGraph's streaming mode to minimise time-to-first-token, but care should be taken when porting LangChain workflows that were not originally designed for voice use cases. 
"""
from dotenv import load_dotenv
from langchain.agents import create_agent
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

ASSISTANT_INSTRUCTIONS = """You are a helpful voice AI assistant with access to tools.
You can look up the weather for any city when asked.
Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols."""


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city.

    Args:
        city: The name of the city to get weather for.
    """
    # Stub implementation - replace with a real weather API call
    return f"The weather in {city} is sunny and 72 degrees Fahrenheit."


_agent_graph = create_agent(
    model=ChatOpenAI(model="gpt-4.1-mini", temperature=0.7),
    tools=[get_weather],
)


class LangChainAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=ASSISTANT_INSTRUCTIONS)

    async def llm_node(self, chat_ctx, tools, model_settings=None):
        """Stream from the LangChain agent graph, yielding only AIMessage chunks.

        The LLMAdapter streams all message types including ToolMessages, this code is responsible for filtering out those ToolMessages so they are not passed to the TTS."""
        state = langchain.LLMAdapter(graph=_agent_graph).chat(
            chat_ctx=chat_ctx, tools=[]
        )
        # Access the internal state conversion, then stream from the graph
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

    await session.start(agent=LangChainAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
