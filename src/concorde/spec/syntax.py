"""Protocol 11 reading syntax: anchors, sections, Terminology tables, definitions and diagrams.

Every parser here reads one reading document's text and returns what it declares together with
the problems it found, each tagged with the identity of the check it violates. Nothing here reads
a file, follows a link or decides whether prose is sufficient.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .repository_base import HEADING, IDENTITY, walk_lines

READING_SECTIONS = ("Purpose", "Terminology", "Usage", "Design", "Relationships")
HEADING_ANCHOR = re.compile(r"[ \t]+\{#([^{}\s]+)\}[ \t]*$")
HTML_ANCHOR_LINE = re.compile(r'^[ \t]*(?:<a id="[^"]*"></a>[ \t]*)+$')
HTML_ANCHOR = re.compile(r'<a id="([^"]*)"></a>')
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
    mermaid: list = field(default_factory=list)
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
    anchor extends to the next heading; either ends at the next anchor group. Requirement and
    scenario headings supply their identity as their anchor.
    """
    heading_at = {heading.line: heading for heading in found}
    groups: list[tuple[tuple[str, ...], int, int | None, str]] = []
    seen: set[str] = set()
    for number, kind, line in lines:
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
    """Contract and Mermaid fences at the outer level."""
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
        if current["language"] in {"concorde-contract", "mermaid"}:
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
    elif fence["language"] == "mermaid":
        reading.mermaid.append((fence["line"], tuple(fence["info"][1:]), body))


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
    if [heading.text for heading in top[:5]] != list(READING_SECTIONS) or any(
        sum(heading.text == name for heading in top) != 1 for name in READING_SECTIONS
    ):
        problems.append(
            Problem(
                "CHK.document.sections",
                "an entry starts with the level-2 sections Purpose, Terminology, Usage, Design "
                "and Relationships, each once and in this order",
            )
        )
        return problems
    total = lines[-1][0] if lines else 0
    heading_lines = {heading.line for heading in found}
    for index, heading in enumerate(top[:5]):
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


# --- Mermaid flowcharts ---------------------------------------------------------------------

DIAGRAM_KEYWORDS = (
    "flowchart",
    "graph",
    "subgraph",
    "end",
    "classDef",
    "class",
    "style",
    "linkStyle",
    "direction",
    "click",
    "accTitle",
    "accDescr",
)
EDGE = re.compile(
    r"(?P<op>x--x|o--o|<-->|-->|---|-\.->|-\.-|==>|===|--x|--o|<--|<==)"
    r"(?:[ \t]*\|(?P<label>[^|]*)\|)?"
)
INLINE_EDGE = re.compile(
    r"--[ \t]+(?P<label>[^-]+?)[ \t]+-->|-\.[ \t]+(?P<label2>[^.]+?)[ \t]+\.->"
    r"|==[ \t]+(?P<label3>[^=]+?)[ \t]+==>"
)
NODE = re.compile(r"(?P<id>[A-Za-z0-9_]+)(?::::\w+)?")
OPENERS = ("(((", "[[", "[(", "((", "{{", "[/", "[\\", "[", "(", "{", ">")
CLOSERS = (")))", "]]", ")]", "))", "}}", "/]", "\\]", "]", ")", "}")


# Edge operators by the direction they draw: forward from the left node to the right one, reversed
# from the right node to the left one, or without a single direction (undirected or both ways).
REVERSED_EDGES = frozenset({"<--", "<=="})
UNDIRECTED_EDGES = frozenset({"---", "-.-", "===", "<-->", "x--x", "o--o"})


class DiagramError(ValueError):
    pass


class UndirectedEdgeError(DiagramError):
    """A checked edge drawn without exactly one direction."""


def first_line(label: str) -> str:
    text = label.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]
    text = re.split(r"<br\s*/?>", text)[0]
    return text.strip()


def diagram_type(body: str) -> str | None:
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("%%"):
            continue
        return line.split()[0]
    return None


