from __future__ import annotations

import json
from pathlib import Path

from proofmesh.service import DocumentAuditService
from scripts.create_demo_bundle import main as create_demo_bundle


def test_demo_bundle_audits_all_supported_formats(monkeypatch, tmp_path: Path) -> None:
    from scripts import create_demo_bundle as demo

    bundle = tmp_path / "demo_bundle"
    monkeypatch.setattr(demo, "DEMO", bundle)
    create_demo_bundle()

    project_root = Path(__file__).resolve().parents[1]
    service = DocumentAuditService(project_root, tmp_path / "proofmesh_home")
    result = service.audit(str(bundle))

    run_dir = Path(result["run_dir"])
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    manifest = json.loads((run_dir / "input_manifest.json").read_text(encoding="utf-8"))
    style_findings = json.loads((run_dir / "style_findings.json").read_text(encoding="utf-8"))

    assert run["format_counts"] == {"docx": 1, "pdf": 1, "pptx": 1, "xlsx": 2}
    assert run["unsupported_count"] == 0
    assert run["issue_count"] == 2
    assert run["review_candidate_count"] == 1
    assert run["model"]["available"] is True
    assert run["model"]["device"] == "CPU"
    assert set(manifest["before"]) == {
        "ground_truth.json",
        "contract-summary.pdf",
        "方案.docx",
        "管理层汇报.pptx",
        "管理层汇报数据.xlsx",
        "预算.xlsx",
    }
    assert manifest["before"] == manifest["after"]
    assert style_findings == []

    report = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "相差 10 倍" in report
    assert "项目实施费用 ↔ 项目执行费用" in report
    assert "不是已经确认的冲突" in report
    assert "ProofMesh 没有修改源文件" in report
    assert "document_hash=" in report
