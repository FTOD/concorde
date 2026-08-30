#!/usr/bin/env python3
"""Order, inspect, and track open entries of the Concorde reflection log for the triage pipeline.

Usage (run from the repository root; stdlib only):
  reflections-queue.py                     table of open entries in configured order, with plan state
  reflections-queue.py --json              same, as JSON
  reflections-queue.py --next N            next N open entries that have no plan yet (JSON, full text)
  reflections-queue.py --entry R-038       one entry: text, fields, feature directory map (JSON)
  reflections-queue.py --plans             every plan file's frontmatter (JSON)
  reflections-queue.py --set R-038 status=implemented branch=x commit=y
                                           update/add frontmatter keys of a plan file
Configuration: .claude/reflections.config.json (log, features_root, plans_dir, order, skip).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ENTRY_RE = re.compile(r"^### (R-\d{3,}) · (.+)$")
FIELDS = ("Phase", "Date", "Feature", "Kind", "Concerns", "Effect", "Status")


def find_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    here = Path(__file__).resolve()
    for candidate in (here.parents[4] if len(here.parents) > 4 else None, Path.cwd()):
        if candidate and (candidate / ".claude" / "reflections.config.json").is_file():
            return candidate
    return Path.cwd()


def load_config(root: Path) -> dict:
    defaults = {
        "log": "specs/concorde/reflections.md",
        "features_root": "specs/concorde/features",
        "plans_dir": ".claude/reflection-plans",
        "order": "newest-first",
        "skip": [],
    }
    path = root / ".claude" / "reflections.config.json"
    if path.is_file():
        defaults.update(json.loads(path.read_text(encoding="utf-8")))
    return defaults


def frontmatter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict = {}
    key_list: str | None = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("  - ") and key_list:
            out.setdefault(key_list, []).append(line[4:].strip())
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            if value == "":
                key_list = key
                out[key] = []
            else:
                key_list = None
                out[key] = value
    return out


def parse_log(text: str) -> list[dict]:
    entries: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        m = ENTRY_RE.match(line)
        if m:
            current = {"id": m.group(1), "title": m.group(2).strip(), "_lines": [line]}
            entries.append(current)
            continue
        if line.startswith("## "):
            current = None
            continue
        if current is not None:
            current["_lines"].append(line)
    for entry in entries:
        body = "\n".join(entry.pop("_lines")).rstrip() + "\n"
        entry["text"] = body
        for label in FIELDS:
            m = re.search(rf"^- \*\*{label}\*\*: (.*)$", body, re.M)
            entry[label.lower()] = m.group(1).strip() if m else None
        entry["number"] = int(entry["id"][2:])
    return entries


def feature_map(root: Path, features_root: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for design in sorted((root / features_root).rglob("design.md")):
        if "attempt" in design.parts:
            continue
        fm = frontmatter(design.read_text(encoding="utf-8"))
        if fm.get("kind") == "feature" and fm.get("id"):
            out[str(fm["id"])] = design.parent.relative_to(root).as_posix()
    return out


def load_plans(root: Path, plans_dir: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    directory = root / plans_dir
    if directory.is_dir():
        for path in sorted(directory.glob("R-*.md")):
            fm = frontmatter(path.read_text(encoding="utf-8"))
            out[str(fm.get("id") or path.stem)] = {"path": path.relative_to(root).as_posix(), **fm}
    return out


def ordered_open(entries: list[dict], config: dict) -> list[dict]:
    skip = set(config.get("skip") or [])
    open_entries = [e for e in entries if e["status"] == "open" and e["id"] not in skip]
    reverse = config.get("order", "newest-first") == "newest-first"
    return sorted(open_entries, key=lambda e: e["number"], reverse=reverse)


def enrich(entry: dict, fmap: dict[str, str], plans: dict[str, dict], root: Path) -> dict:
    plan = plans.get(entry["id"])
    concerns = entry.get("concerns") or ""
    concerns_target = concerns.split("#")[0].split(":")[0]
    concerns_path = fmap.get(concerns_target) or (concerns_target if (root / concerns_target).exists() else None)
    return {
        **entry,
        "feature_directory": fmap.get(entry.get("feature") or ""),
        "concerns_path": concerns_path,
        "plan": {"route": plan.get("route"), "status": plan.get("status"), "path": plan.get("path"),
                 "branch": plan.get("branch"), "implement_in": plan.get("implement_in")} if plan else None,
    }


def set_frontmatter(path: Path, updates: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise SystemExit(f"{path}: no frontmatter")
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    seen: set[str] = set()
    for i in range(1, end):
        m = re.match(r"^([A-Za-z_][\w-]*):", lines[i])
        if m and m.group(1) in updates:
            lines[i] = f"{m.group(1)}: {updates[m.group(1)]}"
            seen.add(m.group(1))
    for key, value in updates.items():
        if key not in seen:
            lines.insert(end, f"{key}: {value}")
            end += 1
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--next", type=int, metavar="N")
    parser.add_argument("--entry", metavar="R-NNN")
    parser.add_argument("--plans", action="store_true")
    parser.add_argument("--set", nargs="+", metavar=("R-NNN", "key=value"))
    args = parser.parse_args()

    root = find_root(args.root)
    config = load_config(root)
    log_path = root / config["log"]
    if not log_path.is_file():
        print(f"reflection log not found: {log_path}", file=sys.stderr)
        return 2
    entries = parse_log(log_path.read_text(encoding="utf-8"))
    fmap = feature_map(root, config["features_root"])
    plans = load_plans(root, config["plans_dir"])

    if args.set:
        entry_id, *pairs = args.set
        plan = plans.get(entry_id)
        if not plan:
            print(f"no plan file for {entry_id} in {config['plans_dir']}", file=sys.stderr)
            return 2
        updates = dict(pair.split("=", 1) for pair in pairs)
        set_frontmatter(root / plan["path"], updates)
        print(json.dumps({"updated": plan["path"], **updates}))
        return 0

    if args.plans:
        print(json.dumps(plans, indent=2))
        return 0

    if args.entry:
        match = [e for e in entries if e["id"] == args.entry]
        if not match:
            print(f"no entry {args.entry}", file=sys.stderr)
            return 2
        payload = enrich(match[0], fmap, plans, root)
        payload["feature_map"] = fmap
        payload["open_total"] = sum(1 for e in entries if e["status"] == "open")
        print(json.dumps(payload, indent=2))
        return 0

    queue = [enrich(e, fmap, plans, root) for e in ordered_open(entries, config)]

    if args.next is not None:
        pending = [e for e in queue if e["plan"] is None][: args.next]
        print(json.dumps(pending, indent=2))
        return 0

    if args.json:
        for e in queue:
            e.pop("text", None)
        print(json.dumps(queue, indent=2))
        return 0

    print(f"{'ID':<6} {'KIND':<14} {'FEATURE (recorded under)':<58} {'PLAN':<22} CONCERNS")
    for e in queue:
        plan = e["plan"]
        plan_str = f"{plan['route']}/{plan['status']}" if plan else "-"
        print(f"{e['id']:<6} {e['kind'] or '':<14} {(e['feature'] or ''):<58} {plan_str:<22} {e['concerns'] or ''}")
    print(f"\n{len(queue)} open in {config['order']} order · {sum(1 for e in queue if e['plan'])} planned · "
          f"{len(entries)} entries total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
