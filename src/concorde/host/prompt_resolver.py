"""Deterministic resolution of Concorde prompt sources (proposal section 4).

A prompt is a Markdown file with YAML front matter declaring ``audience: worker | ambient |
shared``. A prompt body may reference other prompts through one explicit ``@include`` directive
that occupies a whole line starting at column one:

    @include prompts/workflow-host/worktree-handoff.md
    @include prompts/workflow-host/invoke.md capability=concorde-main request=concorde-main-request

Resolution is a pure function of the source tree: given a root (a role root prompt or a skill
source), it walks ``@include`` directives, binds per-inclusion ``{KEY}`` variables, and returns the
fully substituted text. It performs no network or process I/O beyond reading files under
``project_root``.

Skill sources (``skills/<name>/SKILL.md``) are a distinct front-matter shape (``name``,
``description``, ``capability``) with no ``audience`` field; they are always implicit ``ambient``
roots. Agent Specs (``agents/<name>/spec.md``) are a third distinct shape: no front matter at all,
and always an implicit ``worker`` root -- an Agent Spec carries its own ``# concorde-<name>``
heading and behavioral contract directly, not role/audience metadata. Every other prompt lives
under ``prompts/`` and must declare its own ``audience``.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ..frontmatter import FrontMatterError, parse_document


AUDIENCES = frozenset({"worker", "ambient", "shared"})
RESERVED_VARIABLES = frozenset({"CAPABILITY", "SCRIPT", "FRAMEWORK"})
PROTOCOL_PREFIX = "prompts/protocol/"
PROMPTS_ROOT = "prompts/"
SKILLS_ROOT = "skills/"
SPECS_ROOT = "specs/"
AGENTS_ROOT = "agents/"

_DIRECTIVE_LINE = re.compile(r"^@include(?:[ \t]+(?P<rest>\S.*))?[ \t]*$")
_VARIABLE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
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
        or ".." in candidate.parts
        or "\\" in value
    ):
        raise PromptResolverError(
            "CONCORDE-PROMPT-MISSING-001", f"include target must be a safe repository-relative path: {value!r}"
        )
    return candidate.as_posix()


def _read(project_root: Path, relative: str) -> str:
    path = project_root / relative
    if path.is_symlink() or not path.is_file():
        raise PromptResolverError("CONCORDE-PROMPT-MISSING-001", f"include target is missing or unsafe: {relative}")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise PromptResolverError("CONCORDE-PROMPT-MISSING-001", f"cannot read prompt {relative}: {error}") from error


def _parse_prompt_file(project_root: Path, relative: str) -> tuple[str, str]:
    """Return (audience, body) for one file under prompts/."""

    text = _read(project_root, relative)
    try:
        metadata, body = parse_document(text, relative)
    except FrontMatterError as error:
        raise PromptResolverError("CONCORDE-PROMPT-AUDIENCE-002", f"invalid prompt front matter in {relative}: {error}") from error
    audience = metadata.get("audience")
    if audience not in AUDIENCES:
        raise PromptResolverError(
            "CONCORDE-PROMPT-AUDIENCE-002",
            f"prompt {relative} must declare audience as one of {sorted(AUDIENCES)}, found {audience!r}",
        )
    unknown = set(metadata) - {"audience"}
    if unknown:
        raise PromptResolverError(
            "CONCORDE-PROMPT-AUDIENCE-002", f"prompt {relative} has unsupported front matter keys: {sorted(unknown)}"
        )
    return audience, body


def _parse_directive(rest: str | None, relative: str) -> tuple[str, dict[str, str]]:
    if not rest:
        raise PromptResolverError("CONCORDE-PROMPT-UNRESOLVED-001", f"{relative}: @include has no target path")
    try:
        tokens = shlex.split(rest, comments=False, posix=True)
    except ValueError as error:
        raise PromptResolverError("CONCORDE-PROMPT-UNRESOLVED-001", f"{relative}: malformed @include arguments: {error}") from error
    if not tokens:
        raise PromptResolverError("CONCORDE-PROMPT-UNRESOLVED-001", f"{relative}: @include has no target path")
    target = _safe_relative(tokens[0])
    bindings: dict[str, str] = {}
    for token in tokens[1:]:
        if "=" not in token:
            raise PromptResolverError(
                "CONCORDE-PROMPT-UNRESOLVED-001", f"{relative}: @include parameter must be key=value, found {token!r}"
            )
        key, _, value = token.partition("=")
        if not _KEY.fullmatch(key):
            raise PromptResolverError("CONCORDE-PROMPT-UNRESOLVED-001", f"{relative}: invalid @include parameter name {key!r}")
        if key in bindings:
            raise PromptResolverError("CONCORDE-PROMPT-UNRESOLVED-001", f"{relative}: duplicate @include parameter {key!r}")
        bindings[key] = value
    return target, bindings


def _check_scope(target: str, including: str) -> None:
    if target.startswith(SKILLS_ROOT) or target == "skills":
        raise PromptResolverError("CONCORDE-PROMPT-SCOPE-001", f"{including}: cannot include a skill source: {target}")
    if target.startswith(SPECS_ROOT) or target == "specs":
        raise PromptResolverError("CONCORDE-PROMPT-SCOPE-001", f"{including}: cannot include a Spec document: {target}")
    if including.startswith(AGENTS_ROOT) and not target.startswith(PROMPTS_ROOT):
        raise PromptResolverError(
            "CONCORDE-PROMPT-SCOPE-001", f"{including}: an Agent Spec may include only prompts/ files: {target}"
        )
    including_is_protocol = including.startswith(PROTOCOL_PREFIX)
    target_is_protocol = target.startswith(PROTOCOL_PREFIX)
    if including_is_protocol and not target_is_protocol:
        raise PromptResolverError(
            "CONCORDE-PROMPT-PROTOCOL-001", f"{including}: a Protocol prompt cannot include outside {PROTOCOL_PREFIX}: {target}"
        )
    if target_is_protocol and not including_is_protocol:
        raise PromptResolverError(
            "CONCORDE-PROMPT-PROTOCOL-001", f"{including}: cannot include a Protocol prompt from outside {PROTOCOL_PREFIX}: {target}"
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
        if name in RESERVED_VARIABLES:
            return match.group(0)
        if name not in bindings:
            raise PromptResolverError(
                "CONCORDE-PROMPT-UNRESOLVED-001", f"{relative}: variable {{{name}}} has no @include binding"
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
        match = _DIRECTIVE_LINE.match(line)
        if match is None:
            rendered.append(line)
            if index != last_index:
                rendered.append("\n")
            continue
        target, bindings = _parse_directive(match.group("rest"), relative)
        _check_scope(target, relative)
        if target in chain:
            cycle = chain[chain.index(target):] + (target,)
            raise PromptResolverError("CONCORDE-PROMPT-CYCLE-001", "include cycle: " + " -> ".join(cycle))
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
    for match in _VARIABLE.finditer(body):
        if match.group(1) not in RESERVED_VARIABLES:
            raise PromptResolverError(
                "CONCORDE-PROMPT-UNRESOLVED-001", f"{relative}: unresolved variable {{{match.group(1)}}} in output"
            )
    if re.search(r"(?m)^@include\b", body):
        raise PromptResolverError("CONCORDE-PROMPT-UNRESOLVED-001", f"{relative}: unresolved @include directive in output")
    return body


def resolve_role_prompt(project_root: str | Path, relative_path: str) -> ResolvedPrompt:
    """Resolve one role root prompt under ``prompts/`` (its own front matter names the audience)."""

    root = Path(project_root)
    relative = _safe_relative(relative_path)
    audience, body = _parse_prompt_file(root, relative)
    if audience not in {"worker", "shared"}:
        raise PromptResolverError(
            "CONCORDE-PROMPT-AUDIENCE-001", f"role root {relative} must declare audience worker or shared, found {audience!r}"
        )
    sources: set[str] = set()
    resolved = _resolve_body(root, relative, body, "worker", chain=(relative,), visited={relative: (relative,)}, sources=sources)
    resolved = _finalize(resolved, relative)
    return ResolvedPrompt(body=resolved, sources=tuple(sorted({relative, *sources})))


def resolve_skill_source(project_root: str | Path, relative_path: str) -> ResolvedPrompt:
    """Resolve the body of one ``skills/<name>/SKILL.md`` source as an implicit ambient root."""

    root = Path(project_root)
    relative = _safe_relative(relative_path)
    text = _read(root, relative)
    try:
        metadata, body = parse_document(text, relative)
    except FrontMatterError as error:
        raise PromptResolverError("CONCORDE-PROMPT-AUDIENCE-002", f"invalid skill source front matter in {relative}: {error}") from error
    required = {"name", "description", "capability"}
    if set(metadata) != required:
        raise PromptResolverError(
            "CONCORDE-PROMPT-AUDIENCE-002",
            f"skill source {relative} must declare exactly {sorted(required)}, found {sorted(metadata)}",
        )
    sources: set[str] = set()
    resolved = _resolve_body(root, relative, body, "ambient", chain=(relative,), visited={relative: (relative,)}, sources=sources)
    resolved = _finalize(resolved, relative)
    return ResolvedPrompt(body=resolved, sources=tuple(sorted({relative, *sources})))


def resolve_agent_spec(project_root: str | Path, relative_path: str) -> ResolvedPrompt:
    """Resolve one Agent Spec (``agents/<name>/spec.md``): an implicit ``worker`` root with no
    front matter (workflow/agents-and-harnesses.md A1). Unlike a role root or a skill source, an
    Agent Spec carries its own ``# concorde-<name>`` heading and behavioral contract directly, so
    there is no ``audience``/``name``/``description``/``capability`` metadata to parse -- only a
    front-matter fence itself is rejected."""

    root = Path(project_root)
    relative = _safe_relative(relative_path)
    text = _read(root, relative)
    normalized = text.replace("\r\n", "\n")
    first_line = normalized.splitlines()[0].strip() if normalized else ""
    if first_line == "---":
        raise PromptResolverError(
            "CONCORDE-PROMPT-AUDIENCE-002", f"Agent Spec {relative} must carry no front matter"
        )
    sources: set[str] = set()
    resolved = _resolve_body(
        root, relative, text, "worker", chain=(relative,), visited={relative: (relative,)}, sources=sources
    )
    resolved = _finalize(resolved, relative)
    return ResolvedPrompt(body=resolved, sources=tuple(sorted({relative, *sources})))


def find_unreachable_prompts(project_root: str | Path, roots: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Return every ``prompts/**/*.md`` file that no given root reaches (rule: dead text)."""

    root = Path(project_root)
    all_prompts = {
        path.relative_to(root).as_posix()
        for path in (root / "prompts").rglob("*.md")
        if path.is_file() and not path.is_symlink()
    } if (root / "prompts").is_dir() else set()
    visited: set[str] = set()
    for candidate in roots:
        if candidate.startswith(SKILLS_ROOT):
            resolved = resolve_skill_source(root, candidate)
        elif candidate.startswith(AGENTS_ROOT):
            resolved = resolve_agent_spec(root, candidate)
        else:
            resolved = resolve_role_prompt(root, candidate)
        visited.update(resolved.sources)
    return tuple(sorted(all_prompts - visited))


def check_reachability(project_root: str | Path, roots: list[str] | tuple[str, ...]) -> None:
    """Raise CONCORDE-PROMPT-UNREACHABLE-001 when some prompt is dead text given these roots."""

    unreachable = find_unreachable_prompts(project_root, roots)
    if unreachable:
        raise PromptResolverError(
            "CONCORDE-PROMPT-UNREACHABLE-001",
            f"no root reaches: {list(unreachable)}",
        )
