from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .contracts import Issue
from .style_guard import assert_preserved_fields, audit_text


def render_markdown(
    *,
    run_id: str,
    file_count: int,
    total_file_count: int,
    issues: list[Issue],
    unsupported: list[str],
    review_candidates: list[dict[str, Any]],
    incomplete_files: list[dict[str, str]],
    pipeline_warnings: list[str],
) -> str:
    lines = ["# ProofMesh 检查报告", ""]
    if issues:
        lines.append(f"本次完整检查了 {file_count}/{total_file_count} 个文件，找到 {len(issues)} 个需要确认的问题。ProofMesh 没有修改源文件。")
    else:
        lines.append(f"本次完整检查了 {file_count}/{total_file_count} 个文件，没有发现当前规则能够确认的冲突。这个结果不代表所有内容都正确。")
    if unsupported:
        lines.append(f"另有 {len(unsupported)} 个文件尚未处理，文件名列在技术附录。")
    if incomplete_files or pipeline_warnings:
        lines.append("部分检查没有完成，具体原因列在下方。")
    lines.extend(["", "## 需要确认的地方", ""])

    if not issues:
        lines.extend(["当前没有可列出的问题。", ""])

    for index, issue in enumerate(issues, start=1):
        lines.extend([f"### {index}. {issue.title}", "", issue.explanation, ""])
        for observation in issue.observations:
            lines.append(f"- {observation.relative_path} 的 {observation.locator} 写的是 {observation.raw_value}。")
        lines.extend(["", issue.action, ""])

    if review_candidates:
        lines.extend(["## 可能指向同一指标的写法", ""])
        lines.append("下面的名称相似，但它们不是已经确认的冲突。请先确认这些写法是否确实指向同一指标。")
        lines.append("")
        for item in review_candidates:
            lines.append(
                f"- {item['left_label']} ↔ {item['right_label']}："
                f"字面分数 {item['rapidfuzz_score']:.1f}，本地语义分数 {item['openvino_cosine_score']:.3f}。"
            )
            for evidence in item["evidence"]:
                lines.append(f"  - {evidence['relative_path']} 的 {evidence['locator']}")
        lines.append("")

    if incomplete_files or pipeline_warnings:
        lines.extend(["## 没有完成的检查", ""])
        for item in incomplete_files:
            lines.append(f"- {item['relative_path']}：{item['message']}")
        for warning in pipeline_warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.extend(["## 技术附录", "", f"运行编号：`{run_id}`", ""])
    if unsupported:
        lines.extend(["尚未处理的文件：", ""])
        lines.extend(f"- `{name}`" for name in unsupported)
        lines.append("")
    for issue in issues:
        lines.append(f"- `{issue.rule_id}` / `{issue.issue_id}`")
        for observation in issue.observations:
            lines.append(
                "  - "
                f"raw_value=`{observation.raw_value}`; "
                f"normalized_value=`{observation.normalized_value}`; "
                f"relative_path=`{observation.relative_path}`; "
                f"locator=`{observation.locator}`; "
                f"document_hash=`{observation.document_hash}`; "
                f"rule_id=`{issue.rule_id}`"
            )
    text = "\n".join(lines).rstrip() + "\n"

    locked = [observation.to_dict() for issue in issues for observation in issue.observations]
    assert_preserved_fields(locked, text)
    return text


def render_html(
    markdown_text: str,
    issues: list[Issue],
    review_candidates: list[dict[str, Any]],
    incomplete_files: list[dict[str, str]],
    pipeline_warnings: list[str],
) -> str:
    cards: list[str] = []
    for issue in issues:
        evidence = "".join(
            f"<li><code>{html.escape(item.relative_path)}</code> 的 <code>{html.escape(item.locator)}</code> 写的是 <strong>{html.escape(item.raw_value)}</strong>。</li>"
            for item in issue.observations
        )
        cards.append(
            "<article class='issue'>"
            f"<h2>{html.escape(issue.title)}</h2>"
            f"<p>{html.escape(issue.explanation)}</p><ul>{evidence}</ul>"
            f"<p>{html.escape(issue.action)}</p>"
            f"<small>{html.escape(issue.rule_id)} · {html.escape(issue.issue_id)}</small>"
            "</article>"
        )
    candidate_cards = ""
    for item in review_candidates:
        candidate_evidence = "".join(
            f"<li><code>{html.escape(evidence['relative_path'])}</code> 的 <code>{html.escape(evidence['locator'])}</code></li>"
            for evidence in item["evidence"]
        )
        candidate_cards += (
            "<article class='issue'>"
            f"<h2>{html.escape(item['left_label'])} ↔ {html.escape(item['right_label'])}</h2>"
            f"<p>这是一条待确认候选，不是已经确认的冲突。字面分数 {item['rapidfuzz_score']:.1f}，"
            f"本地语义分数 {item['openvino_cosine_score']:.3f}。</p><ul>{candidate_evidence}</ul></article>"
        )
    warning_items = [f"{item['relative_path']}：{item['message']}" for item in incomplete_files] + pipeline_warnings
    warning_card = ""
    if warning_items:
        warning_list = "".join(f"<li>{html.escape(item)}</li>" for item in warning_items)
        warning_card = f"<article class='issue'><h2>没有完成的检查</h2><ul>{warning_list}</ul></article>"
    body = "".join(cards) + candidate_cards + warning_card or "<p>当前没有可列出的问题。</p>"
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ProofMesh 检查报告</title><style>
body{{font-family:"Segoe UI","Microsoft YaHei",sans-serif;max-width:920px;margin:40px auto;padding:0 24px;color:#20242a;line-height:1.7;background:#f6f7f9}}
header,.issue{{background:#fff;border:1px solid #dfe3e8;border-radius:12px;padding:22px 26px;margin:16px 0}}h1,h2{{line-height:1.3}}code{{background:#eef1f4;padding:2px 5px;border-radius:4px}}small{{color:#667085}}
</style></head><body><header><h1>ProofMesh 检查报告</h1><p>{html.escape(markdown_text.splitlines()[2])}</p></header>{body}</body></html>"""


def build_agent_summary(
    run_id: str,
    status: str,
    issues: list[Issue],
    review_candidates: list[dict[str, Any]],
    incomplete_files: list[dict[str, str]],
    pipeline_warnings: list[str],
    report_path: Path,
) -> dict[str, Any]:
    top = [
        {
            "issue_id": issue.issue_id,
            "severity": issue.severity,
            "title": issue.title,
            "evidence_count": len(issue.observations),
        }
        for issue in issues[:5]
    ]
    if status == "partial":
        message = f"检查只完成了一部分，已发现 {len(issues)} 个需要确认的问题。未完成项和证据保存在本地报告中。"
    else:
        message = f"检查完成，发现 {len(issues)} 个需要确认的问题。完整证据保存在本地报告中。"
    return {
        "run_id": run_id,
        "status": status,
        "issue_count": len(issues),
        "review_candidate_count": len(review_candidates),
        "incomplete_check_count": len(incomplete_files) + len(pipeline_warnings),
        "message": message,
        "top_issues": top,
        "local_report": str(report_path),
    }


def style_findings_for(text: str) -> list[dict[str, Any]]:
    return [finding.to_dict() for finding in audit_text(text)]
