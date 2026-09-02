from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.skill_assets import (  # noqa: E402
    SkillAssetError,
    load_skill_prompt,
    render_capabilities,
    render_skill,
)


class SkillAssetTests(unittest.TestCase):
    def test_loads_immutable_leaf_and_operation_prompts(self):
        leaf = load_skill_prompt(REPOSITORY_ROOT, "concorde-plan", "")
        self.assertEqual((leaf.name, leaf.kind), ("concorde-plan", "skill"))
        self.assertEqual(leaf.source_path, "skills/concorde-plan/SKILL.md")
        self.assertIn("python3 scripts/workspace.py --phase plan", leaf.body)
        self.assertIn("./templates/plan-template.md", leaf.body)
        self.assertEqual((leaf.operation, leaf.skills), (None, ()))
        operation = load_skill_prompt(REPOSITORY_ROOT, "concorde-standard-dev-loop", "")
        self.assertEqual(operation.kind, "operation")
        self.assertEqual(
            operation.operation,
            "operations/concorde-standard-dev-loop/operation.py",
        )
        self.assertEqual(operation.skills[:2], ("concorde-specify", "concorde-plan"))
        self.assertIn(
            "python3 operations/concorde-standard-dev-loop/operation.py",
            operation.body,
        )
        for prompt in (leaf, operation):
            self.assertNotIn("{SCRIPT}", prompt.body)
            self.assertNotIn("{FRAMEWORK}", prompt.body)
            self.assertNotIn("{OPERATION}", prompt.body)
        with self.assertRaises(FrozenInstanceError):
            leaf.body = "changed"  # type: ignore[misc]

    def test_source_and_installed_layouts_only_change_resolved_entry_points(self):
        source = load_skill_prompt(REPOSITORY_ROOT, "concorde-plan", "")
        installed = load_skill_prompt(
            REPOSITORY_ROOT, "concorde-plan", ".concorde/framework"
        )
        self.assertIn("python3 scripts/workspace.py --phase plan", source.body)
        self.assertIn(
            "python3 .concorde/framework/scripts/workspace.py --phase plan",
            installed.body,
        )
        source_operation = load_skill_prompt(
            REPOSITORY_ROOT, "concorde-standard-dev-loop", ""
        )
        installed_operation = load_skill_prompt(
            REPOSITORY_ROOT,
            "concorde-standard-dev-loop",
            ".concorde/framework",
        )
        self.assertIn(
            "python3 operations/concorde-standard-dev-loop/operation.py",
            source_operation.body,
        )
        self.assertIn(
            "python3 .concorde/framework/operations/concorde-standard-dev-loop/operation.py",
            installed_operation.body,
        )

    def test_projection_preserves_complete_body_and_adds_capability_provenance(self):
        leaf_path = REPOSITORY_ROOT / "skills/concorde-plan/SKILL.md"
        leaf = load_skill_prompt(REPOSITORY_ROOT, "concorde-plan", "")
        rendered_leaf = render_skill(leaf_path, "codex", "")
        self.assertTrue(rendered_leaf.endswith(leaf.body))
        self.assertIn('source: "skills/concorde-plan/SKILL.md"', rendered_leaf)
        self.assertIn('kind: "skill"', rendered_leaf)

        operation_path = (
            REPOSITORY_ROOT / "operations/concorde-standard-dev-loop/SKILL.md"
        )
        rendered_operation = render_skill(
            operation_path, "claude", "", kind="operation"
        )
        self.assertIn('kind: "operation"', rendered_operation)
        self.assertIn(
            'entrypoint: "operations/concorde-standard-dev-loop/operation.py"',
            rendered_operation,
        )
        self.assertIn("user-invocable: true", rendered_operation)

    def test_complete_manifest_renders_sixteen_leaves_and_two_operations(self):
        manifest = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        for integration, prefix in (("codex", ".agents"), ("claude", ".claude")):
            rendered = render_capabilities(REPOSITORY_ROOT, integration, "")
            self.assertEqual(len(rendered), 18)
            self.assertEqual(
                set(rendered),
                {
                    f"{prefix}/skills/{name}/SKILL.md"
                    for name in (*manifest["skills"], *manifest["operations"])
                },
            )

    def test_rejects_unsafe_unmanifested_missing_and_symlinked_sources(self):
        with self.assertRaisesRegex(SkillAssetError, "invalid Concorde capability name"):
            load_skill_prompt(REPOSITORY_ROOT, "../concorde-plan", "")
        with self.assertRaisesRegex(SkillAssetError, "not declared"):
            load_skill_prompt(REPOSITORY_ROOT, "concorde-not-real", "")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills/concorde-missing").mkdir(parents=True)
            (root / "operations").mkdir()
            (root / "concorde.json").write_text(
                json.dumps({"skills": ["concorde-missing"], "operations": []})
            )
            with self.assertRaisesRegex(SkillAssetError, "exactly"):
                load_skill_prompt(root, "concorde-missing", "")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(REPOSITORY_ROOT / "skills", root / "skills")
            (root / "operations").mkdir()
            (root / "concorde.json").write_text(
                json.dumps({"skills": ["concorde-plan"], "operations": []})
            )
            target = root / "plan-target.md"
            source = root / "skills/concorde-plan/SKILL.md"
            shutil.copy2(source, target)
            source.unlink()
            source.symlink_to(target)
            with self.assertRaisesRegex(SkillAssetError, "exactly|unsafe"):
                load_skill_prompt(root, "concorde-plan", "")

    def test_rejects_bad_leaf_metadata_tokens_and_script_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / "concorde-invalid/SKILL.md"
            skill.parent.mkdir()
            skill.write_text(
                "---\nname: concorde-invalid\ndescription: Invalid\npriority: 10\n"
                "---\n\n# Invalid\n"
            )
            with self.assertRaisesRegex(SkillAssetError, "unsupported metadata"):
                render_skill(skill, "codex")
            skill.write_text(
                "---\nname: concorde-invalid\ndescription: Invalid\nscripts:\n"
                "  py: ../escape.py\n---\n\n# Invalid\n\nRun {SCRIPT}.\n"
            )
            with self.assertRaisesRegex(SkillAssetError, "safe package-relative"):
                render_skill(skill, "codex")
            skill.write_text(
                "---\nname: concorde-invalid\ndescription: Invalid\n---\n\n"
                "# Invalid\n\nRun {OPERATION}.\n"
            )
            with self.assertRaisesRegex(SkillAssetError, "leaf Skill"):
                render_skill(skill, "codex")

    def test_rejects_global_collision_unknown_dependencies_and_inexact_pairs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(REPOSITORY_ROOT / "skills", root / "skills")
            shutil.copytree(REPOSITORY_ROOT / "operations", root / "operations")
            manifest = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
            manifest["operations"] = [*manifest["operations"], "concorde-plan"]
            (root / "concorde.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(SkillAssetError, "globally unique"):
                render_capabilities(root, "codex")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(REPOSITORY_ROOT / "skills", root / "skills")
            shutil.copytree(REPOSITORY_ROOT / "operations", root / "operations")
            manifest = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
            (root / "concorde.json").write_text(json.dumps(manifest))
            operation = root / "operations/concorde-standard-dev-loop/SKILL.md"
            operation.write_text(
                operation.read_text().replace(
                    "  - concorde-specify\n", "  - concorde-unknown\n"
                )
            )
            with self.assertRaisesRegex(SkillAssetError, "unknown Skills"):
                load_skill_prompt(root, "concorde-standard-dev-loop")
            operation.write_text(
                operation.read_text().replace("operation: operation.py", "operation: graph.py")
            )
            with self.assertRaisesRegex(SkillAssetError, "operation: operation.py"):
                load_skill_prompt(root, "concorde-standard-dev-loop")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(REPOSITORY_ROOT / "skills", root / "skills")
            shutil.copytree(REPOSITORY_ROOT / "operations", root / "operations")
            shutil.copy2(
                root / "operations/concorde-standard-dev-loop/operation.py",
                root / "operations/concorde-standard-dev-loop/extra.py",
            )
            (root / "concorde.json").write_text(
                (REPOSITORY_ROOT / "concorde.json").read_text()
            )
            with self.assertRaisesRegex(SkillAssetError, "exactly"):
                load_skill_prompt(root, "concorde-standard-dev-loop")


if __name__ == "__main__":
    unittest.main()
