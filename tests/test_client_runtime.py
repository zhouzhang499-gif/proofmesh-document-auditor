from __future__ import annotations

from scripts import client


def test_pipe_identity_changes_with_runtime_home(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("PROOFMESH_HOME", str(tmp_path / "first"))
    first = client.pipe_address()
    monkeypatch.setenv("PROOFMESH_HOME", str(tmp_path / "second"))
    second = client.pipe_address()

    assert first != second
    assert first.startswith(r"\\.\pipe\proofmesh-")
