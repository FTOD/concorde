"""Protocol 13 reading syntax: anchors, sections, Terminology tables, definitions and diagrams.

Every parser here reads one reading document's text and returns what it declares together with
the problems it found, each tagged with the identity of the check it violates. Nothing here reads
a file, follows a link or decides whether prose is sufficient.
"""

from __future__ import annotations

import json
import re
from itertools import pairwise
from dataclasses import dataclass, field

from .errors import SpecError
from .repository_base import HEADING, IDENTITY, walk_lines

READING_SECTIONS = ("Purpose", "Terminology", "Usage", "Design", "Relationships")
HEADING_ANCHOR = re.compile(r"[ \t]+\{#([^{}\s]+)\}[ \t]*$")
HTML_ANCHOR_LINE = re.compile(r'^[ \t]*(?:<a id="[^"]*"></a>[ \t]*)+$')
HTML_ANCHOR = re.compile(r'<a id="([^"]*)"></a>')
# An anchor group that opens a paragraph or a list item's text, followed by that text.
OPENING_ANCHORS = re.compile(
    r"^(?P<indent>[ \t]*)(?P<marker>(?:[-*+]|\d+[.)])[ \t]+)?"
    r'(?P<group>(?:<a id="[^"]*"></a>[ \t]*)+)(?P<rest>\S.*)$'
)
SCENARIO_HEADING = re.compile(
    r"^(scenario\.[a-z0-9]+(?:[.-][a-z0-9-]+)*)[ \t]+[—–-][ \t]+(\S.*)$"
)
REQUIREMENT_HEADING = re.compile(
    r"^(req\.[a-z0-9]+(?:[.-][a-z0-9-]+)*)[ \t]+[—–-][ \t]+(\S.*)$"
)
LIST_ITEM = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+(.*)$")
STEP = re.compile(r"^(GIVEN|WHEN|THEN|AND|BUT)[ \t]+(\S.*)$")
REQUIREMENT_ITEM = re.compile(r"^req\.[a-z0-9]")
SHALL = re.compile(r"\bSHALL(?: NOT)?\b")
LINK = re.compile(r"!?\[([^\]]*)\]\(([^\s)]+)\)")
INLINE_CODE = re.compile(r"(`+)(?:(?!\1).)+\1")
TEST_DECLARATION = re.compile(r"@verifies\s*\(|//\s*verifies:")
SENTENCE_BREAK = re.compile(r"(?<=[.!?])[\"')\]]*\s+(?=[A-Z])")
STEP_ORDER = {"GIVEN": 0, "WHEN": 1, "THEN": 2}
NODE_PREFIXES = ("concept.", "realization.", "req.", "scenario.", "contract.")
# Fence languages that draw diagrams: D2 is the reading's diagram language, and Mermaid is
# recognized only to be refused.
DIAGRAM_LANGUAGES = ("d2", "mermaid")


@dataclass(frozen=True)
class Problem:
    """One violation found while reading syntax, attributed to a check identity."""

    check: str
    message: str
    line: int | None = None


@dataclass(frozen=True)
class Heading:
    line: int
    level: int
    text: str
    anchor: str | None


@dataclass(frozen=True)
class Anchor:
    """A readable anchor and the prose region it explains."""

    name: str
    line: int
    text: str
    raw: str
    group: tuple[str, ...]


@dataclass(frozen=True)
class TermRow:
    line: int
    term: str
    href: str | None
    definition: str


@dataclass
class Reading:
    """Everything one reading document declares, and the syntax problems found in it."""

    text: str
    headings: list[Heading] = field(default_factory=list)
    anchors: dict[str, Anchor] = field(default_factory=dict)
    requirements: list = field(default_factory=list)
    scenarios: list = field(default_factory=list)
    contracts: list = field(default_factory=list)
    diagrams: list = field(default_factory=list)
    links: list = field(default_factory=list)
    terminology: list[TermRow] | None = None
    problems: list[Problem] = field(default_factory=list)


def one_sentence(text: str) -> bool:
    """Whether text is one nonempty sentence under the deterministic sentence-break rule."""
    stripped = " ".join(text.split())
    return bool(stripped) and len(SENTENCE_BREAK.split(stripped)) == 1


