"""The process that answers one call of the project MCP server, and the tools it presents: those
the installed parts register.

The server runs no tool in its own process: each call runs ``concorde project-mcp --call <tool>`` of
the primary worktree (or, for a tool whose registration names the session's worktree, of that
worktree) as a process of its own (``serve_call`` here), so the answer is always the one of the
Concorde code that ``concorde`` runs at the time of the call, however long the session has been
running. The call's arguments and the session's provenance arrive as one JSON object on standard
input; the answer leaves as one JSON line on standard output.

The host answers none of the tools itself. It loads the installed parts' registering code and calls
the entry the tool's registration names with the call, ``tool`` added, and passes on the part's
answer, ``{"value"}`` or ``{"error": <link>}``, unchanged. A tool of a part the project has not
installed is refused with ``part_missing`` naming the part, a tool no part registers with
``invalid_input``. What the server must do after the answer, the part leaves in it: ``watch``, a
``concorde`` command to run and watch for a channel event, and, for a tool registered as
``long_work``, ``handover``, the command the call's process becomes holding the locks it took
(Tracing's "Handing a lock on"), with ``work``, what the server watches of it.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
from pathlib import Path

from .. import formats, parts

ACTOR = "Concorde project MCP server"
# Opens the server's instructions; each installed part adds its own sentence.
INSTRUCTIONS = (
    "Concorde's project MCP server: the tools the project's installed Concorde parts register, "
    "each call answered fresh by the Concorde the primary worktree's `concorde` runs at that "
    "moment. When this server is loaded as a channel, events arrive as "
    '<channel source="concorde" event="...">: wait_done, wait_failed or merge_ended, with '
    "the task, run or lock in the attributes and the answer or output in the body; act on them "
    "as on a finished background command. Every refusal is an error chain link: read it whole."
)


class Refusal(Exception):
    """A tool call refused with an error link."""

    def __init__(self, link: dict):
        super().__init__(link["detail"])
        self.link = link


def own(tool: str, code: str, detail: str, *, reason="input", explanation=""):
    return Refusal(
        formats.link(
            f"{ACTOR} ({tool})",
            code,
            detail,
            reason=reason,
            explanation=explanation
            or "the call is not one the server can pass on to an installed part",
        )
    )


def presented(
    installed: dict | None = None,
) -> dict[str, tuple[parts.Registration, dict]]:
    """Every tool the installed parts register whose required parts are installed too, by name:
    its registration and the tool's entry in it."""
    installed = parts.installed() if installed is None else installed
    return {
        tool["name"]: (registration, tool)
        for registration in parts.ordered(installed)
        for tool in registration.data["mcp_tools"]
        if all(name in installed for name in tool["requires"])
    }


def listing(installed: dict | None = None) -> list[dict]:
    """The tools as ``tools/list`` gives them, each with the definition its part gives."""
    found = []
    for name, (registration, _) in presented(installed).items():
        definitions = registration.entry(registration.data["mcp_definitions"])
        found.append({"name": name, **definitions[name]})
    return found


def serving(installed: dict | None = None) -> dict[str, dict]:
    """How the server serves each tool, as its registration says."""
    return {
        name: {key: tool[key] for key in ("worktree", "long_work", "threaded")}
        for name, (_, tool) in presented(installed).items()
    }


def instructions(installed: dict | None = None) -> str:
    """The server's instructions: its own, then each installed part's."""
    installed = parts.installed() if installed is None else installed
    return " ".join(
        [INSTRUCTIONS]
        + [
            registration.data["mcp_instructions"]
            for registration in parts.ordered(installed)
            if registration.data["mcp_instructions"]
        ]
    )


