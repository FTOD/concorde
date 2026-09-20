"""Spec Protocol 3.0: the reading entry, its inline architecture diagram and entity listings."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from concorde.harness.host import OperationHost
from concorde.harness.admission import run_operation
from concorde.harness.context import recheck_context, resolve_context
from concorde.spec.initialize import (
    apply_project_proposal,
    project_proposal,
)
from concorde.spec.repository import SpecError, SpecRepository, digest
from concorde.spec.typed_data import typed
from concorde.spec.validation import validate_repository
from concorde.spec.verification import verifies
from tests.concorde.spec.support import (
    CONFIGURATION,
    PACKAGE,
    DocumentSource,
    ModelProcessDouble,
    project,
    source_pairs,
    write_document,
)


def replace_entities(text, update):
    metadata = json.loads(text)
    metadata["entities"] = update(metadata["entities"])
    return json.dumps(metadata, indent=2) + "\n"


class ModuleArchitectureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = project(self.root)
        self.main = "specs/bank/module.md"

    def save(self):
        (self.root / ".concorde/specs.json").write_text(json.dumps(self.registry))

    def call(self, operation, data, callback=None):
        double = ModelProcessDouble(callback)
        return run_operation(
            operation,
            CONFIGURATION,
            typed(operation + "-request", data),
            host_context=OperationHost(
                self.root,
                PACKAGE,
                executor=double.executor,
                allow_primary_worktree=True,
            ),
        )

    @verifies("scenario.spec.select-module")
    def test_main_document_does_not_depend_on_order_or_replace_full_context(self):
        topic = "specs/bank/routing.md"
        write_document(
            self.root,
            topic,
            DocumentSource(
                "# Routing\n\nRead the registered banking responsibilities.\n",
                {
                    "schema_version": 2,
                    "document": {
                        "id": "document.bank.routing",
                        "owner": "scope.bank",
                        "role": "module",
                    },
                    "entities": [],
                    "dependencies": [],
                    "bindings": [],
                },
            ),
        )
        self.registry["targets"][0]["documents"].insert(0, topic)
        self.save()
        repository = SpecRepository(self.root)
        target = repository.select("scope.bank")
        self.assertEqual(self.main, target.primary_document)
        snapshot = resolve_context(repository, target.id).value
        self.assertEqual(
            source_pairs([topic, self.main, "specs/bank/obligations.md"]),
            [source["path"] for source in snapshot["spec_resolution"]["sources"]],
        )
        self.assertEqual(
            source_pairs([topic, self.main, "specs/bank/obligations.md"]),
            [d["path"] for d in snapshot["spec_resolution"]["sources"]],
        )
        self.assertEqual("success", validate_repository(self.root).status)

    def test_missing_duplicate_or_shared_module_entry_is_rejected(self):
        original = copy.deepcopy(self.registry)
        cases = [
            ["specs/bank/topic.md"],
            [self.main, "specs/another/module.md"],
        ]
        for members in cases:
            with self.subTest(members=members):
                self.registry = copy.deepcopy(original)
                self.registry["targets"][0]["documents"] = members
                self.save()
                with self.assertRaisesRegex(SpecError, "exactly one.*module.md"):
                    SpecRepository(self.root)
        self.registry = copy.deepcopy(original)
        self.registry["targets"][2]["documents"].append(self.main)
        self.save()
        with self.assertRaisesRegex(SpecError, "exactly one.*module.md"):
            SpecRepository(self.root)

    @verifies("scenario.spec.query-files", "scenario.spec.validate-structural-errors")
    def test_complete_context_ignores_visibility_and_architecture_heading_is_outside_fences(
        self,
    ):
        metadata = self.root / (self.main + ".json")
        metadata.write_bytes(metadata.read_bytes() + b"\n")
        self.assertIn(
            self.main,
            [
                source["path"]
                for source in resolve_context(
                    SpecRepository(self.root), "scope.bank"
                ).value["spec_resolution"]["sources"]
            ],
        )
        path = self.root / self.main
        body = path.read_text().replace("## Relationships", "## Vocabulary")
        for fence in ("```", "~~~~"):
            with self.subTest(fence=fence):
                path.write_text(
                    body + f"\n{fence}markdown\n### Relationships\n{fence}\n"
                )
                report = validate_repository(self.root)
                self.assertIn(
                    "CONCORDE-MODULE-001", {f.rule_id for f in report.findings}
                )

    @verifies("scenario.spec.validate-structural-errors")
    def test_the_reading_entry_requires_a_mermaid_flowchart_in_its_architecture_section(
        self,
    ):
        path = self.root / self.main
        original = path.read_text()
        start = original.index("```mermaid\n")
        end = original.index("\n```", start) + len("\n```\n")
        path.write_text(original[:start] + original[end:])
        report = validate_repository(self.root)
        self.assertEqual("invalid", report.status)
        self.assertIn("CONCORDE-MODULE-001", {f.rule_id for f in report.findings})
        self.assertTrue(
            any("Mermaid flowchart fence" in f.message for f in report.findings)
        )

    @verifies("scenario.spec.validate-architecture-mismatch")
    def test_diagram_nodes_must_equal_entity_titles_and_every_edge_must_be_labeled(
        self,
    ):
        path = self.root / self.main
        original = path.read_text()
        path.write_text(
            original.replace(
                "request -->|admitted by| transfer", "request --> transfer"
            )
        )
        report = validate_repository(self.root)
        self.assertEqual("invalid", report.status)
        self.assertIn("CONCORDE-ARCHITECTURE-002", {f.rule_id for f in report.findings})
        path.write_text(original.replace('audit["Audit"]', 'audit["Auditing"]'))
        report = validate_repository(self.root)
        self.assertEqual("invalid", report.status)
        self.assertIn("CONCORDE-ARCHITECTURE-001", {f.rule_id for f in report.findings})
        path.write_text(
            original.replace(
                '    request["Transfer request"]', '    request["Transfer request"'
            )
        )
        report = validate_repository(self.root)
        self.assertEqual("invalid", report.status)
        self.assertIn("CONCORDE-ARCHITECTURE-002", {f.rule_id for f in report.findings})

    @verifies("scenario.spec.validate-structural-errors")
    def test_an_entity_can_only_stand_for_a_child_or_used_module(self):
        path = self.root / (self.main + ".json")
        path.write_text(
            replace_entities(
                path.read_text(),
                lambda values: [
                    {**value, "target_id": "module.ledger"}
                    if value["id"] == "entity.bank.audit"
                    else value
                    for value in values
                ],
            )
        )
        report = validate_repository(self.root)
        self.assertEqual("invalid", report.status)
        self.assertIn("CONCORDE-DEFINITION-001", {f.rule_id for f in report.findings})
        self.assertTrue(
            any("unique non-self provider" in f.message for f in report.findings)
        )

    def test_reserved_mermaid_identifiers_are_rejected_before_publication(self):
        path = self.root / self.main
        source = (
            path.read_text()
            .replace('request["Transfer request"]', 'graph["Transfer request"]')
            .replace("request -->", "graph -->")
        )
        path.write_text(source)
        report = validate_repository(self.root)
        self.assertEqual("invalid", report.status)
        self.assertTrue(
            any(
                "reserved Mermaid keyword" in finding.message
                for finding in report.findings
            )
        )

    def test_inline_diagram_bytes_invalidate_an_existing_context(self):
        repository = SpecRepository(self.root)
        snapshot = resolve_context(repository, "scope.bank")
        path = self.root / self.main
        path.write_text(
            path.read_text().replace(
                "accTitle: Banking coordination", "accTitle: Banking settlement"
            )
        )
        with self.assertRaisesRegex(SpecError, "bytes changed"):
            recheck_context(repository, snapshot)

    def test_entity_file_listings_invalidate_an_existing_context(self):
        repository = SpecRepository(self.root)
        snapshot = resolve_context(repository, "service.transfer", phase="plan")
        # A registry-only file listing change leaves every document byte untouched.
        self.registry["targets"][2]["files"] = [
            "app/extra.py",
            "app/transfer.py",
            "checks/transfer_check.py",
        ]
        self.save()
        with self.assertRaisesRegex(SpecError, "changed"):
            recheck_context(repository, snapshot)

    @verifies("scenario.spec.rollback-on-failure")
    def test_direct_diagram_transaction_is_scoped_to_its_explicit_allowed_paths(self):
        from concorde.spec.changes import apply_files, file_change

        path = self.root / self.main
        after = path.read_text().replace(
            "accDescr: A transfer request reaches the transfer service",
            "accDescr: One transfer request reaches the transfer service",
        )
        self.assertNotEqual(path.read_text(), after)
        apply_files(
            self.root,
            [file_change(self.root, self.main, after)],
            {self.main},
            verify=lambda: SpecRepository(self.root).validate(),
        )
        self.assertEqual(after, path.read_text())
        foreign = "specs/audit/module.md"
        before = (self.root / foreign).read_bytes()
        with self.assertRaises(SpecError):
            apply_files(
                self.root, [file_change(self.root, foreign, after)], {self.main}
            )
        self.assertEqual(before, (self.root / foreign).read_bytes())

    @verifies(
        "scenario.spec.rollback-on-failure",
        "scenario.spec.validate-architecture-mismatch",
    )
    def test_an_invalid_inline_diagram_rolls_the_whole_document_back(self):
        from concorde.spec.changes import apply_files, file_change

        path = self.root / self.main
        original = path.read_bytes()
        broken = original.decode().replace(
            "transfer -->|reports accepted changes to| audit", "transfer --> audit"
        )
        self.assertNotEqual(original.decode(), broken)
        with self.assertRaises(SpecError):
            apply_files(
                self.root,
                [file_change(self.root, self.main, broken)],
                {self.main},
                verify=lambda: SpecRepository(self.root).validate(),
            )
        self.assertEqual(original, path.read_bytes())


class InitialModuleTests(unittest.TestCase):
    @verifies(
        "scenario.spec.propose-initialization",
        "scenario.spec.apply-initialization",
        "scenario.spec.rollback-on-failure",
        "scenario.concorde.adopt-initialize",
    )
    def test_initialization_is_honest_and_rolls_back_a_bad_reading_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            from concorde.distribution.project_defaults import install_project_defaults

            install_project_defaults(
                root, PACKAGE
            )  # the installer's outputs precede initialization
            proposal = project_proposal(root, PACKAGE, "New project", CONFIGURATION)
            source = next(
                f for f in proposal["files"] if f["path"] == "specs/project/module.md"
            )
            before = source["content"]
            source["content"] = before.replace("## Relationships", "## Drawing")
            with self.assertRaises(SpecError):
                apply_project_proposal(root, PACKAGE, proposal)
            self.assertFalse((root / ".concorde/config.json").exists())
            self.assertFalse((root / "specs/project/module.md").exists())
            source["content"] = before
            apply_project_proposal(root, PACKAGE, proposal)
            repository = SpecRepository(root, PACKAGE)
            target = repository.select("module.project")
            self.assertEqual("specs/project/module.md", target.primary_document)
            body = repository.document(target.primary_document).body
            self.assertIn("not yet been supplied", body)
            self.assertEqual((), target.files)
            self.assertEqual(
                {"Project Spec", "Developer", "Concorde Framework"},
                {entity.title for entity in repository.entities(target)},
            )
            self.assertEqual(
                "success", validate_repository(root, package_root=PACKAGE).status
            )

    @verifies("scenario.spec.reject-already-initialized")
    def test_an_already_configured_project_refuses_a_second_initialization(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            from concorde.distribution.project_defaults import install_project_defaults

            install_project_defaults(root, PACKAGE)
            apply_project_proposal(
                root,
                PACKAGE,
                project_proposal(root, PACKAGE, "New project", CONFIGURATION),
            )
            paths = [
                ".concorde/config.json",
                ".concorde/specs.json",
                "specs/project/module.md",
                "specs/project/module.md.json",
            ]
            before = {path: (root / path).read_bytes() for path in paths}
            with self.assertRaises(SpecError) as raised:
                project_proposal(root, PACKAGE, "Second project", CONFIGURATION)
            self.assertEqual("already_initialized", raised.exception.code)
            self.assertEqual(
                before, {path: (root / path).read_bytes() for path in paths}
            )

    @verifies("scenario.spec.reject-stale-or-invalid-proposal")
    def test_apply_rejects_an_invalid_out_of_bound_or_stale_proposal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            from concorde.distribution.project_defaults import install_project_defaults

            install_project_defaults(root, PACKAGE)
            original = project_proposal(root, PACKAGE, "New project", CONFIGURATION)

            def mutated(update):
                proposal = copy.deepcopy(original)
                update(proposal)
                return proposal

            def reconfigured(update):
                proposal = copy.deepcopy(original)
                config = json.loads(proposal["files"][0]["content"])
                proposal["files"][0]["content"] = (
                    json.dumps(update(config), indent=2) + "\n"
                )
                return proposal

            cases = [
                (
                    "foreign envelope",
                    "invalid_proposal",
                    mutated(
                        lambda p: p.update(type_id="concorde-topology-application")
                    ),
                ),
                (
                    "issuance token",
                    "invalid_proposal",
                    mutated(lambda p: p.update(issuance_token="accepted")),  # noqa: S106 - deliberately forged proposal field
                ),
                (
                    "registry omitted",
                    "invalid_proposal",
                    mutated(lambda p: p["files"].pop(1)),
                ),
                (
                    "registry rebound",
                    "invalid_proposal",
                    reconfigured(lambda c: {**c, "registry": ".concorde/other.json"}),
                ),
                (
                    "Protocol rebound",
                    "invalid_proposal",
                    reconfigured(
                        lambda c: {
                            **c,
                            "protocol": {
                                **c["protocol"],
                                "digest": digest(b"another Protocol"),
                            },
                        }
                    ),
                ),
                (
                    "replacement claimed",
                    "invalid_proposal",
                    mutated(lambda p: p.update(base_digest=digest(b"earlier"))),
                ),
                (
                    "overwrite claimed",
                    "invalid_proposal",
                    mutated(
                        lambda p: p["files"][2].update(before_digest=digest(b"earlier"))
                    ),
                ),
                (
                    "out of bound file",
                    "permission_denied",
                    mutated(
                        lambda p: p["files"].append(
                            {
                                "path": "specs/project/extra.md",
                                "before_digest": None,
                                "content": "# Extra\n",
                            }
                        )
                    ),
                ),
            ]
            for label, code, proposal in cases:
                with self.subTest(case=label):
                    with self.assertRaises(SpecError) as raised:
                        apply_project_proposal(root, PACKAGE, proposal)
                    self.assertEqual(code, raised.exception.code)
                    self.assertFalse((root / ".concorde/config.json").exists())
                    self.assertFalse((root / "specs/project").exists())
            # The proposal's preconditions changed: a destination the proposal expects to be absent exists.
            (root / "specs/project").mkdir(parents=True)
            (root / "specs/project/module.md").write_text("# Concurrent draft\n")
            with self.assertRaises(SpecError) as raised:
                apply_project_proposal(root, PACKAGE, original)
            self.assertEqual("stale_proposal", raised.exception.code)
            self.assertFalse((root / ".concorde/config.json").exists())
            self.assertFalse((root / ".concorde/specs.json").exists())
            self.assertEqual(
                "# Concurrent draft\n", (root / "specs/project/module.md").read_text()
            )


if __name__ == "__main__":
    unittest.main()
