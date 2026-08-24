from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
from multiprocessing.connection import Client
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from proofmesh.service import default_home  # noqa: E402


MAX_MESSAGE_BYTES = 1024 * 1024


def runtime_dir() -> Path:
    path = default_home() / "runtime"
    path.mkdir(parents=True, exist_ok=True)
    return path


def pipe_address() -> str:
    identity = (
        f"{os.environ.get('USERNAME', 'user')}|{Path.home()}|"
        f"{default_home().resolve()}|{PROJECT_ROOT.resolve()}|protocol=1"
    ).encode("utf-8")
    suffix = hashlib.sha256(identity).hexdigest()[:16]
    return rf"\\.\pipe\proofmesh-{suffix}-v1"


def auth_key(path: Path) -> bytes:
    key_path = path / "auth.key"
    if not key_path.exists():
        try:
            descriptor = os.open(key_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "w", encoding="ascii") as handle:
                handle.write(secrets.token_hex(32))
        except FileExistsError:
            pass
    os.chmod(key_path, 0o600)
    return bytes.fromhex(key_path.read_text(encoding="ascii").strip())


def request(payload: dict, start_server: bool = True) -> dict:
    runtime = runtime_dir()
    key = auth_key(runtime)
    try:
        return _send(payload, key)
    except (FileNotFoundError, ConnectionRefusedError, OSError):
        if not start_server:
            raise
        _start_server(runtime)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            time.sleep(0.2)
            try:
                return _send(payload, key)
            except (FileNotFoundError, ConnectionRefusedError, OSError):
                continue
        raise RuntimeError("本地服务在 15 秒内没有启动。请查看 runtime/server.log。")


def _send(payload: dict, key: bytes) -> dict:
    connection = Client(pipe_address(), family="AF_PIPE", authkey=key)
    try:
        request_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if len(request_bytes) > MAX_MESSAGE_BYTES:
            raise ValueError("请求超过 1 MB 限制。")
        connection.send_bytes(request_bytes)
        response_bytes = connection.recv_bytes(maxlength=MAX_MESSAGE_BYTES)
        return json.loads(response_bytes.decode("utf-8"))
    finally:
        connection.close()


def _start_server(runtime: Path) -> None:
    server = Path(__file__).with_name("server.py")
    log_path = runtime / "server.log"
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    with log_path.open("a", encoding="utf-8") as log:
        subprocess.Popen(
            [sys.executable, str(server)],
            cwd=str(PROJECT_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            creationflags=flags,
            close_fds=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["audit", "status", "show", "shutdown"])
    parser.add_argument("--path")
    parser.add_argument("--run-id")
    args = parser.parse_args()
    payload = {"command": args.command, "path": args.path, "run_id": args.run_id}
    try:
        response = request(payload, start_server=args.command != "shutdown")
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    stream = sys.stderr if response.get("status") == "error" else sys.stdout
    print(json.dumps(response, ensure_ascii=False, indent=2), file=stream)
    return 0 if response.get("status") != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
