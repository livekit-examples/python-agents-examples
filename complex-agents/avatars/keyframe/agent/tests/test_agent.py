"""
Tests for the Keyframe Avatars x LiveKit demo agent.

Tests cover:
  - Cosmo emotion showcase: set_emotion is called with correct emotions
  - Acme Airlines: booking lookup, flight/hotel modifications, empathy
  - Handoff between agents
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from livekit.agents import AgentSession, inference, llm

from agent import AcmeAirlinesAgent, CosmoAgent, SessionState, my_agent


def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")


def _mock_avatar() -> MagicMock:
    """Create a mock Keyframe AvatarSession."""
    avatar = MagicMock()
    avatar.set_emotion = AsyncMock()
    return avatar


# ---------------------------------------------------------------------------
# Part 1: Cosmo Emotion Showcase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cosmo_sets_sad_emotion_for_sad_haiku() -> None:
    """When asked for a sad haiku, Cosmo should call set_emotion('sad')."""
    avatar = _mock_avatar()

    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm) as session,
    ):
        await session.start(CosmoAgent(avatar=avatar))
        result = await session.run(user_input="Tell me a sad haiku")

        result.expect.next_event().is_function_call(
            name="set_emotion", arguments={"emotion": "sad"}
        )


@pytest.mark.asyncio
async def test_cosmo_sets_happy_emotion_for_joke() -> None:
    """When asked for a dad joke, Cosmo should call set_emotion('happy')."""
    avatar = _mock_avatar()

    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm) as session,
    ):
        await session.start(CosmoAgent(avatar=avatar))
        result = await session.run(user_input="Tell me a dad joke")

        result.expect.next_event().is_function_call(
            name="set_emotion", arguments={"emotion": "happy"}
        )


@pytest.mark.asyncio
async def test_cosmo_sets_angry_emotion_when_insulted() -> None:
    """When insulted, Cosmo should call set_emotion('angry')."""
    avatar = _mock_avatar()

    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm) as session,
    ):
        await session.start(CosmoAgent(avatar=avatar))
        result = await session.run(
            user_input="That was horrible, you are the worst comedian of all time. Never tell a joke again."
        )

        result.expect.next_event().is_function_call(
            name="set_emotion", arguments={"emotion": "angry"}
        )


@pytest.mark.asyncio
async def test_cosmo_handoff_to_airline() -> None:
    """When asked about airline support, Cosmo should hand off."""
    avatar = _mock_avatar()

    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm) as session,
    ):
        await session.start(CosmoAgent(avatar=avatar))
        result = await session.run(
            user_input="I'd like to see the airline customer support demo"
        )

        result.expect.contains_agent_handoff(new_agent_type=AcmeAirlinesAgent)


@pytest.mark.asyncio
async def test_cosmo_emits_persona_event_on_enter(monkeypatch) -> None:
    """Cosmo should publish persona details for the frontend label."""
    avatar = _mock_avatar()
    send_frontend_event = AsyncMock()
    monkeypatch.setattr("agent.send_frontend_event", send_frontend_event)

    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm) as session,
    ):
        await session.start(CosmoAgent(avatar=avatar))

    send_frontend_event.assert_awaited_once_with(
        "agent_persona",
        {
            "name": "Cosmo",
            "subtitle": "Charismatic and emotionally expressive",
        },
    )


# ---------------------------------------------------------------------------
# Part 2: Acme Airlines Customer Support
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_airline_looks_up_booking() -> None:
    """The airline agent should look up a booking when given a confirmation code."""
    avatar = _mock_avatar()

    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm, userdata=SessionState()) as session,
    ):
        await session.start(AcmeAirlinesAgent(avatar=avatar))
        result = await session.run(user_input="Hi, my confirmation code is ACM-29471")

        result.expect.next_event().is_function_call(
            name="lookup_booking", arguments={"confirmation_code": "ACM-29471"}
        )


@pytest.mark.asyncio
async def test_airline_empathy_for_illness() -> None:
    """When the customer shares bad news, the agent should express empathy (sad emotion)."""
    avatar = _mock_avatar()

    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm, userdata=SessionState()) as session,
    ):
        await session.start(AcmeAirlinesAgent(avatar=avatar))

        await session.run(
            user_input="My confirmation is ACM-29471. My mother is very sick and I need to cancel our Tokyo trip."
        )

        # Check that set_emotion was called with 'sad' at some point
        emotion_calls = [
            call
            for call in avatar.set_emotion.call_args_list
            if call.args == ("sad",) or call.kwargs.get("emotion") == "sad"
        ]
        assert len(emotion_calls) > 0, (
            f"Expected set_emotion('sad') to be called for empathy. "
            f"Actual calls: {avatar.set_emotion.call_args_list}"
        )


@pytest.mark.asyncio
async def test_airline_cancels_flight() -> None:
    """The agent should be able to cancel a flight."""
    avatar = _mock_avatar()
    state = SessionState()

    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm, userdata=state) as session,
    ):
        await session.start(AcmeAirlinesAgent(avatar=avatar))

        result = await session.run(
            user_input=(
                "I have confirmation ACM-29471. Please cancel the outbound flight FL-1001."
            )
        )

        # The agent may interleave set_emotion calls, so use contains_* for order-agnostic checks
        result.expect.contains_function_call(name="lookup_booking")
        result.expect.contains_function_call(
            name="modify_flight", arguments={"flight_id": "FL-1001", "action": "cancel"}
        )


@pytest.mark.asyncio
async def test_airline_modifies_hotel() -> None:
    """The agent should be able to modify hotel dates."""
    avatar = _mock_avatar()
    state = SessionState()

    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm, userdata=state) as session,
    ):
        await session.start(AcmeAirlinesAgent(avatar=avatar))

        result = await session.run(
            user_input=(
                "My confirmation is ACM-29471. Can you change my hotel check-in to May 5th "
                "and check-out to May 15th?"
            )
        )

        # The agent may interleave set_emotion calls, so use contains_* for order-agnostic checks
        result.expect.contains_function_call(name="lookup_booking")
        result.expect.contains_function_call(
            name="modify_hotel",
            arguments={
                "action": "change",
                "new_check_in": "2026-05-05",
                "new_check_out": "2026-05-15",
            },
        )


@pytest.mark.asyncio
async def test_airline_cancels_entire_trip() -> None:
    """When asked to cancel the whole trip, the agent must cancel both flights AND the hotel."""
    avatar = _mock_avatar()
    state = SessionState()

    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm, userdata=state) as session,
    ):
        await session.start(AcmeAirlinesAgent(avatar=avatar))

        result = await session.run(
            user_input=(
                "I need to cancel my entire trip. Please cancel both flights "
                "and the hotel reservation."
            )
        )

        result.expect.contains_function_call(
            name="modify_flight", arguments={"flight_id": "FL-1001", "action": "cancel"}
        )
        result.expect.contains_function_call(
            name="modify_flight", arguments={"flight_id": "FL-1002", "action": "cancel"}
        )
        result.expect.contains_function_call(
            name="modify_hotel", arguments={"action": "cancel"}
        )


@pytest.mark.asyncio
async def test_airline_responds_with_empathy() -> None:
    """The airline agent should respond empathetically when hearing about illness."""
    avatar = _mock_avatar()

    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm, userdata=SessionState()) as session,
    ):
        await session.start(AcmeAirlinesAgent(avatar=avatar))
        result = await session.run(
            user_input=(
                "I need to cancel my trip. My father was just diagnosed with cancer "
                "and I need to be with him."
            )
        )

        # The agent should respond with empathy somewhere in the turn
        await result.expect.contains_message(role="assistant").judge(
            test_llm,
            intent="""
            Expresses genuine sympathy and empathy for the customer's situation.
            Does NOT immediately jump to logistics without acknowledging the
            emotional weight of the situation first.
            """,
        )


@pytest.mark.asyncio
async def test_lyra_emits_persona_event_on_enter(monkeypatch) -> None:
    """Lyra should publish persona details for the frontend label."""
    avatar = _mock_avatar()
    send_frontend_event = AsyncMock()
    monkeypatch.setattr("agent.send_frontend_event", send_frontend_event)

    async with (
        _llm() as test_llm,
        AgentSession(llm=test_llm, userdata=SessionState()) as session,
    ):
        await session.start(AcmeAirlinesAgent(avatar=avatar))

    send_frontend_event.assert_awaited_once_with(
        "agent_persona",
        {
            "name": "Lyra",
            "subtitle": "Warm, empathetic airline support",
        },
    )


@pytest.mark.asyncio
async def test_keyframe_agent_connects_before_avatar_start(monkeypatch) -> None:
    """The room must be connected before avatar startup work touches local participant APIs."""

    session_instances: list[MagicMock] = []
    avatar_instances: list[MagicMock] = []
    call_order: list[str] = []

    class FakeSession:
        def __init__(self, *args, **kwargs) -> None:
            self.start = AsyncMock()
            session_instances.append(self)

    class FakeAvatarSession:
        def __init__(self, *args, **kwargs) -> None:
            self.start = AsyncMock(
                side_effect=lambda *args, **kwargs: call_order.append("avatar_start")
            )
            avatar_instances.append(self)

    monkeypatch.setattr("agent.AgentSession", FakeSession)
    monkeypatch.setattr("agent.keyframe.AvatarSession", FakeAvatarSession)
    monkeypatch.setattr("agent.MultilingualModel", lambda: object())
    monkeypatch.setattr("agent.inference.STT", lambda *args, **kwargs: object())
    monkeypatch.setattr("agent.inference.LLM", lambda *args, **kwargs: object())
    monkeypatch.setattr("agent.inference.TTS", lambda *args, **kwargs: object())

    room = SimpleNamespace(name="test-room")
    ctx = SimpleNamespace(
        room=room,
        proc=SimpleNamespace(userdata={"vad": object()}),
        connect=AsyncMock(side_effect=lambda: call_order.append("connect")),
        log_context_fields={},
    )

    await my_agent(ctx)

    assert len(session_instances) == 1
    assert len(avatar_instances) == 1

    session_start = session_instances[0].start
    session_start.assert_awaited_once()
    assert session_start.await_args.kwargs["room"] is room

    avatar_instances[0].start.assert_awaited_once_with(session_instances[0], room=room)
    ctx.connect.assert_awaited_once()
    assert call_order[:2] == ["connect", "avatar_start"]
