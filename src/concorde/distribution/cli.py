"""The ``concorde`` command, composed from the registrations of the installed parts.

The command takes a global ``--project-root`` and one subcommand, which it routes to the entry of
the installed part that registers it, after loading the installed parts' code that registers
things (typed value types, trace roots, Operation and command definitions, workflows). An entry
whose registration says ``output: envelope`` answers Spec core's shared envelope, which the command
prints and exits with; any other prints its own output and answers its exit status. A command that
a part of the package registers but the project has not installed is refused with ``part_missing``
naming the part, and a command no part registers with a ``failed`` envelope.

Distribution owns ``build``, ``protocol-manifest``, ``update`` and ``project-mcp``, and adds two
steps of its own around Spec core's commands: ``spec-validation`` reports an update not validated
yet and removes its mark after a result without other errors, and ``init --apply`` brings the
glossary import of the installed ``CLAUDE.md`` block up to date.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import formats, parts

ACTOR = "concorde (Distribution)"
# Distribution's own update mark, which spec-validation reports while it is there.
UPDATE_STATE = ".concorde/update.json"


# --- refusals of the command line -----------------------------------------------------------


def part_missing(part: str, kind: str, name: str) -> dict:
    """The link refusing a command or MCP tool of a part the project has not installed."""
    what = f"`concorde {name}`" if kind == "commands" else f"the MCP tool {name}"
    return formats.link(
        ACTOR,
        "part_missing",
        f"{what} needs the {part} part, which this project has not installed",
        reason="input",
        explanation="Distribution offers only the commands and tools of the installed parts; "
        "installing a part is the developer's choice",
        options=[
            f"install the {part} part into the project: `concorde update --parts {part}`, or "
            f"`python3 <Concorde checkout>/scripts/install-concorde.py <project> --parts {part}`",
            f"do without {what}: the {part} part is optional for the parts installed",
        ],
    )


def _refuse(link: dict) -> int:
    """Print a refusal of the command line as ``{"error": <link>}`` and answer status 1."""
    sys.stdout.write(json.dumps({"error": link}, indent=2, ensure_ascii=False) + "\n")
    return 1


def _unknown(words: list[str], offered: list[str]) -> int:
    """One ``failed`` envelope for a command line naming no command of the package."""
    named = words[0] if words else None
    message = (
        f"invalid command line: concorde has no command {named!r}"
        if named
        else "invalid command line: no command named"
    )
    payload = formats.envelope(
        "concorde",
        "failed",
        error=formats.error_record(
            "invalid_input",
            message,
            reason="the command line names no command of an installed part",
            remediation=f"run one of: {', '.join(sorted(offered))}",
        ),
    )
    sys.stdout.write(formats.canonical_json(payload))
    return formats.exit_code("failed")


def _usage(offered: list[str]) -> str:
    return (
        "usage: concorde [--project-root ROOT] <command> ...\n\n"
        "commands of the installed parts:\n  " + "\n  ".join(sorted(offered)) + "\n"
    )


# --- Distribution's steps around Spec core's commands -----------------------------------------


def with_update_state(root: Path, payload: dict) -> dict:
    """A validation of a project Concorde was updated in: while `concorde update`'s mark is
    there, the project is Concorde unvalidated, which is an error; the first validation that
    passes removes the mark. Only the update sets it, so the project's own changes never do."""
    path = root / UPDATE_STATE
    if not path.is_file():
        return payload
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    commits = state.get("commits") or {}

    def named(version, commit):
        return f"{version} ({commit[:12]})" if commit else f"{version}"

    versions = (
        f"from {named(state.get('from'), commits.get('from'))} "
        f"to {named(state.get('to'), commits.get('to'))}"
    )
    if payload["status"] == "success":
        path.unlink(missing_ok=True)
        return formats.with_findings(
            payload,
            [
                formats.finding(
                    "CONCORDE-UPDATE-002",
                    "info",
                    UPDATE_STATE,
                    f"the update of Concorde {versions} is validated: the project validates "
                    "with the new Concorde",
                    "Nothing to do.",
                )
            ],
        )
    return formats.with_findings(
        payload,
        [
            formats.finding(
                "CONCORDE-UPDATE-001",
                "error",
                UPDATE_STATE,
                f"Concorde was updated {versions} and the project has not validated since: "
                "it is Concorde unvalidated until the other findings are repaired",
                "Repair the other findings and run `concorde spec-validation` again.",
            )
        ],
        status="invalid",
    )


def with_glossary_import(root: Path, payload: dict) -> dict:
    """After an ``init --apply`` that succeeded the first glossary exists: the installed
    CLAUDE.md block imports it, so every Claude Code session starts with the project's terms.
    Spec core's initialization never writes CLAUDE.md; this is Distribution's own step."""
    from .install import CLAUDE_MD, refresh_glossary

    if payload["status"] != "success":
        return payload
    try:
        refresh_glossary(root)
    except (OSError, UnicodeError) as error:
        return {
            **payload,
            "status": "failed",
            "error": formats.error_record(
                "guidance_failed",
                f"the project's Specs were initialized, but the import of its glossary could "
                f"not be added to the Concorde block of {CLAUDE_MD}",
                reason="initialization succeeded and is complete; only Distribution's "
                "amendment of the installed guidance after it failed",
                remediation="repair what the cause names, then run `concorde update` or the "
                "installer again, which installs the block with the glossary import; never run "
                "`init --apply` again, which refuses an initialized project",
                path=CLAUDE_MD,
                causes=[formats.system_cause(error, CLAUDE_MD)],
            ),
        }
    return payload


# --- Distribution's own commands --------------------------------------------------------------


class _Parser(argparse.ArgumentParser):
    """Refuses a command line with argparse's own message instead of exiting."""

    def error(self, message):
        raise _CommandLine(f"invalid command line: {self.prog}: {message}")


class _CommandLine(ValueError):
    pass


def _command_line(tool: str, message: str) -> dict:
    return formats.envelope(
        tool,
        "failed",
        error=formats.error_record(
            "invalid_input",
            message,
            reason="the command line does not match the command's arguments",
            remediation=f"correct the command line; see `concorde {tool} --help`",
        ),
    )


def _failed(tool: str, error: BaseException) -> dict:
    return formats.envelope(
        tool,
        "failed",
        error=formats.error_record(
            "unexpected_error",
            f"{type(error).__name__}: {error}",
            reason="an unexpected error ended the command",
            remediation="read the message, repair its cause and run the command again",
        ),
    )


def build(words, root) -> dict:
    """``concorde build [--check]``: render or check the generated files."""
    from .build import BuildError, check_build, write_build

    parser = _Parser(prog="concorde build")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--format", choices=["json"], default="json")
    try:
        arguments = parser.parse_args(list(words))
    except _CommandLine as error:
        return _command_line("build", str(error))
    root = Path(root)
    try:
        if arguments.check:
            current, differences = check_build(root)
            if current:
                return formats.envelope("build", "success", result={"differences": []})
            return formats.envelope(
                "build",
                "invalid",
                findings=[
                    formats.finding(
                        "CONCORDE-BUILD-001",
                        "error",
                        "generated/",
                        f"Build outputs are stale or missing: {', '.join(differences)}",
                        "Run `python3 scripts/concorde.py build` to refresh the generated "
                        "outputs.",
                    )
                ],
                result={"differences": list(differences)},
            )
        result = write_build(root)
        return formats.envelope(
            "build",
            "success",
            artifacts=[output.path for output in result.outputs]
            + ["generated/build-manifest.json"],
            result={"outputs": len(result.outputs)},
        )
    except BuildError as error:
        return formats.envelope(
            "build",
            "invalid",
            findings=[
                formats.finding(
                    "CONCORDE-BUILD-001",
                    "error",
                    "prompts",
                    str(error),
                    "Repair the prompt, workflow or part registration source and rebuild.",
                )
            ],
        )
    except Exception as error:  # noqa: BLE001 -- the command boundary always answers an envelope
        return _failed("build", error)


