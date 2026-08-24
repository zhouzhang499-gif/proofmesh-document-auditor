from __future__ import annotations

import hashlib
import json
import math
import shutil
from datetime import UTC, datetime
from pathlib import Path

import openvino as ov
import openvino_genai as ov_genai
from huggingface_hub import snapshot_download
from openvino_tokenizers import convert_tokenizer
from transformers import AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / ".build" / "bge-small-zh-v1.5-onnx"
OUTPUT_DIR = ROOT / "models" / "bge-small-zh-v1.5-openvino"
MODEL_REPO = "Qdrant/bge-small-zh-v1.5"
MODEL_REVISION = "46fbe35fd4374a00fee7de77dfddaeb6dd6a2c59"
UPSTREAM_REPO = "BAAI/bge-small-zh-v1.5"
UPSTREAM_REVISION = "7999e1d3359715c523056ef9478215996d62a620"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    denominator = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return numerator / denominator if denominator else 0.0


def main() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source = Path(
        snapshot_download(
            repo_id=MODEL_REPO,
            revision=MODEL_REVISION,
            local_dir=BUILD_DIR,
            allow_patterns=[
                "model_optimized.onnx",
                "config.json",
                "tokenizer.json",
                "tokenizer_config.json",
                "special_tokens_map.json",
                "vocab.txt",
            ],
        )
    )

    model = ov.convert_model(source / "model_optimized.onnx")
    ov.save_model(model, OUTPUT_DIR / "openvino_model.xml", compress_to_fp16=True)

    tokenizer = AutoTokenizer.from_pretrained(source, local_files_only=True)
    tokenizer.model_max_length = 512
    ov_tokenizer = convert_tokenizer(tokenizer)
    ov.save_model(ov_tokenizer, OUTPUT_DIR / "openvino_tokenizer.xml")
    for name in ["config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "vocab.txt"]:
        shutil.copy2(source / name, OUTPUT_DIR / name)

    config = ov_genai.TextEmbeddingPipeline.Config(
        max_length=512,
        pooling_type=ov_genai.TextEmbeddingPipeline.PoolingType.CLS,
        normalize=True,
    )
    pipeline = ov_genai.TextEmbeddingPipeline(OUTPUT_DIR, "CPU", config)
    query = list(pipeline.embed_query("项目总预算"))
    documents = [list(item) for item in pipeline.embed_documents(["预算金额", "团队人数"])]
    scores = [cosine(query, item) for item in documents]
    if not scores[0] > scores[1]:
        raise RuntimeError(f"模型冒烟测试失败：预期预算相关文本得分更高，实际分数为 {scores}")

    files = []
    for path in sorted(OUTPUT_DIR.iterdir()):
        if path.is_file() and path.name != "model-manifest.json":
            files.append({"name": path.name, "size": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {
        "schema_version": 1,
        "built_at": datetime.now(UTC).isoformat(),
        "runtime": {
            "openvino": ov.get_version(),
            "device": "CPU",
            "pipeline": "openvino_genai.TextEmbeddingPipeline",
            "pooling": "CLS",
            "normalize": True,
        },
        "model": {
            "name": "bge-small-zh-v1.5",
            "parameters": 24_000_000,
            "license": "MIT",
            "upstream_repo": UPSTREAM_REPO,
            "upstream_revision": UPSTREAM_REVISION,
            "onnx_distribution_repo": MODEL_REPO,
            "onnx_distribution_revision": MODEL_REVISION,
        },
        "smoke_test": {
            "query": "项目总预算",
            "documents": ["预算金额", "团队人数"],
            "cosine_scores": scores,
        },
        "files": files,
    }
    (OUTPUT_DIR / "model-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": "complete", "output": str(OUTPUT_DIR), "scores": scores}, ensure_ascii=False))


if __name__ == "__main__":
    main()