def strip_heading_anchor(text: str) -> tuple[str, str | None]:
    match = HEADING_ANCHOR.search(" " + text)
    if not match:
        return text.strip(), None
    return (" " + text)[: match.start()].strip(), match.group(1)


def headings(lines) -> list[Heading]:
    result = []
    for number, kind, line in lines:
        if kind != "prose":
            continue
        match = HEADING.match(line)
        if match:
            text, anchor = strip_heading_anchor(match.group(2))
            result.append(Heading(number, len(match.group(1)), text, anchor))
    return result


def sections(text: str, level: int = 2) -> list[tuple[str, int, int]]:
    """Sections at one heading level as (title, heading line, last line)."""
    lines = walk_lines(text)
    found = headings(lines)
    total = lines[-1][0] if lines else 0
    result = []
    for index, heading in enumerate(found):
        if heading.level != level:
            continue
        end = total
        for later in found[index + 1 :]:
            if later.level <= level:
                end = later.line - 1
                break
        result.append((heading.text, heading.line, end))
    return result


def _anchors(lines, found: list[Heading], reading: Reading) -> None:
    """Resolve readable anchors outside fences with bounded explanation regions.

    A heading anchor extends to the next heading of the same or a higher level; a standalone
    anchor extends to the next heading; either ends at the next anchor group. An anchor group
    opening a paragraph or a list item explains exactly that block, its own line included.
    Requirement and scenario headings supply their identity as their anchor.
    """
    heading_at = {heading.line: heading for heading in found}
    groups: list[tuple[tuple[str, ...], int, int | None, str]] = []
    opening_ends: dict[int, int] = {}
    seen: set[str] = set()
    previous_blank = True
    for position, (number, kind, line) in enumerate(lines):
        starts_block = previous_blank
        previous_blank = kind != "prose" or not line.strip() or number in heading_at
        if kind != "prose":
            continue
        heading = heading_at.get(number)
        names: list[str] = []
        if heading is not None:
            definition = REQUIREMENT_HEADING.match(
                heading.text
            ) or SCENARIO_HEADING.match(heading.text)
            if heading.anchor and definition and heading.anchor != definition.group(1):
                reading.problems.append(
                    Problem(
                        "CHK.node.id",
                        f"heading anchor {heading.anchor} differs from the definition identity "
                        f"{definition.group(1)}",
                        number,
                    )
                )
            if definition:
                names = [definition.group(1)]
            elif heading.anchor:
                names = [heading.anchor]
        elif HTML_ANCHOR_LINE.match(line):
            names = HTML_ANCHOR.findall(line)
        elif (opening := OPENING_ANCHORS.match(line)) and (
            starts_block or opening.group("marker")
        ):
            names = HTML_ANCHOR.findall(opening.group("group"))
            opening_ends[number] = _block_end(lines, position, heading_at, opening)
        if not names:
            continue
        for name in names:
            if not IDENTITY.fullmatch(name):
                reading.problems.append(
                    Problem(
                        "CHK.node.meaning",
                        f"anchor is not a stable identity: {name!r}",
                        number,
                    )
                )
            if name in seen:
                reading.problems.append(
                    Problem(
                        "CHK.node.meaning",
                        f"duplicate anchor in document: {name}",
                        number,
                    )
                )
            seen.add(name)
        groups.append((tuple(names), number, heading.level if heading else None, line))
    for index, (names, start, level, _) in enumerate(groups):
        if start in opening_ends:
            region = [
                (n, k, HTML_ANCHOR.sub("", text) if n == start else text)
                for n, k, text in lines
                if start <= n < opening_ends[start]
            ]
            prose_text = "\n".join(
                text for _, k, text in region if k == "prose"
            ).strip()
            raw = "\n".join(text for _, _, text in region).strip()
            for name in names:
                if name not in reading.anchors:
                    reading.anchors[name] = Anchor(name, start, prose_text, raw, names)
            continue
        next_group = groups[index + 1][1] if index + 1 < len(groups) else None
        candidates = [
            heading.line
            for heading in found
            if heading.line > start and (level is None or heading.level <= level)
        ]
        if next_group is not None:
            candidates.append(next_group)
        end = (
            min(candidates)
            if candidates
            else (lines[-1][0] + 1 if lines else start + 1)
        )
        region = [(n, k, text) for n, k, text in lines if start < n < end]
        prose_text = "\n".join(
            text for n, k, text in region if k == "prose" and n not in heading_at
        ).strip()
        raw = "\n".join(text for _, _, text in region).strip()
        for name in names:
            if name not in reading.anchors:
                reading.anchors[name] = Anchor(name, start, prose_text, raw, names)


