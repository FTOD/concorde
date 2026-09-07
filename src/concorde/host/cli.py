"""Stable command-line interface for installed Concorde Tools."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from ..diagnostics import canonical_json, envelope, exit_code, tool_envelope
from ..model import Finding, ToolResult


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

    build = subparsers.add_parser("build")
    build.add_argument("--integration", choices=["claude", "codex", "all"], default="all")
    build.add_argument("--check", action="store_true")
    build.add_argument("--format", choices=["json"], default="json")

    verify_worktree = subparsers.add_parser("verify-worktree")
    verify_worktree.add_argument("--project-root", default=".")
    verify_worktree.add_argument("--loaded-skill-path", required=True)
    verify_worktree.add_argument("--format", choices=["text", "json"], default="text")
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
    if arguments.tool == "build":
        from .build import BuildError, check_build, write_build

        try:
            if arguments.check:
                current, differences = check_build(root, arguments.integration)
                if current:
                    return ToolResult("build", ".", "success", result={"differences": []})
                return ToolResult(
                    "build",
                    ".",
                    "invalid",
                    findings=(
                        Finding(
                            "CONCORDE-BUILD-001",
                            "error",
                            "generated/",
                            f"Build outputs are stale or missing: {', '.join(differences)}",
                            "Run `python -m concorde build` to refresh generated/ outputs.",
                        ),
                    ),
                    result={"differences": list(differences)},
                )
            result = write_build(root, arguments.integration)
            artifacts = tuple(output.path for output in result.outputs) + ("generated/build-manifest.json",)
            return ToolResult("build", ".", "success", artifacts=artifacts, result={"outputs": len(result.outputs)})
        except BuildError as error:
            return ToolResult(
                "build",
                ".",
                "invalid",
                findings=(
                    Finding(
                        "CONCORDE-BUILD-001",
                        "error",
                        "prompts",
                        str(error),
                        "Repair the prompt, role, or skill source and rebuild.",
                    ),
                ),
            )
    from ..understanding.validate import validate_project

    return validate_project(root, arguments.target)


def _verify_worktree(arguments: argparse.Namespace) -> int:
    """Identical semantics and messages to the retired sync-agent-surfaces.py verify-worktree."""

    import json as json_module

    from .worktree_affinity import WorktreeAffinityError, verify_worktree_affinity

    root = Path(arguments.project_root).resolve()
    try:
        verified = verify_worktree_affinity(root, arguments.loaded_skill_path)
        result = {"schema_version": 1, "tool": "verify-worktree", "status": "current", **verified}
        if arguments.format == "json":
            print(json_module.dumps(result, indent=2, sort_keys=True))
        else:
            print(
                "Concorde agent worktree: current "
                f"({verified['integration']}, {verified['capability']}, {verified['project_root']})"
            )
        return 0
    except WorktreeAffinityError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    arguments: argparse.Namespace | None = None
    try:
        arguments = parser.parse_args(argv)
        if arguments.tool == "verify-worktree":
            return _verify_worktree(arguments)
        mutation = arguments.tool in {"init", "deliver", "docsite"} or (
            arguments.tool == "configure" and arguments.apply
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
            if tool in {"init", "configure", "context", "explore", "validate", "deliver", "docsite", "build"}
            else "validate",
            ".",
            "failed",
            [],
            [Finding("CONCORDE-RUN-001", "error", ".concorde/config.json", str(error), "Correct the project configuration or runtime environment and retry.")],
            {},
        )
    sys.stdout.write(canonical_json(payload))
    return exit_code(payload["status"])
