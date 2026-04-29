from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class EmailRecord:
    to: str
    subject: str
    body: str


@dataclass
class EmailProvider:
    sent: List[EmailRecord] = field(default_factory=list)

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append(EmailRecord(to=to, subject=subject, body=body))
