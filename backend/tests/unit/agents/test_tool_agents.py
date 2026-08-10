import pytest

from jarvis.agents.coding import create_coding_agent
from jarvis.agents.research import create_research_agent
from jarvis.agents.tool_agent import ToolAgent
from jarvis.brain.tool_runner import ToolRunner
from jarvis.brain.tools import ToolRegistry, ToolSpec
from jarvis.core.exceptions import PermissionDeniedError
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
        messages = kwargs.get("messages")
        if isinstance(messages, list):
            kwargs = {**kwargs, "messages": list(messages)}
        self.calls.append(kwargs)
        return next(self._responses)


class _FakeClient:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.messages = _FakeMessagesEndpoint(responses)


async def _web_search_handler(arguments: dict[str, object]) -> object:
    return {"results": []}


async def _read_file_handler(arguments: dict[str, object]) -> object:
    return {"content": "file contents"}


async def _run_shell_handler(arguments: dict[str, object]) -> object:
    return {"stdout": "ran", "return_code": 0}


@pytest.fixture
def registry() -> ToolRegistry:
    engine = PermissionEngine()
    audit_log = InMemoryAuditLog()
    registry = ToolRegistry(engine, audit_log)
    registry.register(
        ToolSpec(
            name="web_search", description="search the web", risk_level=RiskLevel.SENSITIVE,
            handler=_web_search_handler, input_schema={"type": "object", "properties": {}},
        )
    )
    registry.register(
        ToolSpec(
            name="read_file", description="read a file", risk_level=RiskLevel.SAFE,
            handler=_read_file_handler, input_schema={"type": "object", "properties": {}},
        )
    )
    registry.register(
        ToolSpec(
            name="run_shell_command", description="run a shell command",
            risk_level=RiskLevel.DANGEROUS, handler=_run_shell_handler,
            input_schema={"type": "object", "properties": {}},
        )
    )
    return registry


@pytest.mark.asyncio
async def test_tool_agent_respond_returns_final_text(registry: ToolRegistry) -> None:
    client = _FakeClient([_FakeResponse([_FakeTextBlock("done")], stop_reason="end_turn")])
    runner = ToolRunner(client, registry=registry)
    agent = ToolAgent(name="custom", system_prompt="be custom", runner=runner)

    reply = await agent.respond("s1", "hello")

    assert reply.content == "done"
    assert reply.pending_confirmation is None


@pytest.mark.asyncio
async def test_research_agent_only_sees_web_tools(registry: ToolRegistry) -> None:
    client = _FakeClient([_FakeResponse([_FakeTextBlock("ok")], stop_reason="end_turn")])
    agent = create_research_agent(client, registry)

    await agent.respond("s1", "find something")

    sent_tools = client.messages.calls[0]["tools"]
    assert isinstance(sent_tools, list)
    assert {t["name"] for t in sent_tools} == {"web_search"}
    assert agent.name == "research"


@pytest.mark.asyncio
async def test_research_agent_cannot_reach_system_tools(registry: ToolRegistry) -> None:
    client = _FakeClient(
        [
            _FakeResponse(
                [_FakeToolUseBlock("t1", "run_shell_command", {})], stop_reason="tool_use"
            )
        ]
    )
    agent = create_research_agent(client, registry, role=Role.OWNER)

    with pytest.raises(PermissionDeniedError):
        await agent.respond("s1", "run something dangerous")


@pytest.mark.asyncio
async def test_coding_agent_only_sees_system_tools(registry: ToolRegistry) -> None:
    client = _FakeClient([_FakeResponse([_FakeTextBlock("ok")], stop_reason="end_turn")])
    agent = create_coding_agent(client, registry)

    await agent.respond("s1", "read the readme")

    sent_tools = client.messages.calls[0]["tools"]
    assert isinstance(sent_tools, list)
    assert {t["name"] for t in sent_tools} == {"read_file", "run_shell_command"}
    assert agent.name == "coding"


@pytest.mark.asyncio
async def test_coding_agent_dangerous_tool_requires_confirmation(registry: ToolRegistry) -> None:
    client = _FakeClient(
        [
            _FakeResponse(
                [_FakeToolUseBlock("t1", "run_shell_command", {})], stop_reason="tool_use"
            )
        ]
    )
    agent = create_coding_agent(client, registry, role=Role.OWNER)

    reply = await agent.respond("s1", "run rm -rf")

    assert reply.pending_confirmation == "run_shell_command"


@pytest.mark.asyncio
async def test_custom_model_is_passed_through(registry: ToolRegistry) -> None:
    client = _FakeClient([_FakeResponse([_FakeTextBlock("ok")], stop_reason="end_turn")])
    agent = create_research_agent(client, registry, model="claude-sonnet-5")

    await agent.respond("s1", "hi")

    assert client.messages.calls[0]["model"] == "claude-sonnet-5"
