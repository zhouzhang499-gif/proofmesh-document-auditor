from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .contracts import FactObservation


MONEY_FACTORS = {
    "元": Decimal("1"),
    "人民币": Decimal("1"),
    "CNY": Decimal("1"),
    "万元": Decimal("10000"),
    "亿元": Decimal("100000000"),
}


def canonicalize_label(label: str, aliases: dict[str, str]) -> str:
    cleaned = re.sub(r"[\s:：()（）\[\]【】]", "", label)
    cleaned = re.sub(r"(同比|环比)", "", cleaned)
    cleaned = re.sub(r"20\d{2}[年-]?[Qq][1-4]", "", cleaned)
    cleaned = re.sub(r"20\d{2}年?", "", cleaned)
    cleaned = re.sub(r"(为|是|达到|预计|约|合计|共计)$", "", cleaned, flags=re.IGNORECASE)
    return aliases.get(cleaned, cleaned)


def _observation_id(document_hash: str, locator: str, fact_type: str) -> str:
    raw = f"{document_hash}|{locator}|{fact_type}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def parse_fact(
    *,
    value: Any,
    label: str,
    number_format: str,
    document_hash: str,
    relative_path: str,
    locator: str,
    evidence_id: str,
    aliases: dict[str, str],
    money_labels: list[str],
    date_labels: list[str],
) -> FactObservation | None:
    raw = _display_value(value, number_format)
    combined = f"{label} {raw}".strip()
    qualifier = "同比" if "同比" in combined else "环比" if "环比" in combined else ""
    canonical_label = canonicalize_label(label or _label_from_inline_value(raw), aliases)
    period = _extract_period(label if isinstance(value, (datetime, date)) else combined)

    if isinstance(value, (datetime, date)):
        normalized = value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
        return _make_observation("date", normalized, raw, "date", canonical_label, period, qualifier, document_hash, relative_path, locator, evidence_id)

    text = str(value).strip()
    percent_match = re.fullmatch(r"([-+]?\d[\d,]*(?:\.\d+)?)\s*[%％]", text)
    if percent_match:
        normalized = _decimal_text(Decimal(percent_match.group(1).replace(",", "")) / Decimal("100"))
        return _make_observation("percentage", normalized, raw, "%", canonical_label, period, qualifier, document_hash, relative_path, locator, evidence_id)

    money_match = re.fullmatch(r"(?:人民币|CNY)?\s*([-+]?\d[\d,]*(?:\.\d+)?)\s*(亿元|万元|元|人民币|CNY)", text, flags=re.IGNORECASE)
    if money_match:
        unit = money_match.group(2)
        number = Decimal(money_match.group(1).replace(",", ""))
        normalized = _decimal_text(number * MONEY_FACTORS[unit])
        return _make_observation("money", normalized, raw, unit, canonical_label, period, qualifier, document_hash, relative_path, locator, evidence_id)

    if isinstance(value, (int, float, Decimal)):
        if "%" in number_format:
            normalized = _decimal_text(Decimal(str(value)))
            return _make_observation("percentage", normalized, raw, "%", canonical_label, period, qualifier, document_hash, relative_path, locator, evidence_id)
        if any(term in label for term in money_labels):
            normalized = _decimal_text(Decimal(str(value)))
            return _make_observation("money", normalized, raw, "元", canonical_label, period, qualifier, document_hash, relative_path, locator, evidence_id)

    date_match = re.fullmatch(r"(20\d{2})[-/.年](\d{1,2})[-/.月](\d{1,2})日?", text)
    if date_match or any(term in label for term in date_labels) and re.search(r"20\d{2}", text):
        if date_match:
            normalized = f"{int(date_match.group(1)):04d}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
            return _make_observation(
                "date",
                normalized,
                raw,
                "date",
                canonical_label,
                _extract_period(label),
                qualifier,
                document_hash,
                relative_path,
                locator,
                evidence_id,
            )

    return None


def _make_observation(
    fact_type: str,
    normalized: str,
    raw: str,
    unit: str,
    label: str,
    period: str,
    qualifier: str,
    document_hash: str,
    relative_path: str,
    locator: str,
    evidence_id: str,
) -> FactObservation:
    return FactObservation(
        observation_id=_observation_id(document_hash, locator, fact_type),
        fact_type=fact_type,
        canonical_label=label or "未命名指标",
        normalized_value=normalized,
        raw_value=raw,
        unit=unit,
        period=period,
        qualifier=qualifier,
        evidence_id=evidence_id,
        relative_path=relative_path,
        locator=locator,
        document_hash=document_hash,
    )


def _display_value(value: Any, number_format: str) -> str:
    if isinstance(value, float) and "%" in number_format:
        return f"{value * 100:g}%"
    if isinstance(value, datetime):
        return value.date().isoformat()
    return str(value)


def _label_from_inline_value(raw: str) -> str:
    return re.sub(r"[-+]?\d[\d,.]*\s*(亿元|万元|元|%|％|人民币|CNY)?", "", raw).strip()


def _extract_period(text: str) -> str:
    quarter = re.search(r"(20\d{2})\s*[年-]?\s*[Qq]([1-4])", text)
    if quarter:
        return f"{quarter.group(1)}Q{quarter.group(2)}"
    year = re.search(r"(20\d{2})年", text)
    if year:
        return year.group(1)
    bare_year = re.search(r"(?<!\d)(20\d{2})(?!\d)", text)
    return bare_year.group(1) if bare_year else ""


def _decimal_text(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == 0:
        return "0"
    return format(normalized, "f")
