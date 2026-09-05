"""Stable command-line interface for installed Concorde Tools."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from ..diagnostics import canonical_json, envelope, exit_code, tool_envelope
from ..model import Finding, ToolResult

PACKAGE_ROOT = Path(__file__).resolve().parents[3]


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="concorde")
    parser.add_argument("--project-root", default=".")
    subparsers = parser.add_subparsers(dest="tool", required=True)

    initialize = subparsers.add_parser("init")
    mode = initialize.add_mutually_exclusive_group(required=True)
    mode.add_argument("--propose", action="store_true")
    mode.add_argument("--apply", action="store_true")
    initialize.add_argument("--proposal")
    initialize.add_argument("--module-id")
    initialize.add_argument("--name")
    initialize.add_argument("--configuration", help="JSON configuration file, or - for stdin; required for a new project")
    initialize.add_argument("--allow-primary-worktree", action="store_true")
    initialize.add_argument("--format", choices=["json"], default="json")

    configure = subparsers.add_parser("configure")
    config_mode = configure.add_mutually_exclusive_group(required=True)
    config_mode.add_argument("--propose", action="store_true")
    config_mode.add_argument("--apply", action="store_true")
    configure.add_argument("--configuration", help="TypedValue JSON file, or - for stdin")
    configure.add_argument("--proposal")
    configure.add_argument("--allow-primary-worktree", action="store_true")
    configure.add_argument("--format", choices=["json"], default="json")

    context = subparsers.add_parser("context")
    context.add_argument("target")
    context.add_argument("--format", choices=["json"], default="json")

    explore = subparsers.add_parser("explore")
    explore.add_argument("target", nargs="?")
    explore.add_argument("--graph")
    explore.add_argument("--alignment")
    explore.add_argument("--revision")
    explore.add_argument("--query")
    explore.add_argument(
        "--status",
        action="append",
        choices=["unknown", "partial", "verified", "disagrees"],
        default=[],
    )
    explore.add_argument("--format", choices=["json"], default="json")

    validate = subparsers.add_parser("validate")
    validate.add_argument("target", nargs="?")
    validate.add_argument("--format", choices=["json"], default="json")

    deliver = subparsers.add_parser("deliver")
    deliver.add_argument("target", nargs="?")
    deliver_mode = deliver.add_mutually_exclusive_group(required=True)
    deliver_mode.add_argument("--propose", action="store_true")
    deliver_mode.add_argument("--apply", action="store_true")
    deliver.add_argument("--proposal")
    deliver.add_argument("--allow-primary-worktree", action="store_true")
    deliver.add_argument("--format", choices=["json"], default="json")

    docsite = subparsers.add_parser("docsite")
    docsite_mode = docsite.add_mutually_exclusive_group(required=True)
    docsite_mode.add_argument("--propose", action="store_true")
    docsite_mode.add_argument("--apply", action="store_true")
    docsite.add_argument("--proposal")
    docsite.add_argument("--title")
    docsite.add_argument("--repository")
    docsite.add_argument("--url")
    docsite.add_argument("--base-url")
    docsite.add_argument("--github-pages", action="store_true")
    docsite.add_argument("--allow-primary-worktree", action="store_true")
    docsite.add_argument("--format", choices=["json"], default="json")

    agent_assets = subparsers.add_parser("agent-assets")
    asset_tools = agent_assets.add_subparsers(dest="agent_asset_tool", required=True)
    for name in ("preview", "sync", "verify", "remove"):
        command = asset_tools.add_parser(name)
        command.add_argument("--integration", choices=["claude", "codex"], required=True)
        command.add_argument("--source-root")
        command.add_argument("--concorde-version", default="source")
        if name in {"sync", "remove"}:
            command.add_argument("--allow-primary-worktree", action="store_true")
        command.add_argument("--format", choices=["json"], default="json")
    return parser


def dispatch(arguments: argparse.Namespace) -> ToolResult:
    root = Path(arguments.project_root)
    configuration = None
    if arguments.tool in {"init", "configure"} and arguments.propose and arguments.configuration:
        from .operation_data import checked_path, decode

        configuration = decode(sys.stdin.read() if arguments.configuration == "-"
                               else checked_path(root, arguments.configuration).read_text(encoding="utf-8"))
    if arguments.tool == "configure":
        from .operation_config import apply_configuration, propose_configuration

        if arguments.apply:
            if not arguments.proposal:
                raise ValueError("configure --apply requires --proposal")
            return apply_configuration(root, arguments.proposal)
        return propose_configuration(root, configuration)
    if arguments.tool == "init":
        from ..understanding.initialize import apply_proposal, propose_initialization

        if arguments.apply:
            if not arguments.proposal:
                return ToolResult(
                    "init",
                    ".",
                    "invalid",
                    findings=(Finding("CONCORDE-INIT-001", "error", ".concorde/config.json", "--apply requires --proposal.", "Pass a project-relative accepted proposal JSON file."),),
                )
            return apply_proposal(root, arguments.proposal)
        return propose_initialization(root, arguments.module_id, arguments.name, configuration)
    if arguments.tool == "context":
        from ..understanding.context import bounded_context

        return bounded_context(root, arguments.target)
    if arguments.tool == "explore":
        from ..understanding.alignment import explore_alignment

        return explore_alignment(
            root,
            arguments.target,
            graph_path=arguments.graph,
            alignment_path=arguments.alignment,
            expected_revision=arguments.revision,
            query=arguments.query,
            statuses=arguments.status,
        )
    if arguments.tool == "deliver":
        from ..lifecycle.delivery import apply_delivery, materialize_delivery_proposal, propose_delivery

        if arguments.apply:
            if not arguments.proposal:
                return ToolResult(
                    "deliver",
                    arguments.target or ".",
                    "invalid",
                    findings=(Finding("CONCORDE-DELIVER-008", "error", ".concorde/feature.json", "--apply requires --proposal.", "Pass the project-relative generated delivery proposal."),),
                )
            return apply_delivery(root, arguments.proposal)
        return materialize_delivery_proposal(root, propose_delivery(root, arguments.target))
    if arguments.tool == "docsite":
        from ..autodocs.docsite_scaffold import apply_docsite, propose_docsite

        if arguments.apply:
            if not arguments.proposal:
                return ToolResult(
                    "docsite",
                    ".",
                    "invalid",
                    findings=(Finding("CONCORDE-DOCSITE-008", "error", "docsite/site.json", "--apply requires --proposal.", "Pass a project-relative accepted proposal JSON file."),),
                )
            return apply_docsite(root, arguments.proposal)
        return propose_docsite(
            root,
            title=arguments.title,
            repository=arguments.repository,
            url=arguments.url,
            base_url=arguments.base_url,
            github_pages=arguments.github_pages,
        )
    if arguments.tool == "agent-assets":
        from ..reflections.agent_assets import (
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
        if arguments.agent_asset_tool == "preview":
            return preview_agent_assets(root, source, arguments.integration, arguments.concorde_version)
        if arguments.agent_asset_tool == "sync":
            return sync_agent_assets(root, source, arguments.integration, arguments.concorde_version)
        if arguments.agent_asset_tool == "verify":
            return verify_agent_assets(root, source, arguments.integration)
        return remove_agent_assets(root, arguments.integration)
    from ..understanding.validate import validate_project

    return validate_project(root, arguments.target)


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    arguments: argparse.Namespace | None = None
    try:
        arguments = parser.parse_args(argv)
        mutation = arguments.tool in {"init", "deliver", "docsite"} or (
            arguments.tool == "configure" and arguments.apply
        ) or (
            arguments.tool == "agent-assets"
            and arguments.agent_asset_tool in {"sync", "remove"}
        )
        if mutation:
            from .worktree import require_isolated_worktree

            require_isolated_worktree(
                arguments.project_root,
                allow_primary_worktree=getattr(
                    arguments, "allow_primary_worktree", False
                ),
            )
        result = dispatch(arguments)
        payload = tool_envelope(result)
    except Exception as error:  # command boundary: always return the normative envelope
        tool = arguments.tool if arguments is not None else (argv[0] if argv else "validate")
        payload = envelope(
            tool
            if tool in {"init", "configure", "context", "explore", "validate", "deliver", "agent-assets", "docsite"}
            else "validate",
            ".",
            "failed",
            [],
            [Finding("CONCORDE-RUN-001", "error", ".concorde/config.json", str(error), "Correct the project configuration or runtime environment and retry.")],
            {},
        )
    sys.stdout.write(canonical_json(payload))
    return exit_code(payload["status"])
