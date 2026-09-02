"""Stable command-line interface for installed Concorde operations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .diagnostics import canonical_json, envelope, exit_code, operation_envelope
from .model import Finding, OperationResult

PACKAGE_ROOT = Path(__file__).resolve().parents[2]


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

    deliver = subparsers.add_parser("deliver")
    deliver.add_argument("target", nargs="?")
    deliver_mode = deliver.add_mutually_exclusive_group(required=True)
    deliver_mode.add_argument("--propose", action="store_true")
    deliver_mode.add_argument("--apply", action="store_true")
    deliver.add_argument("--proposal")
    deliver.add_argument("--format", choices=["json"], default="json")

    agent_assets = subparsers.add_parser("agent-assets")
    asset_commands = agent_assets.add_subparsers(dest="agent_asset_operation", required=True)
    for name in ("preview", "sync", "verify", "remove"):
        command = asset_commands.add_parser(name)
        command.add_argument("--integration", choices=["claude", "codex"], required=True)
        command.add_argument("--source-root")
        command.add_argument("--concorde-version", default="source")
        command.add_argument("--format", choices=["json"], default="json")
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
    if arguments.operation == "deliver":
        from .delivery import apply_delivery, propose_delivery

        if arguments.apply:
            if not arguments.proposal:
                return OperationResult(
                    "deliver",
                    arguments.target or ".",
                    "invalid",
                    findings=(Finding("CONCORDE-DELIVER-008", "error", ".concorde/feature.json", "--apply requires --proposal.", "Pass the project-relative generated delivery proposal."),),
                )
            return apply_delivery(root, arguments.proposal)
        return propose_delivery(root, arguments.target)
    if arguments.operation == "agent-assets":
        from .agent_assets import (
            preview_agent_assets,
            remove_agent_assets,
            sync_agent_assets,
            verify_agent_assets,
        )

        source = (
            Path(arguments.source_root)
            if arguments.source_root
            else PACKAGE_ROOT / "agent-assets/reflections"
        )
        if arguments.agent_asset_operation == "preview":
            return preview_agent_assets(root, source, arguments.integration, arguments.concorde_version)
        if arguments.agent_asset_operation == "sync":
            return sync_agent_assets(root, source, arguments.integration, arguments.concorde_version)
        if arguments.agent_asset_operation == "verify":
            return verify_agent_assets(root, source, arguments.integration)
        return remove_agent_assets(root, arguments.integration)
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
            operation
            if operation in {"init", "context", "validate", "deliver", "agent-assets"}
            else "validate",
            ".",
            "failed",
            [],
            [Finding("CONCORDE-RUN-001", "error", ".concorde/config.json", str(error), "Correct the project configuration or runtime environment and retry.")],
            {},
        )
    sys.stdout.write(canonical_json(payload))
    return exit_code(payload["status"])
