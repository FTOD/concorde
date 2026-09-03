from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT
from tests.concorde.support.reflection_triage import CANONICAL_ASSETS, tree_hashes

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.agent_assets import (  # noqa: E402
    CONFIG_PATH,
    LEGACY_CONFIG,
    LEGACY_CONFIG_ARCHIVE_PATH,
    LEGACY_PLANS,
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
            self.assertEqual((root / ".concorde/reflections/.gitignore").read_text(), "plans/\nworktrees/\nlegacy-*\n")
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


class LegacyReflectionConfigAdoptionTests(unittest.TestCase):
    def _write_legacy_config(self, root: Path, payload: dict) -> Path:
        legacy = root / LEGACY_CONFIG
        legacy.parent.mkdir(parents=True, exist_ok=True)
        legacy.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return legacy

    def _assert_conflict_without_writes(self, root: Path, *, reason_contains: str | None = None) -> None:
        before = tree_hashes(root)
        preview = preview_agent_assets(root, CANONICAL_ASSETS, "claude", "0.9.0")
        self.assertEqual(preview.status, "conflict")
        conflicts = [item for item in preview.result["actions"] if item["action"] == "conflict"]
        self.assertTrue(conflicts)
        self.assertNotIn("adopted_config", preview.result)
        if reason_contains is not None:
            self.assertTrue(any(reason_contains in item["reason"] for item in conflicts))
        result = sync_agent_assets(root, CANONICAL_ASSETS, "claude", "0.9.0")
        self.assertEqual(result.status, "conflict")
        self.assertEqual(tree_hashes(root), before)

    def test_customized_legacy_config_is_previewed_and_adopted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = self._write_legacy_config(
                root,
                {
                    "_doc": "legacy notes",
                    "log": "specs/concorde/reflections.md",
                    "features_root": "specs/concorde/features",
                    "plans_dir": ".claude/reflection-plans",
                    "order": "oldest-first",
                    "investigators": 3,
                    "implementers": 2,
                    "require_approval": False,
                    "skip": ["R-001"],
                },
            )
            legacy_bytes = legacy.read_bytes()

            preview = preview_agent_assets(root, CANONICAL_ASSETS, "claude", "0.9.0")
            self.assertEqual(preview.status, "proposal")
            adopt_actions = [item for item in preview.result["actions"] if item["action"] == "adopt-legacy-config"]
            self.assertEqual(len(adopt_actions), 1)
            action = adopt_actions[0]
            self.assertEqual(action["path"], CONFIG_PATH)
            self.assertEqual(action["source"], LEGACY_CONFIG)
            self.assertEqual(action["archive"], LEGACY_CONFIG_ARCHIVE_PATH)
            self.assertTrue(action["source_sha256"].startswith("sha256:"))
            self.assertTrue(action["content_sha256"].startswith("sha256:"))
            adopted = preview.result["adopted_config"]
            self.assertEqual(
                adopted,
                {
                    "schema_version": 1,
                    "order": "oldest-first",
                    "investigators": 3,
                    "implementers": 2,
                    "require_approval": False,
                    "skip": ["R-001"],
                    "plans_dir": ".concorde/reflections/plans",
                    "worktrees_dir": ".concorde/reflections/worktrees",
                },
            )

            result = sync_agent_assets(root, CANONICAL_ASSETS, "claude", "0.9.0")
            self.assertEqual(result.status, "success")
            self.assertTrue(result.result["config_adopted"])
            self.assertFalse(result.result["config_created"])

            config_path = root / CONFIG_PATH
            self.assertEqual(json.loads(config_path.read_text()), adopted)
            self.assertFalse(legacy.exists())
            archive_path = root / LEGACY_CONFIG_ARCHIVE_PATH
            self.assertEqual(archive_path.read_bytes(), legacy_bytes)

            receipt = json.loads((root / ".concorde/agent-assets.json").read_text())
            receipt_paths = {item["path"] for item in receipt["integrations"]["claude"]["outputs"]}
            self.assertNotIn(CONFIG_PATH, receipt_paths)

            before = tree_hashes(root)
            second = sync_agent_assets(root, CANONICAL_ASSETS, "claude", "0.9.0")
            self.assertEqual(second.status, "unchanged")
            self.assertEqual(tree_hashes(root), before)
            self.assertEqual(verify_agent_assets(root, CANONICAL_ASSETS, "claude").status, "success")

    def test_legacy_config_unsupported_key_conflicts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_legacy_config(root, {"order": "newest-first", "mystery": True})
            self._assert_conflict_without_writes(root, reason_contains="unsupported key")

    def test_legacy_config_invalid_value_conflicts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_legacy_config(root, {"order": "sideways"})
            self._assert_conflict_without_writes(root, reason_contains="order")

    def test_legacy_config_malformed_json_conflicts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / LEGACY_CONFIG
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_text("{not json", encoding="utf-8")
            self._assert_conflict_without_writes(root, reason_contains="not valid JSON")

    def test_legacy_config_symlink_conflicts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "elsewhere.json"
            target.write_text(json.dumps({"order": "newest-first"}), encoding="utf-8")
            legacy = root / LEGACY_CONFIG
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.symlink_to(target)
            self._assert_conflict_without_writes(root, reason_contains="not a regular file")

    def test_both_legacy_and_canonical_config_conflicts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_legacy_config(root, {"order": "newest-first"})
            canonical = root / CONFIG_PATH
            canonical.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text("{}", encoding="utf-8")
            self._assert_conflict_without_writes(root, reason_contains="canonical config exists")

    def test_occupied_archive_path_conflicts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._write_legacy_config(root, {"order": "newest-first"})
            archive = root / LEGACY_CONFIG_ARCHIVE_PATH
            archive.parent.mkdir(parents=True, exist_ok=True)
            archive.write_text("occupied\n", encoding="utf-8")
            self._assert_conflict_without_writes(root, reason_contains="archive path already exists")

    def test_legacy_plans_directory_conflicts_with_or_without_legacy_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / LEGACY_PLANS).mkdir(parents=True)
            self._assert_conflict_without_writes(root, reason_contains=LEGACY_PLANS)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / LEGACY_PLANS).mkdir(parents=True)
            self._write_legacy_config(root, {"order": "newest-first"})
            self._assert_conflict_without_writes(root, reason_contains=LEGACY_PLANS)

    def test_archive_move_failure_removes_canonical_config_and_leaves_tree_untouched(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline = sync_agent_assets(root, CANONICAL_ASSETS, "claude", "0.9.0")
            self.assertEqual(baseline.status, "success")
            config_path = root / CONFIG_PATH
            config_path.unlink()
            self._write_legacy_config(root, {"order": "newest-first"})
            before = tree_hashes(root)
            archive_path = root / LEGACY_CONFIG_ARCHIVE_PATH
            real_replace = os.replace

            def failing_replace(source, destination):
                if Path(destination) == archive_path:
                    raise OSError("simulated archive failure")
                return real_replace(source, destination)

            with mock.patch("concorde.agent_assets.os.replace", side_effect=failing_replace):
                result = sync_agent_assets(root, CANONICAL_ASSETS, "claude", "0.9.0")
            self.assertNotEqual(result.status, "success")
            self.assertEqual(tree_hashes(root), before)


if __name__ == "__main__":
    unittest.main()
