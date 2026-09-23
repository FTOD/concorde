#!/usr/bin/env python3
"""Inspect branch-local Issues; never launch a model."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from concorde.issues.store import list_issues, read_issue


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("list", "show"))
    parser.add_argument("issue_id", nargs="?")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if not (root / ".concorde/config.json").is_file():
            raise ValueError("not an initialized Concorde project")
        if args.action == "show":
            if not args.issue_id:
                raise ValueError("show requires an Issue ID")
            record, revision = read_issue(root, args.issue_id)
            value = {"issue": record, "revision": revision}
        elif args.issue_id:
            raise ValueError("only show accepts an Issue ID")
        else:
            value = {"issues": list_issues(root)}
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({"error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
