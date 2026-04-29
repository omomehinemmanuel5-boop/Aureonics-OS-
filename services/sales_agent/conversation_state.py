from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class SalesState(str, Enum):
    LEAD_DETECTION = "lead_detection"
    ENGAGEMENT = "engagement"
    QUALIFICATION = "qualification"
    OBJECTION_HANDLING = "objection_handling"
    DEMO_CONVERSION = "demo_conversion"
    CLOSING_ATTEMPT = "closing_attempt"
    HANDOFF = "handoff"
    SELF_HEALING_LOOP = "self_healing_loop"


class IntentClass(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    DEAD = "dead"


@dataclass
class LeadProfile:
    lead_id: str
    name: str = ""
    company: str = ""
    channel: str = "email"
    urgency_score: float = 0.0
    budget_hint: float = 0.0
    compliance_interest: float = 0.0
    technical_depth: float = 0.0
    response_speed: float = 0.0


@dataclass
class ConversationMemory:
    objections: List[str] = field(default_factory=list)
    conversion_attempts: List[str] = field(default_factory=list)
    tone_preference: str = "concise"
    response_sensitivity: str = "neutral"
    persona_model: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    lead: LeadProfile
    message: str
    history: List[Dict[str, str]] = field(default_factory=list)
    state: SalesState = SalesState.LEAD_DETECTION
    intent: IntentClass = IntentClass.COLD
    confidence: float = 0.0
    outcome_signal: str = "unknown"
