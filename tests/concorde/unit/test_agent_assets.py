from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT
from tests.concorde.support.reflection_triage import CANONICAL_ASSETS, tree_hashes

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.agent_assets import (  # noqa: E402
    AgentAssetError,
    preview_agent_assets,
    remove_agent_assets,
    render_projection,
    sync_agent_assets,
    verify_agent_assets,
)


class AgentAssetTests(unittest.TestCase):
    def test_canonical_manifest_and_both_projections_require_v5(self):
        manifest = json.loads((CANONICAL_ASSETS / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["protocol"], "reflection-triage/v5")
        for integration in ("claude", "codex"):
            rendered = render_projection(CANONICAL_ASSETS, integration)
            self.assertTrue(all("reflection-triage/v5" in text for text in rendered.values()))

        with tempfile.TemporaryDirectory() as temporary:
            legacy = Path(temporary) / "reflections"
            shutil.copytree(CANONICAL_ASSETS, legacy)
            path = legacy / "manifest.json"
            path.write_text(path.read_text().replace("reflection-triage/v5", "reflection-triage/v4"))
            with self.assertRaisesRegex(AgentAssetError, "reflection-triage/v5"):
                render_projection(legacy, "codex")

    def test_fresh_sync_is_repeatable_and_seeds_shared_config_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".concorde").mkdir()
            first = sync_agent_assets(root, CANONICAL_ASSETS, "codex", "0.9.0")
            self.assertEqual(first.status, "success")
            expected = {
                ".codex/agents/reflection_investigator.toml",
                ".codex/agents/reflection_implementer.toml",
            }
            self.assertEqual(set(first.result["outputs"]), expected)
            config = root / ".concorde/reflections/config.json"
            self.assertTrue(config.is_file())
            self.assertEqual((root / ".concorde/reflections/.gitignore").read_text(), "plans/\nworktrees/\n")
            reflection = root / ".concorde/reflections/R-001.md"
            reflection.write_text("project-authored reflection\n", encoding="utf-8")
            config.write_text(config.read_text().replace('"investigators": 1', '"investigators": 3'))
            before = tree_hashes(root)
            second = sync_agent_assets(root, CANONICAL_ASSETS, "codex", "0.9.0")
            self.assertEqual(second.status, "unchanged")
            self.assertEqual(tree_hashes(root), before)
            self.assertEqual(verify_agent_assets(root, CANONICAL_ASSETS, "codex").status, "success")

    def test_modified_owned_output_conflicts_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sync_agent_assets(root, CANONICAL_ASSETS, "claude", "0.9.0")
            role = root / ".claude/agents/reflection-investigator.md"
            role.write_text(role.read_text() + "\nmaintainer change\n")
            before = tree_hashes(root)
            preview = preview_agent_assets(root, CANONICAL_ASSETS, "claude", "0.5.1")
            self.assertEqual(preview.status, "conflict")
            result = sync_agent_assets(root, CANONICAL_ASSETS, "claude", "0.5.1")
            self.assertEqual(result.status, "conflict")
            self.assertEqual(tree_hashes(root), before)

    def test_byte_identical_legacy_files_are_adopted_and_inactive_integration_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative, content in render_projection(CANONICAL_ASSETS, "claude").items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            adopted = sync_agent_assets(root, CANONICAL_ASSETS, "claude", "0.9.0")
            self.assertEqual(adopted.status, "success")
            self.assertTrue(any(item["action"] == "adopt" for item in adopted.result["actions"]))
            claude_hashes = {
                path: digest for path, digest in tree_hashes(root).items() if path.startswith(".claude/")
            }
            sync_agent_assets(root, CANONICAL_ASSETS, "codex", "0.9.0")
            after = tree_hashes(root)
            self.assertEqual(
                {path: after[path] for path in claude_hashes},
                claude_hashes,
            )

    def test_remove_deletes_only_matching_owned_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sync_agent_assets(root, CANONICAL_ASSETS, "codex", "0.9.0")
            unrelated = root / ".agents/skills/user-skill/SKILL.md"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("user owned\n")
            config = root / ".concorde/reflections/config.json"
            plans = root / ".concorde/reflections/plans/R-001.md"
            plans.parent.mkdir(parents=True)
            plans.write_text("plan\n")
            reflection = root / ".concorde/reflections/R-001.md"
            reflection.write_text("project-authored reflection\n", encoding="utf-8")
            result = remove_agent_assets(root, "codex")
            self.assertEqual(result.status, "success")
            self.assertTrue(unrelated.is_file())
            self.assertTrue(config.is_file())
            self.assertTrue((root / ".concorde/reflections/.gitignore").is_file())
            self.assertTrue(plans.is_file())
            self.assertTrue(reflection.is_file())
            self.assertFalse((root / ".codex/agents/reflection_investigator.toml").exists())
            receipt = json.loads((root / ".concorde/agent-assets.json").read_text())
            self.assertNotIn("codex", receipt["integrations"])


if __name__ == "__main__":
    unittest.main()
