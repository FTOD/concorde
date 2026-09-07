from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.capabilities.build import (  # noqa: E402
    INTEGRATION_ROOTS,
    ROLE_ROOTS,
    SKILL_NAMES,
    BuildError,
    build,
    check_build,
    load_role_prompt,
    verify_fresh,
    write_build,
)


GOLDEN = REPOSITORY_ROOT / "tests/concorde/fixtures/build/golden"
_SOURCE_LINE = re.compile(r'(?m)^(\s*source:\s*).*$')


def _normalize_source_line(text: str) -> str:
    return _SOURCE_LINE.sub(lambda match: match.group(1) + '"NORMALIZED"', text)


class BuildGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = build(REPOSITORY_ROOT, "all")
        cls.by_path = {output.path: output for output in cls.result.outputs}

    def test_role_bodies_match_golden_bytes_exactly(self):
        for role in ROLE_ROOTS:
            with self.subTest(role=role):
                golden = (GOLDEN / "roles" / f"{role}.md").read_bytes()
                mine = self.by_path[f"generated/roles/{role}.md"].content
                self.assertEqual(mine, golden)

    def test_skill_projections_match_golden_modulo_source_line(self):
        for integration, directory in (("claude", "claude"), ("codex", "codex")):
            for name in SKILL_NAMES:
                with self.subTest(integration=integration, skill=name):
                    golden = (GOLDEN / directory / name / "SKILL.md").read_text(encoding="utf-8")
                    mine = self.by_path[f"{INTEGRATION_ROOTS[integration]}/{name}/SKILL.md"].content.decode("utf-8")
                    self.assertEqual(_normalize_source_line(mine), _normalize_source_line(golden))

    def test_skill_source_line_names_the_skill_source(self):
        for integration in ("claude", "codex"):
            mine = self.by_path[f"{INTEGRATION_ROOTS[integration]}/concorde-main/SKILL.md"].content.decode("utf-8")
            self.assertIn('source: "skills/concorde-main/SKILL.md"', mine)

    def test_exactly_fourteen_skill_outputs_nine_role_outputs_and_one_langgraph_config(self):
        skill_outputs = [
            path for path in self.by_path
            if path.startswith(".claude/skills/") or path.startswith(".agents/skills/")
        ]
        role_outputs = [path for path in self.by_path if path.startswith("generated/roles/")]
        self.assertEqual(len(skill_outputs), 14)
        self.assertEqual(len(role_outputs), 9)
        self.assertIn("generated/langgraph.json", self.by_path)

    def test_langgraph_config_names_one_graph_per_skill(self):
        import json

        payload = json.loads(self.by_path["generated/langgraph.json"].content)
        self.assertEqual(set(payload["graphs"]), set(SKILL_NAMES))
        for name in SKILL_NAMES:
            self.assertEqual(
                payload["graphs"][name],
                f"./scripts/development/studio.py:{name.replace('-', '_')}",
            )

    def test_manifest_has_sorted_keys_and_trailing_newline(self):
        manifest = self.result.manifest.decode("utf-8")
        self.assertTrue(manifest.endswith("\n"))
        self.assertNotIn("\r", manifest)
        import json

        payload = json.loads(manifest)
        self.assertEqual(payload["schema_version"], 1)
        self.assertIn("sources", payload)
        self.assertIn("outputs", payload)
        for output in self.result.outputs:
            self.assertIn(output.path, payload["outputs"])
            self.assertEqual(payload["outputs"][output.path]["sources"], sorted(output.sources))


class BuildDeterminismTests(unittest.TestCase):
    def test_building_twice_yields_identical_bytes(self):
        first = build(REPOSITORY_ROOT, "all")
        second = build(REPOSITORY_ROOT, "all")
        self.assertEqual(first.manifest, second.manifest)
        first_by_path = {o.path: o.content for o in first.outputs}
        second_by_path = {o.path: o.content for o in second.outputs}
        self.assertEqual(first_by_path, second_by_path)

    def test_integration_all_equals_the_union_of_claude_and_codex(self):
        all_result = build(REPOSITORY_ROOT, "all")
        claude_result = build(REPOSITORY_ROOT, "claude")
        codex_result = build(REPOSITORY_ROOT, "codex")
        all_paths = {o.path: o.content for o in all_result.outputs}
        for output in (*claude_result.outputs, *codex_result.outputs):
            if output.path.startswith((".claude/skills/", ".agents/skills/")):
                self.assertEqual(all_paths[output.path], output.content)


