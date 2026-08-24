from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OUTPUT = Path(__file__).with_name("fact_pairs.jsonl")


def observation(
    label: str,
    value: Any,
    *,
    number_format: str = "General",
    value_type: str = "text",
) -> dict[str, Any]:
    return {
        "label": label,
        "value": value,
        "number_format": number_format,
        "value_type": value_type,
    }


def pair(
    case_id: str,
    category: str,
    expected: str,
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    difficulty: str,
    expected_rule_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": case_id,
        "category": category,
        "difficulty": difficulty,
        "expected": expected,
        "expected_rule_ids": expected_rule_ids or [],
        "left": left,
        "right": right,
    }


def build_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    for index in range(15):
        cases.append(
            pair(
                f"clear-conflict-money-{index + 1:02d}",
                "clear_conflict",
                "conflict",
                observation(f"合同金额{index + 1}", f"{100 + index}万元"),
                observation(f"合同金额{index + 1}", f"{101 + index}万元"),
                difficulty="money_value",
                expected_rule_ids=["money_value_consistency"],
            )
        )

    for index in range(10):
        cases.append(
            pair(
                f"clear-conflict-percentage-{index + 1:02d}",
                "clear_conflict",
                "conflict",
                observation(f"完成率{index + 1}", f"{10 + index}%"),
                observation(f"完成率{index + 1}", f"{11 + index}%"),
                difficulty="percentage_value",
                expected_rule_ids=["percentage_value_consistency"],
            )
        )

    for index in range(8):
        day = index + 1
        cases.append(
            pair(
                f"clear-conflict-date-{index + 1:02d}",
                "clear_conflict",
                "conflict",
                observation(f"交付日期{index + 1}", f"2026-09-{day:02d}"),
                observation(f"交付日期{index + 1}", f"2026-09-{day + 1:02d}"),
                difficulty="date_value",
                expected_rule_ids=["date_value_consistency"],
            )
        )

    for index in range(7):
        quarter = index % 4 + 1
        cases.append(
            pair(
                f"clear-conflict-growth-{index + 1:02d}",
                "clear_conflict",
                "conflict",
                observation(f"销售增长率 2026Q{quarter} 同比", "18%"),
                observation(f"业绩增长率 2026Q{quarter} 环比", "18%"),
                difficulty="growth_basis",
                expected_rule_ids=["growth_basis_consistency"],
            )
        )

    for index in range(15):
        amount = 30 + index
        cases.append(
            pair(
                f"clear-consistent-money-{index + 1:02d}",
                "clear_consistent",
                "consistent",
                observation(f"采购金额{index + 1}", f"{amount}万元"),
                observation(f"采购金额{index + 1}", f"{amount * 10000}元"),
                difficulty="money_unit_conversion",
            )
        )

    for index in range(10):
        value = 20 + index
        cases.append(
            pair(
                f"clear-consistent-percentage-{index + 1:02d}",
                "clear_consistent",
                "consistent",
                observation(f"签约率{index + 1}", f"{value}%"),
                observation(f"签约率{index + 1}", f"{value}％"),
                difficulty="percentage_full_width_symbol",
            )
        )

    for index in range(8):
        day = index + 10
        cases.append(
            pair(
                f"clear-consistent-date-{index + 1:02d}",
                "clear_consistent",
                "consistent",
                observation(f"版本日期{index + 1}", f"2026/09/{day}"),
                observation(f"版本日期{index + 1}", f"2026年9月{day}日"),
                difficulty="date_notation",
            )
        )

    for index in range(7):
        quarter = index % 4 + 1
        cases.append(
            pair(
                f"clear-consistent-growth-{index + 1:02d}",
                "clear_consistent",
                "consistent",
                observation(f"销售增长率 2026Q{quarter} 同比", "18%"),
                observation(f"业绩增长率 2026Q{quarter} 同比", "18％"),
                difficulty="growth_alias",
            )
        )

    hard_cases = [
        pair(
            "hard-01",
            "hard",
            "conflict",
            observation("项目总预算 2026", "1260万元"),
            observation("预算金额 2026", "126万元"),
            difficulty="alias_and_unit",
            expected_rule_ids=["money_value_consistency"],
        ),
        pair(
            "hard-02",
            "hard",
            "conflict",
            observation("Budget 2026", "1亿元"),
            observation("ProjectBudget 2026", "9000万元"),
            difficulty="english_alias",
            expected_rule_ids=["money_value_consistency"],
        ),
        pair(
            "hard-03",
            "hard",
            "conflict",
            observation("验收通过率 2026Q1", "18.00%"),
            observation("验收通过率 2026Q1", "18.01％"),
            difficulty="small_percentage_delta",
            expected_rule_ids=["percentage_value_consistency"],
        ),
        pair(
            "hard-04",
            "hard",
            "conflict",
            observation("最终交付日", "2026.09.30"),
            observation("最终交付日", "2026年10月1日"),
            difficulty="date_boundary",
            expected_rule_ids=["date_value_consistency"],
        ),
        pair(
            "hard-05",
            "hard",
            "conflict",
            observation("销售增长率 2026Q4 同比", "0.18", number_format="0%", value_type="number"),
            observation("业绩增长率 2026Q4 环比", "18%"),
            difficulty="growth_basis_cross_representation",
            expected_rule_ids=["growth_basis_consistency"],
        ),
        pair(
            "hard-06",
            "hard",
            "conflict",
            observation("合同额 2027", "12,600万元"),
            observation("合同额 2027", "125000000元"),
            difficulty="thousands_separator",
            expected_rule_ids=["money_value_consistency"],
        ),
        pair(
            "hard-07",
            "hard",
            "conflict",
            observation("回款率 2027", "8％"),
            observation("回款率 2027", "0.081", number_format="0.0%", value_type="number"),
            difficulty="numeric_percentage",
            expected_rule_ids=["percentage_value_consistency"],
        ),
        pair(
            "hard-08",
            "hard",
            "conflict",
            observation("项目实施费用 2026", "500万元"),
            observation("项目实施费用 2026", "5500000元"),
            difficulty="money_cross_scale",
            expected_rule_ids=["money_value_consistency"],
        ),
        pair(
            "hard-09",
            "hard",
            "conflict",
            observation("计划截止日", "2026/12/31"),
            observation("计划截止日", "2027-01-01"),
            difficulty="year_boundary",
            expected_rule_ids=["date_value_consistency"],
        ),
        pair(
            "hard-10",
            "hard",
            "conflict",
            observation("业绩增长率 2027Q1 同比", "5%"),
            observation("销售增长率 2027Q1 环比", "6%"),
            difficulty="growth_basis_and_value",
            expected_rule_ids=["growth_basis_consistency", "percentage_value_consistency"],
        ),
        pair(
            "hard-11",
            "hard",
            "consistent",
            observation("项目总预算 2026", "1亿元"),
            observation("预算金额 2026", "10000万元"),
            difficulty="alias_and_large_unit_conversion",
        ),
        pair(
            "hard-12",
            "hard",
            "consistent",
            observation("合同金额 2026", "126,000,000元"),
            observation("合同金额 2026", "12600万元"),
            difficulty="separator_and_unit_conversion",
        ),
        pair(
            "hard-13",
            "hard",
            "consistent",
            observation("完成率 2026", "18%"),
            observation("完成率 2026", "0.18", number_format="0%", value_type="number"),
            difficulty="text_and_numeric_percentage",
        ),
        pair(
            "hard-14",
            "hard",
            "consistent",
            observation("上线日期", "2026.9.1"),
            observation("上线日期", "2026年09月01日"),
            difficulty="date_zero_padding",
        ),
        pair(
            "hard-15",
            "hard",
            "consistent",
            observation("销售增长率 2026Q2 同比", "18％"),
            observation("业绩增长率 2026-Q2 同比", "0.18", number_format="0.0%", value_type="number"),
            difficulty="growth_alias_cross_representation",
        ),
        pair(
            "hard-16",
            "hard",
            "consistent",
            observation("采购金额 2026", "1.20万元"),
            observation("采购金额 2026", "12000元"),
            difficulty="decimal_scale_equivalence",
        ),
        pair(
            "hard-17",
            "hard",
            "consistent",
            observation("验收率 2026", "18.0%"),
            observation("验收率 2026", "18%"),
            difficulty="percentage_decimal_scale",
        ),
        pair(
            "hard-18",
            "hard",
            "consistent",
            observation("Budget 2027", "8000万元"),
            observation("ProjectBudget 2027", "80000000元"),
            difficulty="english_alias_unit_conversion",
        ),
        pair(
            "hard-19",
            "hard",
            "consistent",
            observation("版本日 2026", "2026/08/24"),
            observation("版本日 2026", "2026-08-24"),
            difficulty="date_separator",
        ),
        pair(
            "hard-20",
            "hard",
            "consistent",
            observation("销售增长率 2027Q3 环比", "6%"),
            observation("业绩增长率 2027Q3 环比", "6％"),
            difficulty="growth_alias_full_width_symbol",
        ),
    ]
    cases.extend(hard_cases)

    assert len(cases) == 100
    assert sum(case["category"] == "clear_conflict" for case in cases) == 40
    assert sum(case["category"] == "clear_consistent" for case in cases) == 40
    assert sum(case["category"] == "hard" for case in cases) == 20
    return cases


def main() -> None:
    content = "\n".join(json.dumps(case, ensure_ascii=False, separators=(",", ":")) for case in build_cases())
    OUTPUT.write_text(content + "\n", encoding="utf-8")
    print(f"已生成 {len(build_cases())} 条评测数据：{OUTPUT}")


if __name__ == "__main__":
    main()
