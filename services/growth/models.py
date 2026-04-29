from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Lead:
    lead_id: str
    full_name: str
    title: str
    company: str
    company_size: int
    channel: str
    profile_url: str
    signals: Dict[str, float]
    context: Dict[str, str] = field(default_factory=dict)


@dataclass
class ScoredLead:
    lead: Lead
    component_scores: Dict[str, float]
    total_score: float
    intent: str
    persona: str


@dataclass
class MessageBundle:
    opener: str
    problem: str
    value: str
    cta: str


@dataclass
class ConversationState:
    lead_id: str
    channel: str
    last_contacted_at: Optional[datetime] = None
    followup_count: int = 0
    last_message: Optional[str] = None
    tags: List[str] = field(default_factory=list)
