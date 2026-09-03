"""Parser and collection helpers for per-file project reflections.

Each ``.concorde/reflections/R-NNN.md`` document is the sole prose authority for one
reflection. ``index.json`` contains only the monotonic allocation high-water mark. Recording and
triage are deliberately separate: writers describe the problem, while triage later supplies the
analysis, proposed resolution, and human-intervention decision.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Mapping

from .frontmatter import FrontMatterError, parse_document

REFLECTIONS_PATH = ".concorde/reflections"
INDEX_PATH = f"{REFLECTIONS_PATH}/index.json"
LEGACY_LOG_PATH = f"{REFLECTIONS_PATH}/log.md"
REQUIRED_METADATA = (
    "id",
    "title",
    "phase",
    "date",
    "feature",
    "kind",
    "concerns",
    "status",
    "triage",
)
OPTIONAL_METADATA = frozenset({"human_intervention", "resolution_note"})
PROBLEM_SECTIONS = ("Context", "Expected", "Observed", "Impact", "Evidence")
TRIAGE_SECTIONS = ("Triage Analysis", "Proposed Resolution", "Intervention Rationale")
REQUIRED_SECTIONS = (*PROBLEM_SECTIONS, *TRIAGE_SECTIONS, "User Comments", "Occurrences")

PHASES = frozenset({"plan", "tasks", "implement", "analyze", "converge", "fast-loop"})
KINDS = frozenset(
    {"specification", "architecture", "guidance", "tooling", "environment", "implementation"}
)
STATUSES = frozenset({"open", "resolved", "dismissed"})
TRIAGE_STATES = frozenset({"pending", "complete"})
HUMAN_INTERVENTIONS = frozenset({"required", "not-required"})

REFLECTION_ID_TEXT = r"R-(?:\d{3}|[1-9]\d{3,})"
REFLECTION_ID = re.compile(rf"^{REFLECTION_ID_TEXT}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REFERENCE_SUFFIX = re.compile(r"(#[^\s]*|:\d+)$")
H2 = re.compile(r"^## ([^#].*?)\s*$")
FENCE = re.compile(r"^(```|~~~)")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
OCCURRENCE = re.compile(r"^\s*-\s+(\S.*)$")


def reflections_path() -> str:
    """Project-relative directory holding reflection documents and queue metadata."""
    return REFLECTIONS_PATH


def index_path() -> str:
    """Project-relative path of the reflection ID allocation index."""
    return INDEX_PATH


def reflection_path(identifier: str) -> str:
    """Return the canonical project-relative document path for one reflection ID."""
    if reflection_number(identifier) is None:
        raise ValueError(f"reflection identifier must be canonical: {identifier!r}")
    return f"{REFLECTIONS_PATH}/{identifier}.md"


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
    path: str
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

    @property
    def triage(self) -> str:
        return self.fields.get("Triage", "")


@dataclass(frozen=True)
class ReflectionProblem:
    code: str  # shape | duplicate | vocabulary
    path: str
    line: int
    identifier: str | None
    message: str
    remediation: str


@dataclass(frozen=True)
class ParsedReflections:
    entries: tuple[ReflectionEntry, ...]
    problems: tuple[ReflectionProblem, ...]
    high_water: int | None = None

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
    """Drop an optional ``#fragment`` or ``:line`` suffix from a concern reference."""
    return REFERENCE_SUFFIX.sub("", value.strip())


def reflection_document_paths(auxiliary: Mapping[str, str]) -> tuple[str, ...]:
    """Return canonical reflection document paths from a repository auxiliary map."""
    prefix = REFLECTIONS_PATH + "/"
    return tuple(
        sorted(
            path
            for path in auxiliary
            if path.startswith(prefix)
            and path.count("/") == 2
            and path.endswith(".md")
            and reflection_number(path[len(prefix) : -3]) is not None
        )
    )


def _meaningful(value: str) -> str:
    return COMMENT.sub("", value).strip()


def _sections(body: str, path: str) -> tuple[dict[str, str], dict[str, int], list[ReflectionProblem]]:
    sections: dict[str, str] = {}
    lines_by_name: dict[str, int] = {}
    problems: list[ReflectionProblem] = []
    current: str | None = None
    content: list[str] = []
    fenced = False

    def finish() -> None:
        nonlocal content
        if current is not None:
            sections[current] = "\n".join(content).strip()
        content = []

    for number, line in enumerate(body.splitlines(), start=1):
        if FENCE.match(line.strip()):
            fenced = not fenced
        match = None if fenced else H2.fullmatch(line)
        if match:
            finish()
            current = match.group(1).strip()
            if current in sections or current in lines_by_name:
                problems.append(
                    ReflectionProblem(
                        "shape",
                        path,
                        number,
                        None,
                        f"Reflection document repeats section '{current}'.",
                        "Keep exactly one copy of every required level-two section.",
                    )
                )
            lines_by_name[current] = number
        elif current is not None:
            content.append(line)
    finish()
    return sections, lines_by_name, problems


