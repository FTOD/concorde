"""The prompts and brief helpers of Method's worker-backed Operations."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[3]


def load_prompt(name: str) -> str:
    """The rendered worker prompt ``generated/workers/<name>.md`` of this package."""
    path = PACKAGE_ROOT / "generated/workers" / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} is missing; run the build (python3 scripts/concorde.py build)"
        )
    return path.read_text(encoding="utf-8")


# The Protocol copy's guide to writing a Module specification, in every project Concorde is
# installed in; Spec-writing workers receive it with their brief, since no grant shows it.
PROTOCOL_GUIDE = ".concorde/protocol/kinds/module.md"


def spec_repair_prompt(findings) -> str | None:
    """A resume prompt for a Spec-writing worker from the host's validation findings: the errors
    it can repair, those outside Concorde's control records, which the host reconciles itself."""
    errors = [
        finding
        for finding in findings
        if not (finding.source or "").startswith(".concorde/")
    ]
    if not errors:
        return None
    return (
        "The host validated the Specs after your last round. Repair every structural error "
        "below in the documents you may change, keeping what the documents promise, and end "
        "with a new structured result:\n\n"
        + "".join(
            f"- {finding.rule_id} {finding.source or ''}"
            + (f":{finding.line}" if getattr(finding, "line", None) else "")
            + f": {finding.message}\n"
            for finding in errors
        )
    )


def protocol_guide(worktree: Path) -> str:
    """The project's Protocol writing guide as brief material, or a note that it is missing."""
    path = worktree / PROTOCOL_GUIDE
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return (
            f"\n\n## The Protocol's writing guide\n\n(The project's copy {PROTOCOL_GUIDE} "
            f"cannot be read: {error}; follow the rules above.)\n"
        )
    return (
        f"\n\n## The Protocol's writing guide\n\nThe project's Protocol copy "
        f"({PROTOCOL_GUIDE}), which the host validates your documents against:\n\n"
        + text.strip()
        + "\n"
    )


__all__ = [
    "PROTOCOL_GUIDE",
    "load_prompt",
    "protocol_guide",
    "spec_repair_prompt",
]
