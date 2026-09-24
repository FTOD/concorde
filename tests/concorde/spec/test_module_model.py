"""Realizations, boundary sets and their use by the Harness, on a small Protocol 13 project."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from concorde.spec.boundaries import scope_roots
from concorde.spec.changes import confirm_pending_files
from concorde.spec.repository import SpecError, digest
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
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
    def test_only_profile_17_with_the_installed_protocol_binding_is_admitted(self):
        config = json.loads((self.root / ".concorde/config.json").read_text())
        for profile in (15, 16, 18):
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

    @verifies("scenario.spec.pending-materialized")
    def test_a_pending_entry_whose_file_exists_is_an_error(self):
        self.relist(
            {"realization.a.shared": (["source/shared.py"], ["source/shared.py"])}
        )
        report = validate_repository(self.root, package_root=PACKAGE)
        findings = [
            f for f in report.findings if f.rule_id == "CHK.binds.pending-subset"
        ]
        self.assertEqual(1, len(findings))
        self.assertEqual("error", findings[0].severity)
        self.assertIn("source/shared.py", findings[0].message)

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

    @verifies("scenario.spec.external-reference")
    def test_external_material_is_read_material_not_context_or_implementation(self):
        self.write("references/lib/README.md", "# lib 1.0\n\nAPI reference.\n")
        self.write("references/lib/api.md", "## connect(url)\n")
        self.write("references/lib/.hidden.md", "ignored\n")
        self.write("references/lib/logo.png", "binary")
        self.declare_reference()
        repository = self.repository()
        a = repository.module("module.a")
        self.assertEqual(("references/lib/",), repository.external_inclusions(a))
        self.assertEqual(
            ("references/lib",), scope_roots(repository.external_inclusions(a))
        )
        self.assertEqual(
            ("references/lib/README.md", "references/lib/api.md"),
            repository.external_files("references/lib/"),
        )
        external = repository.boundary_sets("module.a").external_context
        self.assertEqual(
            (
                (
                    "references/lib/",
                    ("references/lib/README.md", "references/lib/api.md"),
                ),
            ),
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
            [{"kind": "external", "path": "references/lib/"}],
            repository.spec_context("module.a").value["references"],
        )
        # A selected Module does not bring its own external material.
        self.assertEqual(
            (), repository.external_inclusions(repository.module("module.root"))
        )
        self.write("references/lib/logo.png", "other binary")
        self.assertEqual(records, self.repository().external_context(a))
        self.write("references/lib/api.md", "## connect(url, timeout)\n")
        self.assertNotEqual(records, self.repository().external_context(a))
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", report.status, errors(report))
        self.assertEqual((), repository.implemented_by("references/lib/api.md"))

    @verifies("scenario.spec.external-reference", "scenario.spec.reference-invalid")
    def test_external_material_cannot_overlap_documents_or_realizations_or_repeat(self):
        for entries, rule in (
            (("specs/b/module.md",), "CHK.external.no-overlap"),
            (("specs/",), "CHK.external.no-overlap"),
            (("source/shared.py",), "CHK.external.no-overlap"),
            (("source/",), "CHK.external.no-overlap"),
            (("references/lib/", "references/lib/"), "CHK.includes.unique"),
        ):
            with self.subTest(entries=entries):
                fixture = ModuleImplementationTests()
                fixture.setUp()
                try:
                    fixture.write("references/lib/api.md", "api\n")
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

        self.write("references/tracked/api.md", "api\n")
        subprocess.run(("git", "init", "-q"), cwd=self.root, check=True)
        subprocess.run(("git", "add", "-A"), cwd=self.root, check=True)
        self.write("references/untracked/api.md", "api\n")
        self.declare_reference(
            entries=(
                "references/tracked/",
                "references/missing/",
                "references/untracked/",
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
        self.assertTrue(any("references/missing/" in m for m in exists), exists)
        self.assertTrue(any("references/untracked/" in m for m in exists), exists)
        self.assertEqual(1, len(overlap), overlap)
        self.assertIn("source/shared.py", overlap[0])
        self.assertFalse(any("references/tracked/" in m for m in exists + overlap))


if __name__ == "__main__":
    unittest.main()
