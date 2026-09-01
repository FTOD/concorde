"""Parser for the project reflection log (``<specification_root>/reflections.md``).

The log is the one maintained file in which coding agents record every difficulty or problem met
during the plan, tasks, implement, analyze, and converge phases of any attempt. Its grammar is
normative in Feature 005's ``contracts/reflection-log.md``; this module is shared by validation,
bounded context, the workspace adapter, and implementation acceptance so that every consumer parses the log
identically. It never writes the log.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

LOG_NAME = "reflections.md"
REQUIRED_FIELDS = (
    "Phase",
    "Date",
    "Feature",
    "Kind",
    "Concerns",
    "Expected",
    "Observed",
    "Effect",
    "Action",
    "Improvement",
    "Status",
)
PHASES = frozenset({"plan", "tasks", "implement", "analyze", "converge", "fast-loop"})
KINDS = frozenset({"specification", "architecture", "guidance", "tooling", "environment", "implementation"})
EFFECTS = frozenset({"assumed", "worked-around", "deferred", "blocked"})
STATUSES = frozenset({"open", "resolved", "dismissed"})

ENTRY_HEADING = re.compile(r"^### (R-\d{3,}) · (.+?)\s*$")
ANY_H3 = re.compile(r"^###\s")
FIELD_LINE = re.compile(r"^- \*\*([A-Za-z]+)\*\*:\s*(.*)$")
CONTINUATION = re.compile(r"^ {2,}(?!- )(\S.*)$")
OCCURRENCE = re.compile(r"^ {2,}- (\S.*)$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FENCE = re.compile(r"^(```|~~~)")
REFERENCE_SUFFIX = re.compile(r"(#[^\s]*|:\d+)$")


def log_path(specification_root: str) -> str:
    """Project-relative path of the one project reflection log."""
    return f"{specification_root.rstrip('/')}/{LOG_NAME}"


@dataclass(frozen=True)
class ReflectionEntry:
    identifier: str
    title: str
    line: int
    fields: Mapping[str, str]
    occurrences: tuple[str, ...]

    @property
    def feature(self) -> str:
        return self.fields.get("Feature", "")

    @property
    def status(self) -> str:
        return self.fields.get("Status", "")


@dataclass(frozen=True)
class LogProblem:
    code: str  # shape | duplicate | vocabulary
    line: int
    identifier: str | None
    message: str
    remediation: str


@dataclass(frozen=True)
class ParsedLog:
    entries: tuple[ReflectionEntry, ...]
    problems: tuple[LogProblem, ...]

    def entries_for(self, feature_id: str) -> tuple[ReflectionEntry, ...]:
        return tuple(entry for entry in self.entries if entry.feature == feature_id)

    def open_count(self, feature_id: str) -> int:
        return sum(1 for entry in self.entries_for(feature_id) if entry.status == "open")

    def summary(self, feature_id: str) -> dict[str, int]:
        selected = self.entries_for(feature_id)
        return {
            "entries": len(selected),
            "open": sum(1 for entry in selected if entry.status == "open"),
            "resolved": sum(1 for entry in selected if entry.status == "resolved"),
            "dismissed": sum(1 for entry in selected if entry.status == "dismissed"),
        }


def strip_reference_suffix(value: str) -> str:
    """Drop an optional ``#fragment`` or ``:line`` suffix from a Concerns reference."""
    return REFERENCE_SUFFIX.sub("", value.strip())


def _finish(
    identifier: str,
    title: str,
    line: int,
    fields: dict[str, str],
    occurrences: list[str],
    seen: set[str],
    entries: list[ReflectionEntry],
    problems: list[LogProblem],
) -> None:
    if identifier in seen:
        problems.append(LogProblem("duplicate", line, identifier, f"Entry identifier {identifier} is used more than once.", "For a collision between new uncommitted entries, allocate the next unused identifier to the colliding new entry; never change an existing entry ID or reuse a removed identifier."))
    seen.add(identifier)
    missing = [name for name in REQUIRED_FIELDS if not fields.get(name, "").strip()]
    if missing:
        problems.append(LogProblem("shape", line, identifier, f"Entry {identifier} is missing required field(s): {', '.join(missing)}.", "Fill every required field in the order Phase, Date, Feature, Kind, Concerns, Expected, Observed, Effect, Action, Improvement, Status."))
    date = fields.get("Date", "").strip()
    if date and not DATE.fullmatch(date):
        problems.append(LogProblem("shape", line, identifier, f"Entry {identifier} has a Date that is not YYYY-MM-DD: {date}.", "Write the date the entry was first recorded as YYYY-MM-DD."))
    for label, vocabulary in (("Phase", PHASES), ("Kind", KINDS), ("Effect", EFFECTS), ("Status", STATUSES)):
        value = fields.get(label, "").strip()
        if value and value not in vocabulary:
            problems.append(LogProblem("vocabulary", line, identifier, f"Entry {identifier} has {label} '{value}' outside the fixed vocabulary.", f"Use one of: {', '.join(sorted(vocabulary))}."))
    status = fields.get("Status", "").strip()
    if status in STATUSES and status != "open" and not fields.get("Note", "").strip():
        problems.append(LogProblem("vocabulary", line, identifier, f"Entry {identifier} is {status} but has no Note.", "Add a Note saying why and referencing the resolving change."))
    entries.append(ReflectionEntry(identifier, title, line, dict(fields), tuple(occurrences)))


def parse_reflection_log(text: str) -> ParsedLog:
    """Parse one log deterministically; malformed input yields problems, never an exception."""
    entries: list[ReflectionEntry] = []
    problems: list[LogProblem] = []
    seen: set[str] = set()
    current: tuple[str, str, int] | None = None
    fields: dict[str, str] = {}
    occurrences: list[str] = []
    last_label: str | None = None
    fenced = False
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip("\n")
        if FENCE.match(line.strip()):
            fenced = not fenced
            continue
        if fenced:
            continue
        if ANY_H3.match(line) or line.startswith("## "):
            if current is not None:
                _finish(*current, fields, occurrences, seen, entries, problems)
                current, fields, occurrences, last_label = None, {}, [], None
            match = ENTRY_HEADING.match(line)
            if match:
                current = (match.group(1), match.group(2), number)
            elif ANY_H3.match(line):
                problems.append(LogProblem("shape", number, None, f"Heading '{line.strip()}' is not an entry heading of the form '### R-NNN · title'.", "Name every entry '### R-NNN · <short title>' with a sequential identifier."))
            continue
        if current is None:
            continue
        field = FIELD_LINE.match(line)
        if field:
            label, value = field.group(1), field.group(2).strip()
            last_label = label
            if label == "Occurrences":
                continue
            fields[label] = value
            continue
        if last_label == "Occurrences":
            occurrence = OCCURRENCE.match(line)
            if occurrence:
                occurrences.append(occurrence.group(1).strip())
                continue
        continuation = CONTINUATION.match(line)
        if continuation and last_label and last_label != "Occurrences":
            fields[last_label] = (fields.get(last_label, "") + " " + continuation.group(1).strip()).strip()
    if current is not None:
        _finish(*current, fields, occurrences, seen, entries, problems)
    return ParsedLog(tuple(entries), tuple(problems))
