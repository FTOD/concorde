"""Realizations, boundary sets and their use by the Harness, on a small Protocol 11 project."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import patch

from concorde.distribution.project_defaults import write_protocol_copy
from concorde.harness.context import recheck_context, resolve_context
from concorde.harness.invocation import Invocation
from concorde.harness.revisions import implementation_digest, target_revision
from concorde.spec.changes import confirm_pending_files
from concorde.spec.initialize import protocol_binding
from concorde.spec.repository import SpecError, SpecRepository, digest
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from concorde.validation.validate import validate as validate_candidate
from tests.concorde.spec.support import (
    MIRRORED,
    DocumentSource,
    module_document,
    source_pairs,
    write_document,
)

PACKAGE = Path(__file__).resolve().parents[3]


def rule_ids(report) -> set[str]:
    return {
        finding.rule_id for finding in report.findings if finding.severity == "error"
    }


def errors(report) -> list[str]:
    return [
        f"{f.rule_id}: {f.source}: {f.message}"
        for f in report.findings
        if f.severity == "error"
    ]


def realization(identity, title, meaning, entries, pending=()):
    return {
        "id": identity,
        "type": "realization",
        "title": title,
        "meaning": meaning,
        "entries": list(entries),
        "pending": list(pending),
    }


ROOT = module_document(
    "document.root",
    "module.root",
    "Root",
    "ROOT_MODULE_CONTRACT: the root composes its two submodules and owns no code.",
    "### scenario.root.value — The root reports a composed value\n\n"
    "- GIVEN both submodules answer\n- WHEN the root is asked for its value\n"
    "- THEN it reports the composed integer\n",
    ("The root delegates both answers to its children.", []),
    "The root contains A and B, which both answer with an integer.",
    "flowchart TB\n    accTitle: root composition\n"
    "    accDescr: The root contains A and B.\n"
    '    root["Root"]\n    a["A"]\n    b["B"]\n'
    "    root -->|contains| a\n    root -->|contains| b",
    contains=[
        {
            "target": "module.a",
            "explanation": "A adapts the shared value and returns an integer.",
        },
        {
            "target": "module.b",
            "explanation": "B reads the shared value and returns 42.",
        },
    ],
)
MODULE_A = module_document(
    "document.a",
    "module.a",
    "A",
    "A_MODULE_CONTRACT: A adapts the shared integer for its own consumers.",
    "### scenario.a.value — A adapts the shared value\n\n"
    "- GIVEN the shared value function\n- WHEN A adapts it\n- THEN it returns the same integer\n"
    "- AND the shared value is unchanged\n",
    (
        "The adapter reads the shared value function.",
        [
            realization(
                "realization.a.adapter",
                "Adapter",
                "Adapts the shared integer.",
                ["source/a.py"],
            ),
            realization(
                "realization.a.shared",
                "Shared value",
                "Answers with the shared integer.",
                ["source/shared.py"],
            ),
        ],
    ),
    "The adapter reads the shared value.",
    "flowchart TB\n    accTitle: A\n"
    "    accDescr: The adapter reads the shared value function.\n"
    '    adapter["Adapter"]\n    shared["Shared value"]\n    adapter -->|reads| shared',
    requirements="### req.a.pure — A never changes the shared value\n\n"
    "A SHALL NOT change the shared value.\n",
    relations=[
        {
            "type": "relates",
            "source": "realization.a.adapter",
            "verb": "reads",
            "target": "realization.a.shared",
        }
    ],
    extra_owned=("details.md",),
)
DETAILS_A = DocumentSource(
    "# Local details\n\nA_OWN_ADDITIONAL_CONTRACT: the adapted integer is never negative.\n",
    {
        "schema_version": 3,
        "document": {"id": "document.a.details", "owner": "module.a", "role": "module"},
        "defines": [],
        "relations": [],
    },
)
MODULE_B = module_document(
    "document.b",
    "module.b",
    "B",
    "B_PRIVATE_SPEC: B reads the shared integer and promises exactly 42.",
    "### scenario.b.value — B reports the shared value\n\n"
    "- GIVEN the shared value function\n- WHEN B is asked for its value\n- THEN it returns 42\n",
    (
        "B holds only the shared value function.",
        [
            realization(
                "realization.b.shared",
                "Shared value",
                "Answers with the shared integer.",
                ["source/shared.py"],
            )
        ],
    ),
    "B collaborates with no other Module.",
)


class ModuleImplementationTests(unittest.TestCase):
    """Root contains A and B; A and B both bind ``source/shared.py``."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.configuration = {
            "type_id": "concorde-operation-configuration",
            "schema_version": 2,
            "data": {"model": "openai-codex/gpt-6-astra", "thinking": "medium"},
        }
        self.write(
            ".concorde/config.json",
            json.dumps(
                {
                    "profile_version": 15,
                    "registry": ".concorde/specs.json",
                    "protocol": protocol_binding(PACKAGE),
                    "operation_configuration": self.configuration,
                    "checks": [],
                }
            ),
        )
        write_protocol_copy(self.root, PACKAGE)
        self.write(
            "source/shared.py", "def value():\n    return 42\n# PRIVATE_SOURCE_MARKER\n"
        )
        self.write("source/a.py", "def adapt(value):\n    return value\n")
        self.entries = {
            "module.root": "specs/root/module.md",
            "module.a": "specs/a/module.md",
            "module.b": "specs/b/module.md",
        }
        self.write("specs/root/module.md", ROOT)
        self.write("specs/a/module.md", MODULE_A)
        self.write("specs/a/details.md", DETAILS_A)
        self.write("specs/b/module.md", MODULE_B)
        self.registry = {"schema_version": 3, "modules": []}
        for module_id, entry in self.entries.items():
            block = json.loads((self.root / (entry + ".json")).read_text())["module"]
            self.registry["modules"].append(
                {"id": module_id, "title": block["title"], "entry": entry}
                | {name: block[name] for name in MIRRORED}
            )
        self.save_registry()

    def write(self, path, content):
        write_document(self.root, path, content)

    def save_registry(self):
        self.write(".concorde/specs.json", json.dumps(self.registry, indent=2))

    def metadata(self, module_id):
        return json.loads((self.root / (self.entries[module_id] + ".json")).read_text())

    def save_metadata(self, module_id, value):
        (self.root / (self.entries[module_id] + ".json")).write_text(
            json.dumps(value, indent=2) + "\n"
        )
        record = next(m for m in self.registry["modules"] if m["id"] == module_id)
        record.update({name: value["module"][name] for name in MIRRORED})
        self.save_registry()

    def update_module(self, module_id, **changes):
        value = self.metadata(module_id)
        value["module"].update(changes)
        self.save_metadata(module_id, value)

    def repository(self):
        return SpecRepository(self.root, PACKAGE)

    def relist(self, entries, module_id="module.a"):
        """Rewrite realization entries: ``{realization id: (entries, pending)}``."""
        value = self.metadata(module_id)
        for record in value["defines"]:
            if record["id"] in entries:
                files, pending = entries[record["id"]]
                record["entries"] = list(files)
                record["pending"] = list(pending)
        self.save_metadata(module_id, value)

    def configure_checks(self, checks):
        config = json.loads((self.root / ".concorde/config.json").read_text())
        config["checks"] = checks
        self.write(".concorde/config.json", json.dumps(config))

    def declare_reference(self, module="module.a", entries=("reference/lib/",)):
        """Declare vendored material as ``includes`` of kind ``external`` of ``module``."""
        includes = [
            item
            for item in self.metadata(module)["module"]["includes"]
            if item["kind"] != "external"
        ] + [
            {
                "kind": "external",
                "target": entry,
                "reason": "the library's API reference",
            }
            for entry in entries
        ]
        self.update_module(module, includes=includes)

    @verifies("scenario.spec.validate-success", "scenario.spec.admit-inventory")
    def test_the_fixture_is_a_valid_project(self):
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, errors(report))
        self.assertEqual("not_proven", report.result["semantic_completeness"])
        self.assertTrue(report.result["source_digest"].startswith("sha256:"))
        repository = self.repository()
        self.assertEqual(
            ["module.root", "module.a", "module.b"], list(repository.targets)
        )
        self.assertEqual("module.root", repository.select("module.a").parent)
        self.assertEqual(
            (
                {"target": "module.a", "meaning": "#contains-module-a"},
                {"target": "module.b", "meaning": "#contains-module-b"},
            ),
            repository.module_declaration("module.root").contains,
        )

    @verifies(
        "scenario.spec.select-module",
        "scenario.spec.select-scenario-focus",
        "scenario.spec.reject-foreign-focus",
    )
    def test_a_scenario_focus_narrows_attention_only_and_must_be_the_targets_own(self):
        repository = self.repository()
        unfocused = repository.select("module.a")
        focused = repository.select("module.a", focus_id="scenario.a.value")
        self.assertEqual(unfocused, focused)
        self.assertEqual(
            (
                ("specs/a/module.md", "specs/a/obligations.md", "specs/a/details.md"),
                ("source/a.py", "source/shared.py"),
                (),
            ),
            (focused.documents, focused.files, focused.checks),
        )
        self.assertEqual(
            repository.spec_context("module.a").value["sources"],
            repository.spec_context("scenario.a.value").value["sources"],
        )
        self.assertEqual(
            source_pairs(
                ["specs/a/module.md", "specs/a/details.md", "specs/a/obligations.md"]
            ),
            sorted(repository.spec_files("module.a")),
        )
        with self.assertRaises(SpecError) as raised:
            repository.select("module.a", focus_id="scenario.b.value")
        self.assertEqual("invalid_focus", raised.exception.code)

    @verifies("scenario.spec.reject-unsupported-profile")
    def test_only_profile_15_with_the_installed_protocol_binding_is_admitted(self):
        config = json.loads((self.root / ".concorde/config.json").read_text())
        for profile in (13, 14, 16):
            with self.subTest(profile=profile):
                self.write(
                    ".concorde/config.json",
                    json.dumps({**config, "profile_version": profile}),
                )
                with self.assertRaises(SpecError) as raised:
                    self.repository()
                self.assertEqual("unsupported_profile", raised.exception.code)
        self.write(
            ".concorde/config.json",
            json.dumps(
                {
                    **config,
                    "protocol": {**config["protocol"], "digest": digest(b"another")},
                }
            ),
        )
        with self.assertRaises(SpecError) as raised:
            self.repository()
        self.assertEqual("protocol_mismatch", raised.exception.code)
        self.write(".concorde/config.json", json.dumps(config))
        self.assertEqual("module.a", self.repository().select("module.a").id)

    def test_parent_context_contains_the_children_and_children_do_not_see_the_parent(
        self,
    ):
        repository = self.repository()
        root = {
            source["path"]
            for source in repository.spec_context("module.root").value["sources"]
        }
        self.assertIn("specs/a/details.md", root)
        self.assertIn("specs/b/module.md.json", root)
        child = {
            source["path"]
            for source in repository.spec_context("module.b").value["sources"]
        }
        self.assertNotIn("specs/root/module.md", child)

    def test_non_code_agents_receive_the_whole_module_and_only_file_names(self):
        from concorde.harness.context import context_documents

        for phase in ("plan", "tasks", "context-solve", "spec-review"):
            with self.subTest(phase=phase):
                snapshot = resolve_context(
                    self.repository(),
                    "module.a",
                    phase=phase,
                    focus_id="scenario.a.value",
                )
                granted = "\n".join(
                    raw.decode()
                    for raw in context_documents(
                        self.repository(), snapshot.value
                    ).values()
                )
                self.assertIn("A_MODULE_CONTRACT", granted)
                self.assertIn("A_OWN_ADDITIONAL_CONTRACT", granted)
                self.assertNotIn("B_PRIVATE_SPEC", granted)
                self.assertNotIn("PRIVATE_SOURCE_MARKER", granted)
                self.assertNotIn("A_MODULE_CONTRACT", snapshot.serialized)
                self.assertNotIn("PRIVATE_SOURCE_MARKER", snapshot.serialized)
                self.assertEqual(
                    [
                        ("source/a.py", "realization.a.adapter", False),
                        ("source/shared.py", "realization.a.shared", False),
                    ],
                    [
                        (item["path"], item["entity_id"], item["pending"])
                        for item in snapshot.value["implementation_files"]
                    ],
                )
                self.assertEqual([], snapshot.value["implementation_artifacts"])

    def test_only_code_phases_receive_the_exact_file_artifacts(self):
        for phase in ("implementation", "code-review"):
            with self.subTest(phase=phase):
                snapshot = resolve_context(self.repository(), "module.a", phase=phase)
                self.assertEqual(
                    {"source/shared.py", "source/a.py"},
                    {
                        item["path"]
                        for item in snapshot.value["implementation_artifacts"]
                    },
                )
                self.assertNotIn("B_PRIVATE_SPEC", snapshot.serialized)
                self.assertNotIn("PRIVATE_SOURCE_MARKER", snapshot.serialized)

    @verifies("scenario.spec.shared-file", "scenario.spec.impact-indexes")
    def test_a_shared_file_has_one_identity_and_every_binding_module(self):
        repository = self.repository()
        self.assertEqual(
            ("module.a", "module.b"), repository.file_users["source/shared.py"]
        )
        self.assertEqual(("module.a",), repository.file_users["source/a.py"])
        self.assertEqual(
            ("module.a", "module.b"), repository.implemented_by("source/shared.py")
        )
        self.assertEqual(
            ("module.a", "module.b"),
            tuple(t.id for t in repository.affected_modules(["source/shared.py"])),
        )
        self.assertEqual(
            ("source/a.py", "source/shared.py"),
            repository.implementation_paths(repository.select("module.a")),
        )

    @verifies("scenario.spec.directory-entry", "scenario.spec.write-sets")
    def test_a_directory_entry_binds_existing_files_and_skips_excluded_ones(self):
        for path in (
            "source/nested/deep.py",
            "source/__pycache__/cached.py",
            "source/build/out.py",
            "source/.hidden.py",
            "source/stale.pyc",
        ):
            self.write(path, "# excluded from every directory binding\n")
        self.relist(
            {
                "realization.a.adapter": (["source/"], ()),
                "realization.a.shared": (["source/shared.py"], ()),
            }
        )
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, errors(report))
        repository = self.repository()
        target = repository.select("module.a")
        self.assertEqual(
            ("source/", "source/shared.py"), repository.implementation_entries(target)
        )
        self.assertEqual(
            ("source", "source/shared.py"), repository.implementation_paths(target)
        )
        self.assertEqual(
            ("source/a.py", "source/nested/deep.py", "source/shared.py"),
            repository.implementation_files(target),
        )
        self.assertEqual(
            ("source/", "source/shared.py"), repository.implementation_scope("module.a")
        )
        self.assertEqual((), repository.missing_entries(target))
        self.assertEqual(
            "realization.a.adapter",
            repository.realization_for_path(target, "source/nested/deep.py").id,
        )
        self.assertEqual(
            "realization.a.shared",
            repository.realization_for_path(target, "source/shared.py").id,
        )
        self.assertIsNone(repository.realization_for_path(target, "elsewhere/other.py"))
        sets = repository.boundary_sets("module.a")
        self.assertTrue(sets.writable("source/brand/new.py"))
        self.assertFalse(sets.writable("source/__pycache__/cached.py"))
        self.assertTrue(sets.writable("specs/a/details.md.json"))
        self.assertFalse(sets.writable("specs/b/module.md"))

    @verifies("scenario.spec.directory-entry")
    def test_the_longest_entry_owns_a_nested_file(self):
        self.write("source/nested/deep.py", "def deep():\n    return 1\n")
        self.relist(
            {
                "realization.a.adapter": (["source/"], ()),
                "realization.a.shared": (["source/nested/", "source/shared.py"], ()),
            }
        )
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, errors(report))
        repository = self.repository()
        target = repository.select("module.a")
        self.assertEqual(
            "realization.a.shared",
            repository.realization_for_path(target, "source/nested/deep.py").id,
        )
        self.assertEqual(
            "realization.a.adapter",
            repository.realization_for_path(target, "source/a.py").id,
        )

    @verifies("scenario.spec.directory-entry")
    def test_a_file_created_under_a_bound_directory_needs_no_pending_declaration(self):
        self.relist(
            {
                "realization.a.adapter": (["source/"], ()),
                "realization.a.shared": (["source/shared.py"], ()),
            }
        )
        repository = self.repository()
        coding = resolve_context(repository, "module.a", phase="implementation")
        planned = resolve_context(repository, "module.a", phase="plan")
        self.write("source/added.py", "def added():\n    return 1\n")
        recheck_context(repository, coding, check_implementation=False)
        with self.assertRaisesRegex(SpecError, "implementation file names changed"):
            recheck_context(repository, planned)
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, errors(report))
        fresh = resolve_context(self.repository(), "module.a", phase="implementation")
        self.assertEqual(
            [
                ("source/", "realization.a.adapter", False, True),
                ("source/shared.py", "realization.a.shared", False, False),
            ],
            [
                (item["path"], item["entity_id"], item["pending"], item["directory"])
                for item in fresh.value["implementation_entries"]
            ],
        )
        self.assertEqual(
            [
                ("source/a.py", "realization.a.adapter"),
                ("source/added.py", "realization.a.adapter"),
                ("source/shared.py", "realization.a.shared"),
            ],
            [
                (item["path"], item["entity_id"])
                for item in fresh.value["implementation_files"]
            ],
        )

    @verifies("scenario.spec.shared-file")
    def test_a_directory_and_an_exact_entry_share_one_file_across_modules(self):
        from concorde.harness.revisions import implementation_users

        self.write("source/nested/deep.py", "def deep():\n    return 1\n")
        self.relist(
            {
                "realization.a.adapter": (["source/"], ()),
                "realization.a.shared": (["source/shared.py"], ()),
            }
        )
        repository = self.repository()
        self.assertEqual(
            ("module.a", "module.b"), repository.listing_users("source/shared.py")
        )
        self.assertEqual(
            ("module.a",), repository.listing_users("source/nested/deep.py")
        )
        for module in ("module.a", "module.b"):
            with self.subTest(module=module):
                selected = repository.select(module)
                self.assertEqual(
                    ("module.a", "module.b"),
                    tuple(t.id for t in repository.covering_modules(selected)),
                )
                self.assertEqual(
                    ("module.a", "module.b"),
                    tuple(t.id for t in implementation_users(repository, selected)),
                )

    @verifies("scenario.spec.pending-entries")
    def test_a_pending_directory_validates_until_delivery_confirms_it(self):
        self.relist(
            {
                "realization.a.adapter": (
                    ["source/a.py", "source/generated/"],
                    ["source/generated/"],
                ),
                "realization.a.shared": (["source/shared.py"], ()),
            }
        )
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, errors(report))
        repository = self.repository()
        target = repository.select("module.a")
        self.assertEqual(("source/generated/",), repository.missing_entries(target))
        self.assertEqual(
            ("source/a.py", "source/shared.py"), repository.implementation_files(target)
        )
        snapshot = resolve_context(repository, "module.a", phase="plan")
        self.assertEqual(
            [
                ("source/a.py", False, False),
                ("source/generated/", True, True),
                ("source/shared.py", False, False),
            ],
            [
                (item["path"], item["pending"], item["directory"])
                for item in snapshot.value["implementation_entries"]
            ],
        )
        # A pending directory declares intent; it never invents a file name for the planner.
        self.assertEqual(
            ["source/a.py", "source/shared.py"],
            [item["path"] for item in snapshot.value["implementation_files"]],
        )
        self.write("source/generated/emitted.py", "def emitted():\n    return 1\n")
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual({"CHK.binds.pending-subset"}, rule_ids(report))
        confirmed, still_pending = confirm_pending_files(self.root, PACKAGE)
        self.assertEqual(
            [
                {
                    "module": "module.a",
                    "realization": "realization.a.adapter",
                    "path": "source/generated/",
                }
            ],
            confirmed,
        )
        self.assertEqual([], still_pending)
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, errors(report))
        self.assertEqual(
            ("source/a.py", "source/generated/emitted.py", "source/shared.py"),
            self.repository().implementation_files(
                self.repository().select("module.a")
            ),
        )

    @verifies("scenario.spec.pending-entries")
    def test_pending_files_are_named_to_planners_until_confirmed(self):
        self.relist(
            {
                "realization.a.adapter": (
                    ["source/a.py", "source/new.py"],
                    ["source/new.py"],
                ),
                "realization.a.shared": (["source/shared.py"], ()),
            }
        )
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, errors(report))
        repository = self.repository()
        target = repository.select("module.a")
        self.assertIn("source/new.py", repository.implementation_paths(target))
        self.assertNotIn("source/new.py", repository.implementation_files(target))
        self.assertIn("source/new.py", repository.implementation_scope("module.a"))
        snapshot = resolve_context(repository, "module.a", phase="plan")
        self.assertEqual(
            [
                ("source/a.py", False),
                ("source/new.py", True),
                ("source/shared.py", False),
            ],
            [
                (item["path"], item["pending"])
                for item in snapshot.value["implementation_files"]
            ],
        )
        self.write("source/new.py", "def added():\n    return 1\n")
        confirmed, still_pending = confirm_pending_files(self.root, PACKAGE)
        self.assertEqual(
            [
                {
                    "module": "module.a",
                    "realization": "realization.a.adapter",
                    "path": "source/new.py",
                }
            ],
            confirmed,
        )
        self.assertEqual([], still_pending)
        self.assertEqual(
            [],
            next(
                item
                for item in self.metadata("module.a")["defines"]
                if item["id"] == "realization.a.adapter"
            )["pending"],
        )
        self.assertEqual(
            "success", validate_repository(self.root, package_root=PACKAGE).status
        )

    @verifies("scenario.spec.pending-entries")
    def test_missing_entries_that_are_not_pending_are_errors(self):
        self.relist(
            {
                "realization.a.adapter": (
                    ["source/a.py", "source/new.py", "source/generated/"],
                    (),
                ),
                "realization.a.shared": (["source/shared.py"], ["source/other.py"]),
            }
        )
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual(
            {"CHK.binds.exists", "CHK.binds.pending-subset"}, rule_ids(report)
        )
        self.assertEqual(
            2, sum(1 for f in report.findings if f.rule_id == "CHK.binds.exists")
        )
        confirmed, still_pending = confirm_pending_files(self.root, PACKAGE)
        self.assertEqual([], confirmed)

    def test_the_implementation_digest_covers_entries_and_the_files_they_bind(self):
        self.relist(
            {
                "realization.a.adapter": (["source/"], ()),
                "realization.a.shared": (["source/shared.py"], ()),
            }
        )
        repository = self.repository()
        before = implementation_digest(repository, repository.select("module.a"))
        self.write("source/added.py", "def added():\n    return 1\n")
        created = self.repository()
        with_new_file = implementation_digest(created, created.select("module.a"))
        self.assertNotEqual(before, with_new_file)
        self.relist(
            {
                "realization.a.adapter": (["source/a.py", "source/added.py"], ()),
                "realization.a.shared": (["source/shared.py"], ()),
            }
        )
        expanded = self.repository()
        self.assertNotEqual(
            with_new_file, implementation_digest(expanded, expanded.select("module.a"))
        )

    def test_unconfirmed_entries_report_only_missing_declarations(self):
        from concorde.harness.revisions import unconfirmed_files

        self.relist(
            {
                "realization.a.adapter": (
                    ["source/", "source/generated/"],
                    ["source/generated/"],
                ),
                "realization.a.shared": (["source/missing.py", "source/shared.py"], ()),
            }
        )
        repository = self.repository()
        self.assertEqual(
            ["source/missing.py"],
            unconfirmed_files(repository, repository.select("module.a")),
        )
        self.write("source/missing.py", "def missing():\n    return 1\n")
        (self.root / "source/generated").mkdir()
        current = self.repository()
        self.assertEqual([], unconfirmed_files(current, current.select("module.a")))

    @verifies("scenario.spec.validate-structural-errors")
    def test_binding_rules_are_reported_as_findings(self):
        cases = (
            (
                {
                    "realization.a.adapter": (["source/a.py"], ()),
                    "realization.a.shared": (["source/a.py"], ()),
                },
                "CHK.binds.disjoint",
            ),
            (
                {
                    "realization.a.adapter": (["source"], ()),
                    "realization.a.shared": (["source/shared.py"], ()),
                },
                "CHK.binds.exists",
            ),
            (
                {
                    "realization.a.adapter": (["source/a.py/"], ()),
                    "realization.a.shared": (["source/shared.py"], ()),
                },
                "CHK.binds.exists",
            ),
            (
                {
                    "realization.a.adapter": (["specs/b/module.md"], ()),
                    "realization.a.shared": (["source/shared.py"], ()),
                },
                "CHK.binds.no-spec",
            ),
            (
                {
                    "realization.a.adapter": (["specs/"], ()),
                    "realization.a.shared": (["source/shared.py"], ()),
                },
                "CHK.binds.no-spec",
            ),
            (
                {
                    "realization.a.adapter": ([".concorde/config.json"], ()),
                    "realization.a.shared": (["source/shared.py"], ()),
                },
                "CHK.binds.no-spec",
            ),
        )
        for entries, rule in cases:
            with self.subTest(rule=rule, entries=entries):
                fixture = ModuleImplementationTests()
                fixture.setUp()
                try:
                    fixture.relist(entries)
                    report = validate_repository(fixture.root, package_root=PACKAGE)
                    self.assertIn(rule, rule_ids(report), errors(report))
                finally:
                    fixture.doCleanups()

    @verifies("scenario.spec.composition-checks")
    def test_a_composition_cycle_stops_loading_and_is_a_validation_finding(self):
        self.update_module(
            "module.a", contains=[{"target": "module.root", "meaning": "#uses-nothing"}]
        )
        with self.assertRaisesRegex(SpecError, "CHK.contains"):
            self.repository()
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertIn("CHK.contains.acyclic", rule_ids(report))

    def test_file_only_change_invalidates_writers_not_planner_context(self):
        repository = self.repository()
        planned = resolve_context(repository, "module.a", phase="plan")
        coding = resolve_context(repository, "module.a", phase="implementation")
        self.write("source/shared.py", "def value():\n    return 43\n")
        recheck_context(repository, planned)
        with self.assertRaisesRegex(SpecError, "implementation input"):
            recheck_context(repository, coding)

    def test_shared_change_invalidates_each_implementation_revision(self):
        before = self.repository()
        old = {
            key: implementation_digest(before, before.select(key))
            for key in ("module.a", "module.b")
        }
        module_revision = target_revision(before, before.select("module.a"))
        self.write("source/shared.py", "def value():\n    return 43\n")
        after = self.repository()
        for key in old:
            self.assertNotEqual(
                old[key], implementation_digest(after, after.select(key))
            )
        self.assertEqual(
            module_revision, target_revision(after, after.select("module.a"))
        )

    def test_validation_runs_both_consumers_checks_and_surfaces_peer_failure(self):
        self.configure_checks(
            [
                {
                    "id": "check." + module,
                    "module": module,
                    "argv": [
                        "{python}",
                        "-c",
                        "from source.shared import value; assert "
                        + ("value() >= 0" if module == "module.a" else "value() == 42"),
                    ],
                    "timeout_seconds": 10,
                }
                for module in ("module.a", "module.b")
            ]
        )

        def validate():
            repository = self.repository()
            run = SimpleNamespace(
                repository=repository,
                target=repository.select("module.a"),
                host=SimpleNamespace(
                    coordinated=True, package_root=PACKAGE, invocation_id="test-impact"
                ),
                work_directory=None,
                completed=[],
                response=lambda outcome="completed", answer="", **kwargs: {
                    "outcome": outcome,
                    **kwargs,
                },
            )
            return validate_candidate(cast(Invocation, run))

        result = validate()
        self.assertEqual("completed", result["outcome"])
        self.assertEqual(
            {"module.a", "module.b"}, {item["target_id"] for item in result["checks"]}
        )
        self.write("source/shared.py", "def value():\n    return 43\n")
        result = validate()
        self.assertEqual("failed", result["outcome"])
        self.assertEqual(
            {"module.b"},
            {
                item["target_id"]
                for item in result["checks"]
                if item["status"] == "failed"
            },
        )

    def test_check_cannot_change_a_using_module_contract_and_claim_fresh_evidence(self):
        self.configure_checks(
            [
                {
                    "id": "check.mutates-peer",
                    "module": "module.a",
                    "argv": [
                        "{python}",
                        "-c",
                        "from pathlib import Path; p=Path('specs/b/module.md'); p.write_text(p.read_text()+'\\nChanged peer promise.')",
                    ],
                    "timeout_seconds": 10,
                }
            ]
        )
        repository = self.repository()
        run = SimpleNamespace(
            repository=repository,
            target=repository.select("module.a"),
            host=SimpleNamespace(
                coordinated=True, package_root=PACKAGE, invocation_id="mutating-check"
            ),
            work_directory=None,
            completed=[],
            response=lambda outcome="completed", answer="", **kwargs: {
                "outcome": outcome,
                **kwargs,
            },
        )
        peer = self.root / "specs/b/module.md"
        original = peer.read_bytes()
        result = validate_candidate(cast(Invocation, run))
        self.assertEqual("failed", result["outcome"])
        self.assertEqual("failed", result["checks"][0]["status"])
        self.assertEqual(original, peer.read_bytes())
        self.configure_checks(
            [
                {
                    "id": "check.mutates-peer",
                    "module": "module.a",
                    "argv": ["{python}", "-c", "print('read-only check')"],
                    "timeout_seconds": 10,
                }
            ]
        )
        run.repository = self.repository()
        run.target = run.repository.select("module.a")
        from concorde.harness.check_executor import execute_check

        def external_change(*args, **kwargs):
            result = execute_check(*args, **kwargs)
            peer.write_bytes(original + b"\nChanged by a concurrent host writer.\n")
            return result

        with (
            patch("concorde.harness.checks.execute_check", external_change),
            self.assertRaisesRegex(SpecError, "using Module"),
        ):
            validate_candidate(cast(Invocation, run))

    @verifies("scenario.spec.shared-file")
    def test_shared_code_review_preserves_separate_module_contexts_and_peer_findings(
        self,
    ):
        from concorde.review.review import review_scope
        from tests.concorde.spec.support import ModelProcessDouble
        from tests.concorde.support.native_planning import OperationHost

        self.write("source/shared.py", "def value():\n    return 43\n")
        seen = []

        def inspect(stage, snapshot, result, cwd):
            if stage != "code-review":
                return
            seen.append(snapshot["target_id"])
            text = json.dumps(snapshot)
            self.assertNotIn("PRIVATE_SOURCE_MARKER", text)
            if snapshot["target_id"] == "module.b":
                self.assertIn("return 43", (cwd / "source/shared.py").read_text())
                result.update(
                    status="findings",
                    issues=[
                        {
                            "id": "finding.b.value",
                            "severity": "blocking",
                            "target_id": "module.b",
                            "document": "specs/b/module.md",
                            "contract": "value() returns 42",
                            "location": {"path": "source/shared.py", "line": 2},
                            "problem": "The shared implementation returns 43.",
                            "affected_task": snapshot["task"],
                        }
                    ],
                )

        double = ModelProcessDouble(inspect)
        host = OperationHost(
            self.root,
            PACKAGE,
            executor=double.executor,
            allow_primary_worktree=True,
            invocation_id="shared-consumer-review",
        )
        run = Invocation(
            "concorde-code-review",
            self.configuration,
            {"target_id": "module.a", "task": "Review the shared value change"},
            host,
        )
        result = review_scope(run, "code")["data"]
        self.assertEqual(["module.a", "module.b"], seen)
        self.assertEqual("conflicting", result["outcome"])

    @verifies("scenario.spec.shared-file")
    def test_code_review_peers_are_only_the_binding_modules_of_changed_files(self):
        import subprocess

        from concorde.harness.change_worktree import ensure_change
        from concorde.review.review import code_review_peers, review_scope
        from tests.concorde.spec.support import ModelProcessDouble
        from tests.concorde.support.native_planning import OperationHost

        for args in [
            ("init", "-q"),
            ("add", "--", "source", "specs"),
            (
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-q",
                "-m",
                "base",
            ),
        ]:
            subprocess.run(
                ("git", *args), cwd=self.root, capture_output=True, check=True
            )
        task = {"target_id": "module.a", "task": "Adapt the private value"}
        ensure_change(self.root, task=task, allow_primary=True)
        seen = []
        double = ModelProcessDouble(
            lambda stage, snapshot, result, cwd: (
                seen.append(snapshot["target_id"]) if stage == "code-review" else None
            )
        )

        def scope():
            host = OperationHost(
                self.root,
                PACKAGE,
                executor=double.executor,
                allow_primary_worktree=True,
            )
            run = Invocation("concorde-code-review", self.configuration, task, host)
            return run, review_scope(run, "code")["data"]

        self.write("source/a.py", "def adapt(value):\n    return value + 1\n")
        run, result = scope()
        self.assertEqual([], [target.id for target in code_review_peers(run)])
        self.assertEqual(["module.a"], seen)
        self.assertEqual("completed", result["outcome"])
        self.write("source/shared.py", "def value():\n    return 43\n")
        seen.clear()
        run, result = scope()
        self.assertEqual(["module.b"], [target.id for target in code_review_peers(run)])
        self.assertEqual(["module.a", "module.b"], seen)

    @verifies("scenario.spec.external-reference")
    def test_external_material_is_read_material_not_context_or_implementation(self):
        self.write("reference/lib/README.md", "# lib 1.0\n\nAPI reference.\n")
        self.write("reference/lib/api.md", "## connect(url)\n")
        self.write("reference/lib/.hidden.md", "ignored\n")
        self.write("reference/lib/logo.png", "binary")
        self.declare_reference()
        repository = self.repository()
        a = repository.select("module.a")
        self.assertEqual(("reference/lib/",), repository.external_references(a))
        self.assertEqual(("reference/lib",), repository.external_reference_paths(a))
        self.assertEqual(
            ("reference/lib/README.md", "reference/lib/api.md"),
            repository.external_reference_files("reference/lib/"),
        )
        external = repository.boundary_sets("module.a").external_context
        self.assertEqual(
            (("reference/lib/", ("reference/lib/README.md", "reference/lib/api.md")),),
            tuple((entry.path, entry.files) for entry in external),
        )
        self.assertEqual(
            ("source/a.py", "source/shared.py"), repository.implementation_files(a)
        )
        records = repository.external_reference_records(a)
        self.assertEqual(
            source_pairs(
                ["specs/a/details.md", "specs/a/module.md", "specs/a/obligations.md"]
            ),
            [
                source["path"]
                for source in repository.spec_context("module.a").value["sources"]
            ],
        )
        self.assertEqual(
            [{"kind": "external", "path": "reference/lib/"}],
            repository.spec_context("module.a").value["references"],
        )
        # A selected Module does not bring its own external material.
        self.assertEqual(
            (), repository.external_references(repository.select("module.root"))
        )
        self.write("reference/lib/logo.png", "other binary")
        self.assertEqual(records, self.repository().external_reference_records(a))
        self.write("reference/lib/api.md", "## connect(url, timeout)\n")
        self.assertNotEqual(records, self.repository().external_reference_records(a))
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, errors(report))
        self.assertEqual((), repository.listing_users("reference/lib/api.md"))

    @verifies("scenario.spec.external-reference")
    def test_missing_external_material_is_an_error(self):
        self.declare_reference(entries=("reference/lib/",))
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertIn("CHK.external.exists", rule_ids(report))
        repository = self.repository()
        self.assertEqual(
            ("reference/lib/",),
            repository.missing_external_references(repository.select("module.a")),
        )
        with self.assertRaises(SpecError) as raised:
            resolve_context(repository, "module.a", phase="plan", task="Adapt")
        self.assertEqual("invalid_reference", raised.exception.code)

    @verifies("scenario.spec.external-reference", "scenario.spec.reference-invalid")
    def test_external_material_cannot_overlap_documents_or_realizations_or_repeat(self):
        for entries, rule in (
            (("specs/b/module.md",), "CHK.external.no-overlap"),
            (("specs/",), "CHK.external.no-overlap"),
            (("source/shared.py",), "CHK.external.no-overlap"),
            (("source/",), "CHK.external.no-overlap"),
            (("reference/lib/", "reference/lib/"), "CHK.includes.unique"),
        ):
            with self.subTest(entries=entries):
                fixture = ModuleImplementationTests()
                fixture.setUp()
                try:
                    fixture.write("reference/lib/api.md", "api\n")
                    fixture.declare_reference(entries=entries)
                    report = validate_repository(fixture.root, package_root=PACKAGE)
                    self.assertIn(rule, rule_ids(report), errors(report))
                finally:
                    fixture.doCleanups()

    def test_code_writer_cannot_author_spec_documents(self):
        from concorde.harness.admission import run_operation
        from concorde.spec.typed_data import typed
        from tests.concorde.spec.support import ModelProcessDouble, project
        from tests.concorde.support.native_planning import OperationHost

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project(root)

            def author(stage, snapshot, data, cwd):
                if stage == "implementation":
                    data["documents"] = [
                        {"path": "specs/transfer/module.md", "content": "# Replaced\n"}
                    ]

            double = ModelProcessDouble(author)
            host = OperationHost(
                root, PACKAGE, executor=double.executor, allow_primary_worktree=True
            )
            task = {"target_id": "service.transfer", "task": "Implement transfer"}
            for operation in ("concorde-plan", "concorde-tasks"):
                admitted = run_operation(
                    operation,
                    self.configuration,
                    typed(operation + "-request", task),
                    host_context=host,
                )
                self.assertEqual("succeeded", admitted["status"], admitted)
            result = run_operation(
                "concorde-implement",
                self.configuration,
                typed("concorde-implement-request", task),
                host_context=host,
            )
            self.assertEqual("blocked", result["status"], result)
            self.assertEqual("permission_denied", result["errors"][0]["code"])
            self.assertIn(
                "# Transfers", (root / "specs/transfer/module.md").read_text()
            )

    @verifies("scenario.spec.directory-entry")
    def test_a_code_writer_may_create_a_file_below_a_bound_directory(self):
        from concorde.harness.admission import run_operation
        from concorde.spec.typed_data import typed
        from tests.concorde.spec.support import (
            ModelProcessDouble,
            project,
            set_realization,
            sync_registry,
        )
        from tests.concorde.support.native_planning import OperationHost

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project(root)
            # The transfer calculation binds the whole app/ directory, shared with the ledger Module.
            set_realization(root, "realization.transfer.calculation", entries=["app/"])
            sync_registry(root)
            report = validate_repository(root, package_root=PACKAGE)
            self.assertEqual("success", report.status, errors(report))
            written = []

            def implement(stage, snapshot, result, cwd):
                if stage != "implementation":
                    return
                written.append(
                    [item["path"] for item in snapshot["implementation_files"]]
                )
                (cwd / "app/helper.py").write_text(
                    "HELPER_CREATED_BELOW_A_BOUND_DIRECTORY = True\n"
                )

            double = ModelProcessDouble(implement)
            host = OperationHost(
                root, PACKAGE, executor=double.executor, allow_primary_worktree=True
            )
            task = {
                "target_id": "service.transfer",
                "task": "Implement the pure transfer contract",
            }
            for operation in ("concorde-plan", "concorde-tasks"):
                admitted = run_operation(
                    operation,
                    self.configuration,
                    typed(operation + "-request", task),
                    host_context=host,
                )
                self.assertEqual("succeeded", admitted["status"], admitted)
            result = run_operation(
                "concorde-implement",
                self.configuration,
                typed("concorde-implement-request", task),
                host_context=host,
            )
            self.assertEqual("succeeded", result["status"], result)
            self.assertEqual(
                [["app/ledger.py", "app/transfer.py", "checks/transfer_check.py"]],
                written,
            )
            repository = SpecRepository(root, PACKAGE)
            target = repository.select("service.transfer")
            self.assertIn("app/helper.py", repository.implementation_files(target))
            self.assertEqual(
                "realization.transfer.calculation",
                repository.realization_for_path(target, "app/helper.py").id,
            )
            self.assertEqual(
                "success", validate_repository(root, package_root=PACKAGE).status
            )


if __name__ == "__main__":
    unittest.main()
