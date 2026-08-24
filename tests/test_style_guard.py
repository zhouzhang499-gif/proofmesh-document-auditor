from pathlib import Path

from proofmesh.style_guard import audit_text


def test_style_guard_finds_template_phrase() -> None:
    findings = audit_text("综上所述，这份材料没有问题。")
    assert findings
    assert findings[0].code == "banned_phrase"


def test_readme_passes_style_guard() -> None:
    readme = Path(__file__).resolve().parents[1] / "README.md"
    findings = audit_text(readme.read_text(encoding="utf-8"))
    assert findings == []

