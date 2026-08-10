"""jarvis.security — permission engine, audit log, secrets vault, RBAC.

See README.md for the full public interface and design notes.
"""

from jarvis.security.audit import AuditEntry, AuditLog, InMemoryAuditLog, SqlAuditLog, redact
from jarvis.security.permissions import PermissionDecision, PermissionEngine, PermissionResult
from jarvis.security.rbac import RiskLevel, Role, role_permits
from jarvis.security.sandbox import SandboxExecutor, SandboxResult
from jarvis.security.secrets import SecretsVault

__all__ = [
    "AuditEntry",
    "AuditLog",
    "InMemoryAuditLog",
    "SqlAuditLog",
    "redact",
    "PermissionDecision",
    "PermissionEngine",
    "PermissionResult",
    "Role",
    "RiskLevel",
    "role_permits",
    "SandboxExecutor",
    "SandboxResult",
    "SecretsVault",
]
