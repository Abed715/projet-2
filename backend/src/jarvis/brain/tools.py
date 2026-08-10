"""The tool registry: brain's shared surface for defining and invoking
tools, wired through `security`'s permission engine and audit log so every
invocation is checked and logged before it runs. See ARCHITECTURE.md §3.1
and §8.

No domain tools are registered yet — `system`, `web`, `automation`, and
`vision` (Phases 3-4) are the modules that will register real tools here.
This module ships the plumbing ahead of them so agents built in this phase
already go through the permission/audit path once tools exist.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum

from jarvis.core.exceptions import ConfigurationError, PermissionDeniedError
from jarvis.security import (
    AuditEntry,
    AuditLog,
    PermissionDecision,
    PermissionEngine,
    RiskLevel,
    Role,
    redact,
)

ToolHandler = Callable[[dict[str, object]], Awaitable[object]]


class ToolInvocationStatus(StrEnum):
    OK = "ok"
    REQUIRES_CONFIRMATION = "requires_confirmation"


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    risk_level: RiskLevel
    handler: ToolHandler


@dataclass(frozen=True, slots=True)
class ToolInvocationResult:
    status: ToolInvocationStatus
    result: object | None = None


class ToolRegistry:
    """Registers tools and mediates every invocation through security."""

    def __init__(self, permission_engine: PermissionEngine, audit_log: AuditLog) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._permission_engine = permission_engine
        self._audit_log = audit_log

    def register(self, tool: ToolSpec) -> None:
        self._tools[tool.name] = tool
        self._permission_engine.register_tool(tool.name, tool.risk_level)

    def get(self, name: str) -> ToolSpec:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ConfigurationError(f"tool {name!r} is not registered") from exc

    def list_tools(self) -> list[ToolSpec]:
        return list(self._tools.values())

    async def invoke(
        self,
        *,
        name: str,
        arguments: dict[str, object],
        role: Role,
        session_id: str,
        actor: str,
        correlation_id: str,
    ) -> ToolInvocationResult:
        tool = self.get(name)
        decision = self._permission_engine.evaluate(
            role=role, tool_name=name, session_id=session_id
        )

        await self._audit_log.record(
            AuditEntry(
                correlation_id=correlation_id,
                actor=actor,
                tool_name=name,
                decision=decision.decision.value,
                params=redact(arguments),
            )
        )

        if decision.decision is PermissionDecision.DENY:
            raise PermissionDeniedError(f"role {role.value!r} may not invoke {name!r}")

        if decision.decision is PermissionDecision.REQUIRES_CONFIRMATION:
            return ToolInvocationResult(status=ToolInvocationStatus.REQUIRES_CONFIRMATION)

        result = await tool.handler(arguments)
        return ToolInvocationResult(status=ToolInvocationStatus.OK, result=result)
