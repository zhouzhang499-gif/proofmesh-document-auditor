from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook

from proofmesh.service import DocumentAuditService


def _write(path: Path, sheet_name: str, label: str, value: str, growth_label: str) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(["指标", "数值"])
    sheet.append([label, value])
    sheet.append([growth_label, "18%"])
    workbook.save(path)


def test_audit_finds_money_and_growth_conflicts_without_changing_inputs(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    _write(bundle / "预算.xlsx", "预算表", "项目总预算", "1260万元", "2026Q1同比增长率")
    _write(bundle / "汇报.xlsx", "汇报数据", "预算金额", "126万元", "2026Q1环比增长率")
    project_root = Path(__file__).resolve().parents[1]
    service = DocumentAuditService(project_root, tmp_path / "home")

    result = service.audit(str(bundle))

    run_dir = Path(result["run_dir"])
    issues = json.loads((run_dir / "issues.json").read_text(encoding="utf-8"))
    rule_ids = {item["rule_id"] for item in issues}
    assert "money_value_consistency" in rule_ids
    assert "growth_basis_consistency" in rule_ids
    report = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "1260万元" in report
    assert "126万元" in report
    assert "预算表!B2" in report
    assert "汇报数据!B2" in report
    assert json.loads((run_dir / "style_findings.json").read_text(encoding="utf-8")) == []
    manifest = json.loads((run_dir / "input_manifest.json").read_text(encoding="utf-8"))
    assert manifest["before"] == manifest["after"]

