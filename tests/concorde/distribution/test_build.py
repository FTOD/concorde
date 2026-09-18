from __future__ import annotations

import ast
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution.build import (  # noqa: E402
    INTEGRATION_ROOTS,
    MODEL_ROOTS,
    RETIRED_SKILL_NAMES,
    SKILL_NAMES,
    BuildError,
    build,
    check_build,
    load_model_instructions,
    verify_fresh,
    write_build,
)
from concorde.spec.verification import verifies  # noqa: E402

GOLDEN = REPOSITORY_ROOT / "tests/concorde/fixtures/build/golden"
_SOURCE_LINE = re.compile(r"(?m)^(\s*source:\s*).*$")


def _normalize_source_line(text: str) -> str:
    return _SOURCE_LINE.sub(lambda match: match.group(1) + '"NORMALIZED"', text)


class BuildGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = build(REPOSITORY_ROOT, "all")
        cls.by_path = {output.path: output for output in cls.result.outputs}

    @verifies("scenario.distribution.build-render")
    def test_golden_inventory_matches_current_projections(self):
        expected = {
            path.removeprefix("generated/")
            for path in self.by_path
            if path.startswith("generated/agents/")
        }
        for integration, prefix in INTEGRATION_ROOTS.items():
            expected.update(
                f"{integration}/{path.removeprefix(prefix + '/')}"
                for path in self.by_path
                if path.startswith(prefix + "/")
            )
        actual = {
            path.relative_to(GOLDEN).as_posix()
            for path in GOLDEN.rglob("*")
            if path.is_file()
        }
        self.assertEqual(actual, expected)
        self.assertFalse(set(RETIRED_SKILL_NAMES) & set(SKILL_NAMES))

    @verifies("scenario.distribution.build-render")
    def test_agent_bodies_match_golden_bytes_exactly(self):
        for path, output in self.by_path.items():
            if path.startswith("generated/agents/"):
                with self.subTest(path=path):
                    golden = (GOLDEN / path.removeprefix("generated/")).read_bytes()
                    self.assertEqual(output.content, golden)

    @verifies("scenario.distribution.build-render")
    def test_skill_projections_match_golden_modulo_source_line(self):
        for integration, directory in (("claude", "claude"), ("codex", "codex")):
            for name in SKILL_NAMES:
                with self.subTest(integration=integration, skill=name):
                    golden = (GOLDEN / directory / name / "SKILL.md").read_text(
                        encoding="utf-8"
                    )
                    mine = self.by_path[
                        f"{INTEGRATION_ROOTS[integration]}/{name}/SKILL.md"
                    ].content.decode("utf-8")
                    self.assertEqual(
                        _normalize_source_line(mine), _normalize_source_line(golden)
                    )

    def test_skill_source_line_names_the_skill_source(self):
        for integration in ("claude", "codex"):
            mine = self.by_path[
                f"{INTEGRATION_ROOTS[integration]}/concorde-main/SKILL.md"
            ].content.decode("utf-8")
            self.assertIn('source: "skills/concorde-main/SKILL.md"', mine)

    @verifies("scenario.distribution.build-checkout-skills-user-invoked")
    def test_checkout_claude_skills_are_user_invoked_while_installed_ones_stay_model_invocable(
        self,
    ):
        installed = {
            output.path: output
            for output in build(
                REPOSITORY_ROOT, "all", framework_prefix=".concorde/framework"
            ).outputs
        }
        for name in SKILL_NAMES:
            claude_path = f"{INTEGRATION_ROOTS['claude']}/{name}/SKILL.md"
            codex_path = f"{INTEGRATION_ROOTS['codex']}/{name}/SKILL.md"
            with self.subTest(skill=name):
                checkout_claude = self.by_path[claude_path].content.decode("utf-8")
                checkout_front, _, _ = checkout_claude.removeprefix("---\n").partition(
                    "\n---\n"
                )
                self.assertIn("\nuser-invocable: true\n", "\n" + checkout_front + "\n")
                self.assertIn(
                    "\ndisable-model-invocation: true\n", "\n" + checkout_front + "\n"
                )
                self.assertIn(
                    f"python3 scripts/run-operation.py {name}", checkout_claude
                )
                installed_claude = installed[claude_path].content.decode("utf-8")
                installed_front, _, _ = installed_claude.removeprefix(
                    "---\n"
                ).partition("\n---\n")
                self.assertIn("\nuser-invocable: true\n", "\n" + installed_front + "\n")
                self.assertIn(
                    "\ndisable-model-invocation: false\n", "\n" + installed_front + "\n"
                )
                self.assertIn(
                    f"python3 .concorde/framework/scripts/run-operation.py {name}",
                    installed_claude,
                )
                for codex in (self.by_path[codex_path], installed[codex_path]):
                    codex_front, _, _ = (
                        codex.content.decode("utf-8")
                        .removeprefix("---\n")
                        .partition("\n---\n")
                    )
                    self.assertNotIn("user-invocable", codex_front)
                    self.assertNotIn("disable-model-invocation", codex_front)

    @verifies("scenario.distribution.build-render")
    def test_eighteen_skills_twelve_agents_and_one_langgraph_config(self):
        skill_outputs = [
            path
            for path in self.by_path
            if path.startswith((".claude/skills/", ".agents/skills/"))
        ]
        agent_outputs = [
            path for path in self.by_path if path.startswith("generated/agents/")
        ]
        self.assertEqual(len(skill_outputs), 18)
        self.assertEqual(len(agent_outputs), 12)
        # One flat rendered file per worker, never a mode subdirectory.
        self.assertTrue(all(path.count("/") == 2 for path in agent_outputs))
        self.assertEqual(
            set(agent_outputs),
            {f"generated/agents/{agent}.md" for agent in MODEL_ROOTS},
        )
        self.assertIn("generated/langgraph.json", self.by_path)

    @verifies("scenario.distribution.build-render")
    def test_langgraph_config_names_one_graph_per_skill(self):

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

        payload = json.loads(manifest)
        self.assertEqual(payload["schema_version"], 1)
        self.assertIn("sources", payload)
        self.assertIn("outputs", payload)
        for output in self.result.outputs:
            self.assertIn(output.path, payload["outputs"])
            self.assertEqual(
                payload["outputs"][output.path]["sources"], sorted(output.sources)
            )

    @verifies("scenario.distribution.build-render")
    def test_runtime_schemas_remain_without_docsite_projections(self):

        self.assertFalse(
            any(path.startswith("generated/docs/") for path in self.by_path)
        )
        schemas = json.loads(self.by_path["generated/protocol/schemas.json"].content)
        self.assertIn("concorde-main-request", schemas)


