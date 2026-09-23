"""Realizations, boundary sets and their use by the Harness, on a small Protocol 11 project."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from typing import cast
from unittest.mock import patch

from concorde.harness.context import recheck_context, resolve_context
from concorde.harness.invocation import Invocation
from concorde.harness.revisions import implementation_digest, target_revision
from concorde.spec.boundaries import scope_roots
from concorde.spec.changes import confirm_pending_files
from concorde.spec.repository import SpecError, digest
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from concorde.validation.validate import validate as validate_candidate
from tests.concorde.support.shared_file_project import (
    PACKAGE,
    SharedFileProject,
)
from tests.concorde.support.spec_project import (
    source_pairs,
)


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


class ModuleImplementationTests(SharedFileProject, unittest.TestCase):
    """Root contains A and B; A and B both bind ``source/shared.py``."""

    @verifies("scenario.spec.validate-success", "scenario.spec.admit-inventory")
    def test_the_fixture_is_a_valid_project(self):
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, errors(report))
        self.assertEqual("not_proven", report.result["semantic_completeness"])
        self.assertTrue(report.result["source_digest"].startswith("sha256:"))
        repository = self.repository()
        self.assertEqual(
            ["module.root", "module.a", "module.b"], list(repository.modules)
        )
        self.assertEqual("module.root", repository.module("module.a").parent)
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
        unfocused = repository.module("module.a")
        focused = repository.module("module.a", scenario="scenario.a.value")
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
            sorted(repository.spec_context("module.a").paths),
        )
        with self.assertRaises(SpecError) as raised:
            repository.module("module.a", scenario="scenario.b.value")
        self.assertEqual("invalid_focus", raised.exception.code)

    @verifies(
        "scenario.spec.reject-unsupported-profile",
        "scenario.spec.reject-configuration-profile",
    )
    def test_only_profile_16_with_the_installed_protocol_binding_is_admitted(self):
        config = json.loads((self.root / ".concorde/config.json").read_text())
        for profile in (14, 15, 17):
            with self.subTest(profile=profile):
                self.write(
                    ".concorde/config.json",
                    json.dumps({**config, "profile_version": profile}),
                )
                written = (self.root / ".concorde/config.json").read_bytes()
                with self.assertRaises(SpecError) as raised:
                    self.repository()
                self.assertEqual("unsupported_profile", raised.exception.code)
                # The configuration is refused as written, never reinterpreted or rewritten.
                self.assertEqual(
                    written, (self.root / ".concorde/config.json").read_bytes()
                )
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
        self.assertEqual("module.a", self.repository().module("module.a").id)

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
        self.assertEqual(("module.a",), repository.implemented_by("source/a.py"))
        self.assertEqual(
            ("module.a", "module.b"), repository.implemented_by("source/shared.py")
        )
        self.assertEqual(
            ("module.a", "module.b"), repository.impact(paths=["source/shared.py"])
        )
        self.assertEqual(
            {"module.b": ("source/shared.py",)}, repository.shared_files("module.a")
        )
        self.assertEqual(
            {"module.a": ("source/shared.py",)}, repository.shared_files("module.b")
        )
        self.assertEqual(
            ("source/a.py", "source/shared.py"),
            scope_roots(repository.implementation_scope("module.a")),
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
        target = repository.module("module.a")
        self.assertEqual(
            ("source/", "source/shared.py"), repository.implementation_scope(target)
        )
        self.assertEqual(
            ("source", "source/shared.py"),
            scope_roots(repository.implementation_scope(target)),
        )
        self.assertEqual(
            ("source/a.py", "source/nested/deep.py", "source/shared.py"),
            repository.bound_files(target),
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

    @verifies("scenario.spec.directory-entry", "scenario.spec.longest-entry")
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
        target = repository.module("module.a")
        self.assertEqual(
            "realization.a.shared",
            repository.realization_for_path(target, "source/nested/deep.py").id,
        )
        self.assertEqual(
            "realization.a.shared",
            repository.realization_for_path(target, "source/shared.py").id,
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
        # The programmer's own files may change during its call.
        recheck_context(repository, coding)
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
        self.write("source/nested/deep.py", "def deep():\n    return 1\n")
        self.relist(
            {
                "realization.a.adapter": (["source/"], ()),
                "realization.a.shared": (["source/shared.py"], ()),
            }
        )
        repository = self.repository()
        self.assertEqual(
            ("module.a", "module.b"), repository.implemented_by("source/shared.py")
        )
        self.assertEqual(
            ("module.a",), repository.implemented_by("source/nested/deep.py")
        )
        self.assertEqual(
            {"module.b": ("source/shared.py",)}, repository.shared_files("module.a")
        )
        self.assertEqual(
            {"module.a": ("source/shared.py",)}, repository.shared_files("module.b")
        )

    @verifies("scenario.spec.pending-entries", "scenario.spec.pending-materialized")
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
        target = repository.module("module.a")
        self.assertEqual(("source/generated/",), repository.missing_entries(target))
        self.assertEqual(
            ("source/a.py", "source/shared.py"), repository.bound_files(target)
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
            self.repository().bound_files(self.repository().module("module.a")),
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
        target = repository.module("module.a")
        self.assertIn(
            "source/new.py", scope_roots(repository.implementation_scope(target))
        )
        self.assertNotIn("source/new.py", repository.bound_files(target))
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

    @verifies("scenario.spec.pending-entries", "scenario.spec.missing-entry")
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
        before = implementation_digest(repository, repository.module("module.a"))
        self.write("source/added.py", "def added():\n    return 1\n")
        created = self.repository()
        with_new_file = implementation_digest(created, created.module("module.a"))
        self.assertNotEqual(before, with_new_file)
        self.relist(
            {
                "realization.a.adapter": (["source/a.py", "source/added.py"], ()),
                "realization.a.shared": (["source/shared.py"], ()),
            }
        )
        expanded = self.repository()
        self.assertNotEqual(
            with_new_file, implementation_digest(expanded, expanded.module("module.a"))
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
            unconfirmed_files(repository, repository.module("module.a")),
        )
        self.write("source/missing.py", "def missing():\n    return 1\n")
        (self.root / "source/generated").mkdir()
        current = self.repository()
        self.assertEqual([], unconfirmed_files(current, current.module("module.a")))

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

    def test_file_only_change_invalidates_readers_not_planner_context(self):
        repository = self.repository()
        planned = resolve_context(repository, "module.a", phase="plan")
        reviewed = resolve_context(repository, "module.a", phase="code-review")
        coding = resolve_context(repository, "module.a", phase="implementation")
        self.write("source/shared.py", "def value():\n    return 43\n")
        recheck_context(repository, planned)
        # The programmer's own file bytes are exempt; changing them is the purpose of its call.
        recheck_context(repository, coding)
        with self.assertRaisesRegex(SpecError, "implementation input"):
            recheck_context(repository, reviewed)

    def test_shared_change_invalidates_each_implementation_revision(self):
        before = self.repository()
        old = {
            key: implementation_digest(before, before.module(key))
            for key in ("module.a", "module.b")
        }
        module_revision = target_revision(before, before.module("module.a"))
        self.write("source/shared.py", "def value():\n    return 43\n")
        after = self.repository()
        for key in old:
            self.assertNotEqual(
                old[key], implementation_digest(after, after.module(key))
            )
        self.assertEqual(
            module_revision, target_revision(after, after.module("module.a"))
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
                target=repository.module("module.a"),
                host=SimpleNamespace(
                    lifecycle={}, package_root=PACKAGE, invocation_id="test-impact"
                ),
                work_directory=None,
                owns_change=lambda: False,
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
            target=repository.module("module.a"),
            host=SimpleNamespace(
                lifecycle={}, package_root=PACKAGE, invocation_id="mutating-check"
            ),
            work_directory=None,
            owns_change=lambda: False,
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
        run.target = run.repository.module("module.a")
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

    @verifies("scenario.spec.external-reference")
    def test_external_material_is_read_material_not_context_or_implementation(self):
        self.write("reference/lib/README.md", "# lib 1.0\n\nAPI reference.\n")
        self.write("reference/lib/api.md", "## connect(url)\n")
        self.write("reference/lib/.hidden.md", "ignored\n")
        self.write("reference/lib/logo.png", "binary")
        self.declare_reference()
        repository = self.repository()
        a = repository.module("module.a")
        self.assertEqual(("reference/lib/",), repository.external_inclusions(a))
        self.assertEqual(
            ("reference/lib",), scope_roots(repository.external_inclusions(a))
        )
        self.assertEqual(
            ("reference/lib/README.md", "reference/lib/api.md"),
            repository.external_files("reference/lib/"),
        )
        external = repository.boundary_sets("module.a").external_context
        self.assertEqual(
            (("reference/lib/", ("reference/lib/README.md", "reference/lib/api.md")),),
            tuple((entry.path, entry.files) for entry in external),
        )
        self.assertEqual(("source/a.py", "source/shared.py"), repository.bound_files(a))
        records = repository.external_context(a)
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
            (), repository.external_inclusions(repository.module("module.root"))
        )
        self.write("reference/lib/logo.png", "other binary")
        self.assertEqual(records, self.repository().external_context(a))
        self.write("reference/lib/api.md", "## connect(url, timeout)\n")
        self.assertNotEqual(records, self.repository().external_context(a))
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, errors(report))
        self.assertEqual((), repository.implemented_by("reference/lib/api.md"))

    @verifies("scenario.spec.external-reference")
    def test_missing_external_material_is_an_error(self):
        self.declare_reference(entries=("reference/lib/",))
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertIn("CHK.external.exists", rule_ids(report))
        repository = self.repository()
        self.assertEqual(
            ["reference/lib/"],
            [
                entry.path
                for entry in repository.external_context("module.a")
                if not entry.exists
            ],
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

    def snapshot(self):
        return {
            str(path.relative_to(self.root)): path.read_bytes()
            for path in sorted(self.root.rglob("*"))
            if path.is_file()
        }

    @verifies("scenario.spec.pending-confirm")
    def test_confirming_pending_entries_rewrites_only_the_affected_metadata(self):
        from concorde.spec import content_changes

        self.relist(
            {
                "realization.a.adapter": (
                    ["source/a.py", "source/new.py", "source/later.py"],
                    ["source/new.py", "source/later.py"],
                ),
                "realization.a.shared": (["source/shared.py"], ()),
            }
        )
        self.relist(
            {
                "realization.b.shared": (
                    ["source/shared.py", "source/b.py"],
                    ["source/b.py"],
                )
            },
            module_id="module.b",
        )
        self.write("source/new.py", "def added():\n    return 1\n")
        self.write("source/b.py", "def b():\n    return 2\n")
        before = self.snapshot()
        with patch.object(
            content_changes, "apply_files", wraps=content_changes.apply_files
        ) as transaction:
            confirmed, missing = confirm_pending_files(self.root, PACKAGE)
        self.assertEqual(1, transaction.call_count)
        self.assertEqual(
            ["specs/a/module.md.json", "specs/b/module.md.json"],
            sorted(item["path"] for item in transaction.call_args.args[1]),
        )
        self.assertEqual(
            [
                {
                    "module": "module.a",
                    "realization": "realization.a.adapter",
                    "path": "source/new.py",
                },
                {
                    "module": "module.b",
                    "realization": "realization.b.shared",
                    "path": "source/b.py",
                },
            ],
            confirmed,
        )
        self.assertEqual(["source/later.py"], missing)
        after = self.snapshot()
        self.assertEqual(
            ["specs/a/module.md.json", "specs/b/module.md.json"],
            sorted(path for path in after if after[path] != before.get(path)),
        )
        self.assertEqual(set(before), set(after))
        pending = {
            record["id"]: record["pending"]
            for module in ("module.a", "module.b")
            for record in self.metadata(module)["defines"]
            if record["type"] == "realization"
        }
        self.assertEqual(["source/later.py"], pending["realization.a.adapter"])
        self.assertEqual([], pending["realization.b.shared"])

    @verifies("scenario.spec.external-reference-invalid")
    def test_missing_untracked_or_overlapping_external_material_is_an_error(self):
        import subprocess

        self.write("reference/tracked/api.md", "api\n")
        subprocess.run(("git", "init", "-q"), cwd=self.root, check=True)
        subprocess.run(("git", "add", "-A"), cwd=self.root, check=True)
        self.write("reference/untracked/api.md", "api\n")
        self.declare_reference(
            entries=(
                "reference/tracked/",
                "reference/missing/",
                "reference/untracked/",
                "source/shared.py",
            )
        )
        report = validate_repository(self.root, package_root=PACKAGE)
        exists = [
            f.message for f in report.findings if f.rule_id == "CHK.external.exists"
        ]
        overlap = [
            f.message for f in report.findings if f.rule_id == "CHK.external.no-overlap"
        ]
        self.assertEqual(2, len(exists), exists)
        self.assertTrue(any("reference/missing/" in m for m in exists), exists)
        self.assertTrue(any("reference/untracked/" in m for m in exists), exists)
        self.assertEqual(1, len(overlap), overlap)
        self.assertIn("source/shared.py", overlap[0])
        self.assertFalse(any("reference/tracked/" in m for m in exists + overlap))


if __name__ == "__main__":
    unittest.main()
