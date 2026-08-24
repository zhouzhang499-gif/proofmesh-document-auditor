from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .service import DocumentAuditService, default_home


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proofmesh")
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit")
    audit.add_argument("--path", required=True)
    show = sub.add_parser("show")
    show.add_argument("--run-id", required=True)
    sub.add_parser("status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = Path(__file__).resolve().parents[2]
    service = DocumentAuditService(project_root, default_home())
    try:
        if args.command == "audit":
            result = service.audit(args.path)
        elif args.command == "show":
            result = service.show(args.run_id)
        else:
            result = {"status": "ready", "home": str(default_home())}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print(json.dumps({"status": "error", "code": "invalid_input", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except Exception as exc:
        print(json.dumps({"status": "error", "code": "audit_failed", "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

