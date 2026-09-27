"""Human worker configuration editor and read-only inspection/check commands."""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

from .. import errors
from ..errors import evidence
from ..spec.schema import validate
from .models import (
    CLIENTS,
    HANDLING,
    ModelConfigError,
    choice,
    config_path,
    load,
    worker_ids,
)

TEXT = {"type": "string", "minLength": 1}
OPTIONAL_TEXT = {"anyOf": [{"type": "null"}, TEXT]}
CHOSEN_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "backend",
        "backend_source",
        "model",
        "reasoning",
        "model_source",
        "reasoning_source",
    ],
    "properties": {
        "backend": {"enum": list(CLIENTS)},
        "backend_source": TEXT,
        "model": OPTIONAL_TEXT,
        "reasoning": OPTIONAL_TEXT,
        "model_source": TEXT,
        "reasoning_source": TEXT,
    },
}
CONFIGURATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["action", "worktree", "config", "configured", "effective"],
    "properties": {
        "action": {"enum": ["show", "check"]},
        "worktree": TEXT,
        "config": TEXT,
        "configured": {"type": "object"},
        "effective": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": CHOSEN_SCHEMA,
            },
        },
    },
}
RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["command", "status", "output", "evidence", "error"],
    "properties": {
        "command": {"const": "configure-workers"},
        "status": {"enum": ["ok", "failed"]},
        "output": {"anyOf": [{"type": "null"}, {"type": "object"}]},
        "evidence": {"type": "array", "items": {"$ref": "#/$defs/evidence"}},
        "error": {"anyOf": [{"type": "null"}, {"$ref": "#/$defs/error"}]},
    },
    "$defs": copy.deepcopy(errors.DEFS),
}


class UsageError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(f"{self.prog}: {message}")


def add_arguments(parser):
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        "--show",
        action="store_true",
        help="show configuration and effective sources, without discovery",
    )
    actions.add_argument(
        "--check",
        action="store_true",
        help="validate the file without discovery or writes",
    )
    parser.add_argument(
        "--json", action="store_true", help="JSON result (requires --show or --check)"
    )


def actor(worktree):
    return f"concorde configure-workers ({worktree})"


def refusal(worktree, error):
    reason, explanation, options = HANDLING.get(
        error.code, ("input", "the request cannot be completed", [])
    )
    return errors.link(
        "command",
        actor(worktree),
        "configuration_refused",
        f"{config_path(worktree)}: {error.code}: {error}",
        reason=reason,
        explanation="the command does not repair configuration or the environment",
        evidence=[evidence("worker-models", str(config_path(worktree)), str(error))],
        causes=[
            errors.link(
                "component",
                "Workers (worker model configuration)",
                error.code,
                str(error),
                reason=reason,
                explanation=explanation,
                options=options,
            )
        ],
        options=options,
    )


def result(worktree: Path, arguments) -> dict:
    try:
        config = load(worktree)
        output = {
            "action": "check" if arguments.check else "show",
            "worktree": str(worktree),
            "config": str(config_path(worktree)),
            "configured": config,
            "effective": {
                name: {worker: choice(config, name, worker) for worker in workers}
                for name, workers in worker_ids().items()
            },
        }
        validate(output, CONFIGURATION_SCHEMA)
        value = {
            "command": "configure-workers",
            "status": "ok",
            "output": output,
            "evidence": [
                evidence(
                    "worker-models",
                    str(config_path(worktree)),
                    "validated without model discovery",
                )
            ],
            "error": None,
        }
    except ModelConfigError as error:
        link = refusal(worktree, error)
        value = {
            "command": "configure-workers",
            "status": "failed",
            "output": None,
            "evidence": link["evidence"],
            "error": link,
        }
    validate(value, RESULT_SCHEMA)
    return value


def _toplevel(here: Path) -> Path:
    try:
        found = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=here,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise UsageError(str(error)) from error
    if found.returncode:
        raise UsageError(f"{here} is not inside a Git worktree: {found.stderr.strip()}")
    return Path(os.path.realpath(found.stdout.strip()))


def main(argv, cwd: Path | None = None) -> int:
    parser = _Parser(prog="concorde configure-workers", description=__doc__)
    add_arguments(parser)
    here = Path(os.path.realpath(cwd or Path.cwd()))
    try:
        arguments = parser.parse_args(list(argv))
        if arguments.json and not (arguments.show or arguments.check):
            raise UsageError("--json requires --show or --check")
        worktree = _toplevel(here)
        if not (arguments.show or arguments.check):
            if not sys.stdin.isatty() or not sys.stdout.isatty():
                raise UsageError(
                    "the editor needs an interactive terminal; use --show --json or --check, or edit .concorde/worker-models.json directly"
                )
            from .configure_tui import run

            try:
                changed = run(worktree)
                print("Worker configuration saved." if changed else "No changes saved.")
                return 0
            except ModelConfigError as error:
                print(errors.render(refusal(worktree, error)), file=sys.stderr)
                return 1
        value = result(worktree, arguments)
    except UsageError as error:
        link = errors.link(
            "command",
            actor(here),
            "invalid_request",
            str(error),
            reason="input",
            explanation="the command requires a supported request inside a Git worktree",
            options=["see concorde configure-workers --help"],
        )
        print(json.dumps({"error": link}, indent=2))
        return 2
    if arguments.json:
        print(json.dumps(value, indent=2, ensure_ascii=False))
    elif value["status"] == "ok":
        output = value["output"]
        print(f"Valid worker configuration: {output['config']}")
        if arguments.show:
            print(json.dumps(output["configured"], indent=2))
            for operation, workers in output["effective"].items():
                for worker, selected in workers.items():
                    print(f"{operation} / {worker}")
                    for field in ("backend", "model", "reasoning"):
                        print(
                            f"  {field}: {selected[field] or 'backend default'} (from {selected[field + '_source']})"
                        )
    if value["error"]:
        print(errors.render(value["error"]), file=sys.stderr)
    return 0 if value["status"] == "ok" else 1
