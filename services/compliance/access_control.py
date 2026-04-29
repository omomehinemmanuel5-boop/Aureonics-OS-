ROLE_PERMISSIONS = {
    "admin": {"view_audit", "send_message", "approve_high_risk", "manage_policy"},
    "sales": {"send_message", "view_deals"},
    "compliance": {"view_audit", "approve_high_risk", "view_deals"},
}


def can(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
