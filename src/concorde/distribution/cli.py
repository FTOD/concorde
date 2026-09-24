"""Stable command-line interface for installed Concorde Tools."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from ..spec.diagnostics import canonical_json, envelope, exit_code, tool_envelope
from ..spec.model import Finding, ToolResult


class _Parser(argparse.ArgumentParser):
    """Refuses a command line with argparse's own message instead of exiting."""

    def error(self, message):
        from ..spec.errors import SpecError

        raise SpecError(
            f"invalid command line: {self.prog}: {message}",
            "invalid_input",
            reason="the command line does not match the command's arguments",
            remediation=f"correct the command line; see `{self.prog} --help`",
        )


def create_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="concorde")
    parser.add_argument("--project-root", default=".")
    subparsers = parser.add_subparsers(dest="tool", required=True, parser_class=_Parser)

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
    docsite.add_argument("--format", choices=["json"], default="json")

    grant = subparsers.add_parser("grant")
    grant.add_argument("--root")
    grant.add_argument("--modules", required=True)
    grant.add_argument("--type", dest="task_type", required=True)
    grant.add_argument("--format", choices=["json"], default="json")

    subparsers.add_parser("spec-mcp")

    init = subparsers.add_parser("init")
    init_mode = init.add_mutually_exclusive_group(required=True)
    init_mode.add_argument("--propose", action="store_true")
    init_mode.add_argument("--apply", action="store_true")
    init.add_argument("--name")
    init.add_argument("--target", default="module.project")
    init.add_argument("--proposal")
    init.add_argument("--format", choices=["json"], default="json")

    build = subparsers.add_parser("build")
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
                            "Run `python3 scripts/concorde.py build` to refresh the generated outputs.",
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
    if arguments.tool == "grant":
        from ..spec.grants import grant_command

        return grant_command(
            Path(arguments.root) if arguments.root else root,
            arguments.modules,
            arguments.task_type,
        )
    if arguments.tool == "init":
        import json as json_module

        from ..spec.errors import SpecError, system_cause
        from ..spec.initialize import initialize

        package = Path(__file__).resolve().parents[3]
        if arguments.apply:
            if not arguments.proposal:
                raise SpecError(
                    "init --apply requires --proposal <file>",
                    "invalid_input",
                    "--proposal",
                )
            try:
                proposed = json_module.loads(
                    (root / arguments.proposal).read_text(encoding="utf-8")
                )
            except (OSError, ValueError) as error:
                raise SpecError(
                    f"the proposal file {arguments.proposal} cannot be read as JSON",
                    "invalid_input",
                    "--proposal",
                    path=arguments.proposal,
                    causes=[system_cause(error, path=arguments.proposal)],
                ) from error
            if not isinstance(proposed, dict) or not {
                "proposal",
                "proposal_digest",
            } <= set(proposed):
                raise SpecError(
                    f"the proposal file {arguments.proposal} must hold the proposal and its "
                    "proposal_digest, as `concorde init --propose` prints them under result",
                    "invalid_proposal",
                    "--proposal",
                    path=arguments.proposal,
                )
            data = {
                "action": "apply",
                "proposal": proposed["proposal"],
                "proposal_digest": proposed["proposal_digest"],
            }
        else:
            if not arguments.name:
                raise SpecError(
                    "init --propose requires --name <project name>",
                    "invalid_input",
                    "--name",
                )
            data = {
                "action": "propose",
                "name": arguments.name,
                "target_id": arguments.target,
            }
        return ToolResult(
            "init", ".", "success", result=initialize(root, package, data)
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


TOOLS = frozenset(
    {
        "validate",
        "registry",
        "docsite",
        "grant",
        "spec-mcp",
        "init",
        "build",
        "protocol-manifest",
    }
)


def _failed(tool: str, error: BaseException) -> dict:
    """The envelope of a command that raised, with Spec tooling's record of the error."""
    from ..spec.errors import unexpected

    return envelope(tool, ".", "failed", [], [], {}, unexpected(error))


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    words = list(sys.argv[1:] if argv is None else argv)
    # Tasks and Operations own their command lines and output; they print no envelope.
    if words and words[0] == "task":
        from ..tasks.cli import main as task_main

        return task_main(words[1:])
    if words and words[0] == "workers":
        from ..harness.models import main as workers_main

        return workers_main(words[1:])
    if words and words[0] == "issues":
        import runpy

        script = Path(__file__).resolve().parents[3] / "scripts/issues.py"
        return runpy.run_path(str(script))["main"](words[1:])
    if words and words[0] == "run":
        from ..operations.host import main as run_main

        return run_main(words[1:])
    requested = next((word for word in words if word in TOOLS), "validate")
    arguments: argparse.Namespace | None = None
    try:
        try:
            arguments = parser.parse_args(words)
        except SystemExit as exit_:
            # --help ends normally; a refused command line raises ValueError from the parser
            # and still prints exactly one envelope rather than only argparse's usage text.
            if exit_.code in (0, None):
                raise
            from ..spec.errors import SpecError

            raise SpecError(
                f"invalid command line: {' '.join(words)}", "invalid_input"
            ) from None
        if arguments.tool == "spec-mcp":
            # The stdio MCP session owns standard output; it prints no envelope.
            from ..spec_mcp.server import main as serve

            return serve()
        if arguments.tool == "protocol-manifest":
            payload = tool_envelope(_protocol_manifest(arguments))
            sys.stdout.write(canonical_json(payload))
            return exit_code(payload["status"])
        result = dispatch(arguments)
        payload = tool_envelope(result)
    except Exception as error:  # noqa: BLE001 -- command boundary always returns the normative envelope
        tool = arguments.tool if arguments is not None else requested
        payload = _failed(tool if tool in TOOLS else "validate", error)
    sys.stdout.write(canonical_json(payload))
    return exit_code(payload["status"])