def _block_end(lines, position: int, heading_at: dict, opening: re.Match) -> int:
    """The line after the paragraph or list item that an opening anchor group starts."""
    indent = len(opening.group("indent").expandtabs())
    item = bool(opening.group("marker"))
    for number, kind, line in lines[position + 1 :]:
        if kind != "prose" or not line.strip() or number in heading_at:
            return number
        marker = LIST_ITEM.match(line)
        if marker and (
            not item
            or len(line[: len(line) - len(line.lstrip())].expandtabs()) <= indent
        ):
            return number
        if HTML_ANCHOR_LINE.match(line):
            return number
    return lines[-1][0] + 1 if lines else position + 1


def explained(anchor: Anchor) -> bool:
    """Whether an anchor region holds prose that is not only links, headings or fences."""
    text = LINK.sub("", anchor.text)
    text = HTML_ANCHOR.sub("", text)
    text = re.sub(r"[|\-*+>#:`\s]", "", text)
    return bool(text)


def _logical_lines(lines) -> list[tuple[int, str, str]]:
    """Join lazy continuation lines onto their list item so wrapped steps stay one item."""
    result: list[tuple[int, str, str]] = []
    previous_item = False
    for number, kind, line in lines:
        if kind != "prose":
            result.append((number, kind, line))
            previous_item = False
            continue
        continuation = (
            previous_item
            and line[:1] in (" ", "\t")
            and line.strip()
            and not LIST_ITEM.match(line)
            and not HEADING.match(line)
        )
        if continuation:
            last_number, last_kind, last_line = result[-1]
            result[-1] = (
                last_number,
                last_kind,
                last_line.rstrip() + " " + line.strip(),
            )
            continue
        result.append((number, kind, line))
        previous_item = bool(LIST_ITEM.match(line))
    return result


