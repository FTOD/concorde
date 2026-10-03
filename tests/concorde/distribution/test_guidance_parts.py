"""Every guidance section stands without the parts it may be composed without: where it names a
command or project MCP tool of such a part, it says what happens where that part is not
installed."""

from __future__ import annotations

import re
import unittest

from concorde.distribution import parts
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

# Dogfooding's develop section is no part's: a develop install composes it only beside these.
DEVELOP = {
    "skill": "generated/dogfooding/skill.md",
    "claude_md": "generated/dogfooding/claude-md.md",
}
DEVELOP_PARTS = ("coordination", "issues")
# "the issues part", "the spec, execution and method parts", "the worker harness part"; a
# lookahead, so that "the merge of the issues part" still finds "the issues part".
NAMED = re.compile(r"(?=\bthe ([a-z ,]+?) parts?\b)")


def closure(everything: dict, names) -> set[str]:
    """The parts ``names`` with every part they depend on and Distribution."""
    return set(parts.closure(everything, names))


def named_parts(paragraph: str) -> set[str]:
    """What a paragraph names as parts, each item of a list of parts on its own."""
    return {
        item.strip()
        for match in NAMED.finditer(paragraph)
        for item in re.split(r",? and |, ", match.group(1))
    }


def mentions(paragraph: str, owners: dict) -> set[tuple[str, str]]:
    """Each command or tool the paragraph names, with the parts it needs."""
    found = set()
    for match in re.finditer(r"\bconcorde ([a-z][a-z-]*)", paragraph):
        for part in owners.get(("command", match.group(1)), ()):
            found.add((part, f"concorde {match.group(1)}"))
    for match in re.finditer(r"`([a-z][a-z_-]*)(?: [^`]*)?`", paragraph):
        word = match.group(1)
        for kind in ("command", "tool"):
            for part in owners.get((kind, word), ()):
                found.add((part, f"`{match.group(0)[1:-1]}`"))
    return found


def unguarded() -> list[str]:
    """Every paragraph of a guidance section that names a command or tool of a part the section
    may be composed without and does not name that part."""
    everything = parts.package_parts(REPOSITORY_ROOT)
    owners: dict[tuple[str, str], set[str]] = {}
    for name, registration in everything.items():
        for entry in registration.data["commands"]:
            owners.setdefault(("command", entry["name"]), set()).add(name)
        for tool in registration.data["mcp_tools"]:
            needs = {name, *tool["requires"]}
            owners.setdefault(("tool", tool["name"]), set()).update(needs)
    sections = []
    for name, registration in everything.items():
        for kind, path in registration.data["guidance"].items():
            if path:
                sections.append((name, kind, path, closure(everything, [name])))
    for kind, path in DEVELOP.items():
        sections.append(("develop", kind, path, closure(everything, DEVELOP_PARTS)))
    found = []
    for owner, kind, path, present in sections:
        if kind == "task_session":
            # Task sessions are Coordination's: its prompt is composed only beside it.
            present = present | closure(everything, ["coordination"])
        text = (REPOSITORY_ROOT / path).read_text(encoding="utf-8")
        for paragraph in re.split(r"\n\s*\n", text):
            paragraph = " ".join(paragraph.split())
            named = named_parts(paragraph)
            for part, what in sorted(mentions(paragraph, owners)):
                if part not in present and part not in named:
                    found.append(
                        f"{path} ({owner}, {kind}) names {what} of the {part} part without "
                        f"naming that part: {paragraph[:160]}…"
                    )
    return found


class GuidanceWithoutPartsTests(unittest.TestCase):
    def test_a_paragraph_names_the_parts_it_lists(self):
        self.assertTrue(
            {"spec", "execution", "method"}
            <= named_parts("where the spec, execution and method parts are installed")
        )
        self.assertIn("worker harness", named_parts("where the worker harness part is"))
        self.assertIn("issues", named_parts("Where the issues part is installed, …"))

    @verifies("scenario.distribution.guidance-absent-parts")
    def test_every_section_stands_without_the_parts_it_may_lack(self):
        self.assertEqual([], unguarded())


if __name__ == "__main__":
    unittest.main()
