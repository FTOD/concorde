from __future__ import annotations

import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT
from tests.concorde.support.reflection_triage import CANONICAL_ASSETS

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.reflections.agent_assets import render_projection  # noqa: E402
from concorde.capabilities.skill_assets import render_capabilities  # noqa: E402


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
    def test_public_guidance_names_v5_and_retained_maintainer_disposition(self):
        paths = (
            "README.md",
            "operations/concorde-reflections-triage/SKILL.md",
            "specs/concorde/modules/reflections/features/001-record-and-triage-reflections.md",
            "specs/concorde/features/002-project-ontology.md",
            "specs/concorde/modules/capabilities/features/004-maintain-agent-surfaces.md",
        )
        combined = "\n".join((REPOSITORY_ROOT / path).read_text(encoding="utf-8") for path in paths)
        self.assertIn("reflection-triage/v5", combined)
        self.assertIn("maintainer disposition", combined)
        self.assertNotIn("reflection-triage/v4", combined)

    def test_projection_manifest_has_exact_claude_codex_and_shared_inventory(self):
        claude = render_projection(CANONICAL_ASSETS, "claude")
        codex = render_projection(CANONICAL_ASSETS, "codex")
        self.assertEqual(
            set(claude),
            {
                ".claude/agents/reflection-investigator.md",
                ".claude/agents/reflection-implementer.md",
            },
        )
        self.assertEqual(
            set(codex),
            {
                ".codex/agents/reflection_investigator.toml",
                ".codex/agents/reflection_implementer.toml",
            },
        )

    def test_platform_projections_bind_to_one_protocol_config_and_helper(self):
        claude = render_projection(CANONICAL_ASSETS, "claude")
        codex = render_projection(CANONICAL_ASSETS, "codex")
        claude_capabilities = render_capabilities(REPOSITORY_ROOT, "claude", ".concorde/framework")
        codex_capabilities = render_capabilities(REPOSITORY_ROOT, "codex", ".concorde/framework")
        claude_skill = claude_capabilities[".claude/skills/concorde-reflections-triage/SKILL.md"]
        codex_skill = codex_capabilities[".agents/skills/concorde-reflections-triage/SKILL.md"]
        self.assertEqual(frontmatter(claude_skill)["name"], "concorde-reflections-triage")
        self.assertEqual(frontmatter(codex_skill)["name"], "concorde-reflections-triage")
        for text in (claude_skill, codex_skill):
            normalized = " ".join(text.split())
            for action in ("status", "investigate", "implement", "merge", "close"):
                self.assertIn(f"- `{action}", text)
            self.assertIn("reflection-triage/v5", text)
            self.assertIn(".concorde/reflections/<bucket>/R-NNN.md", text)
            for bucket in ("`pending/`", "`planned/`", "`needs-comments/`"):
                self.assertIn(bucket, text)
            self.assertIn("--relocate R-NNN", text)
            self.assertIn("--validate-entry R-NNN", text)
            self.assertIn("--remove-closed", text)
            self.assertIn("CONCORDE-REFLECT-005", text)
            self.assertIn(".concorde/reflections/index.json", text)
            self.assertIn(".concorde/reflections/config.json", text)
            self.assertIn(".concorde/framework/scripts/reflections_queue.py", text)
            self.assertIn("scripts/reflections_queue.py", text)
            self.assertIn("Operation", text)
            self.assertIn("maintainer disposition", normalized)
            self.assertIn("verified_commit", text)
            self.assertIn("status=stale", text)
            self.assertNotIn(str(Path.cwd()), text)

        investigator = tomllib.loads(codex[".codex/agents/reflection_investigator.toml"])
        implementer = tomllib.loads(codex[".codex/agents/reflection_implementer.toml"])
        for role in (investigator, implementer):
            self.assertTrue({"name", "description", "developer_instructions"} <= set(role))
            self.assertNotIn("model", role)
            self.assertNotIn("model_reasoning_effort", role)
            for route in ("fast-loop", "specify", "dismiss", "blocked"):
                self.assertIn(route, role["developer_instructions"])
            self.assertIn("reflection-triage/v5", role["developer_instructions"])
            self.assertIn("verified_commit", role["developer_instructions"])
        self.assertEqual(investigator["sandbox_mode"], "read-only")
        self.assertEqual(implementer["sandbox_mode"], "workspace-write")
        self.assertIn("Never change reflection `status`, `resolution_note`", implementer["developer_instructions"])
        self.assertIn("stable-ID validation rules", implementer["developer_instructions"])

        claude_investigator = claude[".claude/agents/reflection-investigator.md"]
        claude_implementer = claude[".claude/agents/reflection-implementer.md"]
        self.assertNotIn("model:", claude_investigator)
        self.assertNotIn("model:", claude_implementer)
        self.assertIn("Return the triage-owned reflection replacement, the complete plan", claude_investigator)
        self.assertIn("assigned worktree", claude_implementer)
        self.assertIn("`verified_commit` (the full HEAD commit ID", claude_investigator)
        self.assertIn("`Verification` section", claude_implementer)
        self.assertIn("Never change reflection `status`, `resolution_note`", claude_implementer)
        self.assertIn("stable-ID validation rules", claude_implementer)


if __name__ == "__main__":
    unittest.main()
