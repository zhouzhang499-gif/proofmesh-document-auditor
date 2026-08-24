from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "run_evaluation.py"
SPEC = importlib.util.spec_from_file_location("run_evaluation", MODULE_PATH)
assert SPEC and SPEC.loader
RUN_EVALUATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN_EVALUATION)


def test_evaluation_dataset_has_required_distribution() -> None:
    cases = RUN_EVALUATION.load_cases(ROOT / "evaluation" / "fact_pairs.jsonl")

    assert len(cases) == 100
    assert sum(case["category"] == "clear_conflict" for case in cases) == 40
    assert sum(case["category"] == "clear_consistent" for case in cases) == 40
    assert sum(case["category"] == "hard" for case in cases) == 20
    assert sum(case["expected"] == "conflict" for case in cases) == 50
    assert sum(case["expected"] == "consistent" for case in cases) == 50


def test_evaluation_reports_metrics_and_writes_both_formats(tmp_path: Path) -> None:
    result = RUN_EVALUATION.evaluate(
        ROOT / "evaluation" / "fact_pairs.jsonl",
        ROOT / "rules" / "default.yaml",
    )
    json_path, markdown_path = RUN_EVALUATION.write_results(result, tmp_path)

    assert result["dataset"]["case_count"] == 100
    assert result["metrics"]["precision"] == 1.0
    assert result["metrics"]["recall"] == 1.0
    assert result["metrics"]["f1"] == 1.0
    assert result["metrics"]["parse_coverage"] == 1.0
    assert result["metrics"]["location_field_completeness"] == 1.0
    assert set(result["candidate_classification"]) == {"clear_conflict", "clear_consistent", "hard"}
    assert result["candidate_classification"]["clear_conflict"]["accuracy"] == 1.0
    assert result["candidate_classification"]["clear_consistent"]["accuracy"] == 1.0
    assert result["candidate_classification"]["hard"]["total"] == 20
    assert result["candidate_classification"]["hard"]["accuracy"] == 1.0
    assert result["errors"] == []

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    report = markdown_path.read_text(encoding="utf-8")
    assert payload["metrics"] == result["metrics"]
    assert "## 核心指标" in report
    assert "## 候选分类统计" in report
    assert "定位字段完整率" in report


def test_dataset_generation_is_reproducible(tmp_path: Path) -> None:
    dataset_module_path = ROOT / "evaluation" / "build_dataset.py"
    spec = importlib.util.spec_from_file_location("build_dataset", dataset_module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    generated = "\n".join(
        json.dumps(case, ensure_ascii=False, separators=(",", ":")) for case in module.build_cases()
    ) + "\n"
    checked_in = (ROOT / "evaluation" / "fact_pairs.jsonl").read_text(encoding="utf-8")
    assert generated == checked_in
