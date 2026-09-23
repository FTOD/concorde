#!/usr/bin/env python3
"""Inspect or check branch-local Issues; never launch a model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from concorde.issues.store import list_issues, read_issue


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("list", "show", "check"))
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
        elif args.action == "check":
            return check(root)
        else:
            value = {"issues": list_issues(root)}
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({"error": str(error)}))
        return 2


def check(root: Path) -> int:
    """Every record reads; an open Issue must name an owner the registry still lists."""
    config = json.loads((root / ".concorde/config.json").read_text(encoding="utf-8"))
    registry = json.loads((root / config["registry"]).read_text(encoding="utf-8"))
    modules = {record["id"] for record in registry["modules"]}
    problems, notes = [], []
    for item in list_issues(root):
        if item["owner_target_id"] in modules:
            continue
        message = f"{item['id']} names unknown owner {item['owner_target_id']}"
        (problems if item["status"] == "open" else notes).append(message)
    print(
        json.dumps({"errors": problems, "notes": notes}, ensure_ascii=False, indent=2)
    )
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