def _definitions(lines, reading: Reading) -> None:
    """Requirement and scenario sections, collecting their problems instead of failing."""
    logical = _logical_lines(lines)
    current: dict | None = None

    def close() -> None:
        nonlocal current
        if current is None:
            return
        if current["kind"] == "scenario":
            keywords = [keyword for keyword, _ in current["steps"]]
            if "WHEN" not in keywords or "THEN" not in keywords:
                reading.problems.append(
                    Problem(
                        "CHK.scenario.steps",
                        f"scenario {current['id']} needs at least one WHEN and one THEN step",
                        current["line"],
                    )
                )
            reading.scenarios.append(
                (
                    current["id"],
                    current["title"],
                    current["line"],
                    tuple(current["steps"]),
                )
            )
        else:
            if current["statement"] is None:
                reading.problems.append(
                    Problem(
                        "CHK.requirement.statement",
                        f"requirement {current['id']} has no statement paragraph",
                        current["line"],
                    )
                )
            reading.requirements.append(
                (
                    current["id"],
                    current["title"],
                    current["line"],
                    current["statement"] or "",
                )
            )
        current = None

    index = 0
    while index < len(logical):
        number, kind, line = logical[index]
        if kind != "prose":
            if (
                current is not None
                and current["kind"] == "requirement"
                and current["statement"] is None
                and kind == "fence-open"
            ):
                reading.problems.append(
                    Problem(
                        "CHK.requirement.statement",
                        f"requirement {current['id']} must state its SHALL sentence before any fence",
                        number,
                    )
                )
                current["statement"] = ""
            index += 1
            continue
        heading = HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            if current is not None and level > current["level"]:
                check = (
                    "CHK.scenario.steps"
                    if current["kind"] == "scenario"
                    else "CHK.requirement.statement"
                )
                reading.problems.append(
                    Problem(check, f"{current['id']} contains a nested heading", number)
                )
            close()
            text, _ = strip_heading_anchor(heading.group(2))
            scenario = SCENARIO_HEADING.match(text)
            requirement = REQUIREMENT_HEADING.match(text)
            if (scenario or requirement) and not 2 <= level <= 5:
                reading.problems.append(
                    Problem(
                        "CHK.scenario.steps"
                        if scenario
                        else "CHK.requirement.statement",
                        "requirement and scenario headings use levels 2 to 5",
                        number,
                    )
                )
            if scenario:
                current = {
                    "kind": "scenario",
                    "id": scenario.group(1),
                    "title": scenario.group(2).strip(),
                    "line": number,
                    "level": level,
                    "steps": [],
                    "phase": None,
                }
            elif requirement:
                current = {
                    "kind": "requirement",
                    "id": requirement.group(1),
                    "title": requirement.group(2).strip(),
                    "line": number,
                    "level": level,
                    "statement": None,
                }
            elif re.match(r"^scenario\.[a-z0-9]", text):
                reading.problems.append(
                    Problem(
                        "CHK.scenario.steps",
                        f"malformed scenario heading: {text}",
                        number,
                    )
                )
            elif re.match(r"^req\.[a-z0-9]", text):
                reading.problems.append(
                    Problem(
                        "CHK.requirement.statement",
                        f"malformed requirement heading: {text}",
                        number,
                    )
                )
            index += 1
            continue
        item = LIST_ITEM.match(line)
        if item and REQUIREMENT_ITEM.match(item.group(1).strip()):
            reading.problems.append(
                Problem(
                    "CHK.requirement.statement",
                    "a list item cannot begin with a requirement identity; "
                    "a requirement is a heading section",
                    number,
                )
            )
        if current is None:
            index += 1
            continue
        if current["kind"] == "requirement":
            if current["statement"] is None and line.strip():
                if item:
                    reading.problems.append(
                        Problem(
                            "CHK.requirement.statement",
                            f"requirement {current['id']} must state its SHALL sentence before any list",
                            number,
                        )
                    )
                    current["statement"] = ""
                    index += 1
                    continue
                end = index
                while (
                    end < len(logical)
                    and logical[end][1] == "prose"
                    and logical[end][2].strip()
                ):
                    if HEADING.match(logical[end][2]):
                        break
                    end += 1
                statement = " ".join(entry[2].strip() for entry in logical[index:end])
                if len(SHALL.findall(statement)) != 1:
                    reading.problems.append(
                        Problem(
                            "CHK.requirement.statement",
                            f"requirement {current['id']} statement must contain SHALL or SHALL NOT exactly once",
                            number,
                        )
                    )
                elif not one_sentence(statement):
                    reading.problems.append(
                        Problem(
                            "CHK.requirement.statement",
                            f"requirement {current['id']} statement must be one sentence",
                            number,
                        )
                    )
                current["statement"] = statement
                index = end
                continue
            index += 1
            continue
        if not item:
            index += 1
            continue
        text = item.group(1).strip()
        step = STEP.match(text)
        if not step:
            reading.problems.append(
                Problem(
                    "CHK.scenario.steps",
                    f"scenario {current['id']} contains a list item that is not a "
                    "GIVEN/WHEN/THEN/AND/BUT step",
                    number,
                )
            )
            index += 1
            continue
        keyword = step.group(1)
        if keyword in {"AND", "BUT"}:
            if current["phase"] is None:
                reading.problems.append(
                    Problem(
                        "CHK.scenario.steps",
                        f"scenario {current['id']} cannot start with {keyword}",
                        number,
                    )
                )
        else:
            previous = current["phase"]
            if previous is None and keyword == "THEN":
                reading.problems.append(
                    Problem(
                        "CHK.scenario.steps",
                        f"scenario {current['id']} cannot start with THEN",
                        number,
                    )
                )
            if previous is not None and STEP_ORDER[keyword] <= STEP_ORDER[previous]:
                reading.problems.append(
                    Problem(
                        "CHK.scenario.steps",
                        f"scenario {current['id']} steps must follow GIVEN, WHEN, THEN order",
                        number,
                    )
                )
            current["phase"] = keyword
        current["steps"].append((keyword, step.group(2).strip()))
        index += 1
    close()


