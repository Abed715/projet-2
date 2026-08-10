import pytest

from jarvis.agents.automation import create_automation_agent
from jarvis.agents.vision import create_vision_agent
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


async def _list_processes_handler(arguments: dict[str, object]) -> object:
    return {"processes": []}


async def _open_application_handler(arguments: dict[str, object]) -> object:
    return {"pid": 123}


async def _capture_screen_handler(arguments: dict[str, object]) -> object:
    return {"image_base64": "ZmFrZQ=="}


async def _extract_text_handler(arguments: dict[str, object]) -> object:
    return {"text": "hi"}


@pytest.fixture
def registry() -> ToolRegistry:
    engine = PermissionEngine()
    audit_log = InMemoryAuditLog()
    registry = ToolRegistry(engine, audit_log)
    registry.register(
        ToolSpec(
            name="list_processes", description="list processes", risk_level=RiskLevel.SAFE,
            handler=_list_processes_handler, input_schema={"type": "object", "properties": {}},
        )
    )
    registry.register(
        ToolSpec(
            name="open_application", description="open an application",
            risk_level=RiskLevel.DANGEROUS, handler=_open_application_handler,
            input_schema={"type": "object", "properties": {}},
        )
    )
    registry.register(
        ToolSpec(
            name="capture_screen", description="capture the screen",
            risk_level=RiskLevel.SENSITIVE, handler=_capture_screen_handler,
            input_schema={"type": "object", "properties": {}},
        )
    )
    registry.register(
        ToolSpec(
            name="extract_text", description="run OCR", risk_level=RiskLevel.SAFE,
            handler=_extract_text_handler, input_schema={"type": "object", "properties": {}},
        )
    )
    return registry


@pytest.mark.asyncio
async def test_automation_agent_only_sees_automation_tools(registry: ToolRegistry) -> None:
    client = _FakeClient([_FakeResponse([_FakeTextBlock("ok")], stop_reason="end_turn")])
    agent = create_automation_agent(client, registry)

    await agent.respond("s1", "list running apps")

    sent_tools = client.messages.calls[0]["tools"]
    assert isinstance(sent_tools, list)
    assert {t["name"] for t in sent_tools} == {"list_processes", "open_application"}
    assert agent.name == "automation"


@pytest.mark.asyncio
async def test_automation_agent_cannot_reach_vision_tools(registry: ToolRegistry) -> None:
    client = _FakeClient(
        [_FakeResponse([_FakeToolUseBlock("t1", "capture_screen", {})], stop_reason="tool_use")]
    )
    agent = create_automation_agent(client, registry, role=Role.OWNER)

    with pytest.raises(PermissionDeniedError):
        await agent.respond("s1", "take a screenshot")


@pytest.mark.asyncio
async def test_automation_agent_dangerous_tool_requires_confirmation(
    registry: ToolRegistry,
) -> None:
    client = _FakeClient(
        [_FakeResponse([_FakeToolUseBlock("t1", "open_application", {})], stop_reason="tool_use")]
    )
    agent = create_automation_agent(client, registry, role=Role.OWNER)

    reply = await agent.respond("s1", "open firefox")

    assert reply.pending_confirmation == "open_application"


@pytest.mark.asyncio
async def test_vision_agent_only_sees_vision_tools(registry: ToolRegistry) -> None:
    client = _FakeClient([_FakeResponse([_FakeTextBlock("ok")], stop_reason="end_turn")])
    agent = create_vision_agent(client, registry)

    await agent.respond("s1", "what's on my screen")

    sent_tools = client.messages.calls[0]["tools"]
    assert isinstance(sent_tools, list)
    assert {t["name"] for t in sent_tools} == {"capture_screen", "extract_text"}
    assert agent.name == "vision"


@pytest.mark.asyncio
async def test_vision_agent_cannot_reach_automation_tools(registry: ToolRegistry) -> None:
    client = _FakeClient(
        [_FakeResponse([_FakeToolUseBlock("t1", "open_application", {})], stop_reason="tool_use")]
    )
    agent = create_vision_agent(client, registry, role=Role.OWNER)

    with pytest.raises(PermissionDeniedError):
        await agent.respond("s1", "open an application")


@pytest.mark.asyncio
async def test_vision_agent_custom_model_is_passed_through(registry: ToolRegistry) -> None:
    client = _FakeClient([_FakeResponse([_FakeTextBlock("ok")], stop_reason="end_turn")])
    agent = create_vision_agent(client, registry, model="claude-sonnet-5")

    await agent.respond("s1", "hi")

    assert client.messages.calls[0]["model"] == "claude-sonnet-5"
