from __future__ import annotations
import sys
from pathlib import Path
import pytest
from livekit.agents import Agent, AgentSession, function_tool, inference

from agent_transfer import LongAgent, ShortAgent

class ShortTestAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are Short Agent. Answer in one concise sentence.
                When the user asks to switch to the long agent, call the function tool change_agent to hand off.
            """
        )

    @function_tool
    async def change_agent(self):
        """Switch to the long agent."""
        self.session.update_agent(LongTestAgent())


class LongTestAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are Long Agent. Respond with flowery, verbose sentences.
                When the user asks to switch to the short agent, call the function tool change_agent to hand off.
            """
        )

    @function_tool
    async def change_agent(self):
        """Switch to the short agent."""
        self.session.update_agent(ShortTestAgent())


def _llm_model() -> inference.LLM:
    return inference.LLM(model="openai/gpt-4o-mini")


@pytest.mark.asyncio
async def test_short_agent_is_brief() -> None:
    async with (_llm_model() as llm, AgentSession(llm=llm) as session):
        await session.start(ShortTestAgent())

        result = await session.run(user_input="Say hello in your usual brief style.")

        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(llm, intent="Responds with a concise greeting.")
        )
        result.expect.no_more_events()


@pytest.mark.asyncio
async def test_switch_to_long_agent_via_tool() -> None:
    async with (_llm_model() as llm, AgentSession(llm=llm) as session):
        await session.start(ShortTestAgent())

        result = await session.run(user_input="Please switch to the long agent and greet me warmly.")

        result.expect.skip_next_event_if(type="message", role="assistant")
        result.expect.next_event().is_function_call(name="change_agent")
        result.expect.next_event().is_function_call_output()
        result.expect.next_event().is_agent_handoff(new_agent_type=LongTestAgent)

        follow_up = await session.run(user_input="Now that you're the long agent, say hello.")
        await (
            follow_up.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="Greets in an overly verbose way consistent with the long agent.",
            )
        )
        follow_up.expect.no_more_events()


@pytest.mark.asyncio
async def test_switch_back_to_short_agent() -> None:
    async with (_llm_model() as llm, AgentSession(llm=llm) as session):
        await session.start(ShortTestAgent())

        initial = await session.run(user_input="Switch to the long agent first.")
        initial.expect.skip_next_event_if(type="message", role="assistant")
        initial.expect.next_event().is_function_call(name="change_agent")
        initial.expect.next_event().is_function_call_output()
        initial.expect.next_event().is_agent_handoff(new_agent_type=LongTestAgent)
        initial.expect.skip_next_event_if(type="message", role="assistant")

        result = await session.run(
            user_input="Now switch back to the short agent and answer quickly."
        )
        result.expect.skip_next_event_if(type="message", role="assistant")
        result.expect.next_event().is_function_call(name="change_agent")
        result.expect.next_event().is_function_call_output()
        result.expect.next_event().is_agent_handoff(new_agent_type=ShortTestAgent)

        follow_up = await session.run(user_input="Confirm you're the short agent now.")
        await (
            follow_up.expect.next_event()
            .is_message(role="assistant")
            .judge(llm, intent="Gives a confirmation without any overly verbose or flowery language.")
        )
        follow_up.expect.no_more_events()
