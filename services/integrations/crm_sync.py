from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class CRMSync:
    records: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def upsert_lead(self, lead_id: str, payload: Dict[str, Any]) -> None:
        self.records[lead_id] = {**self.records.get(lead_id, {}), **payload}
