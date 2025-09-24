"""
---
title: Testing Test
category: testing
tags: [pytest, test-validation, duplicate-test, agent-greeting]
difficulty: beginner
description: Duplicate test file demonstrating basic agent testing patterns
demonstrates:
  - Basic pytest async test structure
  - Agent session lifecycle management
  - Environment variable loading for tests
  - Simple greeting validation pattern
  - LLM judge pattern for response evaluation
---
"""

import pytest
import pytest_asyncio
import sys
from pathlib import Path
from livekit.agents import AgentSession
from livekit.agents.voice.run_result import mock_tools
from livekit.plugins import openai
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / '.env')

from agent import FunctionAgent

@pytest.mark.asyncio
async def test_assistant_greeting() -> None:
    async with (
        openai.LLM(model="gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(FunctionAgent())
        result = await session.run(user_input="Hello")

        await result.expect.next_event().is_message(role="assistant").judge(
            llm, intent="Makes a friendly introduction and offers assistance."
        )



