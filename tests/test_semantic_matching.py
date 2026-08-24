from __future__ import annotations

from pathlib import Path

from proofmesh.semantic_matching import OpenVinoSemanticMatcher


def test_bundled_openvino_model_ranks_related_budget_text_higher() -> None:
    project_root = Path(__file__).resolve().parents[1]
    matcher = OpenVinoSemanticMatcher(project_root / "models" / "bge-small-zh-v1.5-openvino")

    related = matcher.score("项目总预算", "预算金额")
    unrelated = matcher.score("项目总预算", "团队人数")

    assert related is not None
    assert unrelated is not None
    assert related > unrelated
    assert matcher.info()["available"] is True
