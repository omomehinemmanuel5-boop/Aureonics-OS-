from __future__ import annotations

from .closing_engine import ClosingEngine
from .conversation_state import ConversationContext, IntentClass, SalesState
from .message_generator import MessageGenerator
from .objection_handler import ObjectionHandler


class ReasoningEngine:
    def __init__(self) -> None:
        self.objections = ObjectionHandler()
        self.msg = MessageGenerator()
        self.closer = ClosingEngine()

    def transition(self, ctx: ConversationContext) -> ConversationContext:
        objection_reply = self.objections.resolve(ctx.message)
        if objection_reply:
            ctx.state = SalesState.OBJECTION_HANDLING
            ctx.outcome_signal = "objection_detected"
            return ctx

        if ctx.intent == IntentClass.HOT:
            ctx.state = SalesState.CLOSING_ATTEMPT
        elif ctx.intent == IntentClass.WARM:
            ctx.state = SalesState.DEMO_CONVERSION
        elif ctx.intent == IntentClass.COLD:
            ctx.state = SalesState.QUALIFICATION
        else:
            ctx.state = SalesState.HANDOFF
        return ctx

    def compose(self, ctx: ConversationContext) -> str:
        objection_reply = self.objections.resolve(ctx.message)
        if objection_reply:
            return objection_reply
        action = self.closer.next_action(ctx.intent)
        if ctx.intent == IntentClass.HOT:
            return self.closer.close_message(action)
        return self.msg.generate(ctx.intent)
