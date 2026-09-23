"""Stable command-line interface for installed Concorde Tools."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ..spec.diagnostics import canonical_json, envelope, exit_code, tool_envelope
from ..spec.model import Finding, ToolResult


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="concorde")
    parser.add_argument("--project-root", default=".")
    subparsers = parser.add_subparsers(dest="tool", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("target", nargs="?")
    validate.add_argument("--format", choices=["json"], default="json")

    registry = subparsers.add_parser("registry")
    registry_mode = registry.add_mutually_exclusive_group(required=True)
    registry_mode.add_argument("--write", action="store_true")
    registry_mode.add_argument("--check", action="store_true")
    registry.add_argument("--format", choices=["json"], default="json")

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

    check_package = subparsers.add_parser("check-package")
    check_package.add_argument("--format", choices=["json"], default="json")

    build = subparsers.add_parser("build")
    build.add_argument("--check", action="store_true")
    build.add_argument("--format", choices=["json"], default="json")

    protocol_manifest = subparsers.add_parser("protocol-manifest")
    protocol_manifest.add_argument("--write", action="store_true")
    protocol_manifest.add_argument("--bind-project", action="store_true")
    protocol_manifest.add_argument("--format", choices=["json"], default="json")

    selection = subparsers.add_parser("select-session")
    selection_mode = selection.add_mutually_exclusive_group(required=True)
    selection_mode.add_argument("--mode", choices=["test"])
    selection_mode.add_argument("--verify", type=Path)
    selection.add_argument("--pi-entry", type=Path)
    selection.add_argument("--runtime", type=Path)
    selection.add_argument("--output", type=Path)

    status = subparsers.add_parser("status")
    status.add_argument("--register", type=Path)
    status.add_argument("--task")
    status.add_argument(
        "--mode", choices=["operation", "maintenance", "direct"], default="maintenance"
    )
    status.add_argument("--change-id")
    status.add_argument("--child")
    status.add_argument(
        "--phase", choices=["maintenance", "test", "task"], default="maintenance"
    )
    status.add_argument("--release", action="store_true")
    status.add_argument("--manual-merge")
    status.add_argument("--cleanup", choices=["pending", "retained", "removed"])

    return parser


def dispatch(arguments: argparse.Namespace) -> ToolResult:
    root = Path(arguments.project_root)
    if arguments.tool == "check-package":
        from collections import Counter

        from .package_validation import validate_package

        findings = tuple(validate_package(root))
        counts = Counter(finding.severity for finding in findings)
        return ToolResult(
            "check-package",
            ".",
            "invalid" if counts["error"] else "success",
            findings=findings,
        )
    if arguments.tool == "status":
        from ..delivery.manual_merge import record_manual_merge
        from ..harness.change_worktree import ensure_change
        from ..harness.status_store import all_status, coordinate_child, primary_root
        from ..spec.repository import SpecError

        if root.resolve() != primary_root(root) and any(
            (arguments.register, arguments.child)
        ):
            raise SpecError(
                "status coordination requires primary", "primary_session_required"
            )
        if arguments.register:
            if primary_root(arguments.register) != root.resolve():
                raise SpecError(
                    "registered candidate belongs to another repository",
                    "workspace_mismatch",
                )
            if not arguments.task:
                raise SpecError("registration requires a task goal", "invalid_input")
            result = ensure_change(
                arguments.register.resolve(),
                task={"task": arguments.task},
                change_id=arguments.change_id,
                allow_primary=True,
                mode=arguments.mode,
            )
        elif arguments.child and arguments.change_id:
            result = coordinate_child(
                root,
                arguments.change_id,
                child_id=arguments.child,
                phase=arguments.phase,
                release=arguments.release,
            )
        elif (arguments.manual_merge or arguments.cleanup) and arguments.change_id:
            # Without --manual-merge, --cleanup updates only the outcome of an
            # already recorded manual merge; it is never silently ignored.
            result = record_manual_merge(
                root,
                arguments.change_id,
                commit=arguments.manual_merge,
                cleanup=arguments.cleanup or "pending",
            )
        elif any(
            (
                arguments.child,
                arguments.manual_merge,
                arguments.release,
                arguments.cleanup,
            )
        ):
            raise SpecError("status update requires a change ID", "invalid_input")
        else:
            result = {"tasks": all_status(root)}
        return ToolResult("status", ".", "success", result=result)
    if arguments.tool == "select-session":
        from .session_selection import load_selection, save_selection, select_session
        from .build import BuildError

        if arguments.verify:
            if arguments.pi_entry or arguments.runtime or arguments.output:
                raise BuildError(
                    "--verify accepts only a saved selection, not replacement inputs"
                )
            selected = load_selection(root, arguments.verify)
        else:
            if arguments.runtime is None or arguments.pi_entry is None:
                raise BuildError("selection requires --pi-entry and --runtime")
            selected = select_session(
                root, pi_entry=arguments.pi_entry, runtime=arguments.runtime
            )
            if arguments.output:
                save_selection(root, arguments.output, selected)
        return ToolResult("select-session", ".", "success", result=selected)
    if arguments.tool == "docsite":
        from ..views.docsite_scaffold import apply_docsite, propose_docsite

        if arguments.apply:
            if not arguments.proposal:
                return ToolResult(
                    "docsite",
                    ".",
                    "invalid",
                    findings=(
                        Finding(
                            "CONCORDE-DOCSITE-008",
                            "error",
                            "docsite/site.json",
                            "--apply requires --proposal.",
                            "Pass a project-relative accepted proposal JSON file.",
                        ),
                    ),
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
                current, differences = check_build(root)
                if current:
                    return ToolResult(
                        "build", ".", "success", result={"differences": []}
                    )
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
                            "Run `python -m concorde build` to refresh private Pi and runtime outputs.",
                        ),
                    ),
                    result={"differences": list(differences)},
                )
            result = write_build(root)
            artifacts = tuple(output.path for output in result.outputs) + (
                "generated/build-manifest.json",
            )
            return ToolResult(
                "build",
                ".",
                "success",
                artifacts=artifacts,
                result={"outputs": len(result.outputs)},
            )
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
                        "Repair the prompt, role, or operation guidance source and rebuild.",
                    ),
                ),
            )
    if arguments.tool == "registry":
        from ..spec.registry import registry_command

        return registry_command(root, write=arguments.write)
    from ..spec.validation import validate_repository

    return validate_repository(root, arguments.target)


def _protocol_manifest(arguments: argparse.Namespace) -> ToolResult:
    """Recompute tracked Protocol asset digests from the current build (developer-only).

    With neither flag this only reports whether ``protocol/manifest.json`` matches the current
    ``generated/protocol/...`` build; ``--write`` accepts the current build's digests into the tracked manifest;
    ``--bind-project`` pins ``.concorde/config.json``'s ``protocol`` binding to the (possibly just
    rewritten) manifest's version and digest.
    """

    import json as json_module

    from ..spec.repository import digest as digest_bytes
    from .build import (
        PROTOCOL_MANIFEST_PATH,
        BuildError,
        recompute_protocol_manifest,
        verify_fresh,
    )

    root = Path(arguments.project_root)
    try:
        verify_fresh(root)
        updated = recompute_protocol_manifest(root)
    except BuildError as error:
        return ToolResult(
            "protocol-manifest",
            ".",
            "invalid",
            findings=(
                Finding(
                    "CONCORDE-PROTOCOL-MANIFEST-001",
                    "error",
                    PROTOCOL_MANIFEST_PATH,
                    str(error),
                    "Run `python -m concorde build` to refresh generated/protocol/ outputs.",
                ),
            ),
        )
    manifest_path = root / PROTOCOL_MANIFEST_PATH
    current = json_module.loads(manifest_path.read_text(encoding="utf-8"))
    differences = [
        item["path"]
        for item, fresh in zip(current["assets"], updated["assets"], strict=True)
        if item["digest"] != fresh["digest"]
    ]
    artifacts: tuple[str, ...] = ()
    if arguments.write and differences:
        manifest_path.write_text(json_module.dumps(updated, indent=2) + "\n")
        artifacts += (PROTOCOL_MANIFEST_PATH,)
    if arguments.bind_project:
        # The source checkout has no installer run: bind the configuration to the current manifest
        # and refresh its Protocol copy under .concorde/protocol/ from the current build.
        from .project_defaults import PROTOCOL_DIR, write_protocol_copy

        config_path = root / ".concorde/config.json"
        config = json_module.loads(config_path.read_text(encoding="utf-8"))
        config["protocol"] = {
            "version": updated["version"],
            "digest": digest_bytes(manifest_path.read_bytes()),
        }
        config_path.write_text(json_module.dumps(config, indent=2) + "\n")
        write_protocol_copy(root, root)
        artifacts += (".concorde/config.json", PROTOCOL_DIR + "/")
    if differences and not arguments.write:
        return ToolResult(
            "protocol-manifest",
            ".",
            "invalid",
            artifacts=artifacts,
            findings=(
                Finding(
                    "CONCORDE-PROTOCOL-MANIFEST-001",
                    "error",
                    PROTOCOL_MANIFEST_PATH,
                    f"tracked Protocol manifest digests differ from the current build: {differences}",
                    "Run `python -m concorde protocol-manifest --write` to accept the current build's digests.",
                ),
            ),
            result={"differences": differences},
        )
    return ToolResult(
        "protocol-manifest",
        ".",
        "success",
        artifacts=artifacts,
        result={"differences": differences},
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    arguments: argparse.Namespace | None = None
    try:
        arguments = parser.parse_args(argv)
        if arguments.tool == "protocol-manifest":
            payload = tool_envelope(_protocol_manifest(arguments))
            sys.stdout.write(canonical_json(payload))
            return exit_code(payload["status"])
        if arguments.tool == "docsite":
            from ..harness.change_worktree import require_isolated_worktree

            require_isolated_worktree(
                arguments.project_root,
                allow_primary_worktree=getattr(
                    arguments, "allow_primary_worktree", False
                ),
            )
        result = dispatch(arguments)
        payload = tool_envelope(result)
    except Exception as error:  # noqa: BLE001 -- command boundary always returns the normative envelope
        tool = (
            arguments.tool
            if arguments is not None
            else (argv[0] if argv else "validate")
        )
        payload = envelope(
            tool
            if tool
            in {
                "validate",
                "registry",
                "docsite",
                "build",
                "check-package",
                "protocol-manifest",
                "status",
                "select-session",
            }
            else "validate",
            ".",
            "failed",
            [],
            [
                Finding(
                    "CONCORDE-RUN-001",
                    "error",
                    ".concorde/config.json",
                    str(error),
                    "Correct the project configuration or runtime environment and retry.",
                )
            ],
            {},
        )
    sys.stdout.write(canonical_json(payload))
    return exit_code(payload["status"])