def _fences(lines, reading: Reading) -> None:
    """Contract and diagram fences at the outer level."""
    current: dict | None = None
    for number, kind, line in lines:
        if kind == "fence-open":
            info = re.sub(r"^ {0,3}(?:`{3,}|~{3,})", "", line).strip()
            words = info.split()
            language = words[0] if words else ""
            current = {"language": language, "info": words, "line": number, "body": []}
        elif kind == "fenced" and current is not None:
            current["body"].append(line)
        elif kind == "fence-close" and current is not None:
            _close_fence(current, reading)
            current = None
    if current is not None:
        if current["language"] in {"concorde-contract", *DIAGRAM_LANGUAGES}:
            reading.problems.append(
                Problem(
                    "CHK.contract.fence"
                    if current["language"] == "concorde-contract"
                    else "CHK.view.marked",
                    f"unclosed {current['language']} fence",
                    current["line"],
                )
            )


def _close_fence(fence: dict, reading: Reading) -> None:
    body = "\n".join(fence["body"])
    if fence["language"] == "concorde-contract":
        reading.contracts.append((fence["line"], body))
    elif fence["language"] in DIAGRAM_LANGUAGES:
        reading.diagrams.append(
            (fence["line"], fence["language"], tuple(fence["info"][1:]), body)
        )


def contract_problems(body: str) -> tuple[dict | None, list[str]]:
    """Decode one contract fence and report every CHK.contract.fence violation."""
    from .schema import admit, validate
    from .typed_data import decode

    try:
        value = decode(body)
    except ValueError as error:
        return None, [f"contract fence is not JSON: {error}"]
    if not isinstance(value, dict):
        return None, ["contract fence must be a JSON object"]
    problems = []
    fields = {"id", "version", "schema", "semantics", "example"}
    if set(value) != fields:
        problems.append(f"contract fence must have exactly the fields {sorted(fields)}")
    if not isinstance(value.get("id"), str) or not IDENTITY.fullmatch(
        value.get("id", "")
    ):
        problems.append(f"contract identity is invalid: {value.get('id')!r}")
    if type(value.get("version")) is not int or value.get("version", 0) < 1:
        problems.append("contract version must be a positive integer")
    if (
        not isinstance(value.get("semantics"), str)
        or not value.get("semantics", "").strip()
    ):
        problems.append("contract semantics must be nonempty")
    if "schema" in value:
        try:
            admit(value["schema"])
            if _remote_reference(value["schema"]):
                problems.append(
                    "contract schema must not load remote or Spec resources"
                )
            elif "example" in value:
                validate(value["example"], value["schema"])
        except ValueError as error:
            problems.append(f"contract schema or example is invalid: {error}")
    return value, problems


def _remote_reference(schema) -> bool:
    if isinstance(schema, dict):
        reference = schema.get("$ref")
        if isinstance(reference, str) and not reference.startswith("#"):
            return True
        return any(_remote_reference(item) for item in schema.values())
    if isinstance(schema, list):
        return any(_remote_reference(item) for item in schema)
    return False


