from __future__ import annotations

import hashlib
from collections import defaultdict
from decimal import Decimal, InvalidOperation

from .contracts import FactObservation, Issue


def find_issues(observations: list[FactObservation]) -> list[Issue]:
    groups: dict[tuple[str, str, str], list[FactObservation]] = defaultdict(list)
    for item in observations:
        groups[item.group_key].append(item)

    issues: list[Issue] = []
    for key, items in groups.items():
        documents = {item.relative_path for item in items}
        if len(documents) < 2:
            continue

        qualifiers = {item.qualifier for item in items if item.qualifier}
        values = {item.normalized_value for item in items}
        fact_type, label, _period = key

        if len(qualifiers) > 1:
            raw_values = "、".join(sorted({item.raw_value for item in items}))
            qualifier_text = "、".join(sorted(qualifiers))
            issues.append(
                _make_issue(
                    "growth_basis_consistency",
                    "high",
                    label,
                    items,
                    f"材料里的数值为 {raw_values}，口径分别标成{qualifier_text}。百分比相同也不能直接互换口径。",
                    "请确认这里统计的是同比还是环比，并统一相关材料的标签和说明。",
                )
            )
        if len(values) > 1:
            severity = "high" if fact_type in {"money", "date"} else "medium"
            issues.append(
                _make_issue(
                    f"{fact_type}_value_consistency",
                    severity,
                    label,
                    items,
                    _value_explanation(fact_type, items),
                    "请确认采用哪一个值，并同步更新仍在使用旧值的交付材料。",
                )
            )

    return sorted(issues, key=lambda item: (item.severity != "high", item.title, item.issue_id))


def _make_issue(
    rule_id: str,
    severity: str,
    label: str,
    items: list[FactObservation],
    explanation: str,
    action: str,
) -> Issue:
    ordered = tuple(sorted(items, key=lambda item: (item.relative_path, item.locator, item.raw_value)))
    key = rule_id + "|" + "|".join(f"{item.document_hash}:{item.locator}" for item in ordered)
    issue_id = hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]
    title = f"{label}在不同材料中对不上"
    return Issue(issue_id, rule_id, severity, title, explanation, action, ordered)


def _value_explanation(fact_type: str, items: list[FactObservation]) -> str:
    raw_values = sorted({item.raw_value for item in items})
    if fact_type == "money":
        try:
            normalized = sorted({Decimal(item.normalized_value) for item in items})
            if len(normalized) == 2 and normalized[0] != 0:
                ratio = normalized[-1] / normalized[0]
                if ratio == ratio.to_integral_value():
                    lower = f"{normalized[0]:,.0f}元"
                    upper = f"{normalized[-1]:,.0f}元"
                    originals = "、".join(raw_values)
                    return f"原文写法包括 {originals}。统一换算后是 {lower}和{upper}，相差 {ratio:g} 倍。"
        except InvalidOperation:
            pass
    joined = "、".join(raw_values)
    if fact_type == "date":
        return f"材料中出现了 {joined} 这些不同日期。"
    if fact_type == "percentage":
        return f"材料中出现了 {joined} 这些不同百分比。"
    return f"材料中记录了 {joined} 这些不同值。"