class BuildDeterminismTests(unittest.TestCase):
    @verifies("scenario.distribution.build-render")
    def test_building_twice_yields_identical_bytes(self):
        first = build(REPOSITORY_ROOT, "all")
        second = build(REPOSITORY_ROOT, "all")
        self.assertEqual(first.manifest, second.manifest)
        first_by_path = {o.path: o.content for o in first.outputs}
        second_by_path = {o.path: o.content for o in second.outputs}
        self.assertEqual(first_by_path, second_by_path)

    @verifies("scenario.distribution.build-render")
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
        shutil.copytree(REPOSITORY_ROOT / "protocol", self.root / "protocol")
        shutil.copytree(REPOSITORY_ROOT / "skills", self.root / "skills")
        shutil.copytree(REPOSITORY_ROOT / "operations", self.root / "operations")
        shutil.copytree(
            REPOSITORY_ROOT / "src/concorde/spec",
            self.root / "src/concorde/spec",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

    @verifies("scenario.distribution.build-check", "scenario.distribution.build-write")
    def test_check_fails_before_build_and_passes_after(self):
        current, differences = check_build(self.root, "all")
        self.assertFalse(current)
        self.assertIn("generated/build-manifest.json", differences)

        write_build(self.root, "all")
        current, differences = check_build(self.root, "all")
        self.assertTrue(current)
        self.assertEqual(differences, ())

    @verifies("scenario.distribution.build-check")
    def test_check_fails_again_after_editing_a_prompt(self):
        write_build(self.root, "all")
        current, _ = check_build(self.root, "all")
        self.assertTrue(current)

        edited = self.root / "prompts/workflow-host/gap-reporting.md"
        edited.write_text(
            edited.read_text(encoding="utf-8") + "One more sentence.\n",
            encoding="utf-8",
        )

        current, differences = check_build(self.root, "all")
        self.assertFalse(current)
        self.assertTrue(differences)

    @verifies(
        "scenario.distribution.build-check",
        "scenario.distribution.build-stale-blocks-execution",
    )
    def test_independent_protocol_edit_invalidates_runtime_rule_projection(self):
        write_build(self.root, "all")
        chapter = self.root / "protocol/principles.md"
        chapter.write_text(chapter.read_text() + "\nA changed standard.\n")
        with self.assertRaises(BuildError) as context:
            verify_fresh(self.root)
        self.assertEqual(context.exception.code, "stale_build")
        current, differences = check_build(self.root, "all")
        self.assertFalse(current)
        self.assertIn("generated/protocol/principles.md", differences)

    @verifies("scenario.distribution.build-check")
    def test_check_never_writes_under_generated_or_the_skill_roots(self):
        self.assertFalse((self.root / "generated").exists())
        self.assertFalse((self.root / ".claude").exists())
        self.assertFalse((self.root / ".agents").exists())
        check_build(self.root, "all")
        self.assertFalse((self.root / "generated").exists())
        self.assertFalse((self.root / ".claude").exists())
        self.assertFalse((self.root / ".agents").exists())

    @verifies("scenario.distribution.build-check")
    def test_check_ignores_a_third_party_skill_directory(self):
        write_build(self.root, "all")
        other = self.root / ".claude/skills/example-third-party"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text(
            "unrelated third-party skill\n", encoding="utf-8"
        )
        current, differences = check_build(self.root, "all")
        self.assertTrue(current)
        self.assertEqual(differences, ())

    @verifies(
        "scenario.distribution.build-retired-skills",
        "scenario.distribution.build-check",
    )
    def test_retired_skills_are_reported_then_removed_without_a_manifest_entry(self):
        write_build(self.root)
        retired = []
        for prefix in INTEGRATION_ROOTS.values():
            for name in RETIRED_SKILL_NAMES:
                directory = self.root / prefix / name
                directory.mkdir(parents=True)
                (directory / "SKILL.md").write_text("old generated projection\n")
                retired.append(directory)
            for name in ("example-third-party", "concorde-custom"):
                directory = self.root / prefix / name
                directory.mkdir()
                (directory / "SKILL.md").write_text("unowned skill\n")
        before = {
            directory: (directory / "SKILL.md").read_bytes() for directory in retired
        }
        current, differences = check_build(self.root)
        self.assertFalse(current)
        self.assertEqual(
            set(differences),
            {directory.relative_to(self.root).as_posix() for directory in retired},
        )
        for directory, content in before.items():
            self.assertEqual((directory / "SKILL.md").read_bytes(), content)
        write_build(self.root)
        self.assertTrue(all(not directory.exists() for directory in retired))
        for prefix in INTEGRATION_ROOTS.values():
            for name in ("example-third-party", "concorde-custom"):
                self.assertEqual(
                    (self.root / prefix / name / "SKILL.md").read_text(),
                    "unowned skill\n",
                )
        self.assertEqual(check_build(self.root), (True, ()))
        # A second build is a no-op, including retired directories.
        first = write_build(self.root)
        second = write_build(self.root)
        self.assertEqual(first.manifest, second.manifest)

    @verifies("scenario.distribution.build-retired-skills")
    def test_retirement_uses_selected_integration_and_separate_destination(self):
        with tempfile.TemporaryDirectory() as raw_destination:
            destination = Path(raw_destination)
            for base in (self.root, destination):
                for prefix in INTEGRATION_ROOTS.values():
                    directory = base / prefix / RETIRED_SKILL_NAMES[0]
                    directory.mkdir(parents=True)
                    (directory / "SKILL.md").write_text("old projection\n")
            write_build(self.root, "claude", integration_root=destination)
            self.assertFalse(
                (
                    destination / INTEGRATION_ROOTS["claude"] / RETIRED_SKILL_NAMES[0]
                ).exists()
            )
            self.assertTrue(
                (
                    destination / INTEGRATION_ROOTS["codex"] / RETIRED_SKILL_NAMES[0]
                ).exists()
            )
            for prefix in INTEGRATION_ROOTS.values():
                self.assertTrue((self.root / prefix / RETIRED_SKILL_NAMES[0]).exists())

    @verifies("scenario.distribution.build-retired-skills")
    def test_retirement_removes_an_empty_directory(self):
        directory = self.root / INTEGRATION_ROOTS["claude"] / RETIRED_SKILL_NAMES[0]
        directory.mkdir(parents=True)
        write_build(self.root)
        self.assertFalse(directory.exists())

    @verifies("scenario.distribution.build-retired-skills")
    def test_retirement_preflights_all_directories_before_deleting_or_writing(self):
        write_build(self.root)
        manifest = (self.root / "generated/build-manifest.json").read_bytes()
        directories = []
        for prefix in INTEGRATION_ROOTS.values():
            directory = self.root / prefix / RETIRED_SKILL_NAMES[0]
            directory.mkdir(parents=True)
            (directory / "SKILL.md").write_text("old projection\n")
            directories.append(directory)
        unexpected = directories[-1] / "user-notes.txt"
        unexpected.write_text("preserve me\n")
        # Make the next render different to detect an early manifest/output write.
        source = self.root / "prompts/workflow-host/gap-reporting.md"
        source.write_text(source.read_text() + "\nChanged instructions.\n")
        with self.assertRaisesRegex(BuildError, "unexpected retired skill content"):
            write_build(self.root)
        self.assertEqual(unexpected.read_text(), "preserve me\n")
        for directory in directories:
            self.assertEqual((directory / "SKILL.md").read_text(), "old projection\n")
        self.assertEqual(
            (self.root / "generated/build-manifest.json").read_bytes(), manifest
        )

    @verifies("scenario.distribution.build-retired-skills")
    def test_retirement_refuses_symlinks_and_non_directories(self):
        with tempfile.TemporaryDirectory() as raw_outside:
            outside = Path(raw_outside)
            (outside / "SKILL.md").write_text("outside instructions\n")
            directory = self.root / INTEGRATION_ROOTS["claude"] / RETIRED_SKILL_NAMES[0]
            directory.parent.mkdir(parents=True)
            for kind in (
                "directory-link",
                "file-link",
                "dangling-link",
                "regular-file",
            ):
                with self.subTest(kind=kind):
                    if kind == "directory-link":
                        directory.symlink_to(outside, target_is_directory=True)
                    elif kind == "regular-file":
                        directory.write_text("not a directory\n")
                    else:
                        directory.mkdir()
                        target = outside / (
                            "SKILL.md" if kind == "file-link" else "missing"
                        )
                        (directory / "SKILL.md").symlink_to(target)
                    current, differences = check_build(self.root)
                    self.assertFalse(current)
                    self.assertIn(
                        directory.relative_to(self.root).as_posix(), differences
                    )
                    with self.assertRaises(BuildError):
                        write_build(self.root)
                    self.assertFalse((self.root / "generated").exists())
                    self.assertEqual(
                        (outside / "SKILL.md").read_text(), "outside instructions\n"
                    )
                    if directory.is_symlink() or directory.is_file():
                        directory.unlink()
                    else:
                        (directory / "SKILL.md").unlink()
                        directory.rmdir()

    @verifies("scenario.distribution.build-retired-skills")
    def test_retirement_refuses_symlinked_integration_ancestors(self):
        with tempfile.TemporaryDirectory() as raw_outside:
            outside = Path(raw_outside)
            for relative in (".claude", ".claude/skills"):
                with self.subTest(relative=relative):
                    link = self.root / relative
                    link.parent.mkdir(parents=True, exist_ok=True)
                    link.symlink_to(outside, target_is_directory=True)
                    with self.assertRaisesRegex(
                        BuildError, "skill output directory is a symlink"
                    ):
                        write_build(self.root)
                    self.assertEqual(list(outside.iterdir()), [])
                    self.assertFalse((self.root / "generated").exists())
                    link.unlink()

    @verifies("scenario.distribution.build-check")
    def test_check_ignores_an_unrelated_file_under_generated(self):
        """`generated/` is a shared, ignored root; a file another tool writes there (for example
        the legacy initializer's diagram renders under `generated/architecture/`) is not a
        build-owned location and must never be reported as drift."""
        write_build(self.root, "all")
        other = self.root / "generated/architecture"
        other.mkdir(parents=True)
        (other / "example.html").write_text(
            "unrelated diagram render\n", encoding="utf-8"
        )
        current, differences = check_build(self.root, "all")
        self.assertTrue(current)
        self.assertEqual(differences, ())

    @verifies("scenario.distribution.build-check")
    def test_check_reports_an_unexpected_file_in_an_owned_directory(self):
        write_build(self.root, "all")
        (self.root / "generated/agents/extra.md").write_text(
            "not a build output\n", encoding="utf-8"
        )
        current, differences = check_build(self.root, "all")
        self.assertFalse(current)
        self.assertIn("generated/agents/extra.md", differences)

    @verifies("scenario.distribution.build-check")
    def test_check_reports_a_modified_owned_file(self):
        write_build(self.root, "all")
        target = self.root / "generated/agents/planner.md"
        target.write_text(
            target.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8"
        )
        current, differences = check_build(self.root, "all")
        self.assertFalse(current)
        self.assertIn("generated/agents/planner.md", differences)


class BuildFreshnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(REPOSITORY_ROOT / "prompts", self.root / "prompts")
        shutil.copytree(REPOSITORY_ROOT / "protocol", self.root / "protocol")
        shutil.copytree(REPOSITORY_ROOT / "skills", self.root / "skills")
        shutil.copytree(REPOSITORY_ROOT / "operations", self.root / "operations")
        shutil.copytree(
            REPOSITORY_ROOT / "src/concorde/spec",
            self.root / "src/concorde/spec",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

    @verifies("scenario.distribution.build-stale-blocks-execution")
    def test_verify_fresh_fails_closed_with_no_manifest(self):
        with self.assertRaises(BuildError) as failure:
            verify_fresh(self.root)
        self.assertEqual(failure.exception.code, "stale_build")

    def test_verify_fresh_passes_immediately_after_build(self):
        write_build(self.root, "all")
        verify_fresh(self.root)  # must not raise

    @verifies("scenario.distribution.build-stale-blocks-execution")
    def test_verify_fresh_fails_after_editing_a_recorded_source(self):
        write_build(self.root, "all")
        edited = self.root / "prompts/workflow-host/gap-reporting.md"
        edited.write_text(
            edited.read_text(encoding="utf-8") + "Changed.\n", encoding="utf-8"
        )
        with self.assertRaises(BuildError) as failure:
            verify_fresh(self.root)
        self.assertEqual(failure.exception.code, "stale_build")

    @verifies("scenario.distribution.build-stale-blocks-execution")
    def test_child_definition_and_python_contract_edits_both_invalidate_build(self):
        write_build(self.root, "all")
        for relative in (
            "operations/programmer/children/scout.md",
            "operations/programmer/__init__.py",
        ):
            path = self.root / relative
            before = path.read_text()
            with self.subTest(source=relative):
                path.write_text(before + "\n# Changed worker profile\n")
                with self.assertRaises(BuildError) as failure:
                    verify_fresh(self.root)
                self.assertEqual("stale_build", failure.exception.code)
                path.write_text(before)

    @verifies("scenario.distribution.build-stale-blocks-execution")
    def test_verify_fresh_fails_when_a_recorded_source_is_gone(self):
        write_build(self.root, "all")
        (self.root / "prompts/workflow-host/gap-reporting.md").unlink()
        with self.assertRaises(BuildError) as failure:
            verify_fresh(self.root)
        self.assertEqual(failure.exception.code, "stale_build")

    @verifies("scenario.distribution.load-agent")
    def test_load_agent_verifies_freshness_and_returns_effects_and_binding(self):
        write_build(self.root, "all")
        prompt = load_model_instructions(self.root, "concorde-planner")
        self.assertEqual(prompt.name, "concorde-planner")
        self.assertEqual(prompt.kind, "skill")
        self.assertIsNotNone(prompt.effects)
        self.assertTrue(prompt.body.strip())
        self.assertIsNotNone(prompt.binding)
        self.assertEqual(prompt.binding.agent, "planner")
        self.assertEqual(prompt.binding.spec_path, "operations/planner/spec.md")

        edited = self.root / "operations/planner/spec.md"
        edited.write_text(
            edited.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8"
        )
        with self.assertRaises(BuildError) as failure:
            load_model_instructions(self.root, "concorde-planner")
        self.assertEqual(failure.exception.code, "stale_build")

    @verifies("scenario.distribution.load-agent")
    def test_load_agent_accepts_underscore_and_hyphenated_names(self):
        write_build(self.root, "all")
        by_external = load_model_instructions(self.root, "concorde-planner")
        by_underscore = load_model_instructions(self.root, "planner")
        self.assertEqual(by_external.body, by_underscore.body)
        self.assertEqual(by_external.name, "concorde-planner")

    @verifies("scenario.distribution.load-agent")
    def test_load_agent_accepts_a_hyphenated_multiword_agent_name(self):
        write_build(self.root, "all")
        by_external = load_model_instructions(self.root, "concorde-code-reviewer")
        by_underscore = load_model_instructions(self.root, "code_reviewer")
        self.assertEqual(by_external.body, by_underscore.body)
        self.assertEqual(by_external.name, "concorde-code-reviewer")
        self.assertEqual(by_external.binding.agent, "code_reviewer")


class WireHelperBuildTests(unittest.TestCase):
    @verifies(
        "scenario.distribution.build-render",
        "scenario.distribution.build-write",
        "scenario.distribution.build-check",
        "scenario.distribution.build-stale-blocks-execution",
    )
    def test_wire_helper_change_invalidates_and_rebuilds_actual_schema_outputs(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for directory in ("prompts", "protocol", "skills", "operations"):
                shutil.copytree(REPOSITORY_ROOT / directory, root / directory)
            shutil.copytree(
                REPOSITORY_ROOT / "src/concorde/spec",
                root / "src/concorde/spec",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            # This isolated render fixture does not accept a consumer Protocol binding.
            (root / "protocol/manifest.json").unlink()

            def contents():
                return {
                    p.relative_to(root).as_posix(): p.read_bytes()
                    for p in root.rglob("*")
                    if p.is_file()
                }

            def invoke_model_backed_operation():
                # The fixture is this invocation's package root: a top-level model-backed
                # operation verifies the fixture build before admitting anything else.
                from concorde.development.operation_host import (
                    OperationHost,
                    run_operation,
                )
                from concorde.spec.typed_data import typed

                def launched(launch):
                    raise AssertionError("an WorkerProfile launched on a stale build")

                host = OperationHost(
                    root, root, mode="describe-policy", executor=launched
                )
                return run_operation(
                    "concorde-review",
                    None,
                    typed(
                        "concorde-review-request",
                        {
                            "target_id": "module.fixture",
                            "task": "Review",
                            "review_mode": "spec",
                        },
                    ),
                    host_context=host,
                )

            with (
                patch(
                    "subprocess.Popen", side_effect=AssertionError("build process I/O")
                ),
                patch("socket.socket", side_effect=AssertionError("build network I/O")),
            ):
                first = write_build(root)
                verify_fresh(root)
                self.assertEqual((True, ()), check_build(root))
                self.assertEqual(first, build(root))
                admitted = invoke_model_backed_operation()
                self.assertNotEqual(
                    "stale_build", (admitted["errors"] or [{}])[0].get("code"), admitted
                )
                helper = root / "src/concorde/spec/wire_shapes.py"
                before = contents()

                class DescribeStrings(ast.NodeTransformer):
                    def visit_Dict(self, node):
                        self.generic_visit(node)
                        if any(
                            isinstance(k, ast.Constant)
                            and k.value == "type"
                            and isinstance(v, ast.Constant)
                            and v.value == "string"
                            for k, v in zip(node.keys, node.values, strict=True)
                        ):
                            node.keys.append(ast.Constant("description"))
                            node.values.append(
                                ast.Constant("Fixture helper schema change")
                            )
                        return node

                changed = DescribeStrings().visit(ast.parse(helper.read_text()))
                helper.write_text(
                    ast.unparse(ast.fix_missing_locations(changed)) + "\n"
                )
                self.assertEqual(
                    {"src/concorde/spec/wire_shapes.py"},
                    {p for p, data in contents().items() if before.get(p) != data},
                )
                with self.assertRaises(BuildError) as failure:
                    verify_fresh(root)
                self.assertEqual("stale_build", failure.exception.code)
                before_invocation = contents()
                refused = invoke_model_backed_operation()
                self.assertEqual("blocked", refused["status"], refused)
                self.assertEqual("stale_build", refused["errors"][0]["code"], refused)
                self.assertIsNone(refused["output"])
                self.assertEqual(before_invocation, contents())
                before_check = contents()
                current, differences = check_build(root)
                self.assertFalse(current)
                self.assertIn("generated/protocol/schemas.json", differences)
                self.assertEqual(before_check, contents())
                rebuilt = write_build(root)
                schema_path = "generated/protocol/schemas.json"
                schema = (root / schema_path).read_bytes()
                self.assertNotEqual(before[schema_path], schema)
                self.assertIn("Fixture helper schema change", schema.decode())
                verify_fresh(root)
                self.assertEqual((True, ()), check_build(root))
                self.assertEqual(rebuilt, build(root))


class BuildErrorTests(unittest.TestCase):
    def test_unbound_variable_in_a_skill_source_fails_the_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(REPOSITORY_ROOT / "prompts", root / "prompts")
            shutil.copytree(REPOSITORY_ROOT / "protocol", root / "protocol")
            shutil.copytree(REPOSITORY_ROOT / "skills", root / "skills")
            shutil.copytree(REPOSITORY_ROOT / "operations", root / "operations")
            main = root / "skills/concorde-main/SKILL.md"
            main.write_text(
                main.read_text(encoding="utf-8") + "\nUnbound {SOMETHING}.\n",
                encoding="utf-8",
            )
            with self.assertRaises(BuildError):
                build(root, "all")

    def test_broken_schema_helper_fails_the_build_with_build_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for directory in ("prompts", "protocol", "skills", "operations"):
                shutil.copytree(REPOSITORY_ROOT / directory, root / directory)
            shutil.copytree(
                REPOSITORY_ROOT / "src/concorde/spec",
                root / "src/concorde/spec",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            (root / "protocol/manifest.json").unlink()
            helper = root / "src/concorde/spec/wire_shapes.py"
            helper.write_text(
                helper.read_text(encoding="utf-8") + "\nSTRING = {\n", encoding="utf-8"
            )
            for surface in (build, check_build, write_build):
                with (
                    self.subTest(surface=surface.__name__),
                    self.assertRaises(BuildError) as failure,
                ):
                    surface(root)
                self.assertEqual("invalid_build", failure.exception.code)
                self.assertIn("wire_shapes.py", str(failure.exception))
            self.assertFalse((root / "generated").exists())

    def test_incomplete_schema_source_tree_fails_closed_while_a_source_free_root_falls_back(
        self,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for directory in ("prompts", "protocol", "skills", "operations"):
                shutil.copytree(REPOSITORY_ROOT / directory, root / directory)
            shutil.copytree(
                REPOSITORY_ROOT / "src/concorde/spec",
                root / "src/concorde/spec",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            (root / "protocol/manifest.json").unlink()
            (root / "src/concorde/spec/contracts.py").unlink()
            with self.assertRaises(BuildError) as failure:
                build(root)
            self.assertEqual("invalid_build", failure.exception.code)
            self.assertIn("contracts.py", str(failure.exception))
            self.assertFalse((root / "generated").exists())
            shutil.rmtree(root / "src")
            rendered = build(root)
            schemas = next(
                o
                for o in rendered.outputs
                if o.path == "generated/protocol/schemas.json"
            )
            self.assertEqual((), schemas.sources)
            self.assertFalse(
                any(
                    s.startswith("src/concorde/spec/")
                    for o in rendered.outputs
                    for s in o.sources
                )
            )

    def test_root_inventory_missing_a_skill_request_schema_fails_the_build_with_build_error(
        self,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for directory in ("prompts", "protocol", "skills", "operations"):
                shutil.copytree(REPOSITORY_ROOT / directory, root / directory)
            shutil.copytree(
                REPOSITORY_ROOT / "src/concorde/spec",
                root / "src/concorde/spec",
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            (root / "protocol/manifest.json").unlink()
            contracts = root / "src/concorde/spec/contracts.py"
            contracts.write_text(
                contracts.read_text(encoding="utf-8")
                + (
                    "\n_ORIGINAL_EXPORTED_TYPES = exported_types\n"
                    "def exported_types():\n"
                    "    return tuple(n for n in _ORIGINAL_EXPORTED_TYPES() if n != 'concorde-main-request')\n"
                ),
                encoding="utf-8",
            )
            for surface in (build, check_build, write_build):
                with (
                    self.subTest(surface=surface.__name__),
                    self.assertRaises(BuildError) as failure,
                ):
                    surface(root)
                self.assertEqual("invalid_build", failure.exception.code)
                self.assertIn("concorde-main-request", str(failure.exception))
            self.assertFalse((root / "generated").exists())


if __name__ == "__main__":
    unittest.main()