class BuildCheckLifecycleTests(unittest.TestCase):
    """Exercise --check freshness against an isolated copy; the real checkout is never touched."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(REPOSITORY_ROOT / "prompts", self.root / "prompts")
        shutil.copytree(REPOSITORY_ROOT / "skills", self.root / "skills")

    def test_check_fails_before_build_and_passes_after(self):
        current, differences = check_build(self.root, "all")
        self.assertFalse(current)
        self.assertIn("generated/build-manifest.json", differences)

        write_build(self.root, "all")
        current, differences = check_build(self.root, "all")
        self.assertTrue(current)
        self.assertEqual(differences, ())

    def test_check_fails_again_after_editing_a_prompt(self):
        write_build(self.root, "all")
        current, _ = check_build(self.root, "all")
        self.assertTrue(current)

        edited = self.root / "prompts/workflow-host/gap-reporting.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "One more sentence.\n", encoding="utf-8")

        current, differences = check_build(self.root, "all")
        self.assertFalse(current)
        self.assertTrue(differences)

    def test_check_never_writes_under_generated_or_the_skill_roots(self):
        self.assertFalse((self.root / "generated").exists())
        self.assertFalse((self.root / ".claude").exists())
        self.assertFalse((self.root / ".agents").exists())
        check_build(self.root, "all")
        self.assertFalse((self.root / "generated").exists())
        self.assertFalse((self.root / ".claude").exists())
        self.assertFalse((self.root / ".agents").exists())

    def test_check_ignores_a_third_party_skill_directory(self):
        write_build(self.root, "all")
        other = self.root / ".claude/skills/archify"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("unrelated third-party skill\n", encoding="utf-8")
        current, differences = check_build(self.root, "all")
        self.assertTrue(current)
        self.assertEqual(differences, ())


class BuildFreshnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(REPOSITORY_ROOT / "prompts", self.root / "prompts")
        shutil.copytree(REPOSITORY_ROOT / "skills", self.root / "skills")

    def test_verify_fresh_fails_closed_with_no_manifest(self):
        with self.assertRaises(BuildError) as failure:
            verify_fresh(self.root)
        self.assertEqual(failure.exception.code, "stale_build")

    def test_verify_fresh_passes_immediately_after_build(self):
        write_build(self.root, "all")
        verify_fresh(self.root)  # must not raise

    def test_verify_fresh_fails_after_editing_a_recorded_source(self):
        write_build(self.root, "all")
        edited = self.root / "prompts/workflow-host/gap-reporting.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "Changed.\n", encoding="utf-8")
        with self.assertRaises(BuildError) as failure:
            verify_fresh(self.root)
        self.assertEqual(failure.exception.code, "stale_build")

    def test_verify_fresh_fails_when_a_recorded_source_is_gone(self):
        write_build(self.root, "all")
        (self.root / "prompts/workflow-host/gap-reporting.md").unlink()
        with self.assertRaises(BuildError) as failure:
            verify_fresh(self.root)
        self.assertEqual(failure.exception.code, "stale_build")

    def test_load_role_prompt_verifies_freshness_and_returns_effects(self):
        write_build(self.root, "all")
        prompt = load_role_prompt(self.root, "concorde-spec-author")
        self.assertEqual(prompt.name, "concorde-spec-author")
        self.assertEqual(prompt.kind, "skill")
        self.assertEqual(prompt.exposure, "internal")
        self.assertIsNotNone(prompt.effects)
        self.assertTrue(prompt.body.strip())

        edited = self.root / "prompts/spec-context/spec-author.md"
        edited.write_text(edited.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")
        with self.assertRaises(BuildError) as failure:
            load_role_prompt(self.root, "concorde-spec-author")
        self.assertEqual(failure.exception.code, "stale_build")

    def test_load_role_prompt_accepts_underscore_and_hyphenated_names(self):
        write_build(self.root, "all")
        by_external = load_role_prompt(self.root, "concorde-context-assessor")
        by_underscore = load_role_prompt(self.root, "context_assessor")
        self.assertEqual(by_external.body, by_underscore.body)
        self.assertEqual(by_external.name, "concorde-context-assessor")


class BuildErrorTests(unittest.TestCase):
    def test_unbound_variable_in_a_skill_source_fails_the_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(REPOSITORY_ROOT / "prompts", root / "prompts")
            shutil.copytree(REPOSITORY_ROOT / "skills", root / "skills")
            main = root / "skills/concorde-main/SKILL.md"
            main.write_text(main.read_text(encoding="utf-8") + "\nUnbound {SOMETHING}.\n", encoding="utf-8")
            with self.assertRaises(BuildError):
                build(root, "all")


if __name__ == "__main__":
    unittest.main()
