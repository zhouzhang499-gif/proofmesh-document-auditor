from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from proofmesh.service import _model_dir
from scripts.fetch_model import MODEL_NAME, default_destination, install_model, safe_extract, verify_model_dir


def _manifest(files: dict[str, bytes]) -> dict:
    return {
        "files": [
            {
                "name": name,
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for name, content in files.items()
        ]
    }


def test_model_dir_prefers_complete_bundled_model(tmp_path: Path) -> None:
    project = tmp_path / "project"
    bundled = project / "models" / MODEL_NAME
    bundled.mkdir(parents=True)
    for name in {
        "model-manifest.json",
        "openvino_model.xml",
        "openvino_model.bin",
        "openvino_tokenizer.xml",
        "openvino_tokenizer.bin",
    }:
        (bundled / name).write_bytes(b"")

    assert _model_dir(project, tmp_path / "home") == bundled


def test_model_dir_uses_user_cache_for_slim_package(tmp_path: Path) -> None:
    project = tmp_path / "project"
    manifest_only = project / "models" / MODEL_NAME
    manifest_only.mkdir(parents=True)
    (manifest_only / "model-manifest.json").write_text("{}", encoding="utf-8")

    assert _model_dir(project, tmp_path / "home") == tmp_path / "home" / "models" / MODEL_NAME


def test_model_download_uses_proofmesh_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("PROOFMESH_MODEL_DIR", raising=False)
    monkeypatch.setenv("PROOFMESH_HOME", str(tmp_path / "home"))

    assert default_destination() == (tmp_path / "home" / "models" / MODEL_NAME).resolve()


def test_model_archive_is_verified_before_install(tmp_path: Path) -> None:
    files = {"openvino_model.xml": b"xml", "openvino_model.bin": b"bin"}
    manifest = _manifest(files)
    archive = tmp_path / "model.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        for name, content in files.items():
            bundle.writestr(f"{MODEL_NAME}/{name}", content)
        bundle.writestr(f"{MODEL_NAME}/model-manifest.json", json.dumps(manifest))

    destination = tmp_path / "cache" / MODEL_NAME
    backup = install_model(archive, destination, manifest)

    assert backup is None
    assert verify_model_dir(destination, manifest) == []


def test_safe_extract_rejects_parent_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../outside.txt", "bad")

    with pytest.raises(RuntimeError, match="越界路径"):
        safe_extract(archive, tmp_path / "extract")
    assert not (tmp_path / "outside.txt").exists()
