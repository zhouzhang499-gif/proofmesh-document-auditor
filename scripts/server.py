from __future__ import annotations

import json
import os
import sys
import msvcrt
import traceback
from datetime import UTC, datetime
from multiprocessing.connection import Listener
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from client import MAX_MESSAGE_BYTES, auth_key, pipe_address, runtime_dir  # noqa: E402
from proofmesh.service import DocumentAuditService, default_home  # noqa: E402


def main() -> int:
    runtime = runtime_dir()
    lock_path = runtime / "server.lock"
    descriptor = _acquire_lock(lock_path)
    if descriptor is None:
        return 0
    state_path = runtime / "server.json"
    state_path.write_text(
        json.dumps({"pid": os.getpid(), "version": "0.1.0", "protocol": 1, "started_at": datetime.now(UTC).isoformat()}),
        encoding="utf-8",
    )
    listener = None
    try:
        listener = Listener(pipe_address(), family="AF_PIPE", authkey=auth_key(runtime))
        service = DocumentAuditService(PROJECT_ROOT, default_home())
        running = True
        while running:
            connection = listener.accept()
            try:
                payload_bytes = connection.recv_bytes(maxlength=MAX_MESSAGE_BYTES)
                payload = json.loads(payload_bytes.decode("utf-8"))
                command = payload.get("command")
                if command == "audit":
                    response = service.audit(payload.get("path") or "")
                elif command == "show":
                    response = service.show(payload.get("run_id") or "")
                    response["status"] = "complete"
                elif command == "status":
                    response = {
                        "status": "ready",
                        "pid": os.getpid(),
                        "protocol": 1,
                        "version": "0.1.0",
                        "home": str(default_home()),
                        "model": service.semantic_matcher.info(),
                    }
                elif command == "shutdown":
                    response = {"status": "stopping", "pid": os.getpid()}
                    running = False
                else:
                    response = {"status": "error", "code": "unknown_command", "message": "无法识别这个命令。"}
            except Exception as exc:
                response = {"status": "error", "code": "request_failed", "message": str(exc)}
            response_bytes = json.dumps(response, ensure_ascii=False).encode("utf-8")
            if len(response_bytes) > MAX_MESSAGE_BYTES:
                response_bytes = json.dumps(
                    {"status": "error", "code": "response_too_large", "message": "服务响应超过 1 MB 限制。"},
                    ensure_ascii=False,
                ).encode("utf-8")
            connection.send_bytes(response_bytes)
            connection.close()
    finally:
        if listener is not None:
            listener.close()
        descriptor.close()
        lock_path.unlink(missing_ok=True)
        state_path.unlink(missing_ok=True)
    return 0


def _acquire_lock(lock_path: Path):
    handle = lock_path.open("a+b")
    try:
        if lock_path.stat().st_size == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        handle.close()
        return None
    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()).encode("ascii"))
    handle.flush()
    return handle


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise
