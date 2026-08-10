import pytest

from jarvis.core.exceptions import ConfigurationError
from jarvis.security.permissions import PermissionDecision, PermissionEngine
from jarvis.security.rbac import RiskLevel, Role


@pytest.fixture
def engine() -> PermissionEngine:
    engine = PermissionEngine()
    engine.register_tool("read_file", RiskLevel.SAFE)
    engine.register_tool("send_email", RiskLevel.SENSITIVE)
    engine.register_tool("delete_file", RiskLevel.DANGEROUS)
    return engine


def test_unregistered_tool_raises(engine: PermissionEngine) -> None:
    with pytest.raises(ConfigurationError):
        engine.risk_level_of("unknown_tool")


def test_safe_tool_always_allowed(engine: PermissionEngine) -> None:
    result = engine.evaluate(role=Role.GUEST, tool_name="read_file", session_id="s1")

    assert result.decision is PermissionDecision.ALLOW


def test_guest_denied_sensitive_tool(engine: PermissionEngine) -> None:
    result = engine.evaluate(role=Role.GUEST, tool_name="send_email", session_id="s1")

    assert result.decision is PermissionDecision.DENY


def test_operator_allowed_sensitive_tool(engine: PermissionEngine) -> None:
    result = engine.evaluate(role=Role.OPERATOR, tool_name="send_email", session_id="s1")

    assert result.decision is PermissionDecision.ALLOW


def test_guest_denied_dangerous_tool(engine: PermissionEngine) -> None:
    result = engine.evaluate(role=Role.GUEST, tool_name="delete_file", session_id="s1")

    assert result.decision is PermissionDecision.DENY


def test_owner_dangerous_tool_requires_confirmation_by_default(engine: PermissionEngine) -> None:
    result = engine.evaluate(role=Role.OWNER, tool_name="delete_file", session_id="s1")

    assert result.decision is PermissionDecision.REQUIRES_CONFIRMATION


def test_session_grant_allows_dangerous_tool_without_reconfirmation(
    engine: PermissionEngine,
) -> None:
    engine.grant_for_session("s1", "delete_file")

    result = engine.evaluate(role=Role.OWNER, tool_name="delete_file", session_id="s1")

    assert result.decision is PermissionDecision.ALLOW


def test_session_grant_is_scoped_to_session(engine: PermissionEngine) -> None:
    engine.grant_for_session("s1", "delete_file")

    result = engine.evaluate(role=Role.OWNER, tool_name="delete_file", session_id="s2")

    assert result.decision is PermissionDecision.REQUIRES_CONFIRMATION


def test_revoke_removes_the_grant(engine: PermissionEngine) -> None:
    engine.grant_for_session("s1", "delete_file")
    engine.revoke_for_session("s1", "delete_file")

    result = engine.evaluate(role=Role.OWNER, tool_name="delete_file", session_id="s1")

    assert result.decision is PermissionDecision.REQUIRES_CONFIRMATION


def test_re_registering_a_tool_updates_its_risk_level(engine: PermissionEngine) -> None:
    engine.register_tool("read_file", RiskLevel.DANGEROUS)

    result = engine.evaluate(role=Role.GUEST, tool_name="read_file", session_id="s1")

    assert result.decision is PermissionDecision.DENY