def protocol_manifest(words, root) -> dict:
    """``concorde protocol-manifest [--write] [--bind-project]``: reconcile the tracked Protocol
    manifest with the current build, as Distribution's Spec describes.

    With neither flag this only reports whether ``protocol/manifest.json`` matches the current
    ``generated/protocol/...`` build; ``--write`` accepts the current build's digests into the
    tracked manifest; ``--bind-project`` binds ``.concorde/config.json``'s ``protocol`` to the
    (possibly just rewritten) manifest's version and digest and refreshes this checkout's
    Protocol copy.
    """
    from .build import (
        PROTOCOL_MANIFEST_PATH,
        BuildError,
        recompute_protocol_manifest,
        verify_fresh,
    )
    from .project_defaults import PROTOCOL_DIR, CopyError, binding, write_protocol_copy

    parser = _Parser(prog="concorde protocol-manifest")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--bind-project", action="store_true")
    parser.add_argument("--format", choices=["json"], default="json")
    try:
        arguments = parser.parse_args(list(words))
    except _CommandLine as error:
        return _command_line("protocol-manifest", str(error))
    root = Path(root)
    try:
        verify_fresh(root)
        updated = recompute_protocol_manifest(root)
    except BuildError as error:
        return formats.envelope(
            "protocol-manifest",
            "invalid",
            findings=[
                formats.finding(
                    "CONCORDE-PROTOCOL-MANIFEST-001",
                    "error",
                    PROTOCOL_MANIFEST_PATH,
                    str(error),
                    "Run `python -m concorde build` to refresh generated/protocol/ outputs.",
                )
            ],
        )
    try:
        manifest_path = root / PROTOCOL_MANIFEST_PATH
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
        differences = [
            item["path"]
            for item, fresh in zip(current["assets"], updated["assets"], strict=True)
            if item["digest"] != fresh["digest"]
        ]
        artifacts: list[str] = []
        if arguments.write and differences:
            manifest_path.write_text(json.dumps(updated, indent=2) + "\n")
            artifacts.append(PROTOCOL_MANIFEST_PATH)
        if arguments.bind_project:
            # The source checkout has no installer run: bind the configuration to the current
            # manifest and refresh its Protocol copy under .concorde/protocol/ from the build.
            config_path = root / ".concorde/config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["protocol"] = binding(manifest_path.read_bytes())
            config_path.write_text(json.dumps(config, indent=2) + "\n")
            artifacts.append(".concorde/config.json")
            try:
                write_protocol_copy(root, root)
            except CopyError as error:
                return formats.envelope(
                    "protocol-manifest",
                    "failed",
                    artifacts=artifacts,
                    result={"differences": differences},
                    error=formats.error_record(
                        error.code,
                        str(error),
                        reason="the Protocol copy would not match the current build",
                        remediation="accept the build's digests with `--write --bind-project`",
                        path=PROTOCOL_DIR,
                    ),
                )
            artifacts.append(PROTOCOL_DIR + "/")
    except Exception as error:  # noqa: BLE001 -- the command boundary always answers an envelope
        return _failed("protocol-manifest", error)
    if differences and not arguments.write:
        return formats.envelope(
            "protocol-manifest",
            "invalid",
            artifacts=artifacts,
            findings=[
                formats.finding(
                    "CONCORDE-PROTOCOL-MANIFEST-001",
                    "error",
                    PROTOCOL_MANIFEST_PATH,
                    "tracked Protocol manifest digests differ from the current build: "
                    f"{differences}",
                    "Run `python -m concorde protocol-manifest --write` to accept the current "
                    "build's digests.",
                )
            ],
            result={"differences": differences},
        )
    return formats.envelope(
        "protocol-manifest",
        "success",
        artifacts=artifacts,
        result={"differences": differences},
    )


