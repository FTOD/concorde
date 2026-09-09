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

    protocol_manifest = subparsers.add_parser("protocol-manifest")
    protocol_manifest.add_argument("--write", action="store_true")
    protocol_manifest.add_argument("--bind-project", action="store_true")
    protocol_manifest.add_argument("--format", choices=["json"], default="json")
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


def _protocol_manifest(arguments: argparse.Namespace) -> ToolResult:
    """Recompute tracked Protocol asset digests from the current build (developer-only).

    Mirrors the former ``sync-protocol-assets.py --bind-project``: with neither flag this only
    reports whether ``protocol/manifest.json`` matches the current ``generated/protocol/...``
    build; ``--write`` accepts the current build's digests into the tracked manifest;
    ``--bind-project`` pins ``.concorde/config.json``'s ``protocol`` binding to the (possibly just
    rewritten) manifest's version and digest.
    """

    import json as json_module

    from .build import BuildError, PROTOCOL_MANIFEST_PATH, recompute_protocol_manifest, verify_fresh
    from ..specification.repository import digest as digest_bytes

    root = Path(arguments.project_root)
    try:
        verify_fresh(root)
        updated = recompute_protocol_manifest(root)
    except BuildError as error:
        return ToolResult("protocol-manifest", ".", "invalid", findings=(
            Finding("CONCORDE-PROTOCOL-MANIFEST-001", "error", PROTOCOL_MANIFEST_PATH, str(error),
                    "Run `python -m concorde build` to refresh generated/protocol/ outputs."),
        ))
    manifest_path = root / PROTOCOL_MANIFEST_PATH
    current = json_module.loads(manifest_path.read_text(encoding="utf-8"))
    differences = [item["path"] for item, fresh in zip(current["assets"], updated["assets"])
                   if item["digest"] != fresh["digest"]]
    artifacts: tuple[str, ...] = ()
    if arguments.write and differences:
        manifest_path.write_text(json_module.dumps(updated, indent=2) + "\n")
        artifacts += (PROTOCOL_MANIFEST_PATH,)
    if arguments.bind_project:
        config_path = root / ".concorde/config.json"
        config = json_module.loads(config_path.read_text(encoding="utf-8"))
        config["protocol"] = {"version": updated["version"], "digest": digest_bytes(manifest_path.read_bytes())}
        config_path.write_text(json_module.dumps(config, indent=2) + "\n")
        artifacts += (".concorde/config.json",)
    if differences and not arguments.write:
        return ToolResult("protocol-manifest", ".", "invalid", artifacts=artifacts, findings=(
            Finding("CONCORDE-PROTOCOL-MANIFEST-001", "error", PROTOCOL_MANIFEST_PATH,
                    f"tracked Protocol manifest digests differ from the current build: {differences}",
                    "Run `python -m concorde protocol-manifest --write` to accept the current build's digests."),
        ), result={"differences": differences})
    return ToolResult("protocol-manifest", ".", "success", artifacts=artifacts, result={"differences": differences})


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    arguments: argparse.Namespace | None = None
    try:
        arguments = parser.parse_args(argv)
        if arguments.tool == "protocol-manifest":
            payload = tool_envelope(_protocol_manifest(arguments))
            sys.stdout.write(canonical_json(payload))
            return exit_code(payload["status"])
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
            if tool in {"init", "configure", "context", "explore", "validate", "deliver", "docsite", "build", "protocol-manifest"}
            else "validate",
            ".",
            "failed",
            [],
            [Finding("CONCORDE-RUN-001", "error", ".concorde/config.json", str(error), "Correct the project configuration or runtime environment and retry.")],
            {},
        )
    sys.stdout.write(canonical_json(payload))
    return exit_code(payload["status"])
