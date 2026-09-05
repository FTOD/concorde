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

    validate = subparsers.add_parser("validate")
    validate.add_argument("target", nargs="?")
    validate.add_argument("--format", choices=["json"], default="json")

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
    if not (list(argv) if argv is not None else sys.argv[1:]):
        from .scoped_operations import json_main
        return json_main(PACKAGE_ROOT)
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
