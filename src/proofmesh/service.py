from __future__ import annotations

import json
import os
import stat
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .reporting import build_agent_summary, render_html, render_markdown, style_findings_for
from .rule_engine import find_issues
from .run_store import RunStore
from .semantic_matching import OpenVinoSemanticMatcher, build_review_candidates
from .docx_parser import parse_docx
from .pdf_parser import parse_pdf
from .pptx_parser import parse_pptx
from .xlsx_parser import parse_xlsx, sha256_file


class DocumentAuditService:
    def __init__(self, project_root: Path, home: Path | None = None):
        self.project_root = project_root.resolve()
        self.home = (home or default_home()).resolve()
        self.store = RunStore(self.home)
        self.rules_path = self.project_root / "rules" / "default.yaml"
        self.semantic_matcher = OpenVinoSemanticMatcher(_model_dir(self.project_root, self.home))

    def audit(self, input_path: str) -> dict[str, Any]:
        root = self._safe_input_root(Path(input_path))
        if self.home.is_relative_to(root):
            raise ValueError("PROOFMESH_HOME 不能放在待检查目录里面。")
        files = self._collect_input_files(root)
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        run_dir = self.store.create_run(run_id)
        started_at = datetime.now(UTC).isoformat()
        manifest_before = {path.relative_to(root).as_posix(): sha256_file(path) for path in files}
        document_files = [path for path in files if path.suffix.lower() in {".xlsx", ".docx", ".pptx", ".pdf"} and not path.name.startswith("~$")]
        parsers = {
            ".xlsx": parse_xlsx,
            ".docx": parse_docx,
            ".pptx": parse_pptx,
            ".pdf": parse_pdf,
        }
        supported_files = [path for path in document_files if path.suffix.lower() in parsers]
        unsupported: list[str] = []

        evidence = []
        observations = []
        errors: list[dict[str, str]] = []
        file_results: list[dict[str, str]] = []
        format_counts: dict[str, int] = {}
        for path in supported_files:
            relative_path = path.relative_to(root).as_posix()
            try:
                suffix = path.suffix.lower()
                file_evidence, file_observations = parsers[suffix](path, root, self.rules_path)
                evidence.extend(file_evidence)
                observations.extend(file_observations)
                formula_warnings = [item for item in file_evidence if item.extractor == "openpyxl-formula-missing-cache"]
                if suffix == ".pdf" and not file_evidence:
                    file_results.append({"relative_path": relative_path, "status": "needs_ocr", "message": "没有读到文本层，需要 OCR。"})
                elif formula_warnings:
                    file_results.append(
                        {
                            "relative_path": relative_path,
                            "status": "parsed_with_warnings",
                            "message": f"有 {len(formula_warnings)} 个公式没有缓存结果，相关数值未参与核对。",
                        }
                    )
                    format_counts[suffix.lstrip(".")] = format_counts.get(suffix.lstrip("."), 0) + 1
                else:
                    file_results.append({"relative_path": relative_path, "status": "parsed", "message": ""})
                    format_counts[suffix.lstrip(".")] = format_counts.get(suffix.lstrip("."), 0) + 1
            except Exception as exc:
                errors.append({"file": relative_path, "error": str(exc)})
                file_results.append({"relative_path": relative_path, "status": "error", "message": str(exc)})

        referenced_evidence = {item.evidence_id for item in observations}
        evidence = [
            item
            for item in evidence
            if item.evidence_id in referenced_evidence or item.extractor == "openpyxl-formula-missing-cache"
        ]
        issues = find_issues(observations)
        model_info = self.semantic_matcher.info()
        review_candidates = build_review_candidates(observations, self.semantic_matcher) if model_info["available"] else []
        incomplete_files = [item for item in file_results if item["status"] in {"needs_ocr", "parsed_with_warnings", "error"}]
        pipeline_warnings = []
        if not model_info["available"]:
            pipeline_warnings.append("OpenVINO 语义模型没有加载成功，近似指标候选未执行。")
        run_status = "partial" if incomplete_files or pipeline_warnings else "complete"
        checked_file_count = sum(item["status"] in {"parsed", "parsed_with_warnings"} for item in file_results)
        manifest_after = {path.relative_to(root).as_posix(): sha256_file(path) for path in files}
        if manifest_before != manifest_after:
            raise RuntimeError("输入文件在审计期间发生了变化，本次结果已停止生成。")

        markdown = render_markdown(
            run_id=run_id,
            file_count=checked_file_count,
            total_file_count=len(document_files),
            issues=issues,
            unsupported=unsupported,
            review_candidates=review_candidates,
            incomplete_files=incomplete_files,
            pipeline_warnings=pipeline_warnings,
        )
        style_findings = style_findings_for(markdown)
        if any(item["severity"] == "error" for item in style_findings):
            raise RuntimeError("报告触发了 error 级写作规则，请修正模板后重试。")
        html_report = render_html(markdown, issues, review_candidates, incomplete_files, pipeline_warnings)
        report_path = run_dir / "report.html"
        agent_summary = build_agent_summary(
            run_id,
            run_status,
            issues,
            review_candidates,
            incomplete_files,
            pipeline_warnings,
            report_path,
        )

        self.store.write_json(run_dir, "input_manifest.json", {"before": manifest_before, "after": manifest_after})
        self.store.write_text(run_dir, "evidence_atoms.jsonl", _jsonl(item.to_dict() for item in evidence))
        self.store.write_text(run_dir, "fact_observations.jsonl", _jsonl(item.to_dict() for item in observations))
        self.store.write_json(run_dir, "issues.json", [item.to_dict() for item in issues])
        self.store.write_json(run_dir, "review_candidates.json", review_candidates)
        self.store.write_json(run_dir, "model_info.json", model_info)
        self.store.write_json(run_dir, "file_results.json", file_results)
        self.store.write_json(
            run_dir,
            "matching_info.json",
            {
                "rapidfuzz_threshold": 45.0,
                "openvino_cosine_threshold": 0.80,
                "rules_sha256": sha256_file(self.rules_path),
                "model_manifest_sha256": model_info.get("manifest_sha256"),
                "model_available": model_info["available"],
            },
        )
        self.store.write_json(run_dir, "style_findings.json", style_findings)
        self.store.write_text(run_dir, "report.md", markdown)
        self.store.write_text(run_dir, "report.html", html_report)
        self.store.write_json(run_dir, "agent_summary.json", agent_summary)
        run_record = {
            "run_id": run_id,
            "status": run_status,
            "started_at": started_at,
            "finished_at": datetime.now(UTC).isoformat(),
            "input_root": str(root),
            "file_count": len(document_files),
            "checked_file_count": checked_file_count,
            "format_counts": format_counts,
            "unsupported_count": len(unsupported),
            "issue_count": len(issues),
            "review_candidate_count": len(review_candidates),
            "model": model_info,
            "errors": errors,
        }
        self.store.write_json(run_dir, "run.json", run_record)
        return {"status": run_status, "run_id": run_id, "agent_summary": agent_summary, "run_dir": str(run_dir)}

    def show(self, run_id: str) -> dict[str, Any]:
        return {
            "run": self.store.read_json(run_id, "run.json"),
            "agent_summary": self.store.read_json(run_id, "agent_summary.json"),
        }

    @staticmethod
    def _safe_input_root(path: Path) -> Path:
        raw = str(path)
        if raw.startswith("\\\\"):
            raise ValueError("首版不读取 UNC 或网络路径。")
        resolved = path.expanduser().resolve(strict=True)
        if not resolved.is_dir():
            raise ValueError("--path 必须指向一个目录。")
        return resolved

    @staticmethod
    def _collect_input_files(root: Path) -> list[Path]:
        files: list[Path] = []
        for path in root.rglob("*"):
            attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
            is_reparse = bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
            if path.is_symlink() or is_reparse:
                raise ValueError(f"待检查目录包含链接或重解析点：{path.relative_to(root).as_posix()}")
            if not path.is_file():
                continue
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(root):
                raise ValueError(f"文件越过了待检查目录：{path.relative_to(root).as_posix()}")
            files.append(path)
        return sorted(files)


def default_home() -> Path:
    override = os.environ.get("PROOFMESH_HOME")
    if override:
        return Path(override)
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".proofmesh")
    return Path(base) / "ProofMesh"


def _model_dir(project_root: Path, home: Path) -> Path:
    override = os.environ.get("PROOFMESH_MODEL_DIR")
    if override:
        return Path(override).expanduser().resolve()

    bundled = project_root / "models" / "bge-small-zh-v1.5-openvino"
    required = {
        "model-manifest.json",
        "openvino_model.xml",
        "openvino_model.bin",
        "openvino_tokenizer.xml",
        "openvino_tokenizer.bin",
    }
    if bundled.is_dir() and required.issubset({path.name for path in bundled.iterdir() if path.is_file()}):
        return bundled
    return home / "models" / "bge-small-zh-v1.5-openvino"


def _jsonl(values: Any) -> str:
    return "".join(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n" for value in values)
