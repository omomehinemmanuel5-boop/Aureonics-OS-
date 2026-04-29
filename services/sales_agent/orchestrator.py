from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List

from .conversation_state import ConversationContext, LeadProfile, SalesState
from .intent_classifier import IntentClassifier
from .memory import PersistentMemory
from .reasoning_engine import ReasoningEngine
from .recovery_engine import RecoveryEngine


class SalesAgentOrchestrator:
    def __init__(self) -> None:
        self.classifier = IntentClassifier()
        self.reasoner = ReasoningEngine()
        self.memory = PersistentMemory()
        self.recovery = RecoveryEngine()

    def process(self, message: str, lead: LeadProfile, history: List[Dict[str, str]]) -> Dict[str, Any]:
        intent, confidence = self.classifier.classify(message, lead)
        ctx = ConversationContext(lead=lead, message=message, history=history, intent=intent, confidence=confidence)
        ctx = self.reasoner.transition(ctx)
        response = self.reasoner.compose(ctx)

        outcome = "positive" if ctx.state in {SalesState.CLOSING_ATTEMPT, SalesState.DEMO_CONVERSION} else "neutral"
        mem = self.memory.get(lead.lead_id)
        if ctx.state == SalesState.OBJECTION_HANDLING:
            mem.objections.append(message)
        mem.conversion_attempts.append(ctx.state.value)
        self.memory.update(lead.lead_id, mem)

        return {
            "response_message": response,
            "state_transition": ctx.state.value,
            "confidence_score": round(confidence, 3),
            "outcome_signal": outcome,
            "intent": intent.value,
            "memory": asdict(mem),
        }

    def self_heal(self, lead_id: str, failure_type: str) -> Dict[str, str]:
        result = self.recovery.recover(failure_type)
        mem = self.memory.get(lead_id)
        mem.persona_model["last_shift"] = result.strategy_shift
        self.memory.update(lead_id, mem)
        return asdict(result)
