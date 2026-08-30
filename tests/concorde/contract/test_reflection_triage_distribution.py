from __future__ import annotations

import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from tests.concorde.support.paths import RUNTIME_ROOT
from tests.concorde.support.reflection_triage import CANONICAL_ASSETS

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.agent_assets import render_projection  # noqa: E402


def frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line == "---":
            break
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


class ReflectionTriageDistributionContractTests(unittest.TestCase):
    def test_projection_manifest_has_exact_claude_codex_and_shared_inventory(self):
        claude = render_projection(CANONICAL_ASSETS, "claude")
        codex = render_projection(CANONICAL_ASSETS, "codex")
        self.assertEqual(
            set(claude),
            {
                ".claude/skills/reflections-triage/SKILL.md",
                ".claude/agents/reflection-investigator.md",
                ".claude/agents/reflection-implementer.md",
            },
        )
        self.assertEqual(
            set(codex),
            {
                ".agents/skills/reflections-triage/SKILL.md",
                ".codex/agents/reflection_investigator.toml",
                ".codex/agents/reflection_implementer.toml",
            },
        )

    def test_platform_projections_bind_to_one_protocol_config_and_helper(self):
        claude = render_projection(CANONICAL_ASSETS, "claude")
        codex = render_projection(CANONICAL_ASSETS, "codex")
        claude_skill = claude[".claude/skills/reflections-triage/SKILL.md"]
        codex_skill = codex[".agents/skills/reflections-triage/SKILL.md"]
        self.assertEqual(frontmatter(claude_skill)["name"], "reflections-triage")
        self.assertEqual(frontmatter(codex_skill)["name"], "reflections-triage")
        for text in (claude_skill, codex_skill):
            for action in ("status", "investigate", "implement", "merge"):
                self.assertIn(f"`{action}`", text)
            self.assertIn("reflection-triage/v1", text)
            self.assertIn(".concorde/reflections/config.json", text)
            self.assertIn(".specify/extensions/concorde/scripts/python/reflections_queue.py", text)
            self.assertNotIn(str(Path.cwd()), text)

        investigator = tomllib.loads(codex[".codex/agents/reflection_investigator.toml"])
        implementer = tomllib.loads(codex[".codex/agents/reflection_implementer.toml"])
        for role in (investigator, implementer):
            self.assertTrue({"name", "description", "developer_instructions"} <= set(role))
            self.assertNotIn("model", role)
            self.assertNotIn("model_reasoning_effort", role)
            for route in ("fast-loop", "specify", "dismiss", "blocked"):
                self.assertIn(route, role["developer_instructions"])
        self.assertEqual(investigator["sandbox_mode"], "read-only")
        self.assertEqual(implementer["sandbox_mode"], "workspace-write")

        claude_investigator = claude[".claude/agents/reflection-investigator.md"]
        claude_implementer = claude[".claude/agents/reflection-implementer.md"]
        self.assertNotIn("model:", claude_investigator)
        self.assertNotIn("model:", claude_implementer)
        self.assertIn("Return the complete plan", claude_investigator)
        self.assertIn("assigned worktree", claude_implementer)


if __name__ == "__main__":
    unittest.main()