def _scan_node(line: str, position: int) -> tuple[str, str | None, int]:
    match = NODE.match(line, position)
    if not match:
        raise DiagramError(
            f"cannot interpret diagram text near {line[position : position + 20]!r}"
        )
    node_id = match.group("id")
    if node_id in DIAGRAM_KEYWORDS:
        raise DiagramError(
            f"reserved Mermaid keyword cannot be a node identifier: {node_id}"
        )
    position = match.end()
    rest = line[position:]
    for opener in OPENERS:
        if rest.startswith(opener):
            inner_start = position + len(opener)
            if line[inner_start : inner_start + 1] == '"':
                end = line.find('"', inner_start + 1)
                if end < 0:
                    raise DiagramError("unterminated quoted node label")
                label = line[inner_start + 1 : end]
                after = end + 1
            else:
                closer_index = min(
                    (
                        line.find(c, inner_start)
                        for c in CLOSERS
                        if line.find(c, inner_start) >= 0
                    ),
                    default=-1,
                )
                if closer_index < 0:
                    raise DiagramError("unterminated node label")
                label = line[inner_start:closer_index]
                after = closer_index
            for closer in CLOSERS:
                if line.startswith(closer, after):
                    after += len(closer)
                    break
            else:
                raise DiagramError("node shape is not closed")
            if line.startswith(":::", after):
                style = re.compile(r":::\w+").match(line, after)
                if style is None:
                    raise DiagramError("node style name is missing")
                after = style.end()
            return node_id, label, after
    return node_id, None, position


def flowchart_model(
    text: str,
) -> tuple[dict[str, str], list[tuple[str, str | None, str]]]:
    """Node labels and directed, labeled edges of one Mermaid flowchart.

    Each edge is ``(source, label, target)`` in the drawn direction: ``<--`` and ``<==`` point from
    the right node to the left one. An edge without exactly one direction (``---``, ``-.-``,
    ``===``, ``<-->``, ``x--x``, ``o--o``) raises UndirectedEdgeError; an unreadable line raises
    DiagramError.
    """
    nodes: dict[str, str] = {}
    edges: list[tuple[str, str | None, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("%%"):
            continue
        head = re.split(r"[\s:]", line, 1)[0]
        if head in DIAGRAM_KEYWORDS:
            continue
        position = 0
        groups: list[list[str]] = []
        pending_edges: list[str | None] = []
        reversed_edges: list[bool] = []
        current: list[str] = []
        while position < len(line):
            while position < len(line) and line[position] in " \t":
                position += 1
            if position >= len(line):
                break
            if line.startswith("&", position):
                position += 1
                continue
            inline = INLINE_EDGE.match(line, position)
            if inline:
                label = (
                    inline.group("label")
                    or inline.group("label2")
                    or inline.group("label3")
                )
                groups.append(current)
                current = []
                pending_edges.append(label.strip() if label and label.strip() else None)
                reversed_edges.append(False)
                position = inline.end()
                continue
            edge = EDGE.match(line, position)
            if edge:
                operator = edge.group("op")
                if operator in UNDIRECTED_EDGES:
                    raise UndirectedEdgeError(
                        f"edge {operator!r} has no single direction: {raw.strip()!r}"
                    )
                label = edge.group("label")
                groups.append(current)
                current = []
                pending_edges.append(label.strip() if label and label.strip() else None)
                reversed_edges.append(operator in REVERSED_EDGES)
                position = edge.end()
                continue
            node_id, label, position = _scan_node(line, position)
            if label is not None:
                nodes[node_id] = label
            else:
                nodes.setdefault(node_id, node_id)
            current.append(node_id)
        groups.append(current)
        if len(groups) != len(pending_edges) + 1 or any(not group for group in groups):
            raise DiagramError(f"cannot interpret diagram line: {raw.strip()!r}")
        for index, label in enumerate(pending_edges):
            for left in groups[index]:
                for right in groups[index + 1]:
                    edges.append(
                        (right, label, left)
                        if reversed_edges[index]
                        else (left, label, right)
                    )
    return nodes, edges


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True)