def parse_reflection_document(text: str, path: str) -> tuple[ReflectionEntry | None, tuple[ReflectionProblem, ...]]:
    """Parse one reflection document; malformed input yields findings rather than exceptions."""
    problems: list[ReflectionProblem] = []
    try:
        metadata, body = parse_document(text, path)
    except FrontMatterError as error:
        line = error.line or 1
        return None, (
            ReflectionProblem("shape", path, line, None, str(error), "Use the Reflection Document v2 template."),
        )

    identifier_value = metadata.get("id")
    identifier = identifier_value if isinstance(identifier_value, str) else None
    missing = [
        name
        for name in REQUIRED_METADATA
        if not isinstance(metadata.get(name), str) or not str(metadata[name]).strip()
    ]
    if missing:
        problems.append(
            ReflectionProblem(
                "shape",
                path,
                1,
                identifier,
                f"Reflection document is missing metadata field(s): {', '.join(missing)}.",
                "Fill every required metadata field from the Reflection Document v2 template.",
            )
        )
    allowed = set(REQUIRED_METADATA) | OPTIONAL_METADATA
    unknown = sorted(set(metadata) - allowed)
    if unknown:
        problems.append(
            ReflectionProblem(
                "shape",
                path,
                1,
                identifier,
                f"Reflection document has unsupported metadata field(s): {', '.join(unknown)}.",
                "Keep problem metadata in the fixed front matter and prose in its required section.",
            )
        )

    path_name = path.rsplit("/", 1)[-1]
    expected_identifier = path_name[:-3] if path_name.endswith(".md") else ""
    if reflection_number(expected_identifier) is None or identifier != expected_identifier:
        problems.append(
            ReflectionProblem(
                "shape",
                path,
                1,
                identifier,
                f"Reflection filename and id must be the same canonical R-NNN value: {path_name!r} / {identifier!r}.",
                "Name the file and id with the same allocated identifier, for example R-001.md and R-001.",
            )
        )

    sections, section_lines, section_problems = _sections(body, path)
    problems.extend(section_problems)
    missing_sections = [name for name in REQUIRED_SECTIONS if name not in sections]
    if missing_sections:
        problems.append(
            ReflectionProblem(
                "shape",
                path,
                1,
                identifier,
                f"Reflection document is missing section(s): {', '.join(missing_sections)}.",
                "Keep every required section, including blank triage and User Comments sections.",
            )
        )
    for name in PROBLEM_SECTIONS:
        if name in sections and not _meaningful(sections[name]):
            problems.append(
                ReflectionProblem(
                    "shape",
                    path,
                    section_lines.get(name, 1),
                    identifier,
                    f"Problem section '{name}' is empty.",
                    "Record enough concrete context, expected and observed behavior, impact, and evidence to investigate later.",
                )
            )

    date = str(metadata.get("date", "")).strip()
    if date and not DATE.fullmatch(date):
        problems.append(
            ReflectionProblem("shape", path, 1, identifier, f"Reflection Date is not YYYY-MM-DD: {date}.", "Record the first-seen date as YYYY-MM-DD.")
        )
    for label, vocabulary in (
        ("phase", PHASES),
        ("kind", KINDS),
        ("status", STATUSES),
        ("triage", TRIAGE_STATES),
    ):
        value = str(metadata.get(label, "")).strip()
        if value and value not in vocabulary:
            problems.append(
                ReflectionProblem(
                    "vocabulary",
                    path,
                    1,
                    identifier,
                    f"Reflection {label} '{value}' is outside the fixed vocabulary.",
                    f"Use one of: {', '.join(sorted(vocabulary))}.",
                )
            )

    status = str(metadata.get("status", "")).strip()
    if status in STATUSES and status != "open" and not str(metadata.get("resolution_note", "")).strip():
        problems.append(
            ReflectionProblem(
                "vocabulary",
                path,
                1,
                identifier,
                f"Reflection is {status} but has no resolution_note.",
                "Add the maintainer's reason and the resolving change as resolution_note.",
            )
        )

    triage = str(metadata.get("triage", "")).strip()
    human = metadata.get("human_intervention")
    human_value = str(human).strip() if human is not None else ""
    triage_content = {name: _meaningful(sections.get(name, "")) for name in TRIAGE_SECTIONS}
    if triage == "pending":
        if human_value or any(triage_content.values()):
            problems.append(
                ReflectionProblem(
                    "shape",
                    path,
                    1,
                    identifier,
                    "A pending reflection already contains triage analysis, a proposed resolution, or a human-intervention decision.",
                    "At recording time describe only the problem; leave triage-owned content blank until reflection triage runs.",
                )
            )
    elif triage == "complete":
        if human_value not in HUMAN_INTERVENTIONS:
            problems.append(
                ReflectionProblem(
                    "vocabulary",
                    path,
                    1,
                    identifier,
                    f"Completed triage has invalid human_intervention {human_value!r}.",
                    "Triage must decide required or not-required.",
                )
            )
        missing_triage = [name for name, value in triage_content.items() if not value]
        if missing_triage:
            problems.append(
                ReflectionProblem(
                    "shape",
                    path,
                    1,
                    identifier,
                    f"Completed triage is missing detail in: {', '.join(missing_triage)}.",
                    "Triage must record its analysis, proposed resolution, and intervention rationale.",
                )
            )

    occurrences = tuple(
        match.group(1).strip()
        for line in sections.get("Occurrences", "").splitlines()
        if (match := OCCURRENCE.fullmatch(line))
    )
    title = str(metadata.get("title", "")).strip()
    expected_heading = f"# {identifier} · {title}" if identifier and title else ""
    first_heading = next((line.strip() for line in body.splitlines() if line.strip()), "")
    if expected_heading and first_heading != expected_heading:
        problems.append(
            ReflectionProblem(
                "shape",
                path,
                1,
                identifier,
                "Reflection heading does not match its id and title metadata.",
                f"Use exactly '{expected_heading}'.",
            )
        )

    if identifier is None or reflection_number(identifier) is None:
        return None, tuple(problems)
    fields = {
        "Phase": str(metadata.get("phase", "")),
        "Date": date,
        "Feature": str(metadata.get("feature", "")),
        "Kind": str(metadata.get("kind", "")),
        "Concerns": str(metadata.get("concerns", "")),
        "Status": status,
        "Triage": triage,
        "Human Intervention": human_value,
        "Note": str(metadata.get("resolution_note", "")),
        **{name: sections.get(name, "") for name in REQUIRED_SECTIONS},
    }
    return ReflectionEntry(identifier, title, path, 1, len(text.splitlines()), fields, occurrences), tuple(problems)


