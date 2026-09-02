"""Parser for the project reflection log (``.concorde/reflections/log.md``).

The log is the one maintained file in which coding agents record every difficulty or problem met
during the plan, tasks, implement, analyze, and converge phases of any attempt. Its grammar is
normative in Feature 005's embedded reflection interface inside its direct feature file; this module
is shared by validation, bounded context, the workspace adapter, and cleanup-only delivery so every consumer parses the log
identically. It never writes the log.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

LOG_PATH = ".concorde/reflections/log.md"
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

REFLECTION_ID_TEXT = r"R-(?:\d{3}|[1-9]\d{3,})"
REFLECTION_ID = re.compile(rf"^{REFLECTION_ID_TEXT}$")
ENTRY_HEADING = re.compile(rf"^### ({REFLECTION_ID_TEXT}) · (.+?)\s*$")
ANY_H3 = re.compile(r"^###\s")
FIELD_LINE = re.compile(r"^- \*\*([A-Za-z]+)\*\*:\s*(.*)$")
CONTINUATION = re.compile(r"^ {2,}(?!- )(\S.*)$")
OCCURRENCE = re.compile(r"^ {2,}- (\S.*)$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FENCE = re.compile(r"^(```|~~~)")
REFERENCE_SUFFIX = re.compile(r"(#[^\s]*|:\d+)$")
HIGH_WATER_MARKER = re.compile(
    rf"^<!-- concorde-reflection-high-water: ({REFLECTION_ID_TEXT}|R-000) -->$"
)
HIGH_WATER_PREFIX = "<!-- concorde-reflection-high-water:"


def log_path() -> str:
    """Project-relative path of the one project reflection log."""
    return LOG_PATH


def reflection_number(value: str, *, allow_zero: bool = False) -> int | None:
    """Return one canonical reflection number, rejecting padded aliases such as ``R-0001``."""
    if value == "R-000":
        return 0 if allow_zero else None
    if not REFLECTION_ID.fullmatch(value):
        return None
    number = int(value[2:])
    return number if number > 0 and format_reflection_id(number) == value else None


def format_reflection_id(number: int) -> str:
    if not isinstance(number, int) or isinstance(number, bool) or number < 0:
        raise ValueError("reflection number must be a non-negative integer")
    return f"R-{number:03d}"


@dataclass(frozen=True)
class ReflectionEntry:
    identifier: str
    title: str
    line: int
    end_line: int
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
    high_water: int | None = None
    high_water_line: int | None = None

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
    end_line: int,
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
    entries.append(ReflectionEntry(identifier, title, line, end_line, dict(fields), tuple(occurrences)))


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
    high_water: int | None = None
    high_water_line: int | None = None
    lines = text.splitlines()
    for number, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        if FENCE.match(line.strip()):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith(HIGH_WATER_PREFIX):
            marker = HIGH_WATER_MARKER.fullmatch(line)
            if marker is None:
                problems.append(LogProblem("shape", number, None, "Reflection high-water marker is malformed.", "Use exactly '<!-- concorde-reflection-high-water: R-NNN -->' with one canonical ID."))
            elif high_water is not None:
                problems.append(LogProblem("shape", number, None, "Reflection log contains more than one high-water marker.", "Keep exactly one tracked high-water marker in the log preamble."))
            else:
                high_water = reflection_number(marker.group(1), allow_zero=True)
                high_water_line = number
            continue
        if ANY_H3.match(line) or line.startswith("## "):
            if current is not None:
                _finish(*current, number - 1, fields, occurrences, seen, entries, problems)
                current, fields, occurrences, last_label = None, {}, [], None
            match = ENTRY_HEADING.match(line)
            if match and reflection_number(match.group(1)) is not None:
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
        _finish(*current, len(lines), fields, occurrences, seen, entries, problems)
    if high_water is not None:
        highest_entry = max((reflection_number(entry.identifier) or 0 for entry in entries), default=0)
        if high_water < highest_entry:
            problems.append(LogProblem("shape", high_water_line or 1, None, f"Reflection high-water {format_reflection_id(high_water)} is below existing entry {format_reflection_id(highest_entry)}.", "Raise the tracked high-water marker to at least the greatest issued entry ID; never lower it."))
    return ParsedLog(tuple(entries), tuple(problems), high_water, high_water_line)
