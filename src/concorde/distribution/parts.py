"""The part registrations: which parts the package builds, which are installed, and the entries
through which Distribution alone reaches their code.

Each part keeps its registration, plain data in the shape of
``contract.distribution.part-registration``, as ``registration.json`` in its own directory of
``src/concorde/``; reading it imports nothing. Distribution imports a part's code only through the
entries a registration names (``<module>:<attribute>``, relative to the part's own package, so an
entry never leaves its part), and only for an installed part. In a source checkout every part the
package builds is installed; in a project, the parts the receipt ``.concorde/install.json`` beside
the Framework copy names under ``parts``, every part when it names none. The build's parts index,
``generated/parts.json``, records what every part of the package registers, so that a command or
tool of a part that is not installed is refused naming that part without loading its registration.
"""

from __future__ import annotations

import importlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

# The package Concorde runs from: a source checkout, or a project's Framework copy.
PACKAGE = Path(__file__).resolve().parents[3]
SOURCE = "src/concorde"
REGISTRATION = "registration.json"
# The build's record of every part of the package with the names it registers.
INDEX = "generated/parts.json"
# The receipt of an installed Concorde, beside its Framework copy `.concorde/framework`.
RECEIPT = "install.json"

PART_NAME = re.compile(r"^[a-z][a-z ]*[a-z]$|^[a-z]$")
COMMAND_NAME = re.compile(r"^[a-z][a-z-]*$")
TOOL_NAME = re.compile(r"^[a-z][a-z_]*$")
MODULE_ID = re.compile(r"^module\.[a-z][a-z0-9-]*$")
MODULE_PATH = re.compile(r"^[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*$")
ENTRY = re.compile(r"^[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*:[A-Za-z_][A-Za-z0-9_]*$")

FIELDS = (
    "part",
    "module",
    "depends_on",
    "loads",
    "commands",
    "mcp_tools",
    "mcp_definitions",
    "mcp_instructions",
    "typed_types",
    "guidance",
    "renders",
    "install",
    "idle_check",
    "after_update",
)
# The guidance sections a part may contribute: the project skill, the task-session prompt and the
# ``CLAUDE.md`` block.
GUIDANCE_FIELDS = ("skill", "task_session", "claude_md")
GUIDANCE_PATH = re.compile(r"^generated/[a-z0-9_./-]+\.md$")
INSTALL_FIELDS = (
    "files",
    "defaults",
    "gitignore",
    "permissions",
    "programs",
    "python_dependencies",
    "prepare",
    "bind",
)
# A framework-relative file a part ships beside its code directory, or a whole directory when the
# path ends with ``/``.
SHIPPED_PATH = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*/?$")
# The programs a part may need placed: the pinned d2 and the pi runtime.
PROGRAMS = ("d2", "pi-runtime")


class RegistrationError(ValueError):
    """A registration that does not satisfy the registration contract, or a composition of
    registrations that cannot be served, such as two parts registering one name."""

    def __init__(self, code: str, message: str, path: str | None = None):
        super().__init__(message)
        self.code = code
        self.path = path


@dataclass(frozen=True)
class Registration:
    """One part's registration and the directory of ``src/concorde/`` its code lives in."""

    data: dict
    directory: str

    @property
    def part(self) -> str:
        return self.data["part"]

    @property
    def path(self) -> str:
        return f"{SOURCE}/{self.directory}/{REGISTRATION}"

    def entry(self, name: str):
        """The attribute an entry of this registration names, imported from the part's own
        package: Distribution's one way into a part's code."""
        module, attribute = name.split(":", 1)
        return getattr(
            importlib.import_module(f"concorde.{self.directory}.{module}"), attribute
        )

    def load(self) -> None:
        """Import the part's modules that register what its code provides when it loads."""
        for module in self.data["loads"]:
            importlib.import_module(f"concorde.{self.directory}.{module}")


def _fail(path: str, message: str) -> RegistrationError:
    return RegistrationError("invalid_registration", f"{path}: {message}", path)


def _strings(path: str, field: str, value, pattern=None) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise _fail(path, f"{field} is not a list of non-empty strings")
    if len(set(value)) != len(value):
        raise _fail(path, f"{field} repeats an item")
    for item in value:
        if pattern is not None and not pattern.match(item):
            raise _fail(path, f"{field} holds {item!r}, which is not of the right form")


def _optional(path: str, field: str, value, pattern=None) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not value:
        raise _fail(path, f"{field} is neither null nor a non-empty string")
    if pattern is not None and not pattern.match(value):
        raise _fail(
            path, f"{field} {value!r} is no entry `<module>:<attribute>` of the part"
        )


def _exact(path: str, field: str, value, fields) -> None:
    if not isinstance(value, dict):
        raise _fail(path, f"{field} is not an object")
    if set(value) != set(fields):
        missing = sorted(set(fields) - set(value))
        extra = sorted(set(value) - set(fields))
        raise _fail(
            path,
            f"{field} must have exactly the fields {', '.join(fields)}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unknown {', '.join(extra)}" if extra else ""),
        )