def _cells(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|") and not stripped.endswith("\\|"):
        stripped = stripped[:-1]
    cells, current, code = [], "", False
    index = 0
    while index < len(stripped):
        character = stripped[index]
        if (
            character == "\\"
            and index + 1 < len(stripped)
            and stripped[index + 1] == "|"
        ):
            current += "|"
            index += 2
            continue
        if character == "`":
            code = not code
        if character == "|" and not code:
            cells.append(current.strip())
            current = ""
        else:
            current += character
        index += 1
    cells.append(current.strip())
    return cells


def _terminology(lines, found: list[Heading], reading: Reading) -> None:
    """Parse the Terminology section's table into defining and import rows."""
    top = [heading for heading in found if heading.level <= 2]
    section = next(
        (
            heading
            for heading in top
            if heading.level == 2 and heading.text == "Terminology"
        ),
        None,
    )
    if section is None:
        return
    end = next((heading.line for heading in top if heading.line > section.line), None)
    region = [
        (number, kind, line)
        for number, kind, line in lines
        if number > section.line and (end is None or number < end)
    ]
    tables: list[list[tuple[int, str]]] = []
    previous_table = False
    for number, kind, line in region:
        is_row = kind == "prose" and line.strip().startswith("|")
        if is_row:
            if not previous_table:
                tables.append([])
            tables[-1].append((number, line))
        previous_table = is_row
    rows: list[TermRow] = []
    reading.terminology = rows
    if len(tables) > 1:
        reading.problems.append(
            Problem(
                "CHK.terminology.rows",
                "a Terminology section holds at most one table",
                tables[1][0][0],
            )
        )
    if not tables:
        return
    table = tables[0]
    header = _cells(table[0][1])
    if (
        header != ["Term", "Definition"]
        or len(table) < 2
        or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in _cells(table[1][1]))
    ):
        reading.problems.append(
            Problem(
                "CHK.terminology.rows",
                "the Terminology table must have the columns Term and Definition",
                table[0][0],
            )
        )
        return
    for number, line in table[2:]:
        cells = _cells(line)
        if len(cells) != 2:
            reading.problems.append(
                Problem(
                    "CHK.terminology.rows",
                    "a Terminology row has exactly two cells",
                    number,
                )
            )
            continue
        term, definition = cells
        link = re.fullmatch(r"\[([^\]]+)\]\(([^\s)]+)\)", term)
        if link:
            rows.append(
                TermRow(number, link.group(1).strip(), link.group(2), definition)
            )
        else:
            rows.append(TermRow(number, term.strip("*_ ").strip(), None, definition))


def _links(lines, reading: Reading) -> None:
    for number, kind, line in lines:
        if kind != "prose":
            continue
        text = INLINE_CODE.sub("", line)
        for match in LINK.finditer(text):
            reading.links.append((number, match.group(2)))


def parse_reading(text: str) -> Reading:
    """Every declaration of one reading document, with its syntax problems."""
    reading = Reading(text)
    lines = walk_lines(text)
    reading.headings = headings(lines)
    _anchors(lines, reading.headings, reading)
    _definitions(lines, reading)
    _fences(lines, reading)
    _terminology(lines, reading.headings, reading)
    _links(lines, reading)
    return reading


def test_declarations(text: str) -> list[int]:
    """Lines outside fences holding test-declaration syntax."""
    return [
        number
        for number, kind, line in walk_lines(text)
        if kind == "prose" and TEST_DECLARATION.search(line)
    ]


def entry_section_problems(text: str) -> list[Problem]:
    """CHK.document.sections and CHK.document.prose for an entry ``module.md``."""
    lines = walk_lines(text)
    found = headings(lines)
    top = [heading for heading in found if heading.level == 2]
    problems = []
    counts = {
        name: sum(heading.text == name for heading in top) for name in READING_SECTIONS
    }
    wrong = [f"{name} ({count} times)" for name, count in counts.items() if count != 1]
    if wrong:
        problems.append(
            Problem(
                "CHK.document.sections",
                "an entry has the level-2 sections Purpose, Terminology, Usage, Design and "
                "Relationships, each exactly once in any order; found "
                + ", ".join(wrong),
            )
        )
        return problems
    total = lines[-1][0] if lines else 0
    heading_lines = {heading.line for heading in found}
    for heading in (heading for heading in top if heading.text in READING_SECTIONS):
        end = next(
            (
                later.line
                for later in found
                if later.line > heading.line and later.level <= 2
            ),
            total + 1,
        )
        region = [(n, k, line) for n, k, line in lines if heading.line < n < end]
        if heading.text == "Purpose":
            if not any(k == "prose" and line.strip() for _, k, line in region) or any(
                k != "prose"
                or n in heading_lines
                or re.match(r"\s*(?:\||[-*+] |\d+[.)] |>)", line)
                for n, k, line in region
                if line.strip() or k != "prose"
            ):
                problems.append(
                    Problem(
                        "CHK.document.prose",
                        "Purpose is nonempty plain prose without headings, lists, tables or fences",
                        heading.line,
                    )
                )
        elif heading.text != "Terminology":
            meaningful = [
                line
                for n, k, line in region
                if k == "prose"
                and n not in heading_lines
                and line.strip()
                and not HTML_ANCHOR_LINE.match(line)
            ]
            prose_text = LINK.sub("", " ".join(meaningful))
            prose_text = re.sub(r"[|\-*+>#:`\s]", "", prose_text)
            if not prose_text:
                problems.append(
                    Problem(
                        "CHK.document.prose",
                        f"{heading.text} holds explanatory prose, not only links, headings or diagrams",
                        heading.line,
                    )
                )
    return problems


