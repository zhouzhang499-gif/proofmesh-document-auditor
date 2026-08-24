from __future__ import annotations

import re
from typing import Any

from .contracts import FactObservation
from .normalization import parse_fact


FACT_PATTERN = re.compile(
    r"(?:20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}日?)"
    r"|(?:(?:人民币|CNY)\s*)?[-+]?\d[\d,]*(?:\.\d+)?\s*(?:亿元|万元|元|人民币|CNY)"
    r"|(?:[-+]?\d[\d,]*(?:\.\d+)?\s*[%％])",
    flags=re.IGNORECASE,
)


def extract_facts_from_text(
    *,
    text: str,
    base_locator: str,
    document_hash: str,
    relative_path: str,
    evidence_id: str,
    rules: dict[str, Any],
) -> list[FactObservation]:
    facts: list[FactObservation] = []
    for match in FACT_PATTERN.finditer(text):
        raw_value = match.group(0).strip()
        label = _label_before(text, match.start())
        locator = f"{base_locator}/text:{match.start()}-{match.end()}"
        fact = parse_fact(
            value=raw_value,
            label=label,
            number_format="General",
            document_hash=document_hash,
            relative_path=relative_path,
            locator=locator,
            evidence_id=evidence_id,
            aliases=rules.get("aliases", {}),
            money_labels=rules.get("money_labels", []),
            date_labels=rules.get("date_labels", []),
        )
        if fact:
            facts.append(fact)
    return facts


def _label_before(text: str, start: int) -> str:
    prefix = text[max(0, start - 60):start]
    segment = re.split(r"[。；;，,、！？!?\n]", prefix)[-1]
    segment = re.sub(r"^[\s\-—,:：]+|[\s\-—,:：]+$", "", segment)
    segment = re.sub(r"(为|是|达到|预计|约|合计|共计)\s*$", "", segment, flags=re.IGNORECASE)
    return segment[-30:].strip()
