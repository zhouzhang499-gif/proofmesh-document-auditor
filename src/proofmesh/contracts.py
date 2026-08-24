from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceAtom:
    evidence_id: str
    document_hash: str
    relative_path: str
    media_type: str
    locator: str
    raw_text: str
    extractor: str
    extraction_confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FactObservation:
    observation_id: str
    fact_type: str
    canonical_label: str
    normalized_value: str
    raw_value: str
    unit: str
    period: str
    qualifier: str
    evidence_id: str
    relative_path: str
    locator: str
    document_hash: str

    @property
    def group_key(self) -> tuple[str, str, str]:
        return (self.fact_type, self.canonical_label, self.period)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Issue:
    issue_id: str
    rule_id: str
    severity: str
    title: str
    explanation: str
    action: str
    observations: tuple[FactObservation, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["observations"] = [item.to_dict() for item in self.observations]
        return data

