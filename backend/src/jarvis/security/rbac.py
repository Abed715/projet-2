"""Roles and the risk levels they're allowed to act on.

Multi-user support is a later phase (see ARCHITECTURE.md §8), but the model
exists from day one so nothing downstream has to be retrofitted for it.
"""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    """Who is asking. Ordered least to most privileged."""

    GUEST = "guest"
    OPERATOR = "operator"
    OWNER = "owner"


class RiskLevel(StrEnum):
    """How dangerous a tool/action is, as tagged in the tool registry."""

    SAFE = "safe"
    SENSITIVE = "sensitive"
    DANGEROUS = "dangerous"


#: Risk levels a role may invoke at all. A role attempting a risk level not
#: in its set is denied outright, before confirmation is even considered.
_ROLE_CEILINGS: dict[Role, frozenset[RiskLevel]] = {
    Role.GUEST: frozenset({RiskLevel.SAFE}),
    Role.OPERATOR: frozenset({RiskLevel.SAFE, RiskLevel.SENSITIVE, RiskLevel.DANGEROUS}),
    Role.OWNER: frozenset({RiskLevel.SAFE, RiskLevel.SENSITIVE, RiskLevel.DANGEROUS}),
}


def role_permits(role: Role, risk_level: RiskLevel) -> bool:
    """Whether `role` is allowed to invoke a tool tagged `risk_level` at all.

    This is the coarse RBAC gate; `security.permissions.PermissionEngine`
    applies the finer-grained confirmation flow on top for `DANGEROUS`
    actions a role is otherwise permitted to reach.
    """
    return risk_level in _ROLE_CEILINGS[role]
