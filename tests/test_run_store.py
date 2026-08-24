from pathlib import Path

import pytest

from proofmesh.run_store import RunStore


def test_run_store_writes_and_reads_json(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run = store.create_run("run-1")
    store.write_json(run, "run.json", {"status": "complete"})
    assert store.read_json("run-1", "run.json") == {"status": "complete"}


def test_run_id_cannot_escape_runs_directory(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    with pytest.raises(ValueError):
        store.run_path("../outside")

