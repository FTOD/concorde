from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError, asdict
from pathlib import Path
from unittest.mock import patch

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.distribution.build import (
    MODEL_ROOTS,
    BuildError,
    ModelInstructions,
    build,
    check_build,
    load_model_instructions,
    verify_fresh,
    write_build,
)
from concorde.distribution.build import (
    PRIVATE_PI_SESSION_SHIM as PI_SESSION_SHIM,
)

# Imported eagerly: the schema-source test below patches ``subprocess.Popen`` while it invokes an
# Operation, and a module first imported under that patch would keep the mock in any
# definition-time default, leaking into every later test of the same process.
from concorde.operations.dispatch import run_operation  # noqa: E402
from concorde.spec.typed_data import typed  # noqa: E402
from concorde.spec.verification import verifies  # noqa: E402
from concorde.harness.host import OperationHost  # noqa: E402
from concorde.operations.catalog import PUBLIC_OPERATIONS  # noqa: E402

GOLDEN = REPOSITORY_ROOT / "tests/concorde/fixtures/build/golden"


class BuildGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = build(REPOSITORY_ROOT)
        cls.by_path = {output.path: output for output in cls.result.outputs}

    @verifies("scenario.distribution.build-render")
    def test_golden_inventory_matches_current_projections(self):
        expected = {
            path.removeprefix("generated/")
            for path in self.by_path
            if path.startswith(("generated/agents/", "generated/native/"))
        }
        expected.add("pi/concorde-session.ts")
        actual = {
            path.relative_to(GOLDEN).as_posix()
            for path in GOLDEN.rglob("*")
            if path.is_file()
        }
        self.assertEqual(actual, expected)

    @verifies("scenario.distribution.build-render")
    def test_agent_bodies_match_golden_bytes_exactly(self):
        for path, output in self.by_path.items():
            if path.startswith(("generated/agents/", "generated/native/")):
                with self.subTest(path=path):
                    golden = (GOLDEN / path.removeprefix("generated/")).read_bytes()
                    self.assertEqual(output.content, golden)

    @verifies("scenario.distribution.build-render")
    def test_one_pi_catalog_and_seven_workers(self):
        session_outputs = [
            p for p in self.by_path if p.startswith("generated/session/")
        ]
        agent_outputs = [
            path for path in self.by_path if path.startswith("generated/agents/")
        ]
        self.assertEqual(session_outputs, [PI_SESSION_SHIM])
        self.assertEqual(len(agent_outputs), 7)
        self.assertIn(PI_SESSION_SHIM, self.by_path)
        # One flat rendered file per worker, never a mode subdirectory.
        self.assertTrue(all(path.count("/") == 2 for path in agent_outputs))
        self.assertEqual(
            set(agent_outputs),
            {f"generated/agents/{agent}.md" for agent in MODEL_ROOTS},
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
        schemas = json.loads(self.by_path["generated/schemas.json"].content)
        self.assertIn("concorde-context-solve-request", schemas)


class BuildDeterminismTests(unittest.TestCase):
    @verifies("scenario.distribution.build-render")
    def test_building_twice_yields_identical_bytes(self):
        first = build(REPOSITORY_ROOT)
        second = build(REPOSITORY_ROOT)
        self.assertEqual(first.manifest, second.manifest)
        first_by_path = {o.path: o.content for o in first.outputs}
        second_by_path = {o.path: o.content for o in second.outputs}
        self.assertEqual(first_by_path, second_by_path)


class BuildCheckLifecycleTests(unittest.TestCase):
    """Exercise --check freshness against an isolated copy; the real checkout is never touched."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(REPOSITORY_ROOT / "prompts", self.root / "prompts")
        shutil.copytree(REPOSITORY_ROOT / "protocol", self.root / "protocol")
        shutil.copytree(REPOSITORY_ROOT / "agents", self.root / "agents")
        shutil.copytree(REPOSITORY_ROOT / "operations", self.root / "operations")
        shutil.copytree(
            REPOSITORY_ROOT / "src/concorde/spec",
            self.root / "src/concorde/spec",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

    @verifies("scenario.distribution.build-check", "scenario.distribution.build-write")
    def test_check_fails_before_build_and_passes_after(self):
        current, differences = check_build(self.root)
        self.assertFalse(current)
        self.assertIn("generated/build-manifest.json", differences)

        write_build(self.root)
        current, differences = check_build(self.root)
        self.assertTrue(current)
        self.assertEqual(differences, ())

    @verifies("scenario.distribution.build-check")
    def test_check_fails_again_after_editing_a_prompt(self):
        write_build(self.root)
        current, _ = check_build(self.root)
        self.assertTrue(current)

        edited = self.root / "prompts/native/context-assessor.md"
        edited.write_text(
            edited.read_text(encoding="utf-8") + "One more sentence.\n",
            encoding="utf-8",
        )

        current, differences = check_build(self.root)
        self.assertFalse(current)
        self.assertTrue(differences)

    @verifies(
        "scenario.distribution.build-check",
        "scenario.admission.stale-build",
    )
    def test_independent_protocol_edit_invalidates_runtime_rule_projection(self):
        write_build(self.root)
        chapter = self.root / "protocol/principles.md"
        chapter.write_text(chapter.read_text() + "\nA changed standard.\n")
        with self.assertRaises(BuildError) as context:
            verify_fresh(self.root)
        self.assertEqual(context.exception.code, "stale_build")
        current, differences = check_build(self.root)
        self.assertFalse(current)
        self.assertIn("generated/protocol/principles.md", differences)

    @verifies("scenario.distribution.build-check")
    def test_check_never_writes(self):
        self.assertFalse((self.root / "generated").exists())
        self.assertFalse((self.root / ".pi").exists())
        check_build(self.root)
        self.assertFalse((self.root / "generated").exists())
        self.assertFalse((self.root / ".pi").exists())

    @verifies("scenario.distribution.build-check")
    def test_check_ignores_an_unrelated_file_under_generated(self):
        """`generated/` is a shared, ignored root; a file another tool writes there (for example
        diagram renders under `generated/architecture/`) is not a build-owned location and must
        never be reported as drift."""
        write_build(self.root)
        other = self.root / "generated/architecture"
        other.mkdir(parents=True)
        (other / "example.html").write_text(
            "unrelated diagram render\n", encoding="utf-8"
        )
        current, differences = check_build(self.root)
        self.assertTrue(current)
        self.assertEqual(differences, ())

    @verifies("scenario.distribution.build-check")
    def test_check_reports_an_unexpected_file_in_an_owned_directory(self):
        write_build(self.root)
        (self.root / "generated/agents/extra.md").write_text(
            "not a build output\n", encoding="utf-8"
        )
        current, differences = check_build(self.root)
        self.assertFalse(current)
        self.assertIn("generated/agents/extra.md", differences)

    @verifies("scenario.distribution.build-check")
    def test_check_reports_a_modified_owned_file(self):
        write_build(self.root)
        target = self.root / "generated/agents/planner.md"
        target.write_text(
            target.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8"
        )
        current, differences = check_build(self.root)
        self.assertFalse(current)
        self.assertIn("generated/agents/planner.md", differences)


class BuildFreshnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(REPOSITORY_ROOT / "prompts", self.root / "prompts")
        shutil.copytree(REPOSITORY_ROOT / "protocol", self.root / "protocol")
        shutil.copytree(REPOSITORY_ROOT / "agents", self.root / "agents")
        shutil.copytree(REPOSITORY_ROOT / "operations", self.root / "operations")
        shutil.copytree(
            REPOSITORY_ROOT / "src/concorde/spec",
            self.root / "src/concorde/spec",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

    @verifies("scenario.admission.stale-build")
    def test_verify_fresh_fails_closed_with_no_manifest(self):
        with self.assertRaises(BuildError) as failure:
            verify_fresh(self.root)
        self.assertEqual(failure.exception.code, "stale_build")

    def test_verify_fresh_passes_immediately_after_build(self):
        write_build(self.root)
        verify_fresh(self.root)  # must not raise

    @verifies("scenario.admission.stale-build")
    def test_verify_fresh_fails_after_editing_a_recorded_source(self):
        write_build(self.root)
        edited = self.root / "prompts/native/context-assessor.md"
        edited.write_text(
            edited.read_text(encoding="utf-8") + "Changed.\n", encoding="utf-8"
        )
        with self.assertRaises(BuildError) as failure:
            verify_fresh(self.root)
        self.assertEqual(failure.exception.code, "stale_build")

    @verifies("scenario.admission.stale-build")
    def test_role_and_python_contract_edits_both_invalidate_build(self):
        write_build(self.root)
        for relative in (
            "agents/programmer/spec.md",
            "agents/programmer/__init__.py",
        ):
            path = self.root / relative
            before = path.read_text()
            with self.subTest(source=relative):
                path.write_text(before + "\n# Changed worker profile\n")
                with self.assertRaises(BuildError) as failure:
                    verify_fresh(self.root)
                self.assertEqual("stale_build", failure.exception.code)
                path.write_text(before)

    @verifies("scenario.admission.stale-build")
    def test_verify_fresh_fails_when_a_recorded_source_is_gone(self):
        write_build(self.root)
        (self.root / "prompts/native/context-assessor.md").unlink()
        with self.assertRaises(BuildError) as failure:
            verify_fresh(self.root)
        self.assertEqual(failure.exception.code, "stale_build")

    @verifies("scenario.context.agent-bind")
    def test_load_agent_verifies_freshness_and_returns_effects_and_binding(self):
        write_build(self.root)
        prompt = load_model_instructions(self.root, "concorde-planner")
        self.assertEqual(prompt.name, "concorde-planner")
        self.assertIs(type(prompt), ModelInstructions)
        self.assertIsNotNone(prompt.effects)
        self.assertTrue(prompt.body.strip())
        self.assertIsNotNone(prompt.binding)
        self.assertEqual(prompt.binding.agent, "planner")
        self.assertEqual(prompt.binding.spec_path, "agents/planner/spec.md")

        edited = self.root / "agents/planner/spec.md"
        edited.write_text(
            edited.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8"
        )
        with self.assertRaises(BuildError) as failure:
            load_model_instructions(self.root, "concorde-planner")
        self.assertEqual(failure.exception.code, "stale_build")

    @verifies("scenario.context.agent-bind")
    def test_worker_instruction_records_retain_every_field_and_binding_digest(self):
        from concorde.harness.worker_profile import (
            binding_digest,
            profile_digest,
            worker_profile,
        )

        def digest(content):
            return "sha256:" + hashlib.sha256(content).hexdigest()

        write_build(self.root)
        for name in MODEL_ROOTS:
            with self.subTest(worker=name):
                prompt = load_model_instructions(self.root, name)
                profile = worker_profile(name)
                binding = prompt.binding
                self.assertIs(type(prompt), ModelInstructions)
                self.assertEqual(
                    {
                        "name",
                        "description",
                        "source_path",
                        "body",
                        "effects",
                        "binding",
                    },
                    set(asdict(prompt)),
                )
                self.assertEqual("concorde-" + name, prompt.name)
                self.assertEqual(f"Concorde {name} agent.", prompt.description)
                self.assertEqual(profile.spec, prompt.source_path)
                self.assertEqual(profile.contract.effects, prompt.effects)
                self.assertEqual(profile.name, binding.agent)
                self.assertEqual(profile.spec, binding.spec_path)
                self.assertEqual(
                    f"generated/agents/{name}.md", binding.instructions_path
                )
                self.assertEqual(
                    (self.root / binding.instructions_path).read_text(), prompt.body
                )
                self.assertEqual(
                    digest((self.root / profile.spec).read_bytes()), binding.spec_digest
                )
                self.assertEqual(
                    digest(prompt.body.encode()), binding.instructions_digest
                )
                self.assertEqual(
                    profile_digest(self.root, profile), binding.profile_digest
                )
                self.assertEqual(
                    digest((self.root / "generated/build-manifest.json").read_bytes()),
                    binding.build_manifest_digest,
                )
                self.assertEqual(profile.timeout_seconds, binding.timeout_seconds)
                self.assertEqual(binding_digest(binding), binding.digest)
                self.assertEqual(
                    {
                        "agent",
                        "spec_path",
                        "spec_digest",
                        "instructions_path",
                        "instructions_digest",
                        "profile_digest",
                        "build_manifest_digest",
                        "timeout_seconds",
                        "digest",
                    },
                    set(asdict(binding)),
                )
                with self.assertRaises(FrozenInstanceError):
                    prompt.body = "replacement"

    @verifies("scenario.context.agent-bind")
    def test_public_catalog_entries_do_not_imply_worker_instructions(self):
        write_build(self.root)
        for name in PUBLIC_OPERATIONS:
            with self.subTest(operation=name), self.assertRaises(BuildError) as failure:
                load_model_instructions(self.root, name)
            self.assertEqual("unknown_agent", failure.exception.code)

    @verifies("scenario.context.agent-bind")
    def test_load_agent_accepts_underscore_and_hyphenated_names(self):
        write_build(self.root)
        by_external = load_model_instructions(self.root, "concorde-planner")
        by_underscore = load_model_instructions(self.root, "planner")
        self.assertEqual(by_external.body, by_underscore.body)
        self.assertEqual(by_external.name, "concorde-planner")

    @verifies("scenario.context.agent-bind")
    def test_load_agent_accepts_a_hyphenated_multiword_agent_name(self):
        write_build(self.root)
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
        "scenario.admission.stale-build",
    )
    def test_a_schema_source_change_invalidates_until_rebuilt(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for directory in ("agents", "prompts", "protocol", "operations"):
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
                host = OperationHost(root, root, mode="describe-policy")
                return run_operation(
                    "concorde-spec-review",
                    None,
                    typed(
                        "concorde-spec-review-request",
                        {
                            "target_id": "module.fixture",
                            "task": "Review",
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
                helper = root / "src/concorde/spec/typed_data.py"
                before = contents()
                helper.write_text(
                    helper.read_text() + "\n# Fixture schema source change.\n"
                )
                self.assertEqual(
                    {"src/concorde/spec/typed_data.py"},
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
                self.assertIn("generated/build-manifest.json", differences)
                self.assertEqual(before_check, contents())
                rebuilt = write_build(root)
                verify_fresh(root)
                self.assertEqual((True, ()), check_build(root))
                self.assertEqual(rebuilt, build(root))


class BuildErrorTests(unittest.TestCase):
    def test_unbound_variable_in_operation_guidance_fails_the_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(REPOSITORY_ROOT / "prompts", root / "prompts")
            shutil.copytree(REPOSITORY_ROOT / "protocol", root / "protocol")
            shutil.copytree(REPOSITORY_ROOT / "agents", root / "agents")
            shutil.copytree(REPOSITORY_ROOT / "operations", root / "operations")
            main = root / "prompts/operation-guidance/concorde-context-solve.md"
            main.write_text(
                main.read_text(encoding="utf-8") + "\nUnbound {SOMETHING}.\n",
                encoding="utf-8",
            )
            with self.assertRaises(BuildError):
                build(root)

    def test_a_source_free_root_renders_the_registered_schemas_without_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for directory in ("agents", "prompts", "protocol", "operations"):
                shutil.copytree(REPOSITORY_ROOT / directory, root / directory)
            (root / "protocol/manifest.json").unlink()
            rendered = build(root)
            schemas = next(
                o for o in rendered.outputs if o.path == "generated/schemas.json"
            )
            self.assertIn("concorde-plan-artifact", json.loads(schemas.content))
            self.assertFalse(
                any(
                    s.startswith("src/concorde/")
                    for o in rendered.outputs
                    for s in o.sources
                )
            )

    @verifies("scenario.distribution.build-guidance-invalid")
    def test_a_capability_without_a_registered_request_schema_fails_the_build(self):
        from concorde.distribution import build as build_module

        registered = build_module.registered_schemas

        def without_request(project_root):
            payload, sources = registered(project_root)
            payload.pop("concorde-context-solve-request")
            return payload, sources

        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.object(build_module, "registered_schemas", without_request),
        ):
            root = Path(temporary)
            for directory in ("agents", "prompts", "protocol", "operations"):
                shutil.copytree(REPOSITORY_ROOT / directory, root / directory)
            (root / "protocol/manifest.json").unlink()
            for surface in (build, check_build, write_build):
                with (
                    self.subTest(surface=surface.__name__),
                    self.assertRaises(BuildError) as failure,
                ):
                    surface(root)
                self.assertEqual("invalid_build", failure.exception.code)
                self.assertIn("concorde-context-solve-request", str(failure.exception))
            self.assertFalse((root / "generated").exists())


class StaleOutputRemovalTests(unittest.TestCase):
    """An owned output the render no longer produces is removed only under manifest ownership."""

    setUp = BuildCheckLifecycleTests.setUp

    def recorded(self, root, relative, content=b"old generated bytes\n"):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        manifest_path = root / "generated/build-manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifest["outputs"][relative] = {
            "sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
            "sources": [],
        }
        manifest_path.write_text(json.dumps(manifest))
        return path

    @verifies("scenario.distribution.build-write", "scenario.distribution.build-check")
    def test_recorded_output_no_longer_produced_is_removed_with_empty_directories(self):
        write_build(self.root)
        stale = self.recorded(self.root, "generated/native/retired/worker.md")
        self.assertFalse(check_build(self.root)[0])
        write_build(self.root)
        self.assertFalse(stale.exists())
        self.assertFalse(stale.parent.exists())
        self.assertEqual((True, ()), check_build(self.root))

    @verifies("scenario.distribution.build-write")
    def test_removal_preflights_every_path_and_preserves_unverified_bytes(self):
        from tests.concorde.support.build_fixture import build_package_copy

        for defect in ("modified", "link", "unknown", "destination-link"):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                build_package_copy(root)
                old = self.recorded(root, "generated/native/retired-a.md")
                other = self.recorded(root, "generated/native/retired-b.md")
                if defect == "modified":
                    other.write_text("user edit")
                elif defect == "link":
                    other.unlink()
                    other.symlink_to(old)
                elif defect == "unknown":
                    (root / "generated/agents/unknown.md").write_text("user data")
                else:
                    dest = root / PI_SESSION_SHIM
                    dest.unlink()
                    dest.symlink_to(old)
                manifest = (root / "generated/build-manifest.json").read_bytes()
                with self.assertRaises(BuildError):
                    write_build(root)
                self.assertEqual(b"old generated bytes\n", old.read_bytes())
                self.assertEqual(
                    manifest, (root / "generated/build-manifest.json").read_bytes()
                )


if __name__ == "__main__":
    unittest.main()
