"""External references are resource context: granted read-only to the modes that read them."""

import unittest

from concorde.harness.context import recheck_context, resolve_context
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies
from tests.concorde.spec.support import source_pairs
from tests.concorde.spec.test_module_model import PACKAGE, ModuleImplementationTests


class ExternalReferenceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ModuleImplementationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.write("reference/lib/api.md", "## connect(url)\n")
        self.fixture.write("reference/lib/diagram.png", "binary")
        self.fixture.write("reference/other/api.md", "undeclared\n")
        self.fixture.declare_reference()

    @verifies("scenario.harness.external-references")
    def test_every_phase_sees_the_entries_and_a_byte_change_stales_them(self):
        from concorde.harness.worker_profile import worker_profile

        repository = self.fixture.repository()
        expected = [entry.record() for entry in repository.external_context("module.a")]
        self.assertEqual(1, len(expected))
        for phase, agent, inputs in (
            ("context-solve", worker_profile("context-assessor"), ()),
            ("plan", worker_profile("planner"), ()),
            ("code-review", worker_profile("code-reviewer"), ()),
            (
                "implementation",
                worker_profile("programmer"),
                (
                    {
                        "type_id": "concorde-implementation-task",
                        "schema_version": 1,
                        "data": {"plan": "Plan", "tasks": []},
                    },
                ),
            ),
        ):
            with self.subTest(phase=phase):
                snapshot = resolve_context(
                    repository,
                    "module.a",
                    phase=phase,
                    task="Adapt",
                    agent=agent,
                    stage_inputs=inputs,
                ).value
                self.assertEqual(7, snapshot["schema_version"])
                self.assertEqual(expected, snapshot["external_references"])
        ask = resolve_context(
            repository, "module.a", phase="context-solve", task="Adapt"
        )
        self.fixture.write("reference/lib/diagram.png", "other binary")
        recheck_context(self.fixture.repository(), ask)
        self.fixture.write("reference/lib/api.md", "## connect(url, timeout)\n")
        with self.assertRaises(SpecError) as raised:
            recheck_context(self.fixture.repository(), ask)
        self.assertEqual("stale_context", raised.exception.code)

    @verifies("scenario.harness.external-references")
    def test_reading_modes_are_granted_the_declared_references_only(self):
        from tests.concorde.support.native_planning import OperationHost
        from concorde.harness.admission import run_operation
        from concorde.spec.typed_data import typed
        from tests.concorde.spec.support import ModelProcessDouble

        seen = {}

        def inspect(stage, snapshot, result, cwd):
            seen[stage] = {
                "copy": (cwd / "reference/lib/api.md").read_text()
                if (cwd / "reference/lib/api.md").exists()
                else None,
                "media": (cwd / "reference/lib/diagram.png").exists(),
                "undeclared": (cwd / "reference/other/api.md").exists(),
                "entries": [item["path"] for item in snapshot["external_references"]],
            }
            if stage == "plan":
                result["plan"] = "Use connect(url) as documented."

        double = ModelProcessDouble(inspect)
        host = OperationHost(
            self.fixture.root,
            PACKAGE,
            executor=double.executor,
            allow_primary_worktree=True,
        )
        result = run_operation(
            "concorde-plan",
            self.fixture.configuration,
            typed(
                "concorde-plan-request",
                {"target_id": "module.a", "task": "Adapt the value"},
            ),
            host_context=host,
        )
        self.assertEqual("succeeded", result["status"], result)
        self.assertEqual(
            {
                "copy": None,
                "media": False,
                "undeclared": False,
                "entries": ["reference/lib/"],
            },
            seen["context-solve"],
        )
        self.assertEqual(
            {
                "copy": "## connect(url)\n",
                "media": False,
                "undeclared": False,
                "entries": ["reference/lib/"],
            },
            seen["plan"],
        )
        policies = {item["phase"]: item for item in host.descriptions}
        self.assertIn("reference/lib", policies["plan"]["read_paths"])
        self.assertNotIn("reference/lib", policies["context-solve"]["read_paths"])
        self.assertTrue(
            all(
                "reference/other" not in path for path in policies["plan"]["read_paths"]
            )
        )

    @verifies("scenario.harness.external-references")
    def test_candidate_worktrees_receive_the_primary_reference_checkouts(self):
        import subprocess
        import tempfile
        from pathlib import Path

        from concorde.harness.change_worktree import (
            replicate_reference_checkouts,
            submodule_paths,
        )

        root = self.fixture.root
        subprocess.run(("git", "init", "-q"), cwd=root, check=True)
        (root / ".gitmodules").write_text(
            '[submodule "reference/lib"]\n\tpath = reference/lib\n\turl = https://example.invalid/lib.git\n'
        )
        (root / "reference/lib/.git").write_text("gitdir: elsewhere\n")
        self.assertEqual(("reference/lib",), submodule_paths(root))
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            replicate_reference_checkouts(root, destination)
            self.assertEqual(
                "## connect(url)\n", (destination / "reference/lib/api.md").read_text()
            )
            self.assertFalse((destination / "reference/lib/diagram.png").exists())
            self.assertFalse((destination / "reference/lib/.git").exists())
            self.assertFalse((destination / "reference/other").exists())


class SharedFileReaderTests(unittest.TestCase):
    """A and B both bind ``source/shared.py``; neither selects the other's documents."""

    def setUp(self):
        self.fixture = ModuleImplementationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    @verifies("scenario.harness.shared-file-readers")
    def test_a_programmer_also_reads_every_module_that_binds_its_files(self):
        from concorde.harness.context import context_documents

        def shared(value):
            return [
                source
                for source in value["spec_resolution"]["sources"]
                if any(reason["relation"] == "shares" for reason in source["reasons"])
            ]

        repository = self.fixture.repository()
        for phase in ("plan", "code-review", "implementation"):
            with self.subTest(phase=phase):
                snapshot = resolve_context(repository, "module.a", phase=phase)
                value = snapshot.value
                granted = "\n".join(
                    raw.decode()
                    for raw in context_documents(repository, value).values()
                )
                if phase != "implementation":
                    self.assertFalse(value["spec_resolution"]["shares"])
                    self.assertEqual([], shared(value))
                    self.assertNotIn("B_PRIVATE_SPEC", granted)
                    continue
                self.assertTrue(value["spec_resolution"]["shares"])
                self.assertEqual(
                    source_pairs(["specs/b/module.md", "specs/b/obligations.md"]),
                    [source["path"] for source in shared(value)],
                )
                self.assertEqual(
                    [
                        {
                            "relation": "shares",
                            "id": "module.b",
                            "files": ["source/shared.py"],
                        }
                    ],
                    shared(value)[0]["reasons"],
                )
                self.assertIn("B_PRIVATE_SPEC", granted)
                self.assertNotIn("B_PRIVATE_SPEC", snapshot.serialized)
                # Reading the sharer's documents widens no write set.
                self.assertFalse(
                    {source["path"] for source in shared(value)}
                    & set(repository.spec_scope("module.a"))
                )
        programmer = resolve_context(repository, "module.a", phase="implementation")
        planner = resolve_context(repository, "module.a", phase="plan")
        self.assertNotEqual(programmer.id, planner.id)
        entry_b = self.fixture.root / "specs/b/module.md"
        entry_b.write_text(entry_b.read_text() + "\nB reads nothing else.\n")
        recheck_context(self.fixture.repository(), planner)
        with self.assertRaises(SpecError) as raised:
            recheck_context(self.fixture.repository(), programmer)
        self.assertEqual("stale_context", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