def check(data, path: str) -> dict:
    """``data`` when it satisfies the registration contract; ``RegistrationError`` naming the
    first field that does not."""
    _exact(path, "the registration", data, FIELDS)
    if not isinstance(data["part"], str) or not PART_NAME.match(data["part"]):
        raise _fail(path, "part is no part name")
    if not isinstance(data["module"], str) or not MODULE_ID.match(data["module"]):
        raise _fail(path, "module is no Module identity")
    _strings(path, "depends_on", data["depends_on"], PART_NAME)
    _strings(path, "loads", data["loads"], MODULE_PATH)
    if not isinstance(data["commands"], list):
        raise _fail(path, "commands is not a list")
    for command in data["commands"]:
        _exact(path, "a command", command, ("name", "entry", "output"))
        if not isinstance(command["name"], str) or not COMMAND_NAME.match(
            command["name"]
        ):
            raise _fail(
                path, f"command name {command['name']!r} is not of the right form"
            )
        _optional(path, f"the entry of {command['name']}", command["entry"], ENTRY)
        if command["entry"] is None or command["output"] not in ("own", "envelope"):
            raise _fail(
                path,
                f"command {command['name']} needs an entry and an output own or envelope",
            )
    if not isinstance(data["mcp_tools"], list):
        raise _fail(path, "mcp_tools is not a list")
    for tool in data["mcp_tools"]:
        _exact(
            path,
            "an MCP tool",
            tool,
            ("name", "entry", "worktree", "long_work", "threaded", "requires"),
        )
        if not isinstance(tool["name"], str) or not TOOL_NAME.match(tool["name"]):
            raise _fail(path, f"tool name {tool['name']!r} is not of the right form")
        _optional(path, f"the entry of {tool['name']}", tool["entry"], ENTRY)
        if tool["entry"] is None or tool["worktree"] not in ("primary", "session"):
            raise _fail(
                path,
                f"tool {tool['name']} needs an entry and a worktree primary or session",
            )
        if not isinstance(tool["long_work"], bool) or not isinstance(
            tool["threaded"], bool
        ):
            raise _fail(
                path, f"long_work and threaded of tool {tool['name']} are not booleans"
            )
        _strings(path, f"requires of tool {tool['name']}", tool["requires"], PART_NAME)
    _optional(path, "mcp_definitions", data["mcp_definitions"], ENTRY)
    if data["mcp_tools"] and data["mcp_definitions"] is None:
        raise _fail(
            path, "a part with MCP tools names their definitions in mcp_definitions"
        )
    _optional(path, "mcp_instructions", data["mcp_instructions"])
    _strings(path, "typed_types", data["typed_types"])
    if data["guidance"] is not None:
        _exact(path, "guidance", data["guidance"], GUIDANCE_FIELDS)
        for kind, section in data["guidance"].items():
            _optional(path, f"guidance.{kind}", section)
            if section is not None and (
                not GUIDANCE_PATH.match(section) or ".." in section.split("/")
            ):
                raise _fail(
                    path,
                    f"guidance.{kind} {section!r} is no Markdown render under generated/",
                )
    _optional(path, "renders", data["renders"], ENTRY)
    install = data["install"]
    _exact(path, "install", install, INSTALL_FIELDS)
    for field in ("gitignore", "permissions", "python_dependencies"):
        _strings(path, f"install.{field}", install[field])
    _strings(path, "install.files", install["files"], SHIPPED_PATH)
    if any(".." in item.split("/") for item in install["files"]):
        raise _fail(path, "install.files leaves the Framework copy")
    _strings(path, "install.programs", install["programs"])
    unknown = sorted(set(install["programs"]) - set(PROGRAMS))
    if unknown:
        raise _fail(
            path,
            f"install.programs names {', '.join(unknown)}, which the installer cannot place; "
            f"it places {', '.join(PROGRAMS)}",
        )
    if not isinstance(install["defaults"], dict) or not all(
        isinstance(key, str) and key and isinstance(value, str)
        for key, value in install["defaults"].items()
    ):
        raise _fail(path, "install.defaults is not an object of texts by path")
    _optional(path, "install.prepare", install["prepare"], ENTRY)
    _optional(path, "install.bind", install["bind"], ENTRY)
    _optional(path, "idle_check", data["idle_check"], ENTRY)
    _optional(path, "after_update", data["after_update"], ENTRY)
    return data


def package_parts(package: Path = PACKAGE) -> dict[str, Registration]:
    """Every part the package builds, by name, read from the registrations of its directories."""
    found: dict[str, Registration] = {}
    source = package / SOURCE
    for path in sorted(source.glob(f"*/{REGISTRATION}")):
        relative = path.relative_to(package).as_posix()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as error:
            raise _fail(relative, f"cannot be read as JSON: {error}") from error
        registration = Registration(check(data, relative), path.parent.name)
        if registration.part in found:
            raise RegistrationError(
                "name_conflict",
                f"{relative} and {found[registration.part].path} both register the part "
                f"{registration.part!r}",
                relative,
            )
        found[registration.part] = registration
    return found


