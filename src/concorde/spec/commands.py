"""The spec part's ``concorde`` commands, as its part registration names them.

Each command is an entry Distribution's ``concorde`` command calls with the rest of the command
line and the project root: ``spec-validation``, ``registry``, ``docsite``, ``grant`` and ``init``
answer with Spec core's shared envelope, which Distribution prints, and ``spec-mcp`` runs the stdio
Spec MCP server, which owns standard input and output. A refused command line and an unexpected
failure are answered with a ``failed`` envelope too, so each of them prints exactly one.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path

from .diagnostics import tool_envelope
from .errors import SpecError, system_cause, unexpected
from .model import Finding, ToolResult

# The package the spec part was installed from, whose Protocol initialization reads.
PACKAGE = Path(__file__).resolve().parents[3]


class _Parser(argparse.ArgumentParser):
    """Refuses a command line with argparse's own message instead of exiting."""

    def error(self, message):
        raise SpecError(
            f"invalid command line: {self.prog}: {message}",
            "invalid_input",
            reason="the command line does not match the command's arguments",
            remediation=f"correct the command line; see `{self.prog} --help`",
        )


def _parser(name: str) -> _Parser:
    parser = _Parser(prog=f"concorde {name}")
    parser.add_argument("--format", choices=["json"], default="json")
    return parser


def _validation(words: list[str], root: Path) -> ToolResult:
    from .validation import validate_repository

    parser = _parser("spec-validation")
    parser.add_argument("target", nargs="?")
    arguments = parser.parse_args(words)
    return validate_repository(root, arguments.target)


def _registry(words: list[str], root: Path) -> ToolResult:
    from .registry import registry_command

    parser = _parser("registry")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    arguments = parser.parse_args(words)
    return registry_command(root, write=arguments.write)


def _docsite(words: list[str], root: Path) -> ToolResult:
    from .views.docsite_scaffold import apply_docsite, propose_docsite

    parser = _parser("docsite")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--propose", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--proposal")
    parser.add_argument("--title")
    parser.add_argument("--repository")
    parser.add_argument("--url")
    parser.add_argument("--base-url")
    parser.add_argument("--github-pages", action="store_true")
    arguments = parser.parse_args(words)
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


def _grant(words: list[str], root: Path) -> ToolResult:
    from .grants import grant_command

    parser = _parser("grant")
    parser.add_argument("--root")
    parser.add_argument("--modules", required=True)
    parser.add_argument("--type", dest="task_type", required=True)
    arguments = parser.parse_args(words)
    return grant_command(
        Path(arguments.root) if arguments.root else root,
        arguments.modules,
        arguments.task_type,
    )


def _init(words: list[str], root: Path) -> ToolResult:
    from .initialize import initialize

    parser = _parser("init")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--propose", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--name")
    parser.add_argument("--target", default="module.project")
    parser.add_argument(
        "--python",
        help="the project's own interpreter, which its checks run as {python} "
        "(default: .venv/bin/python or venv/bin/python when present)",
    )
    parser.add_argument("--proposal")
    arguments = parser.parse_args(words)
    if arguments.apply:
        if not arguments.proposal:
            raise SpecError(
                "init --apply requires --proposal <file>", "invalid_input", "--proposal"
            )
        try:
            proposed = json.loads(
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
            **({"python": arguments.python} if arguments.python else {}),
        }
    return ToolResult("init", ".", "success", result=initialize(root, PACKAGE, data))


def _answer(tool: str, command: Callable, words, root) -> dict:
    """The command's envelope; a refusal or an unexpected failure is a ``failed`` one."""
    try:
        return tool_envelope(command(list(words), Path(root)))
    except Exception as error:  # noqa: BLE001 -- the command boundary always answers an envelope
        return tool_envelope(ToolResult(tool, ".", "failed", error=unexpected(error)))


def spec_validation(words, root) -> dict:
    return _answer("spec-validation", _validation, words, root)


def registry(words, root) -> dict:
    return _answer("registry", _registry, words, root)


def docsite(words, root) -> dict:
    return _answer("docsite", _docsite, words, root)


def grant(words, root) -> dict:
    return _answer("grant", _grant, words, root)


def init(words, root) -> dict:
    return _answer("init", _init, words, root)


def spec_mcp(words, root) -> int:
    """The stdio Spec MCP server, which owns standard input and output and prints no envelope."""
    from .mcp.server import main

    return main()


__all__ = ["docsite", "grant", "init", "registry", "spec_mcp", "spec_validation"]