def digest(tools: list[dict]) -> str:
    """The digest of a tool listing, by which the server notices that the tools changed."""
    text = json.dumps(tools, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def describe() -> dict:
    """What ``concorde project-mcp --tools`` prints: the tools, their digest, how each is served
    and the server's instructions."""
    installed = parts.installed()
    parts.load(installed)
    tools = listing(installed)
    return {
        "tools": tools,
        "digest": digest(tools),
        "serving": serving(installed),
        "instructions": instructions(installed),
    }


def answer(name: str, envelope: dict) -> tuple[dict, dict | None]:
    """One call's reply, ``{"value"}`` or ``{"error"}`` with the digest of this code's tools and
    what the part asks the server to do afterwards; and the hand-over, when the call's process is
    to become the long work it started."""
    installed = parts.installed()
    tools = presented(installed)
    try:
        parts.load(installed)
        listed = digest(listing(installed))
    except Exception as failure:  # noqa: BLE001 -- every failure is a detailed error link
        return {
            "error": formats.from_exception(
                f"{ACTOR} ({name})",
                failure,
                explanation="the installed parts' code could not be loaded, so no tool can answer",
            )
        }, None
    try:
        if not isinstance(envelope.get("primary"), str) or not isinstance(
            envelope.get("where"), str
        ):
            raise own(
                str(name),
                "invalid_input",
                "the call's input lacks the session's provenance: the primary worktree and the "
                "session's folder",
                reason="environment",
                explanation="only the project MCP server starts a call's process, and it always "
                "passes the primary worktree and the session's folder",
            )
        found = tools.get(name)
        if found is None:
            from ..cli import part_missing

            owner = parts.owner_of("mcp_tools", name)
            if owner is not None and owner not in installed:
                raise Refusal(part_missing(owner, "mcp_tools", name))
            # A tool of an installed part that requires a part the project has not installed.
            for registration in installed.values():
                for tool in registration.data["mcp_tools"]:
                    absent = [
                        item for item in tool["requires"] if item not in installed
                    ]
                    if tool["name"] == name and absent:
                        raise Refusal(part_missing(absent[0], "mcp_tools", name))
            raise own(
                str(name),
                "invalid_input",
                f"there is no tool {name!r}; the tools are {', '.join(tools)}",
            )
        registration, tool = found
        reply = registration.entry(tool["entry"])({**envelope, "tool": name})
    except Refusal as refusal:
        return {"error": refusal.link, "tools": listed}, None
    except Exception as failure:  # noqa: BLE001 -- every failure is a detailed error link
        link = formats.from_exception(
            f"{ACTOR} ({name})",
            failure,
            explanation="the server has no recovery for an unexpected error; nothing after it ran",
        )
        return {"error": link, "tools": listed}, None
    handover = reply.pop("handover", None) if isinstance(reply, dict) else None
    if not isinstance(reply, dict) or not ("value" in reply or "error" in reply):
        link = own(
            str(name),
            "invalid_answer",
            f"the {registration.part} part answered the call with no value and no error: "
            f"{reply!r}"[:2000],
            reason="environment",
            explanation='a tool\'s entry answers {"value"} or {"error"}',
        ).link
        return {"error": link, "tools": listed}, None
    if "error" in reply or not tool["long_work"]:
        handover = None
    return {**reply, "tools": listed}, handover


def _write(descriptor: int, text: str) -> None:
    data = text.encode("utf-8")
    while data:
        data = data[os.write(descriptor, data) :]


def hand_over(name: str, plan: dict, line: str, writer) -> int:
    """Become the long work a ``long_work`` tool started: answer through a copy of standard output
    that the exec closes, which ends the answer, then replace this process with the work's command,
    its standard output and error going to the files the plan names and the locked descriptors
    inherited.

    When the exec fails, a second answer line refuses the call with ``start_failed``, the plan's
    folder is removed again, and this process ends, which releases the locks."""
    writer.flush()
    reply = os.dup(writer.fileno())  # not inheritable: the exec closes it
    for path, target in ((plan["output"], 1), (plan["messages"], 2)):
        opened = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.dup2(opened, target)
        os.close(opened)
    null = os.open(os.devnull, os.O_RDONLY)
    os.dup2(null, 0)
    os.close(null)
    for descriptor in plan["descriptors"]:
        os.set_inheritable(descriptor, True)
    _write(reply, line)
    try:
        os.execve(plan["argv"][0], plan["argv"], plan["environment"])
    except OSError as error:
        for path in (plan["output"], plan["messages"]):
            Path(path).unlink(missing_ok=True)
        try:
            Path(plan["folder"]).rmdir()
        except OSError:
            pass
        link = own(
            name,
            "start_failed",
            f"`{shlex.join(plan['argv'])}` could not be started: {error}; its locks were "
            "released",
            reason="environment",
            explanation="the operating system refused to start the process",
        ).link
        _write(reply, json.dumps({"error": link}, ensure_ascii=False) + "\n")
        return 1


def serve_call(name: str, reader, writer) -> int:
    """``concorde project-mcp --call <tool>``: answer one call of the server, read as one JSON
    object from ``reader``, with one JSON line on ``writer``."""
    handover = None
    try:
        envelope = json.loads(reader.read())
        problem = None if isinstance(envelope, dict) else "it is no JSON object"
    except ValueError as error:
        problem = str(error)
    if problem is not None:
        link = own(
            str(name),
            "invalid_input",
            f"the call's input cannot be read: {problem}",
            reason="environment",
            explanation="only the project MCP server starts a call's process, with one JSON "
            "object on its standard input",
        ).link
        reply = {"error": link}
    else:
        reply, handover = answer(name, envelope)
    line = json.dumps(reply, ensure_ascii=False, separators=(",", ":")) + "\n"
    if handover is not None:
        return hand_over(name, handover, line, writer)
    writer.write(line)
    writer.flush()
    return 0


__all__ = [
    "ACTOR",
    "Refusal",
    "answer",
    "describe",
    "digest",
    "instructions",
    "listing",
    "presented",
    "serve_call",
    "serving",
]
