"""The permission engine: the enforcement point every tool call passes
through before it runs. See ARCHITECTURE.md §8.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from jarvis.core.exceptions import ConfigurationError
from jarvis.security.rbac import RiskLevel, Role, role_permits


class PermissionDecision(StrEnum):
    ALLOW = "allow"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class PermissionResult:
    decision: PermissionDecision
    reason: str


class PermissionEngine:
    """Evaluates whether a (role, tool) pair may proceed.

    Tools register their risk level once — typically at startup, from the
    tool registry in `brain` — and every invocation is evaluated here before
    it reaches the tool implementation. This engine only knows about risk
    levels and role ceilings; it has no knowledge of what a tool actually
    does, keeping it reusable across every domain module.
    """

    def __init__(self) -> None:
        self._tool_risk: dict[str, RiskLevel] = {}
        self._session_grants: set[tuple[str, str]] = set()

    def register_tool(self, tool_name: str, risk_level: RiskLevel) -> None:
        """Register (or re-register) a tool's risk level."""
        self._tool_risk[tool_name] = risk_level

    def risk_level_of(self, tool_name: str) -> RiskLevel:
        try:
            return self._tool_risk[tool_name]
        except KeyError as exc:
            raise ConfigurationError(
                f"tool {tool_name!r} is not registered with the permission engine"
            ) from exc

    def grant_for_session(self, session_id: str, tool_name: str) -> None:
        """Record an "always allow this action" opt-in for the session.

        Only meaningful for `DANGEROUS` tools — `SAFE`/`SENSITIVE` tools
        never require confirmation in the first place.
        """
        self._session_grants.add((session_id, tool_name))

    def revoke_for_session(self, session_id: str, tool_name: str) -> None:
        self._session_grants.discard((session_id, tool_name))

    def evaluate(self, *, role: Role, tool_name: str, session_id: str) -> PermissionResult:
        risk_level = self.risk_level_of(tool_name)

        if not role_permits(role, risk_level):
            return PermissionResult(
                PermissionDecision.DENY,
                f"role {role.value!r} may not invoke {risk_level.value} tools",
            )

        if risk_level is not RiskLevel.DANGEROUS:
            return PermissionResult(
                PermissionDecision.ALLOW, f"{risk_level.value} tools run without confirmation"
            )

        if (session_id, tool_name) in self._session_grants:
            return PermissionResult(
                PermissionDecision.ALLOW, "previously granted for this session"
            )

        return PermissionResult(
            PermissionDecision.REQUIRES_CONFIRMATION,
            "dangerous action requires explicit user confirmation",
        )
