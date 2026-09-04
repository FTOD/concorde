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

from concorde.capabilities.skill_assets import (  # noqa: E402
    EffectDeclaration,
    SkillAssetError,
    load_skill_prompt,
    render_capabilities,
    render_skill,
    resolve_skill_prompt,
)


class SkillAssetTests(unittest.TestCase):
    def test_parses_exposure_effects_and_mixed_operation_capabilities(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            leaf = root / "concorde-private/SKILL.md"
            leaf.parent.mkdir()
            leaf.write_text(
                "---\nname: concorde-private\ndescription: Private leaf.\n"
                "exposure: internal\neffects:\n"
                "  reads:\n    - selected-feature\n    - attempt\n"
                "  writes:\n    - attempt\n"
                "  network: false\n  credentials: none\n"
                "---\n\n# Private\n\nDo bounded work.\n",
                encoding="utf-8",
            )
            prompt = resolve_skill_prompt(leaf, "skill", "")
            self.assertEqual(prompt.exposure, "internal")
            self.assertEqual(
                prompt.effects,
                EffectDeclaration(
                    reads=("selected-feature", "attempt"),
                    writes=("attempt",),
                    network=False,
                    credentials="none",
                ),
            )

            operation = root / "concorde-parent/SKILL.md"
            operation.parent.mkdir()
            operation.write_text(
                "---\nname: concorde-parent\ndescription: Parent operation.\n"
                "exposure: public\noperation: operation.py\ncapabilities:\n"
                "  - concorde-private\n  - concorde-child\n"
                "---\n\n# Parent\n\nRun {OPERATION}.\n",
                encoding="utf-8",
            )
            parent = resolve_skill_prompt(operation, "operation", "")
            self.assertEqual(parent.exposure, "public")
            self.assertEqual(parent.capabilities, ("concorde-private", "concorde-child"))
            self.assertIsNone(parent.effects)

    def test_internal_leaf_is_loadable_but_not_projected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills").mkdir()
            (root / "operations").mkdir()
            manifest = {
                "skills": ["concorde-alpha", "concorde-beta", "concorde-private"],
                "operations": ["concorde-loop"],
            }
            for name in ("concorde-alpha", "concorde-beta"):
                directory = root / "skills" / name
                directory.mkdir()
                (directory / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Public leaf.\n"
                    "exposure: public\n---\n\n# Public\n",
                    encoding="utf-8",
                )
            internal = root / "skills/concorde-private"
            internal.mkdir()
            (internal / "SKILL.md").write_text(
                "---\nname: concorde-private\ndescription: Private leaf.\n"
                "exposure: internal\neffects:\n  reads: []\n  writes: []\n"
                "  network: false\n  credentials: none\n---\n\n# Private\n",
                encoding="utf-8",
            )
            operation = root / "operations/concorde-loop"
            operation.mkdir()
            (operation / "SKILL.md").write_text(
                "---\nname: concorde-loop\ndescription: Public operation.\n"
                "operation: operation.py\ncapabilities:\n"
                "  - concorde-private\n  - concorde-alpha\n"
                "---\n\n# Loop\n\nRun {OPERATION}.\n",
                encoding="utf-8",
            )
            (operation / "operation.py").write_text("# fixture\n", encoding="utf-8")
            (root / "concorde.json").write_text(json.dumps(manifest), encoding="utf-8")

            self.assertEqual(load_skill_prompt(root, "concorde-private", "").exposure, "internal")
            rendered = render_capabilities(root, "codex", "")
            self.assertNotIn(".agents/skills/concorde-private/SKILL.md", rendered)

    def test_loads_immutable_leaf_and_operation_prompts(self):
        leaf = load_skill_prompt(REPOSITORY_ROOT, "concorde-plan-author", "")
        self.assertEqual((leaf.name, leaf.kind), ("concorde-plan-author", "skill"))
        self.assertEqual(leaf.source_path, "skills/concorde-plan-author/SKILL.md")
        self.assertEqual(leaf.exposure, "internal")
        self.assertIn("Planning workflow", leaf.body)
        self.assertEqual((leaf.operation, leaf.capabilities), (None, ()))
        planner = load_skill_prompt(REPOSITORY_ROOT, "concorde-plan", "")
        self.assertEqual((planner.kind, planner.exposure), ("operation", "public"))
        self.assertEqual(
            planner.capabilities,
            ("concorde-plan-context", "concorde-plan-author"),
        )
        operation = load_skill_prompt(REPOSITORY_ROOT, "concorde-standard-dev-loop", "")
        self.assertEqual(operation.kind, "operation")
        self.assertEqual(
            operation.operation,
            "operations/concorde-standard-dev-loop/operation.py",
        )
        self.assertEqual(operation.capabilities[:2], ("concorde-specify", "concorde-plan"))
        self.assertIn(
            "python3 scripts/run-operation.py "
            "operations/concorde-standard-dev-loop/operation.py",
            operation.body,
        )
        for prompt in (leaf, planner, operation):
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
        self.assertIn(
            "python3 scripts/run-operation.py operations/concorde-plan/operation.py",
            source.body,
        )
        self.assertIn(
            "python3 .concorde/framework/scripts/run-operation.py "
            ".concorde/framework/operations/concorde-plan/operation.py",
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
            "python3 scripts/run-operation.py "
            "operations/concorde-standard-dev-loop/operation.py",
            source_operation.body,
        )
        self.assertIn(
            "python3 .concorde/framework/scripts/run-operation.py "
            ".concorde/framework/operations/concorde-standard-dev-loop/operation.py",
            installed_operation.body,
        )
        source_analyze = load_skill_prompt(REPOSITORY_ROOT, "concorde-analyze", "")
        installed_analyze = load_skill_prompt(
            REPOSITORY_ROOT, "concorde-analyze", ".concorde/framework"
        )
        self.assertEqual(source_analyze.script_paths, ("scripts/workspace.py",))
        self.assertEqual(
            installed_analyze.script_paths,
            (".concorde/framework/scripts/workspace.py",),
        )

    def test_projection_preserves_complete_body_and_adds_capability_provenance(self):
        plan_path = REPOSITORY_ROOT / "operations/concorde-plan/SKILL.md"
        plan = load_skill_prompt(REPOSITORY_ROOT, "concorde-plan", "")
        rendered_plan = render_skill(plan_path, "codex", "", kind="operation")
        self.assertTrue(rendered_plan.endswith(plan.body))
        self.assertIn('source: "operations/concorde-plan/SKILL.md"', rendered_plan)
        self.assertIn('kind: "operation"', rendered_plan)

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

    def test_complete_manifest_renders_fifteen_public_leaves_and_three_operations(self):
        manifest = json.loads((REPOSITORY_ROOT / "concorde.json").read_text())
        for integration, prefix in (("codex", ".agents"), ("claude", ".claude")):
            rendered = render_capabilities(REPOSITORY_ROOT, integration, "")
            self.assertEqual(len(rendered), 18)
            expected_public = set(manifest["skills"]) - {
                "concorde-plan-context",
                "concorde-plan-author",
            }
            self.assertEqual(
                set(rendered),
                {f"{prefix}/skills/{name}/SKILL.md" for name in (*expected_public, *manifest["operations"])},
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
                json.dumps({"skills": ["concorde-specify"], "operations": []})
            )
            target = root / "plan-target.md"
            source = root / "skills/concorde-specify/SKILL.md"
            shutil.copy2(source, target)
            source.unlink()
            source.symlink_to(target)
            with self.assertRaisesRegex(SkillAssetError, "exactly|unsafe"):
                load_skill_prompt(root, "concorde-specify", "")

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
            manifest["skills"] = [*manifest["skills"], "concorde-plan"]
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
            with self.assertRaisesRegex(SkillAssetError, "unknown capabilities"):
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
