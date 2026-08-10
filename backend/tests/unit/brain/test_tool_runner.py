import pytest

from jarvis.brain.tool_runner import ToolRunner
from jarvis.brain.tools import ToolRegistry, ToolSpec
from jarvis.core.exceptions import ConfigurationError, PermissionDeniedError
from jarvis.security import InMemoryAuditLog, PermissionEngine, RiskLevel, Role


class _FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _FakeToolUseBlock:
    def __init__(self, tool_id: str, name: str, tool_input: dict[str, object]) -> None:
        self.type = "tool_use"
        self.id = tool_id
        self.name = name
        self.input = tool_input


class _FakeResponse:
    def __init__(self, content: list[object], stop_reason: str) -> None:
        self.content = content
        self.stop_reason = stop_reason
        self.model = "fake-model"


class _FakeMessagesEndpoint:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = iter(responses)
        self.calls: list[dict[str, object]] = []

    async def create(self, **kwargs: object) -> _FakeResponse:
        # Snapshot the mutable `messages` list as it stood at call time —
        # ToolRunner keeps mutating the same list object across iterations.
        messages = kwargs.get("messages")
        if isinstance(messages, list):
            kwargs = {**kwargs, "messages": list(messages)}
        self.calls.append(kwargs)
        return next(self._responses)


class _FakeClient:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.messages = _FakeMessagesEndpoint(responses)


async def _add_handler(arguments: dict[str, object]) -> object:
    a = arguments["a"]
    b = arguments["b"]
    assert isinstance(a, int | float)
    assert isinstance(b, int | float)
    return {"sum": a + b}


async def _delete_handler(arguments: dict[str, object]) -> object:
    return {"deleted": True}


@pytest.fixture
def registry() -> ToolRegistry:
    engine = PermissionEngine()
    audit_log = InMemoryAuditLog()
    registry = ToolRegistry(engine, audit_log)
    registry.register(
        ToolSpec(
            name="add",
            description="Add two numbers",
            risk_level=RiskLevel.SAFE,
            handler=_add_handler,
            input_schema={
                "type": "object",
                "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                "required": ["a", "b"],
            },
        )
    )
    registry.register(
        ToolSpec(
            name="delete_everything",
            description="Deletes everything",
            risk_level=RiskLevel.DANGEROUS,
            handler=_delete_handler,
            input_schema={"type": "object", "properties": {}},
        )
    )
    return registry


@pytest.mark.asyncio
async def test_run_returns_final_text_with_no_tool_use(registry: ToolRegistry) -> None:
    client = _FakeClient([_FakeResponse([_FakeTextBlock("hello")], stop_reason="end_turn")])
    runner = ToolRunner(client, registry=registry)

    result = await runner.run(
        system_prompt="sys",
        user_message="hi",
        role=Role.OPERATOR,
        session_id="s1",
        actor="research",
        correlation_id="corr-1",
    )

    assert result.final_text == "hello"
    assert result.iterations == 1
    assert result.pending_confirmation is None


@pytest.mark.asyncio
async def test_run_executes_tool_and_continues(registry: ToolRegistry) -> None:
    client = _FakeClient(
        [
            _FakeResponse(
                [_FakeToolUseBlock("t1", "add", {"a": 2, "b": 3})], stop_reason="tool_use"
            ),
            _FakeResponse([_FakeTextBlock("the sum is 5")], stop_reason="end_turn"),
        ]
    )
    runner = ToolRunner(client, registry=registry)

    result = await runner.run(
        system_prompt="sys",
        user_message="what is 2+3?",
        role=Role.OPERATOR,
        session_id="s1",
        actor="research",
        correlation_id="corr-1",
    )

    assert result.final_text == "the sum is 5"
    assert result.iterations == 2

    second_call_messages = client.messages.calls[1]["messages"]
    assert isinstance(second_call_messages, list)
    tool_result_message = second_call_messages[-1]
    assert tool_result_message["role"] == "user"
    assert tool_result_message["content"][0]["tool_use_id"] == "t1"
    assert "5" in tool_result_message["content"][0]["content"]


@pytest.mark.asyncio
async def test_run_stops_on_requires_confirmation(registry: ToolRegistry) -> None:
    client = _FakeClient(
        [
            _FakeResponse(
                [_FakeToolUseBlock("t1", "delete_everything", {})], stop_reason="tool_use"
            ),
        ]
    )
    runner = ToolRunner(client, registry=registry)

    result = await runner.run(
        system_prompt="sys",
        user_message="delete it all",
        role=Role.OWNER,
        session_id="s1",
        actor="coding",
        correlation_id="corr-1",
    )

    assert result.pending_confirmation == "delete_everything"
    assert result.final_text == ""


@pytest.mark.asyncio
async def test_run_raises_on_denied_tool(registry: ToolRegistry) -> None:
    client = _FakeClient(
        [
            _FakeResponse(
                [_FakeToolUseBlock("t1", "delete_everything", {})], stop_reason="tool_use"
            ),
        ]
    )
    runner = ToolRunner(client, registry=registry)

    with pytest.raises(PermissionDeniedError):
        await runner.run(
            system_prompt="sys",
            user_message="delete it all",
            role=Role.GUEST,
            session_id="s1",
            actor="coding",
            correlation_id="corr-1",
        )


@pytest.mark.asyncio
async def test_run_enforces_allowed_tools_scope(registry: ToolRegistry) -> None:
    client = _FakeClient(
        [_FakeResponse([_FakeToolUseBlock("t1", "add", {"a": 1, "b": 1})], stop_reason="tool_use")]
    )
    runner = ToolRunner(client, registry=registry, allowed_tools=frozenset({"delete_everything"}))

    with pytest.raises(PermissionDeniedError):
        await runner.run(
            system_prompt="sys",
            user_message="add numbers",
            role=Role.OWNER,
            session_id="s1",
            actor="coding",
            correlation_id="corr-1",
        )


@pytest.mark.asyncio
async def test_tool_definitions_are_filtered_by_allowed_tools(registry: ToolRegistry) -> None:
    client = _FakeClient([_FakeResponse([_FakeTextBlock("ok")], stop_reason="end_turn")])
    runner = ToolRunner(client, registry=registry, allowed_tools=frozenset({"add"}))

    await runner.run(
        system_prompt="sys",
        user_message="hi",
        role=Role.OPERATOR,
        session_id="s1",
        actor="research",
        correlation_id="corr-1",
    )

    sent_tools = client.messages.calls[0]["tools"]
    assert isinstance(sent_tools, list)
    assert [t["name"] for t in sent_tools] == ["add"]


@pytest.mark.asyncio
async def test_run_raises_if_loop_never_converges(registry: ToolRegistry) -> None:
    responses = [
        _FakeResponse([_FakeToolUseBlock(f"t{i}", "add", {"a": 1, "b": 1})], stop_reason="tool_use")
        for i in range(5)
    ]
    client = _FakeClient(responses)
    runner = ToolRunner(client, registry=registry, max_iterations=3)

    with pytest.raises(ConfigurationError):
        await runner.run(
            system_prompt="sys",
            user_message="loop forever",
            role=Role.OPERATOR,
            session_id="s1",
            actor="research",
            correlation_id="corr-1",
        )
