from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from proofmesh.normalization import parse_fact  # noqa: E402
from proofmesh.rule_engine import find_issues  # noqa: E402


LOCATION_FIELDS = ("relative_path", "locator", "evidence_id", "document_hash")


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        case = json.loads(line)
        if not isinstance(case, dict):
            raise ValueError(f"第 {line_number} 行不是 JSON 对象")
        cases.append(case)
    return cases


def evaluate(dataset_path: Path, rules_path: Path) -> dict[str, Any]:
    cases = load_cases(dataset_path)
    rules = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
    totals = Counter()
    category_stats: dict[str, Counter[str]] = defaultdict(Counter)
    difficulty_stats: dict[str, Counter[str]] = defaultdict(Counter)
    case_results: list[dict[str, Any]] = []
    location_total = 0
    location_complete = 0
    parsed_observations = 0
    expected_observations = len(cases) * 2

    for case in cases:
        observations = []
        for side in ("left", "right"):
            source = case[side]
            relative_path = f"{case['id']}/{side}.json"
            locator = f"$.{side}.value"
            document_hash = hashlib.sha256(f"{case['id']}:{side}".encode("utf-8")).hexdigest()
            evidence_id = hashlib.sha256(f"evidence:{case['id']}:{side}".encode("utf-8")).hexdigest()[:20]
            value = _coerce_value(source)
            item = parse_fact(
                value=value,
                label=source["label"],
                number_format=source.get("number_format", "General"),
                document_hash=document_hash,
                relative_path=relative_path,
                locator=locator,
                evidence_id=evidence_id,
                aliases=rules["aliases"],
                money_labels=rules["money_labels"],
                date_labels=rules["date_labels"],
            )
            if item is not None:
                observations.append(item)
                parsed_observations += 1
                for field in LOCATION_FIELDS:
                    location_total += 1
                    if getattr(item, field, ""):
                        location_complete += 1

        issues = find_issues(observations)
        predicted = "conflict" if issues else "consistent"
        expected = case["expected"]
        expected_positive = expected == "conflict"
        predicted_positive = predicted == "conflict"
        if expected_positive and predicted_positive:
            totals["true_positive"] += 1
        elif not expected_positive and predicted_positive:
            totals["false_positive"] += 1
        elif expected_positive and not predicted_positive:
            totals["false_negative"] += 1
        else:
            totals["true_negative"] += 1

        category = case["category"]
        difficulty = case["difficulty"]
        category_stats[category][f"expected_{expected}"] += 1
        category_stats[category][f"predicted_{predicted}"] += 1
        difficulty_stats[difficulty]["total"] += 1
        if predicted == expected:
            category_stats[category]["correct"] += 1
            difficulty_stats[difficulty]["correct"] += 1

        actual_rule_ids = sorted({issue.rule_id for issue in issues})
        expected_rule_ids = sorted(case.get("expected_rule_ids", []))
        rule_ids_match = actual_rule_ids == expected_rule_ids
        if rule_ids_match:
            totals["rule_ids_exact_match"] += 1
        case_results.append(
            {
                "id": case["id"],
                "category": category,
                "difficulty": difficulty,
                "expected": expected,
                "predicted": predicted,
                "correct": predicted == expected,
                "expected_rule_ids": expected_rule_ids,
                "actual_rule_ids": actual_rule_ids,
                "rule_ids_exact_match": rule_ids_match,
                "parsed_observation_count": len(observations),
            }
        )

    precision = _safe_divide(totals["true_positive"], totals["true_positive"] + totals["false_positive"])
    recall = _safe_divide(totals["true_positive"], totals["true_positive"] + totals["false_negative"])
    f1 = _safe_divide(2 * precision * recall, precision + recall)
    total_cases = len(cases)
    correct = totals["true_positive"] + totals["true_negative"]

    return {
        "schema_version": 1,
        "dataset": {
            "path": _display_path(dataset_path),
            "sha256": _sha256_file(dataset_path),
            "case_count": total_cases,
            "category_counts": dict(Counter(case["category"] for case in cases)),
        },
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": _safe_divide(correct, total_cases),
            "true_positive": totals["true_positive"],
            "false_positive": totals["false_positive"],
            "false_negative": totals["false_negative"],
            "true_negative": totals["true_negative"],
            "parse_coverage": _safe_divide(parsed_observations, expected_observations),
            "location_field_completeness": _safe_divide(location_complete, location_total),
            "rule_ids_exact_match_rate": _safe_divide(totals["rule_ids_exact_match"], total_cases),
        },
        "candidate_classification": {
            category: _stats_dict(stats) for category, stats in sorted(category_stats.items())
        },
        "difficulty_classification": {
            difficulty: {
                "total": stats["total"],
                "correct": stats["correct"],
                "accuracy": _safe_divide(stats["correct"], stats["total"]),
            }
            for difficulty, stats in sorted(difficulty_stats.items())
        },
        "location_fields": {
            "required": list(LOCATION_FIELDS),
            "complete": location_complete,
            "total": location_total,
        },
        "errors": [result for result in case_results if not result["correct"] or not result["rule_ids_exact_match"]],
        "cases": case_results,
    }


