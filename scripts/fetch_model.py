from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "bge-small-zh-v1.5-openvino"
SOURCE_MODEL_DIR = ROOT / "models" / MODEL_NAME
SOURCE_MANIFEST = SOURCE_MODEL_DIR / "model-manifest.json"
SOURCE_DISTRIBUTION = ROOT / "models" / "model-distribution.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"模型清单不存在：{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_model_dir(model_dir: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    for item in manifest.get("files", []):
        path = model_dir / item["name"]
        if not path.is_file():
            errors.append(f"缺少 {item['name']}")
            continue
        if path.stat().st_size != item["size"]:
            errors.append(f"{item['name']} 大小不符")
            continue
        if sha256_file(path) != item["sha256"]:
            errors.append(f"{item['name']} SHA256 不符")
    if not manifest.get("files"):
        errors.append("模型清单没有 files 字段")
    return errors


def default_destination() -> Path:
    override = os.environ.get("PROOFMESH_MODEL_DIR")
    if override:
        return Path(override).expanduser().resolve()
    proofmesh_home = os.environ.get("PROOFMESH_HOME")
    if proofmesh_home:
        return (Path(proofmesh_home).expanduser() / "models" / MODEL_NAME).resolve()
    local_app_data = os.environ.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / ".proofmesh"
    return (base / "ProofMesh" / "models" / MODEL_NAME).resolve()


def download_with_resume(url: str, partial: Path) -> None:
    partial.parent.mkdir(parents=True, exist_ok=True)
    existing = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": "ProofMesh/0.1.0"}
    if existing:
        headers["Range"] = f"bytes={existing}-"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            append = existing > 0 and getattr(response, "status", None) == 206
            mode = "ab" if append else "wb"
            with partial.open(mode) as handle:
                shutil.copyfileobj(response, handle, length=1024 * 1024)
    except urllib.error.HTTPError as exc:
        if exc.code == 416 and partial.exists():
            return
        raise RuntimeError(f"模型下载失败，HTTP {exc.code}：{url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"模型下载失败：{exc.reason}") from exc


def safe_extract(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        for item in bundle.infolist():
            target = (destination / item.filename).resolve()
            if target != destination_root and not target.is_relative_to(destination_root):
                raise RuntimeError(f"模型包包含越界路径：{item.filename}")
        bundle.extractall(destination)
    nested = destination / MODEL_NAME
    return nested if nested.is_dir() else destination


def install_model(archive: Path, destination: Path, manifest: dict) -> str | None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="proofmesh-model-", dir=destination.parent) as temp_name:
        extracted = safe_extract(archive, Path(temp_name))
        errors = verify_model_dir(extracted, manifest)
        if errors:
            raise RuntimeError("模型包校验失败：" + "；".join(errors))
        archive_manifest = extracted / "model-manifest.json"
        if not archive_manifest.is_file():
            raise RuntimeError("模型包缺少 model-manifest.json")

        backup: Path | None = None
        if destination.exists():
            backup = destination.with_name(f"{destination.name}.invalid-{uuid.uuid4().hex[:8]}")
            destination.rename(backup)
        try:
            extracted.rename(destination)
        except Exception:
            if backup and backup.exists() and not destination.exists():
                backup.rename(destination)
            raise
        return str(backup) if backup else None


def main() -> int:
    parser = argparse.ArgumentParser(description="下载并校验 ProofMesh OpenVINO 模型")
    parser.add_argument("--url", help="模型 ZIP 地址；默认读取清单或 PROOFMESH_MODEL_URL")
    parser.add_argument("--sha256", help="模型 ZIP 的 SHA256；默认读取模型清单")
    parser.add_argument("--destination", type=Path, default=default_destination())
    parser.add_argument("--offline", action="store_true", help="只验证现有模型，不访问网络")
    args = parser.parse_args()

    manifest = load_manifest(SOURCE_MANIFEST)
    bundled_errors = verify_model_dir(SOURCE_MODEL_DIR, manifest)
    if not bundled_errors:
        print(json.dumps({"status": "bundled", "model_dir": str(SOURCE_MODEL_DIR)}, ensure_ascii=False))
        return 0

    destination = args.destination.expanduser().resolve()
    cached_errors = verify_model_dir(destination, manifest)
    if not cached_errors:
        print(json.dumps({"status": "cached", "model_dir": str(destination)}, ensure_ascii=False))
        return 0
    if args.offline:
        raise RuntimeError("本地模型不完整，离线模式不能下载：" + "；".join(cached_errors))

    distribution = (
        json.loads(SOURCE_DISTRIBUTION.read_text(encoding="utf-8"))
        if SOURCE_DISTRIBUTION.is_file()
        else manifest.get("distribution", {})
    )
    url = args.url or os.environ.get("PROOFMESH_MODEL_URL") or distribution.get("archive_url")
    expected_sha256 = args.sha256 or distribution.get("archive_sha256")
    if not url or not expected_sha256:
        raise RuntimeError("模型下载地址或归档 SHA256 尚未配置。请设置 PROOFMESH_MODEL_URL，或更新模型清单。")

    downloads = destination.parent / ".downloads"
    partial = downloads / f"{MODEL_NAME}.zip.partial"
    download_with_resume(url, partial)
    actual_sha256 = sha256_file(partial)
    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            f"模型归档 SHA256 不符：期望 {expected_sha256}，实际 {actual_sha256}。"
            "保留 .partial 文件供排查，修正后重试。"
        )
    archive = partial.with_suffix("")
    partial.replace(archive)
    backup = install_model(archive, destination, manifest)
    print(
        json.dumps(
            {
                "status": "downloaded",
                "model_dir": str(destination),
                "archive_sha256": actual_sha256,
                "previous_model": backup,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
