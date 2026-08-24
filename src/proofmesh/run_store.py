from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class RunStore:
    def __init__(self, home: Path):
        self.home = home
        self.runs_dir = home / "runs"

    def create_run(self, run_id: str) -> Path:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        path = self.runs_dir / run_id
        path.mkdir(parents=False, exist_ok=False)
        return path

    def run_path(self, run_id: str) -> Path:
        path = (self.runs_dir / run_id).resolve()
        if path.parent != self.runs_dir.resolve():
            raise ValueError("运行编号越过了运行目录。")
        return path

    def write_json(self, directory: Path, name: str, value: Any) -> Path:
        return self._atomic_write(directory / name, json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    def write_text(self, directory: Path, name: str, value: str) -> Path:
        return self._atomic_write(directory / name, value)

    def read_json(self, run_id: str, name: str) -> Any:
        with (self.run_path(run_id) / name).open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _atomic_write(path: Path, text: str) -> Path:
        temp = path.with_suffix(path.suffix + ".partial")
        with temp.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        return path