def first_section(text: str) -> str | None:
    found = [heading for heading in headings(walk_lines(text)) if heading.level == 2]
    return found[0].text if found else None


def link_target(document_path: str, href: str) -> tuple[str, str] | None:
    """The project-relative path and fragment a local link addresses, or None for external links."""
    import posixpath
    from urllib.parse import unquote, urlsplit

    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or parsed.path.startswith("/"):
        return None
    location = unquote(parsed.path)
    path = (
        posixpath.normpath(posixpath.join(posixpath.dirname(document_path), location))
        if location
        else document_path
    )
    return path, unquote(parsed.fragment)


# --- D2 diagrams ----------------------------------------------------------------------------

# D2 keywords: each sets how a diagram looks or adds structure beyond shapes, nesting and edges.
D2_KEYWORDS = frozenset(
    {
        "label",
        "shape",
        "style",
        "class",
        "classes",
        "direction",
        "near",
        "icon",
        "tooltip",
        "link",
        "width",
        "height",
        "top",
        "left",
        "constraint",
        "vars",
        "layers",
        "scenarios",
        "steps",
        "grid-rows",
        "grid-columns",
        "grid-gap",
        "vertical-gap",
        "horizontal-gap",
        "source-arrowhead",
        "target-arrowhead",
        "filled",
        "multiple",
        "3d",
    }
)
D2_OTHER_ARROWS = ("<->", "<-", "--")


class DiagramError(SpecError):
    """A checked D2 diagram outside the semantic subset of the Views chapter."""

    DEFAULT_CODE = "invalid_diagram"

    def __init__(self, message: str, line: int) -> None:
        super().__init__(message, line=line)


@dataclass(frozen=True)
class DiagramShape:
    """One shape: its key path from the root and the text that resolves it."""

    path: tuple[str, ...]
    label: str
    line: int


@dataclass(frozen=True)
class DiagramEdge:
    source: tuple[str, ...]
    target: tuple[str, ...]
    label: str | None
    line: int


def _d2_statements(source: str) -> list[tuple[str, int, str]]:
    """Statements as (text, line, ending), where ending is 'open', 'close' or 'end'."""
    result: list[tuple[str, int, str]] = []
    text = ""
    line = start = 1
    quote = False
    index = 0

    def flush(ending: str) -> None:
        nonlocal text
        if text.strip():
            result.append((text.strip(), start, ending))
        elif ending == "open":
            raise DiagramError("a block opens without a shape", line)
        text = ""

    while index < len(source):
        char = source[index]
        if quote:
            text += char
            if char == "\\" and index + 1 < len(source):
                index += 1
                text += source[index]
            elif char == '"':
                quote = False
            elif char == "\n":
                raise DiagramError("a quoted key or label is not closed", line)
            index += 1
            continue
        if not text.strip():
            start = line
        if char == '"':
            quote = True
            text += char
        elif char == "#":
            while index + 1 < len(source) and source[index + 1] != "\n":
                index += 1
        elif char in "\n;":
            flush("end")
            if char == "\n":
                line += 1
        elif char == "{":
            flush("open")
        elif char == "}":
            flush("end")
            result.append(("", line, "close"))
        elif char in "|`$[]":
            raise DiagramError(
                f"{char!r} (block strings, substitutions or arrays) is not part of the "
                "semantic subset",
                line,
            )
        else:
            text += char
        index += 1
    if quote:
        raise DiagramError("a quoted key or label is not closed", line)
    flush("end")
    return result


