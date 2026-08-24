"""Stable command-line interface for installed Concorde operations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .diagnostics import canonical_json, envelope, exit_code, operation_envelope
from .model import Finding, OperationResult


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="concorde")
    parser.add_argument("--project-root", default=".")
    subparsers = parser.add_subparsers(dest="operation", required=True)

    initialize = subparsers.add_parser("init")
    mode = initialize.add_mutually_exclusive_group(required=True)
    mode.add_argument("--propose", action="store_true")
    mode.add_argument("--apply", action="store_true")
    initialize.add_argument("--proposal")
    initialize.add_argument("--module-id")
    initialize.add_argument("--name")
    initialize.add_argument("--format", choices=["json"], default="json")

    context = subparsers.add_parser("context")
    context.add_argument("target")
    context.add_argument("--format", choices=["json"], default="json")

    validate = subparsers.add_parser("validate")
    validate.add_argument("target", nargs="?")
    validate.add_argument("--format", choices=["json"], default="json")

    feature = subparsers.add_parser("feature")
    feature_commands = feature.add_subparsers(dest="feature_operation", required=True)
    create = feature_commands.add_parser("create")
    create.add_argument("--module-id", required=True)
    create.add_argument("--feature-id", required=True)
    create.add_argument("--short-name", required=True)
    create.add_argument("--number")
    create.add_argument("--participant-module", action="append", default=[])
    create.add_argument("--format", choices=["json"], default="json")
    select = feature_commands.add_parser("select")
    select.add_argument("target")
    select.add_argument("--resume", action="store_true")
    select.add_argument("--format", choices=["json"], default="json")
    harden = feature_commands.add_parser("harden")
    harden.add_argument("target", nargs="?")
    harden_mode = harden.add_mutually_exclusive_group(required=True)
    harden_mode.add_argument("--propose", action="store_true")
    harden_mode.add_argument("--apply", action="store_true")
    harden.add_argument("--proposal")
    harden.add_argument("--format", choices=["json"], default="json")
    return parser


def dispatch(arguments: argparse.Namespace) -> OperationResult:
    root = Path(arguments.project_root)
    if arguments.operation == "init":
        from .initialize import apply_proposal, propose_initialization

        if arguments.apply:
            if not arguments.proposal:
                return OperationResult(
                    "init",
                    ".",
                    "invalid",
                    findings=(Finding("CONCORDE-INIT-001", "error", ".concorde/config.json", "--apply requires --proposal.", "Pass a project-relative accepted proposal JSON file."),),
                )
            return apply_proposal(root, arguments.proposal)
        return propose_initialization(root, arguments.module_id, arguments.name)
    if arguments.operation == "context":
        from .context import bounded_context

        return bounded_context(root, arguments.target)
    if arguments.operation == "feature":
        from .feature_hardening import apply_hardening, propose_hardening
        from .feature_workspace import propose_feature, select_feature

        if arguments.feature_operation == "create":
            return propose_feature(
                root,
                arguments.module_id,
                arguments.feature_id,
                arguments.short_name,
                arguments.number,
                tuple(arguments.participant_module),
            )
        if arguments.feature_operation == "select":
            return select_feature(root, arguments.target, arguments.resume)
        if arguments.apply:
            if not arguments.proposal:
                return OperationResult(
                    "feature.harden",
                    arguments.target or ".",
                    "invalid",
                    findings=(Finding("CONCORDE-HARDEN-008", "error", ".specify/feature.json", "--apply requires --proposal.", "Pass the project-relative reviewed hardening proposal."),),
                )
            return apply_hardening(root, arguments.proposal)
        return propose_hardening(root, arguments.target)
    from .validate import validate_project

    return validate_project(root, arguments.target)


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    try:
        result = dispatch(parser.parse_args(argv))
        payload = operation_envelope(result)
    except Exception as error:  # command boundary: always return the normative envelope
        operation = argv[0] if argv else "validate"
        payload = envelope(
            operation if operation in {"init", "context", "validate"} else "validate",
            ".",
            "failed",
            [],
            [Finding("CONCORDE-RUN-001", "error", ".concorde/config.json", str(error), "Correct the project configuration or runtime environment and retry.")],
            {},
        )
    sys.stdout.write(canonical_json(payload))
    return exit_code(payload["status"])
