import pytest

from jarvis.security.rbac import RiskLevel, Role, role_permits


@pytest.mark.parametrize(
    ("role", "risk_level", "expected"),
    [
        (Role.GUEST, RiskLevel.SAFE, True),
        (Role.GUEST, RiskLevel.SENSITIVE, False),
        (Role.GUEST, RiskLevel.DANGEROUS, False),
        (Role.OPERATOR, RiskLevel.SAFE, True),
        (Role.OPERATOR, RiskLevel.SENSITIVE, True),
        (Role.OPERATOR, RiskLevel.DANGEROUS, True),
        (Role.OWNER, RiskLevel.SAFE, True),
        (Role.OWNER, RiskLevel.SENSITIVE, True),
        (Role.OWNER, RiskLevel.DANGEROUS, True),
    ],
)
def test_role_permits_matrix(role: Role, risk_level: RiskLevel, expected: bool) -> None:
    assert role_permits(role, risk_level) is expected
