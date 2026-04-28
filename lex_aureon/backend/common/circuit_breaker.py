from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CircuitBreaker:
    threshold: int = 3
    failure_count: int = 0
    open_state: bool = False

    def execute(self, fn, fallback):
        if self.open_state:
            return fallback()
        try:
            result = fn()
            self.failure_count = 0
            return result
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.threshold:
                self.open_state = True
            return fallback()

    def reset(self) -> None:
        self.failure_count = 0
        self.open_state = False
