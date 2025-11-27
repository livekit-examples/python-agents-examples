from __future__ import annotations

import aiohttp
import pytest
from livekit.agents import AgentSession, inference
from answer_call import SimpleAgent

@pytest.mark.asyncio
async def test_assistant_greeting() -> None:
    async with aiohttp.ClientSession() as http_session:
        async with (
            inference.LLM(model="gpt-4.1-mini") as llm,
            AgentSession(llm=llm) as session,
        ):
            agent = SimpleAgent()
            # Inject http_session into STT/TTS so they don't need http_context
            # agent.stt._session = http_session
            # agent.tts._session = http_session

            await session.start(agent)

            result = await session.run(user_input="Hello")

            await result.expect.next_event().is_message(role="assistant").judge(
                llm, intent="Makes a friendly introduction and offers assistance."
            )

            result.expect.no_more_events()
