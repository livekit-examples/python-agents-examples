import json
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest

from livekit_ext import get_state, install_extensions
from livekit_ext.chunk import extract_text, inject_text
from livekit_ext.content_filter import ContentFilter
from livekit_ext.pipeline import Pipeline
from livekit_ext.rpc import RPC, rpc_call
from livekit_ext.context_augmented_generation import ContextAugmentedGeneration


@dataclass
class FakeDelta:
    content: str | None


@dataclass
class FakeChunk:
    delta: FakeDelta


class DummyAgent:
    def __init__(self) -> None:
        self.helpers = None


@pytest.mark.asyncio
async def test_chunk_extract_and_inject() -> None:
    chunk = FakeChunk(FakeDelta("hello"))
    assert extract_text(chunk) == "hello"

    mutated = inject_text(chunk, "world")
    assert mutated is chunk
    assert chunk.delta.content == "world"

    assert extract_text("raw") == "raw"
    assert extract_text(object()) is None


@pytest.mark.asyncio
async def test_pipeline_runs_processors_in_order() -> None:
    async def base_stream():
        for word in ("hello", "world"):
            yield word

    async def upper(stream):
        async for chunk in stream:
            yield chunk.upper()

    async def suffix(stream):
        async for chunk in stream:
            yield f"{chunk}!"

    pipeline = Pipeline()
    pipeline.add(upper)
    pipeline.add(suffix)

    results: list[str] = []
    async for item in pipeline.process(base_stream()):
        results.append(item)

    assert results == ["HELLO!", "WORLD!"]


@pytest.mark.asyncio
async def test_content_filter_extension_filters_terms() -> None:
    agent = DummyAgent()
    install_extensions(agent, ContentFilter(terms=["fail"], replacement="BLOCKED"))

    state = get_state(agent)
    assert state.pipeline, "content_filter should register a processor"

    async def base_stream():
        yield FakeChunk(FakeDelta("This will fail soon"))
        yield FakeChunk(FakeDelta("All good here"))

    filtered: list[str | None] = []
    async for chunk in state.pipeline.process(base_stream()):
        filtered.append(extract_text(chunk))

    assert filtered == ["BLOCKED", "All good here"]


class FakeLocalParticipant:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self.handlers: dict[str, Any] = {}

    async def perform_rpc(self, destination_identity: str, method: str, payload: Any):
        self.calls.append((destination_identity, method, payload))

    def register_rpc_method(self, method: str, handler: Any) -> None:
        self.handlers[method] = handler


class FakeRoom:
    def __init__(self) -> None:
        self.local_participant = FakeLocalParticipant()
        self.remote_participants = {"user-1": SimpleNamespace(identity="user-1")}


class FakeCtx:
    def __init__(self) -> None:
        self.room = FakeRoom()


@pytest.mark.asyncio
async def test_rpc_extension_binds_and_sends() -> None:
    agent = DummyAgent()
    install_extensions(agent, RPC())

    helper = agent.helpers.rpc
    ctx = FakeCtx()

    helper.bind(ctx=ctx)

    await helper.send("client.flashcard", {"action": "show"})

    assert ctx.room.local_participant.calls == [
        ("user-1", "client.flashcard", '{"action": "show"}')
    ]


@pytest.mark.asyncio
async def test_rpc_register_defers_until_bound() -> None:
    agent = DummyAgent()
    install_extensions(agent, RPC())

    helper = agent.helpers.rpc
    handler_called: list[str] = []

    async def handler(data):
        handler_called.append(helper.payload_text(data) or "")

    helper.register("agent.echo", handler)
    ctx = FakeCtx()
    helper.bind(ctx=ctx)

    assert "agent.echo" in ctx.room.local_participant.handlers

    payload = SimpleNamespace(payload='{"message": "hi"}')
    json_payload = helper.load_json(payload)
    assert json_payload == {"message": "hi"}


@dataclass
class DemoPayload:
    id: str | None = None
    text: str = ""


class RPCConsumer(DummyAgent):
    @rpc_call("client.echo", model=DemoPayload)
    async def echo(self, payload: DemoPayload) -> str:
        return payload.text


@pytest.mark.asyncio
async def test_rpc_call_decorator_instantiates_payload() -> None:
    agent = RPCConsumer()
    install_extensions(agent, RPC())

    helper = agent.helpers.rpc
    ctx = FakeCtx()
    helper.bind(ctx=ctx)

    result = await agent.echo(text="hello")
    assert result == "hello"

    identity, method, payload = ctx.room.local_participant.calls[0]
    assert identity == "user-1"
    assert method == "client.echo"
    transmitted = json.loads(payload)
    assert transmitted["text"] == "hello"
    assert transmitted["id"]


class FakeStream:
    def __init__(self, chunks: list[str]) -> None:
        self._chunks = list(chunks)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._chunks:
            raise StopAsyncIteration
        text = self._chunks.pop(0)
        return SimpleNamespace(delta=SimpleNamespace(content=text))


class FakeLLM:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.chat_contexts: list[Any] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def chat(self, chat_ctx: Any):
        self.chat_contexts.append(chat_ctx)
        return FakeStream(self.responses.copy())


@pytest.mark.asyncio
async def test_context_augmented_generation_uses_llm_factory() -> None:
    calls: list[str] = []

    def factory(model: str):
        calls.append(model)
        return FakeLLM(["Answer with context."])

    agent = DummyAgent()
    install_extensions(
        agent,
        ContextAugmentedGeneration(
            model="mock-model",
            context=["Fact A", "Fact B"],
            llm_factory=factory,
        ),
    )

    helper = agent.helpers.context_augmented_generation
    result = await helper.ask("What is A?")

    assert result == "Answer with context."
    assert calls == ["mock-model"]