def _split_outside(text: str, separator: str) -> list[str]:
    """Split text at every separator outside double quotes."""
    parts: list[str] = []
    current = ""
    quote = False
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"' and (index == 0 or text[index - 1] != "\\"):
            quote = not quote
        if not quote and text.startswith(separator, index):
            parts.append(current)
            current = ""
            index += len(separator)
            continue
        current += char
        index += 1
    parts.append(current)
    return parts


def _unquote(text: str, line: int) -> str:
    stripped = text.strip()
    if stripped.startswith('"'):
        if len(stripped) < 2 or not stripped.endswith('"'):
            raise DiagramError(f"malformed quoted text {stripped}", line)
        return re.sub(r"\\(.)", r"\1", stripped[1:-1])
    return stripped


def _key_path(text: str, line: int) -> tuple[str, ...]:
    segments = [segment.strip() for segment in _split_outside(text.strip(), ".")]
    for segment in segments:
        if not segment:
            raise DiagramError(f"empty key in {text.strip()!r}", line)
        if segment.startswith('"'):
            continue
        if segment in D2_KEYWORDS:
            raise DiagramError(
                f"{segment!r} sets how the diagram looks; styling and layout belong to the "
                "publisher",
                line,
            )
        if re.search(r"[*&!()<>@]", segment) or segment.startswith("..."):
            raise DiagramError(
                f"{segment!r} uses globs, filters, references or imports, which are not part "
                "of the semantic subset",
                line,
            )
    return tuple(_unquote(segment, line) for segment in segments)


def diagram_model(
    source: str,
) -> tuple[list[DiagramShape], list[DiagramEdge]]:
    """Shapes and directed edges of one checked D2 diagram in the semantic subset.

    A shape is ``key`` or ``key: Label``, a ``{ ... }`` block after a shape nests statements in it,
    and an edge is ``a -> b`` or ``a -> b: label`` between key paths relative to the enclosing
    block; shapes named only by an edge or a dotted path are declared by that use. Anything else
    raises DiagramError with the line of the block that holds it.
    """
    shapes: dict[tuple[str, ...], DiagramShape] = {}
    edges: list[DiagramEdge] = []
    scope: list[tuple[str, ...]] = [()]

    def declare(path: tuple[str, ...], line: int, label: str | None = None) -> None:
        for size in range(1, len(path) + 1):
            prefix = path[:size]
            own = label if size == len(path) else None
            if prefix not in shapes:
                shapes[prefix] = DiagramShape(prefix, own or prefix[-1], line)
            elif own is not None:
                shapes[prefix] = DiagramShape(prefix, own, shapes[prefix].line)

    for text, line, ending in _d2_statements(source):
        if ending == "close":
            if len(scope) == 1:
                raise DiagramError("a block closes that was never opened", line)
            scope.pop()
            continue
        here = scope[-1]
        for arrow in D2_OTHER_ARROWS:
            if len(_split_outside(text, arrow)) > 1:
                raise DiagramError(
                    f"{arrow!r} has no single declared direction; draw every edge with '->'",
                    line,
                )
        ends = _split_outside(text, "->")
        if len(ends) > 1:
            if ending == "open":
                raise DiagramError(
                    "an edge block styles the edge; styling belongs to the publisher",
                    line,
                )
            last = _split_outside(ends[-1], ":")
            if len(last) > 2:
                raise DiagramError(f"malformed edge {text!r}", line)
            ends[-1] = last[0]
            label = _unquote(last[1], line) if len(last) == 2 else None
            paths = [here + _key_path(end, line) for end in ends]
            for path in paths:
                declare(path, line)
            for source_path, target_path in pairwise(paths):
                edges.append(DiagramEdge(source_path, target_path, label or None, line))
            continue
        parts = _split_outside(text, ":")
        if len(parts) > 2:
            raise DiagramError(f"malformed shape {text!r}", line)
        path = here + _key_path(parts[0], line)
        label = _unquote(parts[1], line) if len(parts) == 2 else None
        if label == "":
            raise DiagramError(f"empty label in {text!r}", line)
        declare(path, line, label)
        if ending == "open":
            scope.append(path)
    if len(scope) > 1:
        raise DiagramError(
            f"the block of {'.'.join(scope[-1])} is not closed",
            len(source.splitlines()) or 1,
        )
    return list(shapes.values()), edges


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True)
