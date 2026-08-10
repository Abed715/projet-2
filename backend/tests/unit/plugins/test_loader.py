import pytest

from jarvis.brain.tools import ToolRegistry, ToolSpec
from jarvis.core.exceptions import ConfigurationError
from jarvis.plugins.loader import PluginLoader
from jarvis.plugins.manifest import PluginManifest
from jarvis.security import InMemoryAuditLog, PermissionEngine, RiskLevel, Role


class _FakePlugin:
    def __init__(self, name: str, *, tool_name: str) -> None:
        self._manifest = PluginManifest(name=name, version="1.0", description="a fake plugin")
        self._tool_name = tool_name
        self.registered_into: ToolRegistry | None = None

    @property
    def manifest(self) -> PluginManifest:
        return self._manifest

    def register_tools(self, registry: ToolRegistry) -> None:
        self.registered_into = registry

        async def handler(arguments: dict[str, object]) -> object:
            return {"ok": True}

        registry.register(
            ToolSpec(
                name=self._tool_name,
                description="fake tool",
                risk_level=RiskLevel.SAFE,
                handler=handler,
                input_schema={"type": "object", "properties": {}},
            )
        )


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry(PermissionEngine(), InMemoryAuditLog())


def test_register_then_list_plugins() -> None:
    loader = PluginLoader()
    plugin = _FakePlugin("demo", tool_name="demo_tool")

    loader.register(plugin)

    assert loader.list_plugins() == [plugin.manifest]


def test_register_duplicate_name_raises(registry: ToolRegistry) -> None:
    loader = PluginLoader()
    loader.register(_FakePlugin("demo", tool_name="demo_tool_1"))

    with pytest.raises(ConfigurationError):
        loader.register(_FakePlugin("demo", tool_name="demo_tool_2"))


def test_load_all_registers_every_plugins_tools(registry: ToolRegistry) -> None:
    loader = PluginLoader()
    loader.register(_FakePlugin("alpha", tool_name="alpha_tool"))
    loader.register(_FakePlugin("beta", tool_name="beta_tool"))

    manifests = loader.load_all(registry)

    assert {m.name for m in manifests} == {"alpha", "beta"}
    assert {t.name for t in registry.list_tools()} == {"alpha_tool", "beta_tool"}


@pytest.mark.asyncio
async def test_plugin_tool_goes_through_normal_permission_and_audit_path(
    registry: ToolRegistry,
) -> None:
    loader = PluginLoader()
    loader.register(_FakePlugin("demo", tool_name="demo_tool"))
    loader.load_all(registry)

    result = await registry.invoke(
        name="demo_tool",
        arguments={},
        role=Role.GUEST,
        session_id="s1",
        actor="plugin",
        correlation_id="c1",
    )

    assert result.result == {"ok": True}
