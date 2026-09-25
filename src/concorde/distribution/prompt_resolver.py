"""Deterministic resolution of Concorde prompt sources.

A prompt is a Markdown file with YAML front matter declaring ``audience: worker | ambient |
shared``. A prompt body may reference other prompts through an explicit ``@path.md`` reference
that occupies a whole line starting at column one:

    @prompts/workers/common/boundary.md
    @prompts/workers/common/result.md KIND=review

Resolution is a pure function of the source tree: given a root prompt, it walks references,
binds per-inclusion ``{KEY}`` variables, and returns the fully substituted text. It performs no
network or process I/O beyond reading files under ``project_root``.

Every prompt lives under ``prompts/`` and must declare its own ``audience``. Independent standard chapters under
``protocol/`` are plain Markdown, implicitly shared, and can only be included by Protocol adapters
or other standard chapters. They are not project Specs or agent prompt definitions.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ..spec.frontmatter import FrontMatterError, parse_document

AUDIENCES = frozenset({"worker", "ambient", "shared"})
PROTOCOL_PREFIX = "prompts/protocol/"
PROTOCOL_TEXT_ROOT = "protocol/"
SPECS_ROOT = "specs/"

# Path-shaped tokens only: ordinary mentions, emails and decorators stay literal.
_DIRECTIVE_LINE = re.compile(r"^@(?P<target>[^\s@`\"'()<>]+)(?:[ \t]+.*)?$")
# A variable is {name}; {{name}} is the literal text {name}, such as a placeholder the prompt
# explains to its reader.
_VARIABLE = re.compile(r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)\}(?!\})")
_ESCAPED = re.compile(r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}")
_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class PromptResolverError(ValueError):
    """A prompt source violates one deterministic resolution rule."""

    def __init__(self, rule_id: str, message: str):
        self.rule_id = rule_id
        super().__init__(f"{rule_id}: {message}")


@dataclass(frozen=True)
class ResolvedPrompt:
    """One fully substituted root prompt and the exact sources that contributed to it."""

    body: str
    sources: tuple[str, ...]


def _safe_relative(value: str) -> str:
    candidate = PurePosixPath(value)
    if (
        not value
        or candidate.is_absolute()
        or value.startswith("~")
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or "\\" in value
        or ":" in value
        or any(ord(char) < 32 for char in value)
    ):
        raise PromptResolverError(
            "CONCORDE-PROMPT-MISSING-001",
            f"include target must be a safe repository-relative path: {value!r}",
        )
    return candidate.as_posix()


def _read(project_root: Path, relative: str) -> str:
    path = project_root / relative
    if (
        any(
            (project_root / Path(*Path(relative).parts[:i])).is_symlink()
            for i in range(1, len(Path(relative).parts) + 1)
        )
        or not path.is_file()
    ):
        raise PromptResolverError(
            "CONCORDE-PROMPT-MISSING-001",
            f"include target is missing or unsafe: {relative}",
        )
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise PromptResolverError(
            "CONCORDE-PROMPT-MISSING-001", f"cannot read prompt {relative}: {error}"
        ) from error


def _parse_prompt_file(project_root: Path, relative: str) -> tuple[str, str]:
    """Return (audience, body) for one file under prompts/."""

    text = _read(project_root, relative)
    if relative.startswith(PROTOCOL_TEXT_ROOT):
        if not relative.endswith(".md"):
            raise PromptResolverError(
                "CONCORDE-PROMPT-SCOPE-001",
                f"Protocol text must be Markdown: {relative}",
            )
        return "shared", text
    try:
        metadata, body = parse_document(text, relative)
    except FrontMatterError as error:
        raise PromptResolverError(
            "CONCORDE-PROMPT-AUDIENCE-002",
            f"invalid prompt front matter in {relative}: {error}",
        ) from error
    audience = metadata.get("audience")
    if audience not in AUDIENCES:
        raise PromptResolverError(
            "CONCORDE-PROMPT-AUDIENCE-002",
            f"prompt {relative} must declare audience as one of {sorted(AUDIENCES)}, found {audience!r}",
        )
    unknown = set(metadata) - {"audience"}
    if unknown:
        raise PromptResolverError(
            "CONCORDE-PROMPT-AUDIENCE-002",
            f"prompt {relative} has unsupported front matter keys: {sorted(unknown)}",
        )
    return audience, body


def _parse_directive(rest: str | None, relative: str) -> tuple[str, dict[str, str]]:
    if not rest:
        raise PromptResolverError(
            "CONCORDE-PROMPT-UNRESOLVED-001",
            f"{relative}: reference has no target path",
        )
    try:
        tokens = shlex.split(rest, comments=False, posix=True)
    except ValueError as error:
        raise PromptResolverError(
            "CONCORDE-PROMPT-UNRESOLVED-001",
            f"{relative}: malformed reference arguments: {error}",
        ) from error
    if not tokens:
        raise PromptResolverError(
            "CONCORDE-PROMPT-UNRESOLVED-001",
            f"{relative}: reference has no target path",
        )
    target = _safe_relative(tokens[0])
    if not target.endswith(".md"):
        raise PromptResolverError(
            "CONCORDE-PROMPT-MISSING-001",
            f"{relative}: reference target must be Markdown (.md): {target}",
        )
    bindings: dict[str, str] = {}
    for token in tokens[1:]:
        if "=" not in token:
            raise PromptResolverError(
                "CONCORDE-PROMPT-UNRESOLVED-001",
                f"{relative}: reference parameter must be key=value, found {token!r}",
            )
        key, _, value = token.partition("=")
        if not _KEY.fullmatch(key):
            raise PromptResolverError(
                "CONCORDE-PROMPT-UNRESOLVED-001",
                f"{relative}: invalid reference parameter name {key!r}",
            )
        if key in bindings:
            raise PromptResolverError(
                "CONCORDE-PROMPT-UNRESOLVED-001",
                f"{relative}: duplicate reference parameter {key!r}",
            )
        bindings[key] = value
    return target, bindings


def _check_scope(target: str, including: str) -> None:
    if target.startswith(SPECS_ROOT) or target == "specs":
        raise PromptResolverError(
            "CONCORDE-PROMPT-SCOPE-001",
            f"{including}: cannot include a Spec document: {target}",
        )
    including_is_protocol = including.startswith((PROTOCOL_PREFIX, PROTOCOL_TEXT_ROOT))
    target_is_protocol = target.startswith((PROTOCOL_PREFIX, PROTOCOL_TEXT_ROOT))
    if including_is_protocol and not target_is_protocol:
        raise PromptResolverError(
            "CONCORDE-PROMPT-PROTOCOL-001",
            f"{including}: a Protocol prompt cannot include outside {PROTOCOL_PREFIX}: {target}",
        )
    if target_is_protocol and not including_is_protocol:
        raise PromptResolverError(
            "CONCORDE-PROMPT-PROTOCOL-001",
            f"{including}: cannot include a Protocol prompt from outside {PROTOCOL_PREFIX}: {target}",
        )


def _check_audience(root_audience: str, target_audience: str, target: str) -> None:
    if target_audience == "shared":
        return
    if target_audience != root_audience:
        raise PromptResolverError(
            "CONCORDE-PROMPT-AUDIENCE-001",
            f"a {root_audience} root cannot include {target} (audience: {target_audience})",
        )


def _substitute(body: str, bindings: dict[str, str], relative: str) -> str:
    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in bindings:
            raise PromptResolverError(
                "CONCORDE-PROMPT-UNRESOLVED-001",
                f"{relative}: variable {{{name}}} has no reference binding",
            )
        return bindings[name]

    return _VARIABLE.sub(replace, body)


def _resolve_body(
    project_root: Path,
    relative: str,
    body: str,
    root_audience: str,
    *,
    chain: tuple[str, ...],
    visited: dict[str, tuple[str, ...]],
    sources: set[str],
) -> str:
    lines = body.split("\n")
    rendered: list[str] = []
    last_index = len(lines) - 1
    for index, line in enumerate(lines):
        match = _DIRECTIVE_LINE.fullmatch(line)
        if match is None or not (
            match.group("target").endswith(".md")
            or "/" in match.group("target")
            or "\\" in match.group("target")
        ):
            rendered.append(line)
            if index != last_index:
                rendered.append("\n")
            continue
        _safe_relative(match.group("target"))
        target, bindings = _parse_directive(line[1:], relative)
        _check_scope(target, relative)
        if target in chain:
            cycle = chain[chain.index(target) :] + (target,)
            raise PromptResolverError(
                "CONCORDE-PROMPT-CYCLE-001", "include cycle: " + " -> ".join(cycle)
            )
        if target in visited:
            raise PromptResolverError(
                "CONCORDE-PROMPT-DIAMOND-001",
                f"{target} is reached twice within one root: {' -> '.join(visited[target])} and {' -> '.join(chain + (target,))}",
            )
        target_audience, target_body = _parse_prompt_file(project_root, target)
        _check_audience(root_audience, target_audience, target)
        new_chain = chain + (target,)
        visited[target] = new_chain
        sources.add(target)
        bound_body = _substitute(target_body, bindings, target)
        resolved = _resolve_body(
            project_root,
            target,
            bound_body,
            root_audience,
            chain=new_chain,
            visited=visited,
            sources=sources,
        )
        rendered.append(resolved)
        if index != last_index:
            pass  # the included body already carries its own trailing newline
    return "".join(rendered)


def _finalize(body: str, relative: str) -> str:
    match = _VARIABLE.search(body)
    if match:
        raise PromptResolverError(
            "CONCORDE-PROMPT-UNRESOLVED-001",
            f"{relative}: unresolved variable {{{match.group(1)}}} in output",
        )
    return _ESCAPED.sub(r"{\1}", body)


def resolve_role_prompt(project_root: str | Path, relative_path: str) -> ResolvedPrompt:
    """Resolve one role root prompt under ``prompts/`` (its own front matter names the audience)."""

    root = Path(project_root)
    relative = _safe_relative(relative_path)
    audience, body = _parse_prompt_file(root, relative)
    if audience not in {"worker", "shared"}:
        raise PromptResolverError(
            "CONCORDE-PROMPT-AUDIENCE-001",
            f"role root {relative} must declare audience worker or shared, found {audience!r}",
        )
    sources: set[str] = set()
    resolved = _resolve_body(
        root,
        relative,
        body,
        "worker",
        chain=(relative,),
        visited={relative: (relative,)},
        sources=sources,
    )
    resolved = _finalize(resolved, relative)
    return ResolvedPrompt(body=resolved, sources=tuple(sorted({relative, *sources})))


def find_unreachable_prompts(
    project_root: str | Path, roots: list[str] | tuple[str, ...]
) -> tuple[str, ...]:
    """Return every ``prompts/**/*.md`` file that no given root reaches (rule: dead text)."""

    root = Path(project_root)
    all_prompts = (
        {
            path.relative_to(root).as_posix()
            for path in (root / "prompts").rglob("*.md")
            if path.is_file() and not path.is_symlink()
        }
        if (root / "prompts").is_dir()
        else set()
    )
    visited: set[str] = set()
    for candidate in roots:
        visited.update(resolve_role_prompt(root, candidate).sources)
    return tuple(sorted(all_prompts - visited))