def _parse_index(text: str | None) -> tuple[int | None, tuple[ReflectionProblem, ...]]:
    if text is None:
        return None, ()
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        return None, (
            ReflectionProblem("shape", INDEX_PATH, error.lineno, None, f"Reflection index is invalid JSON: {error.msg}.", "Use schema_version 1 with one canonical high_water ID."),
        )
    if not isinstance(value, dict) or set(value) != {"schema_version", "high_water"} or value.get("schema_version") != 1:
        return None, (
            ReflectionProblem("shape", INDEX_PATH, 1, None, "Reflection index must contain exactly schema_version 1 and high_water.", "Restore the Reflection Document v2 index shape."),
        )
    high_water = value.get("high_water")
    if not isinstance(high_water, str) or reflection_number(high_water, allow_zero=True) is None:
        return None, (
            ReflectionProblem("shape", INDEX_PATH, 1, None, f"Reflection index high_water is not canonical: {high_water!r}.", "Use R-000 or one canonical allocated R-NNN identifier."),
        )
    return reflection_number(high_water, allow_zero=True), ()


def parse_reflections(documents: Mapping[str, str], index_text: str | None) -> ParsedReflections:
    """Parse and validate the complete per-file reflection collection."""
    entries: list[ReflectionEntry] = []
    problems: list[ReflectionProblem] = []
    high_water, index_problems = _parse_index(index_text)
    problems.extend(index_problems)
    seen: dict[str, str] = {}
    for path in sorted(documents):
        entry, document_problems = parse_reflection_document(documents[path], path)
        problems.extend(document_problems)
        if entry is None:
            continue
        previous = seen.get(entry.identifier)
        if previous is not None:
            problems.append(
                ReflectionProblem(
                    "duplicate",
                    path,
                    1,
                    entry.identifier,
                    f"Reflection identifier {entry.identifier} is used by both {previous} and {path}.",
                    "Keep one canonical file per allocated identity; never renumber an existing reflection or reuse a removed ID.",
                )
            )
        else:
            seen[entry.identifier] = path
        entries.append(entry)
    entries.sort(key=lambda entry: reflection_number(entry.identifier) or 0)
    if entries and high_water is None and not index_problems:
        problems.append(
            ReflectionProblem("shape", INDEX_PATH, 1, None, "Reflection documents exist without an allocation index.", "Create index.json with a high_water at least as large as every issued ID."),
        )
    if high_water is not None:
        highest = max((reflection_number(entry.identifier) or 0 for entry in entries), default=0)
        if high_water < highest:
            problems.append(
                ReflectionProblem(
                    "shape",
                    INDEX_PATH,
                    1,
                    None,
                    f"Reflection high_water {format_reflection_id(high_water)} is below existing document {format_reflection_id(highest)}.",
                    "Raise high_water to at least the greatest issued ID; never lower or reuse it.",
                )
            )
    return ParsedReflections(tuple(entries), tuple(problems), high_water)


def parse_auxiliary_reflections(auxiliary: Mapping[str, str]) -> ParsedReflections:
    """Parse reflections already loaded by ``ProjectRepository``."""
    documents = {path: auxiliary[path] for path in reflection_document_paths(auxiliary)}
    return parse_reflections(documents, auxiliary.get(INDEX_PATH))
