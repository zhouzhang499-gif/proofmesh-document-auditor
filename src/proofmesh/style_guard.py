from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class StyleFinding:
    code: str
    severity: str
    message: str
    line: int
    column: int
    span: tuple[int, int]
    excerpt: str
    suggestion: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _default_config_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "writing_style.yaml"


def load_style_config(path: Path | None = None) -> dict[str, Any]:
    selected = path or _default_config_path()
    with selected.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def audit_text(text: str, config_path: Path | None = None) -> list[StyleFinding]:
    config = load_style_config(config_path)
    findings: list[StyleFinding] = []
    lines = text.splitlines()

    for line_number, line in enumerate(lines, start=1):
        for phrase in config.get("banned_phrases", []):
            start = line.find(phrase)
            if start >= 0:
                findings.append(
                    StyleFinding(
                        code="banned_phrase",
                        severity="error",
                        message=f"这句话包含模板化短语“{phrase}”。",
                        line=line_number,
                        column=start + 1,
                        span=(start, start + len(phrase)),
                        excerpt=line.strip(),
                        suggestion="删掉铺垫，直接写事实、判断或动作。",
                    )
                )

        for rule in config.get("banned_regex", []):
            match = re.search(rule["pattern"], line)
            if match:
                findings.append(
                    StyleFinding(
                        code=rule["code"],
                        severity="error",
                        message=rule["message"],
                        line=line_number,
                        column=match.start() + 1,
                        span=(match.start(), match.end()),
                        excerpt=line.strip(),
                        suggestion=rule["message"],
                    )
                )

    return findings


def assert_preserved_fields(before: list[dict[str, Any]], after_text: str) -> None:
    fields = load_style_config()["report_rules"]["preserve_fields"]
    missing: list[str] = []
    for item in before:
        for field_name in fields:
            value = item.get(field_name)
            if value in (None, ""):
                continue
            if str(value) not in after_text:
                missing.append(f"{field_name}={value}")
    if missing:
        raise ValueError("报告漏掉了锁定证据字段：" + ", ".join(missing[:8]))

