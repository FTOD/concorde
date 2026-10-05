"""The decidable part of the Protocol's sentence style (``protocol/style.md``), measured on Markdown.

The style's rules are inspired by the structural rules of ASD-STE100 Simplified Technical English;
only the few a program decides are measured here, and each is reported at strictness ``warning``:

- ``CHK.style.sentence-length``: a sentence of more than ``SENTENCE_LIMIT`` words, or a concept
  definition of more than ``DEFINITION_LIMIT`` words, but never the statement of a requirement;
- ``CHK.style.semicolon``: a semicolon in prose;
- ``CHK.style.one-obligation``: a sentence with more than one normative keyword.

Only prose is measured, as a reader sees it: fences, headings, tables, front matter and HTML
anchors are skipped, a link counts as its text, and an inline code span counts as one word. Each
paragraph and each list item is split into sentences by the deterministic sentence-break rule of
``CHK.concept.definition``. A requirement's statement is the first sentence of the paragraph that
follows its heading, as ``CHK.requirement.statement`` reads it: it keeps its one obligation with
all its conditions, exceptions and failures, so its length is not measured.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .repository_base import HEADING as SECTION_HEADING
from .repository_base import walk_lines
from .syntax import (
    HTML_ANCHOR,
    INLINE_CODE,
    LINK,
    LIST_ITEM,
    REQUIREMENT_HEADING,
    SENTENCE_BREAK,
    strip_heading_anchor,
)

# The sentence length above which a sentence is reported. The style's target is 25 words or
# fewer, and the check warns only where a sentence is clearly too long to read in one pass.
SENTENCE_LIMIT = 35
# The length above which a concept definition is reported. A definition is one sentence that must
# identify its term, so it may be longer than a sentence of a reading.
DEFINITION_LIMIT = 50
# A normative keyword of the Protocol's requirement language, a NOT after it included.
KEYWORD = re.compile(r"\b(?:MUST|SHALL|SHOULD|MAY)(?: NOT)?\b")
WORD = re.compile(r"[^\W_]")
HEADING = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")
TABLE_ROW = re.compile(r"^[ \t]*\|")
QUOTE = re.compile(r"^[ \t]*>[ \t]?")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
EMPHASIS = re.compile(r"(\*\*|__|\*|(?<!\w)_|_(?!\w))")
# What stands for the n-th inline code span while a block is split: one word, capitalized so that
# a sentence may start with it, and restored in the sentence's text.
CODE_WORD = "Code\x02{}\x02"
CODE_MARK = re.compile("Code\x02(\\d+)\x02")

STYLE_CHECKS = (
    "CHK.style.sentence-length",
    "CHK.style.semicolon",
    "CHK.style.one-obligation",
)


@dataclass(frozen=True)
class Sentence:
    """One sentence of prose: the line it starts on, its text as a reader sees it, the same text
    with each inline code span replaced by one word, its number of words, and whether it is the
    statement of a requirement."""

    line: int
    text: str
    prose: str
    words: int
    statement: bool = False


@dataclass(frozen=True)
class StyleProblem:
    """One violation of a decidable style rule, at the line where its sentence starts."""

    check: str
    line: int
    message: str


def _front_matter_end(lines: list[str]) -> int:
    """The number of leading lines that are YAML front matter, or 0."""
    if not lines or lines[0].strip() != "---":
        return 0
    for index in range(1, len(lines)):
        if lines[index].strip() in ("---", "..."):
            return index + 1
    return 0


def _blocks(text: str) -> list[tuple[bool, list[tuple[int, str]]]]:
    """Each paragraph and each list item of prose, as its lines with their numbers, marked when
    it is the statement paragraph of a requirement."""
    lines = walk_lines(text)
    skip = _front_matter_end([line for _, _, line in lines])
    blocks: list[tuple[bool, list[tuple[int, str]]]] = []
    current: list[tuple[int, str]] | None = None
    # Whether a requirement heading was read and its statement paragraph not yet: like
    # ``CHK.requirement.statement``, only blank lines may stand between the two.
    statement = False
    for number, kind, line in lines:
        if number <= skip or kind != "prose":
            current = None
            statement = False
            continue
        line = QUOTE.sub("", line)
        if not line.strip():
            current = None
            continue
        section = SECTION_HEADING.match(line)
        if section:
            statement = bool(
                REQUIREMENT_HEADING.match(strip_heading_anchor(section.group(2))[0])
            )
        if (
            section
            or HEADING.match(line)
            or TABLE_ROW.match(line)
            or not HTML_ANCHOR.sub("", line).strip()
        ):
            current = None
            statement = statement and bool(section)
            continue
        item = LIST_ITEM.match(line)
        if item:
            current = [(number, item.group(1))]
            blocks.append((False, current))
            statement = False
            continue
        if current is None:
            current = []
            blocks.append((statement, current))
            statement = False
        current.append((number, line.strip()))
    return blocks


def _plain(text: str, codes: list[str]) -> str:
    """Text as a reader sees it: a link as its text, no anchors, comments or emphasis markers,
    and each inline code span replaced by a mark that ``codes`` resolves."""

    def code(match: re.Match) -> str:
        codes.append(match.group(0))
        return CODE_WORD.format(len(codes) - 1)

    text = INLINE_CODE.sub(code, text)
    text = COMMENT.sub(" ", text)
    text = HTML_ANCHOR.sub(" ", text)
    text = LINK.sub(lambda match: match.group(1), text)
    return EMPHASIS.sub("", text)


def sentences(text: str) -> list[Sentence]:
    """Every sentence of the prose of a Markdown text, in order."""
    found: list[Sentence] = []
    for statement, block in _blocks(text):
        # Code and links are resolved over the whole block, since either may wrap.
        codes: list[str] = []
        plain = _plain("\n".join(line for _, line in block), codes)
        flat = plain.replace("\n", " ")
        bounds = [
            0,
            *(match.end() for match in SENTENCE_BREAK.finditer(flat)),
            len(flat),
        ]
        for begin, end in zip(bounds, bounds[1:]):
            part = " ".join(flat[begin:end].split())
            words = sum(1 for token in part.split() if WORD.search(token))
            if not words:
                continue
            first = begin + len(flat[begin:end]) - len(flat[begin:end].lstrip())
            line = block[plain.count("\n", 0, first)][0]
            shown = CODE_MARK.sub(lambda match: codes[int(match.group(1))], part)
            prose = CODE_MARK.sub("Code", part)
            # Only the first sentence of a statement paragraph is the requirement's statement.
            found.append(Sentence(line, shown, prose, words, statement and begin == 0))
    return found


def style_problems(text: str, limit: int = SENTENCE_LIMIT) -> list[StyleProblem]:
    """Every violation of the decidable style rules in the prose of a Markdown text, a sentence
    being too long above ``limit`` words unless it is the statement of a requirement."""
    problems: list[StyleProblem] = []
    for sentence in sentences(text):
        if sentence.words > limit and not sentence.statement:
            problems.append(
                StyleProblem(
                    "CHK.style.sentence-length",
                    sentence.line,
                    f"sentence of {sentence.words} words, more than {limit}: "
                    f"{_quote(sentence.text)}",
                )
            )
        if ";" in sentence.prose:
            problems.append(
                StyleProblem(
                    "CHK.style.semicolon",
                    sentence.line,
                    f"semicolon in prose: {_quote(sentence.text)}",
                )
            )
        keywords = KEYWORD.findall(sentence.prose)
        if len(keywords) > 1:
            problems.append(
                StyleProblem(
                    "CHK.style.one-obligation",
                    sentence.line,
                    f"{len(keywords)} normative keywords ({', '.join(keywords)}) in one "
                    f"sentence: {_quote(sentence.text)}",
                )
            )
    return problems


def _quote(text: str, length: int = 80) -> str:
    return repr(text if len(text) <= length else text[: length - 1] + "…")
