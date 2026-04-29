from dataclasses import dataclass


@dataclass(frozen=True)
class SOC2Control:
    control_id: str
    domain: str
    description: str


SOC2_CONTROLS = [
    SOC2Control("CC6.1", "Logical Access", "RBAC enforced on all sensitive actions."),
    SOC2Control("CC7.2", "Change Mgmt", "All outbound automations are auditable."),
    SOC2Control("CC8.1", "Monitoring", "Anomaly/escalation coverage for high-risk actions."),
]
