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

from concorde.command_assets import (  # noqa: E402
    CommandAssetError,
    load_command_prompt,
    render_command,
)


class CommandPromptTests(unittest.TestCase):
    def test_loads_immutable_canonical_prompt_without_integration_frontmatter(self):
        prompt = load_command_prompt(REPOSITORY_ROOT, "concorde.plan", "")
        self.assertEqual(prompt.command_id, "concorde.plan")
        self.assertEqual(prompt.source_path, "commands/concorde.plan.md")
        self.assertIn("Plan one Concorde feature change", prompt.description)
        self.assertIn("python3 scripts/workspace.py --phase plan", prompt.body)
        self.assertIn("./templates/plan-template.md", prompt.body)
        self.assertNotIn("{SCRIPT}", prompt.body)
        self.assertNotIn("{FRAMEWORK}", prompt.body)
        self.assertFalse(prompt.body.startswith("---"))
        with self.assertRaises(FrozenInstanceError):
            prompt.body = "changed"  # type: ignore[misc]

    def test_source_and_installed_layouts_change_only_resolved_package_paths(self):
        source = load_command_prompt(REPOSITORY_ROOT, "concorde.plan", "")
        installed = load_command_prompt(
            REPOSITORY_ROOT,
            "concorde.plan",
            ".concorde/framework",
        )
        self.assertIn("python3 scripts/workspace.py --phase plan", source.body)
        self.assertIn(
            "python3 .concorde/framework/scripts/workspace.py --phase plan",
            installed.body,
        )
        self.assertIn("./templates/plan-template.md", source.body)
        self.assertIn(".concorde/framework/templates/plan-template.md", installed.body)
        self.assertEqual(source.command_id, installed.command_id)
        self.assertEqual(source.description, installed.description)

    def test_render_command_wraps_the_same_resolved_prompt_body(self):
        path = REPOSITORY_ROOT / "commands/concorde.plan.md"
        prompt = load_command_prompt(REPOSITORY_ROOT, "concorde.plan", "")
        rendered = render_command(path, "codex", "")
        self.assertTrue(rendered.endswith(prompt.body))
        self.assertIn('source: "commands/concorde.plan.md"', rendered)

    def test_rejects_unsafe_unmanifested_missing_and_symlinked_prompt_sources(self):
        with self.assertRaisesRegex(CommandAssetError, "invalid Concorde command"):
            load_command_prompt(REPOSITORY_ROOT, "../concorde.plan", "")
        with self.assertRaisesRegex(CommandAssetError, "not declared"):
            load_command_prompt(REPOSITORY_ROOT, "concorde.not-real", "")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "commands").mkdir()
            (root / "concorde.json").write_text(
                json.dumps({"commands": ["concorde.missing"]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(CommandAssetError, "missing"):
                load_command_prompt(root, "concorde.missing", "")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "concorde.json").write_text(
                json.dumps({"commands": ["concorde.plan"]}),
                encoding="utf-8",
            )
            (root / "commands").symlink_to(REPOSITORY_ROOT / "commands", target_is_directory=True)
            with self.assertRaisesRegex(CommandAssetError, "symlink"):
                load_command_prompt(root, "concorde.plan", "")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "commands").mkdir()
            (root / "concorde.json").write_text(
                json.dumps({"commands": ["concorde.plan"]}),
                encoding="utf-8",
            )
            shutil.copy2(
                REPOSITORY_ROOT / "commands/concorde.plan.md",
                root / "plan-target.md",
            )
            (root / "commands/concorde.plan.md").symlink_to(root / "plan-target.md")
            with self.assertRaisesRegex(CommandAssetError, "symlink"):
                load_command_prompt(root, "concorde.plan", "")


if __name__ == "__main__":
    unittest.main()