def ordered(parts: dict[str, Registration]) -> list[Registration]:
    """The parts with every part after those it depends on, otherwise by name."""
    done: list[str] = []
    pending = sorted(parts)
    while pending:
        ready = [
            name
            for name in pending
            if all(
                item in done or item not in parts
                for item in parts[name].data["depends_on"]
            )
        ]
        if not ready:
            raise RegistrationError(
                "invalid_registration",
                f"the parts {', '.join(pending)} depend on each other in a cycle",
            )
        done.append(ready[0])
        pending.remove(ready[0])
    return [parts[name] for name in done]


def receipt_path(package: Path = PACKAGE) -> Path | None:
    """The receipt beside an installed Framework copy, or None for a source checkout."""
    if package.name == "framework" and package.parent.name == ".concorde":
        return package.parent / RECEIPT
    return None


def installed_names(package: Path = PACKAGE) -> set[str] | None:
    """The parts the receipt names under ``parts``, or None when every part is installed: in a
    source checkout, and in a project whose receipt names none."""
    path = receipt_path(package)
    if path is None:
        return None
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    parts = receipt.get("parts") if isinstance(receipt, dict) else None
    if not isinstance(parts, dict):
        return None
    return set(parts)


def closure(everything: dict[str, Registration], names) -> dict[str, Registration]:
    """The parts ``names`` with every part they depend on, transitively, and Distribution, out of
    ``everything`` the package builds; ``RegistrationError`` ``unknown_part`` naming a part the
    package does not build, whether named or depended on."""
    chosen: dict[str, Registration] = {}
    pending = [("distribution", None), *((name, None) for name in names)]
    while pending:
        name, needed_by = pending.pop()
        if name in chosen:
            continue
        if name not in everything:
            raise RegistrationError(
                "unknown_part",
                (
                    f"the part {name!r}, which {needed_by} depends on, is not built by this "
                    "package"
                    if needed_by
                    else f"no part of this package is named {name!r}"
                )
                + f"; its parts are {', '.join(sorted(everything))}",
            )
        chosen[name] = everything[name]
        pending += [(item, name) for item in everything[name].data["depends_on"]]
    return chosen


def installed(package: Path = PACKAGE) -> dict[str, Registration]:
    """The installed parts, by name; Distribution is installed with any part."""
    everything = package_parts(package)
    names = installed_names(package)
    if names is None:
        return everything
    return {
        name: registration
        for name, registration in everything.items()
        if name in names or name == "distribution"
    }


def index(package: Path = PACKAGE) -> dict:
    """The build's parts index, ``{part: {"commands", "mcp_tools"}}``; empty when unreadable."""
    try:
        value = json.loads((package / INDEX).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    parts = value.get("parts") if isinstance(value, dict) else None
    return parts if isinstance(parts, dict) else {}


def index_of(parts: dict[str, Registration]) -> dict:
    """The parts index the build records: what each part registers, by name."""
    return {
        "schema_version": 1,
        "parts": {
            name: {
                "module": registration.data["module"],
                "depends_on": list(registration.data["depends_on"]),
                "commands": [item["name"] for item in registration.data["commands"]],
                "mcp_tools": [item["name"] for item in registration.data["mcp_tools"]],
            }
            for name, registration in sorted(parts.items())
        },
    }


def conflicts(parts: dict[str, Registration]) -> list[str]:
    """Each command or MCP tool name two parts register, with the parts that register it."""
    found = []
    for kind in ("commands", "mcp_tools"):
        owners: dict[str, list[str]] = {}
        for name, registration in sorted(parts.items()):
            for item in registration.data[kind]:
                owners.setdefault(item["name"], []).append(name)
        found += [
            f"{'command' if kind == 'commands' else 'MCP tool'} {item} is registered by "
            f"{' and '.join(names)}"
            for item, names in sorted(owners.items())
            if len(names) > 1
        ]
    return found


def owner_of(kind: str, name: str, package: Path = PACKAGE) -> str | None:
    """The part of the package that registers the command or tool ``name``, by the index."""
    for part, entry in sorted(index(package).items()):
        if isinstance(entry, dict) and name in (entry.get(kind) or []):
            return part
    return None


def version(package: Path = PACKAGE) -> str:
    """The one version every part carries, the package's."""
    return json.loads((package / "concorde.json").read_text(encoding="utf-8"))[
        "version"
    ]


def load(parts: dict[str, Registration]) -> None:
    """Load the code of the given parts that registers things, dependencies first."""
    for registration in ordered(parts):
        registration.load()


__all__ = [
    "INDEX",
    "PACKAGE",
    "Registration",
    "RegistrationError",
    "check",
    "closure",
    "conflicts",
    "index",
    "index_of",
    "installed",
    "installed_names",
    "load",
    "ordered",
    "owner_of",
    "package_parts",
    "receipt_path",
    "version",
]