def update_main(words, root=None) -> int:
    """`concorde update [--from <checkout>]`: run the installer of the Concorde checkout this
    project was installed from (or ``--from``) in update mode."""
    import subprocess

    from .install import ArgumentParser, InstallError, refusal

    parser = ArgumentParser(
        prog="concorde update",
        description="Update the installed Concorde from the checkout its receipt names. Start no "
        "other concorde command, in any worktree of the project, until the update ends: it is "
        "refused only for runs already running when it checks, and a command started meanwhile "
        "may load partly replaced code.",
    )
    parser.add_argument("--from", dest="source")
    parser.add_argument(
        "--parts",
        action="append",
        metavar="PART[,PART...]",
        help="parts to install besides those the receipt names, with the parts they depend on",
    )
    parser.add_argument("--project-root", default=str(root or "."))
    try:
        arguments = parser.parse_args(list(words))
    except InstallError as error:
        sys.stdout.write(
            json.dumps(
                {"error": refusal(error.code, str(error), actor="concorde update")},
                indent=2,
            )
            + "\n"
        )
        return 1
    project = Path(arguments.project_root).resolve()
    try:
        receipt = json.loads((project / ".concorde/install.json").read_text())
    except (OSError, ValueError) as error:
        receipt = {}
        problem = f"{project / '.concorde/install.json'} cannot be read ({error})"
    else:
        problem = None
    source = arguments.source or receipt.get("source")
    installer = Path(source or ".") / "scripts/install-concorde.py"
    if not source or not installer.is_file():
        detail = problem or (
            "the receipt names no Concorde checkout to update from"
            if not source
            else f"{installer} does not exist"
        )
        sys.stdout.write(
            json.dumps(
                {
                    "error": refusal(
                        "update_source_missing",
                        f"{detail}; pass the checkout with --from",
                        actor="concorde update",
                    )
                },
                indent=2,
            )
            + "\n"
        )
        return 1
    command = [sys.executable, str(installer), str(project), "--update"]
    for value in arguments.parts or []:
        command += ["--parts", value]
    return subprocess.run(command, check=False).returncode


# --- routing ----------------------------------------------------------------------------------


def _global(words: list[str]) -> tuple[Path, list[str]]:
    """The global ``--project-root`` and the words after it."""
    root = Path(".")
    while words and words[0].startswith("--project-root"):
        if words[0] == "--project-root" and len(words) > 1:
            root, words = Path(words[1]), words[2:]
        elif words[0].startswith("--project-root="):
            root, words = Path(words[0].split("=", 1)[1]), words[1:]
        else:
            break
    return root, words


def main(argv: Sequence[str] | None = None) -> int:
    words = list(sys.argv[1:] if argv is None else argv)
    root, words = _global(words)
    try:
        installed = parts.installed()
    except parts.RegistrationError as error:
        return _refuse(
            formats.link(
                ACTOR,
                error.code,
                str(error),
                reason="input",
                explanation="the command is composed from the part registrations, and one of "
                "them cannot be served",
                options=[
                    "repair the registration and rebuild, or install Concorde again"
                ],
            )
        )
    commands = {
        item["name"]: (registration, item)
        for registration in installed.values()
        for item in registration.data["commands"]
    }
    if words and words[0] in ("-h", "--help"):
        sys.stdout.write(_usage(list(commands)))
        return 0
    if not words:
        return _unknown(words, list(commands))
    name, rest = words[0], words[1:]
    found = commands.get(name)
    if found is None:
        owner = parts.owner_of("commands", name)
        if owner is not None and owner not in installed:
            return _refuse(part_missing(owner, "commands", name))
        return _unknown(words, list(commands))
    owners = sorted(
        registration.part
        for registration in installed.values()
        if any(item["name"] == name for item in registration.data["commands"])
    )
    if len(owners) > 1:
        return _refuse(
            formats.link(
                ACTOR,
                "name_conflict",
                f"the command {name} is registered by {' and '.join(owners)}",
                reason="input",
                explanation="two parts registering one name are never resolved by order",
                options=["rebuild, which refuses the conflict, and install again"],
            )
        )
    registration, command = found
    if registration.part != "distribution":
        parts.load(installed)
    entry = registration.entry(command["entry"])
    if command["output"] != "envelope":
        return int(entry(rest, root) or 0)
    payload = entry(rest, root)
    if name == "spec-validation":
        payload = with_update_state(root, payload)
    elif name == "init" and "--apply" in rest:
        payload = with_glossary_import(root, payload)
    sys.stdout.write(formats.canonical_json(payload))
    return formats.exit_code(payload["status"])


__all__ = [
    "build",
    "main",
    "part_missing",
    "protocol_manifest",
    "update_main",
    "with_update_state",
]
