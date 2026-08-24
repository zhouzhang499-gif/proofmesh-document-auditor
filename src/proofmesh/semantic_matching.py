from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

from .contracts import FactObservation


class OpenVinoSemanticMatcher:
    def __init__(self, model_dir: Path, device: str = "CPU") -> None:
        self.model_dir = model_dir
        self.device = device
        self._pipeline: Any | None = None
        self._cache: dict[str, list[float]] = {}
        self._load_error = ""
        self._load_attempted = False
        self._manifest: dict[str, Any] = {}

    def ensure_loaded(self) -> bool:
        if self._pipeline is not None:
            return True
        if self._load_attempted:
            return False
        self._load_attempted = True
        try:
            self._verify_manifest()
            import openvino as ov
            import openvino_genai as ov_genai

            config = ov_genai.TextEmbeddingPipeline.Config(
                max_length=512,
                pooling_type=ov_genai.TextEmbeddingPipeline.PoolingType.CLS,
                normalize=True,
            )
            self._pipeline = ov_genai.TextEmbeddingPipeline(self.model_dir, self.device, config)
            self._runtime_version = ov.get_version()
            self._load_error = ""
            return True
        except Exception as exc:
            self._load_error = str(exc)
            return False

    def score(self, left: str, right: str) -> float | None:
        if not self.ensure_loaded():
            return None
        left_vector = self._embedding(left)
        right_vector = self._embedding(right)
        numerator = sum(a * b for a, b in zip(left_vector, right_vector, strict=True))
        denominator = math.sqrt(sum(a * a for a in left_vector)) * math.sqrt(sum(b * b for b in right_vector))
        return numerator / denominator if denominator else 0.0

    def info(self) -> dict[str, Any]:
        available = self.ensure_loaded()
        manifest_path = self.model_dir / "model-manifest.json"
        manifest = self._manifest
        return {
            "available": available,
            "device": self.device if available else None,
            "runtime_version": getattr(self, "_runtime_version", None),
            "model": manifest.get("model", {}).get("name"),
            "model_revision": manifest.get("model", {}).get("upstream_revision"),
            "manifest_sha256": _sha256_file(manifest_path) if manifest_path.exists() else None,
            "error": self._load_error or None,
        }

    def _embedding(self, text: str) -> list[float]:
        if text not in self._cache:
            self._cache[text] = list(self._pipeline.embed_query(text))
        return self._cache[text]

    def _verify_manifest(self) -> None:
        manifest_path = self.model_dir / "model-manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"模型清单不存在：{manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self._manifest = manifest
        for item in manifest.get("files", []):
            path = self.model_dir / item["name"]
            if not path.exists():
                raise FileNotFoundError(f"模型文件不存在：{path.name}")
            if path.stat().st_size != item["size"] or _sha256_file(path) != item["sha256"]:
                raise RuntimeError(f"模型文件校验失败：{path.name}")


def build_review_candidates(
    observations: list[FactObservation],
    matcher: OpenVinoSemanticMatcher,
    *,
    fuzzy_threshold: float = 45.0,
    semantic_threshold: float = 0.80,
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], dict[str, list[FactObservation]]] = defaultdict(lambda: defaultdict(list))
    for item in observations:
        groups[(item.fact_type, item.period)][item.canonical_label].append(item)

    candidates: list[dict[str, Any]] = []
    for (fact_type, period), label_groups in groups.items():
        labels = sorted(label_groups)
        for index, left in enumerate(labels):
            for right in labels[index + 1 :]:
                left_items = label_groups[left]
                right_items = label_groups[right]
                if not _crosses_documents(left_items, right_items):
                    continue
                fuzzy_score = float(fuzz.WRatio(left, right))
                if fuzzy_score < fuzzy_threshold:
                    continue
                semantic_score = matcher.score(left, right)
                if semantic_score is None or semantic_score < semantic_threshold:
                    continue
                evidence = sorted(
                    {
                        (item.relative_path, item.locator, item.document_hash)
                        for item in [*left_items, *right_items]
                    }
                )
                raw_id = f"{fact_type}|{period}|{left}|{right}|{evidence}".encode("utf-8")
                candidates.append(
                    {
                        "candidate_id": hashlib.sha256(raw_id).hexdigest()[:20],
                        "status": "needs_review",
                        "fact_type": fact_type,
                        "period": period,
                        "left_label": left,
                        "right_label": right,
                        "rapidfuzz_score": round(fuzzy_score, 3),
                        "openvino_cosine_score": round(semantic_score, 6),
                        "evidence": [
                            {"relative_path": path, "locator": locator, "document_hash": document_hash}
                            for path, locator, document_hash in evidence
                        ],
                    }
                )
    return sorted(candidates, key=lambda item: (-item["openvino_cosine_score"], item["candidate_id"]))


def _crosses_documents(left: list[FactObservation], right: list[FactObservation]) -> bool:
    return any(left_item.relative_path != right_item.relative_path for left_item in left for right_item in right)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
