from __future__ import annotations

from collections import defaultdict
from typing import Callable

from lex_aureon.backend.common.models import EventEnvelope


class EventBus:
    def publish(self, event: EventEnvelope) -> None:  # pragma: no cover
        raise NotImplementedError

    def subscribe(self, event_type: str, handler: Callable[[EventEnvelope], None]) -> None:  # pragma: no cover
        raise NotImplementedError


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[EventEnvelope], None]]] = defaultdict(list)
        self.events: list[EventEnvelope] = []

    def publish(self, event: EventEnvelope) -> None:
        self.events.append(event)
        for handler in self._handlers.get(event.event_type.value, []):
            handler(event)

    def subscribe(self, event_type: str, handler: Callable[[EventEnvelope], None]) -> None:
        self._handlers[event_type].append(handler)


event_bus = InMemoryEventBus()
