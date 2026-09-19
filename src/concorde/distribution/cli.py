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
    build.add_argument(
        "--integration", choices=["claude", "codex", "pi", "all"], default="all"
    )
    build.add_argument("--check", action="store_true")
    build.add_argument("--format", choices=["json"], default="json")

    protocol_manifest = subparsers.add_parser("protocol-manifest")
    protocol_manifest.add_argument("--write", action="store_true")
    protocol_manifest.add_argument("--bind-project", action="store_true")
    protocol_manifest.add_argument("--format", choices=["json"], default="json")

    skills = subparsers.add_parser("skills")
    skills.add_argument(
        "--write",
        action="store_true",
        help="render the tracked published Skills under skills/ from prompts/skills/",
    )
    skills.add_argument("--check", action="store_true")
    skills.add_argument("--format", choices=["json"], default="json")

    selection = subparsers.add_parser("select-session")
    selection.add_argument(
        "--mode", choices=["maintenance", "test", "task"], required=True
    )
    selection.add_argument("--skill", action="append", default=[])
    selection.add_argument("--runtime", required=True)
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
    status.add_argument(
        "--cleanup", choices=["pending", "retained", "removed"], default="pending"
    )

    migration = subparsers.add_parser("migrate-status")
    migration.add_argument("--apply", action="store_true")

    usage = subparsers.add_parser("usage")
    usage.add_argument(
        "--run",
        help="root invocation id of one operation run; default: every recorded run",
    )
    usage.add_argument("--format", choices=["json"], default="json")
    return parser


def dispatch(arguments: argparse.Namespace) -> ToolResult:
    root = Path(arguments.project_root)
    if arguments.tool == "status":
        from ..harness.change_worktree import ensure_change
        from ..harness.status_store import (
            all_status,
            coordinate_child,
            primary_root,
            record_manual_merge,
        )
        from ..spec.repository import SpecError

        if root.resolve() != primary_root(root) and any(
            (arguments.register, arguments.child, arguments.manual_merge)
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
        elif arguments.manual_merge and arguments.change_id:
            result = record_manual_merge(
                root,
                arguments.change_id,
                commit=arguments.manual_merge,
                cleanup=arguments.cleanup,
            )
        elif any((arguments.child, arguments.manual_merge, arguments.release)):
            raise SpecError("status update requires a change ID", "invalid_input")
        else:
            result = {"tasks": all_status(root)}
        return ToolResult("status", ".", "success", result=result)
    if arguments.tool == "select-session":
        from .session_selection import select_session

        selected = select_session(
            root,
            mode=arguments.mode,
            skill_paths=arguments.skill,
            runtime=Path(arguments.runtime),
        )
        if arguments.output:
            from ..harness.status_store import atomic_write
            from ..harness.change_worktree import (
                _exclude_control_files,
                repository_lock,
            )
            from .build import BuildError
            import json

            try:
                relative = arguments.output.relative_to(root.resolve()).as_posix()
            except ValueError as error:
                raise BuildError(
                    "selection output must remain in its candidate"
                ) from error
            if not relative.startswith(".concorde/work/"):
                raise BuildError(
                    "selection output belongs only in candidate .concorde/work scratch"
                )
            with repository_lock(root):
                _exclude_control_files(root)
                atomic_write(
                    root.resolve(),
                    relative,
                    (json.dumps(selected, sort_keys=True) + "\n").encode(),
                )
        return ToolResult("select-session", ".", "success", result=selected)
    if arguments.tool == "migrate-status":
        from ..harness.status_store import migrate_legacy

        return ToolResult(
            "migrate-status",
            ".",
            "success",
            result=migrate_legacy(root, apply=arguments.apply),
        )
    if arguments.tool == "usage":
        from ..harness.usage import read_usage, summarize_usage

        records = read_usage(root, arguments.run)
        if arguments.run and not records:
            return ToolResult(
                "usage",
                ".",
                "invalid",
                findings=(
                    Finding(
                        "CONCORDE-USAGE-001",
                        "error",
                        f".concorde/runs/{arguments.run}/usage.jsonl",
                        "no usage records exist for this run",
                        "Pass the root invocation id printed by the operation result, or omit --run.",
                    ),
                ),
            )
        return ToolResult(
            "usage",
            ".",
            "success",
            result={
                "runs": sorted(
                    {
                        run_id
                        for r in records
                        if isinstance(r, dict)
                        and isinstance(run_id := r.get("root_invocation_id"), str)
                        and run_id
                    }
                ),
                "records": len(records),
                **summarize_usage(records),
            },
        )
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
                current, differences = check_build(root, arguments.integration)
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
                            "Run `python -m concorde build` to refresh generated/ outputs and "
                            "`python -m concorde skills --write` for the tracked skills/.",
                        ),
                    ),
                    result={"differences": list(differences)},
                )
            result = write_build(root, arguments.integration)
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
                        "Repair the prompt, role, or skill source and rebuild.",
                    ),
                ),
            )
    if arguments.tool == "skills":
        return _published_skills(root, arguments)
    from ..spec.validation import validate_repository

    return validate_repository(root, arguments.target)


def _published_skills(root: Path, arguments: argparse.Namespace) -> ToolResult:
    """Check or write the tracked published Skills (developer-only).

    ``skills/`` is tracked content that the Agent Skills CLI installs into projects, so unlike
    ``generated/`` it changes only through this explicit step: ``--write`` renders every public
    Operation's published Skill from its ``prompts/skills/`` source; without it (or with
    ``--check``) the current files are compared with a fresh render and nothing is written.
    """
    from .build import (
        PUBLISHED_SKILLS_ROOT,
        BuildError,
        check_published_skills,
        write_published_skills,
    )

    try:
        if arguments.write:
            outputs = write_published_skills(root)
            return ToolResult(
                "skills",
                ".",
                "success",
                artifacts=tuple(output.path for output in outputs),
                result={"outputs": len(outputs)},
            )
        current, differences = check_published_skills(root)
    except BuildError as error:
        return ToolResult(
            "skills",
            ".",
            "invalid",
            findings=(
                Finding(
                    "CONCORDE-SKILLS-001",
                    "error",
                    "prompts/skills",
                    str(error),
                    "Repair the Skill source or its includes and rerun `skills --write`.",
                ),
            ),
        )
    if current:
        return ToolResult("skills", ".", "success", result={"differences": []})
    return ToolResult(
        "skills",
        ".",
        "invalid",
        findings=(
            Finding(
                "CONCORDE-SKILLS-001",
                "error",
                f"{PUBLISHED_SKILLS_ROOT}/",
                f"Published Skills are stale, missing or retired: {', '.join(differences)}",
                "Run `python -m concorde skills --write` and commit skills/ with its sources; "
                "delete the directory of a retired Skill.",
            ),
        ),
        result={"differences": list(differences)},
    )


def _protocol_manifest(arguments: argparse.Namespace) -> ToolResult:
    """Recompute tracked Protocol asset digests from the current build (developer-only).

    Mirrors the former ``sync-protocol-assets.py --bind-project``: with neither flag this only
    reports whether ``protocol/manifest.json`` matches the current ``generated/protocol/...``
    build; ``--write`` accepts the current build's digests into the tracked manifest;
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
            from ..harness.worktree import require_isolated_worktree

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
                "docsite",
                "build",
                "protocol-manifest",
                "skills",
                "usage",
                "status",
                "select-session",
                "migrate-status",
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
