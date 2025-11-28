from __future__ import annotations

import pytest
from livekit.agents import AgentSession, inference, llm

from answer_call import SimpleAgent

def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")

@pytest.mark.asyncio
async def test_assistant_greeting() -> None:
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = SimpleAgent()
        await session.start(agent)

        result = await session.run(user_input="Hello")

        await result.expect.next_event().is_message(role="assistant").judge(
            llm, intent="Makes a friendly introduction and offers assistance."
        )

        result.expect.no_more_events()
