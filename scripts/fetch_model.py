from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
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


def download_with_resume(url: str, partial: Path, expected_bytes: int) -> None:
    if expected_bytes <= 0:
        raise RuntimeError("模型归档大小必须是正整数。")
    partial.parent.mkdir(parents=True, exist_ok=True)
    existing = partial.stat().st_size if partial.exists() else 0
    if existing > expected_bytes:
        partial.unlink()
        raise RuntimeError("现有模型下载临时文件超过声明大小，已删除。")
    if existing == expected_bytes:
        return
    headers = {"User-Agent": "ProofMesh/0.1.0"}
    if existing:
        headers["Range"] = f"bytes={existing}-"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            append = existing > 0 and getattr(response, "status", None) == 206
            mode = "ab" if append else "wb"
            received = existing if append else 0
            with partial.open(mode) as handle:
                while block := response.read(1024 * 1024):
                    received += len(block)
                    if received > expected_bytes:
                        handle.close()
                        partial.unlink(missing_ok=True)
                        raise RuntimeError("模型下载超过发布清单声明大小，已停止并删除临时文件。")
                    handle.write(block)
    except urllib.error.HTTPError as exc:
        if exc.code == 416 and partial.exists() and partial.stat().st_size == expected_bytes:
            return
        raise RuntimeError(f"模型下载失败，HTTP {exc.code}：{url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"模型下载失败：{exc.reason}") from exc
    if partial.stat().st_size != expected_bytes:
        raise RuntimeError(
            f"模型下载尚不完整：期望 {expected_bytes} bytes，实际 {partial.stat().st_size} bytes。可重试续传。"
        )


def safe_extract(archive: Path, destination: Path, expected_sizes: dict[str, int] | None = None) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()
    expected_sizes = expected_sizes or {}
    maximum_entries = len(expected_sizes) + 2 if expected_sizes else 64
    maximum_uncompressed = sum(expected_sizes.values()) + 1024 * 1024 if expected_sizes else 512 * 1024 * 1024
    seen_files: set[str] = set()
    total_uncompressed = 0
    with zipfile.ZipFile(archive) as bundle:
        if len(bundle.infolist()) > maximum_entries:
            raise RuntimeError("模型包条目数量超过允许上限。")
        for item in bundle.infolist():
            normalized = item.filename.replace("\\", "/")
            parts = tuple(part for part in normalized.split("/") if part not in {"", "."})
            if not parts or normalized.startswith("/") or ".." in parts:
                raise RuntimeError(f"模型包包含越界路径：{item.filename}")
            target = destination.joinpath(*parts).resolve()
            if target != destination_root and not target.is_relative_to(destination_root):
                raise RuntimeError(f"模型包包含越界路径：{item.filename}")
            unix_mode = (item.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(unix_mode):
                raise RuntimeError(f"模型包包含符号链接：{item.filename}")
            if item.is_dir():
                continue
            inner_parts = parts[1:] if parts[0] == MODEL_NAME else parts
            inner_name = "/".join(inner_parts)
            if expected_sizes and inner_name not in expected_sizes and inner_name != "model-manifest.json":
                raise RuntimeError(f"模型包包含未声明文件：{item.filename}")
            if inner_name in seen_files:
                raise RuntimeError(f"模型包包含重复文件：{item.filename}")
            seen_files.add(inner_name)
            if inner_name in expected_sizes and item.file_size != expected_sizes[inner_name]:
                raise RuntimeError(f"模型包内 {inner_name} 的声明大小不符。")
            if inner_name == "model-manifest.json" and item.file_size > 1024 * 1024:
                raise RuntimeError("模型包内 model-manifest.json 超过 1MB。")
            total_uncompressed += item.file_size
            if total_uncompressed > maximum_uncompressed:
                raise RuntimeError("模型包解压后大小超过允许上限。")
        if expected_sizes and not set(expected_sizes).issubset(seen_files):
            missing = sorted(set(expected_sizes) - seen_files)
            raise RuntimeError("模型包缺少清单文件：" + "、".join(missing))
        bundle.extractall(destination)
    nested = destination / MODEL_NAME
    return nested if nested.is_dir() else destination


def install_model(archive: Path, destination: Path, manifest: dict) -> str | None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected_sizes = {item["name"]: int(item["size"]) for item in manifest.get("files", [])}
    with tempfile.TemporaryDirectory(prefix="proofmesh-model-", dir=destination.parent) as temp_name:
        extracted = safe_extract(archive, Path(temp_name), expected_sizes)
        errors = verify_model_dir(extracted, manifest)
        if errors:
            raise RuntimeError("模型包校验失败：" + "；".join(errors))
        archive_manifest = extracted / "model-manifest.json"
        if not archive_manifest.is_file():
            raise RuntimeError("模型包缺少 model-manifest.json")
        if load_manifest(archive_manifest) != manifest:
            raise RuntimeError("模型包内 model-manifest.json 与发布清单不一致。")

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
    parser.add_argument("--bytes", type=int, help="模型 ZIP 的精确字节数；默认读取发布清单")
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
    expected_bytes = args.bytes or distribution.get("archive_bytes")
    if not url or not expected_sha256 or not isinstance(expected_bytes, int) or expected_bytes <= 0:
        raise RuntimeError("模型下载地址、归档 SHA256 或归档字节数尚未配置。请更新模型发布清单。")

    downloads = destination.parent / ".downloads"
    partial = downloads / f"{MODEL_NAME}.zip.partial"
    download_with_resume(url, partial, expected_bytes)
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