def render_markdown(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    lines = [
        "# ProofMesh 量化评测报告",
        "",
        f"- 数据集：`{result['dataset']['path']}`",
        f"- SHA256：`{result['dataset']['sha256']}`",
        f"- 事实对：{result['dataset']['case_count']}",
        "",
        "## 核心指标",
        "",
        "| 指标 | 结果 |",
        "| --- | ---: |",
        f"| Precision | {_percent(metrics['precision'])} |",
        f"| Recall | {_percent(metrics['recall'])} |",
        f"| F1 | {_percent(metrics['f1'])} |",
        f"| Accuracy | {_percent(metrics['accuracy'])} |",
        f"| 事实解析覆盖率 | {_percent(metrics['parse_coverage'])} |",
        f"| 定位字段完整率 | {_percent(metrics['location_field_completeness'])} |",
        f"| 规则 ID 完全匹配率 | {_percent(metrics['rule_ids_exact_match_rate'])} |",
        "",
        "## 混淆矩阵",
        "",
        "| TP | FP | FN | TN |",
        "| ---: | ---: | ---: | ---: |",
        f"| {metrics['true_positive']} | {metrics['false_positive']} | {metrics['false_negative']} | {metrics['true_negative']} |",
        "",
        "## 候选分类统计",
        "",
        "| 类别 | 数量 | 期望冲突 | 期望一致 | 预测冲突 | 预测一致 | 正确率 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for category, stats in result["candidate_classification"].items():
        lines.append(
            f"| {category} | {stats['total']} | {stats['expected_conflict']} | {stats['expected_consistent']} "
            f"| {stats['predicted_conflict']} | {stats['predicted_consistent']} | {_percent(stats['accuracy'])} |"
        )

    lines.extend(["", "## 未完全命中的样例", ""])
    if result["errors"]:
        lines.extend(
            [
                "| ID | 难点 | 期望 | 预测 | 期望规则 | 实际规则 |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for item in result["errors"]:
            lines.append(
                f"| {item['id']} | {item['difficulty']} | {item['expected']} | {item['predicted']} "
                f"| {', '.join(item['expected_rule_ids']) or '-'} | {', '.join(item['actual_rule_ids']) or '-'} |"
            )
    else:
        lines.append("无。")
    lines.append("")
    return "\n".join(lines)


def write_results(result: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "evaluation.json"
    markdown_path = output_dir / "evaluation.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(result), encoding="utf-8")
    return json_path, markdown_path


def _coerce_value(source: dict[str, Any]) -> Any:
    value_type = source.get("value_type", "text")
    value = source["value"]
    if value_type == "number":
        return float(value)
    if value_type == "date":
        return date.fromisoformat(value)
    return value


def _stats_dict(stats: Counter[str]) -> dict[str, Any]:
    total = stats["expected_conflict"] + stats["expected_consistent"]
    return {
        "total": total,
        "expected_conflict": stats["expected_conflict"],
        "expected_consistent": stats["expected_consistent"],
        "predicted_conflict": stats["predicted_conflict"],
        "predicted_consistent": stats["predicted_consistent"],
        "correct": stats["correct"],
        "accuracy": _safe_divide(stats["correct"], total),
    }


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 ProofMesh 的轻量事实对评测")
    parser.add_argument("--dataset", type=Path, default=ROOT / "evaluation" / "fact_pairs.jsonl")
    parser.add_argument("--rules", type=Path, default=ROOT / "rules" / "default.yaml")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "evaluation" / "results")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = evaluate(args.dataset, args.rules)
    json_path, markdown_path = write_results(result, args.output_dir)
    metrics = result["metrics"]
    print(f"评测完成：{result['dataset']['case_count']} 条事实对")
    print(f"Precision={metrics['precision']:.4f} Recall={metrics['recall']:.4f} F1={metrics['f1']:.4f}")
    print(f"JSON：{json_path}")
    print(f"Markdown：{markdown_path}")


if __name__ == "__main__":
    main()
