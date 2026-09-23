"""``concorde task open|list|show|close``: print one JSON value; refusals exit 1, bad usage 2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import store


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="concorde task")
    commands = root.add_subparsers(dest="command", required=True)
    opening = commands.add_parser("open")
    opening.add_argument("task_id")
    opening.add_argument("--goal", required=True)
    opening.add_argument("--modules", required=True)
    opening.add_argument("--base")
    opening.add_argument("--path")
    listing = commands.add_parser("list")
    listing.add_argument("--state", choices=store.STATES)
    showing = commands.add_parser("show")
    showing.add_argument("task_id")
    closing = commands.add_parser("close")
    closing.add_argument("task_id")
    mode = closing.add_mutually_exclusive_group(required=True)
    mode.add_argument("--merged", action="store_true")
    mode.add_argument("--abandoned", action="store_true")
    closing.add_argument("--force", action="store_true")
    return root


def main(argv, cwd: Path | None = None) -> int:
    try:
        arguments = parser().parse_args(argv)
    except SystemExit as exit_:
        return 0 if exit_.code in (0, None) else 2
    here = Path(cwd or Path.cwd())
    try:
        if arguments.command == "open":
            value = store.open_task(
                here,
                arguments.task_id,
                arguments.goal,
                [item.strip() for item in arguments.modules.split(",") if item.strip()],
                base=arguments.base,
                path=Path(arguments.path) if arguments.path else None,
            )
        elif arguments.command == "list":
            value = store.list_tasks(store.primary_of(here), arguments.state)
        elif arguments.command == "show":
            value = store.show_task(store.primary_of(here), arguments.task_id)
        else:
            if arguments.force and not arguments.abandoned:
                raise store.TaskError(
                    "invalid_input", "--force applies only to --abandoned"
                )
            value = store.close_task(
                here,
                arguments.task_id,
                merged=arguments.merged,
                abandoned=arguments.abandoned,
                force=arguments.force,
            )
    except store.TaskError as error:
        sys.stdout.write(
            json.dumps({"error": error.code, "message": str(error)}) + "\n"
        )
        return 1
    sys.stdout.write(json.dumps(value, indent=2) + "\n")
    return 0
