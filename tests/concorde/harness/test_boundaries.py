"""Behavioral regression gates replacing Profile 7 ambient/ancestor context contracts."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

from concorde.harness.host import OperationHost
from concorde.harness.admission import run_operation
from concorde.harness.context import resolve_context
from concorde.spec.boundaries import scope_roots
from concorde.spec.changes import apply_files, file_change
from concorde.spec.repository import SpecError, SpecRepository
from concorde.spec.schema import ContractError, admit
from concorde.spec.typed_data import TypedDataError, typed, validate_typed
from concorde.spec.verification import verifies
from tests.concorde.spec.support import (
    CONFIGURATION,
    PACKAGE,
    project,
    set_realization,
    sync_registry,
    update_document_declaration,
    update_module,
)


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.registry = project(self.root)
        self.task = {
            "target_id": "service.transfer",
            "task": "Implement the specified transfer",
        }

    def validation_rules(self):
        from concorde.spec.validation import validate_repository

        report = validate_repository(self.root, package_root=PACKAGE)
        return {f.rule_id for f in report.findings if f.severity == "error"}

    def call_operation(self, name, data=None, mode="execute"):
        self.host = OperationHost(
            self.root,
            PACKAGE,
            allow_primary_worktree=True,
            mode=mode,
        )
        return run_operation(
            name,
            CONFIGURATION,
            typed(name + "-request", data or self.task),
            host_context=self.host,
        )

    @verifies("scenario.harness.context-freeze")
    def test_shared_physical_markdown_is_one_hop_context_not_entity_expansion(self):
        update_module(
            self.root,
            "module.ledger",
            includes=[
                {
                    "kind": "document",
                    "target": "document.transfer.promises",
                    "reason": "the amount rules the balance store must accept",
                }
            ],
        )
        update_document_declaration(
            self.root, "specs/transfer/promises.md", owner="service.transfer"
        )
        repo = SpecRepository(self.root)
        service = resolve_context(repo, "service.transfer").value
        module = resolve_context(repo, "module.ledger").value
        self.assertEqual(
            ["specs/transfer/promises.md"],
            [
                item["path"]
                for item in service["spec_resolution"]["sources"]
                if item["path"].endswith("promises.md")
            ],
        )
        self.assertEqual(
            ["specs/transfer/promises.md", "specs/transfer/promises.md.json"],
            [
                item["path"]
                for item in module["spec_resolution"]["sources"]
                if item["owner"] != "module.ledger"
            ],
        )
        self.assertEqual(
            [
                "specs/ledger/module.md",
                "specs/ledger/module.md.json",
                "specs/ledger/obligations.md",
                "specs/ledger/obligations.md.json",
            ],
            [
                item["path"]
                for item in module["spec_resolution"]["sources"]
                if item["owner"] == "module.ledger"
            ],
        )
        self.assertNotIn("specs/transfer/module.md", json.dumps(module))

    def test_a_directory_is_bound_only_with_an_explicit_trailing_slash(self):
        set_realization(self.root, "realization.ledger.store", entries=["app"])
        self.assertIn("CHK.binds.exists", self.validation_rules())
        # The trailing slash binds every regular file below the directory, including a new one.
        set_realization(self.root, "realization.ledger.store", entries=["app/"])
        sync_registry(self.root)
        self.assertNotIn("CHK.binds.exists", self.validation_rules())
        repo = SpecRepository(self.root)
        ledger = repo.module("module.ledger")
        self.assertEqual(("app/",), repo.implementation_scope(ledger))
        self.assertEqual(("app",), scope_roots(repo.implementation_scope(ledger)))
        self.assertEqual(("app/ledger.py", "app/transfer.py"), repo.bound_files(ledger))
        realization = repo.realization_for_path(ledger, "app/transfer.py")
        assert realization is not None
        self.assertEqual("realization.ledger.store", realization.id)
        self.assertEqual(
            ("module.ledger", "service.transfer"),
            repo.impact(paths=["app/transfer.py"]),
        )

    def test_control_and_spec_paths_cannot_be_bound(self):
        for path in (
            ".concorde/config.json",
            ".concorde/",
            "generated/protocol/principles.md",
            "specs/ledger/module.md",
            "specs/",
        ):
            with self.subTest(path=path):
                set_realization(self.root, "realization.transfer.check", entries=[path])
                self.assertIn("CHK.binds.no-spec", self.validation_rules())

    def test_module_and_scenario_share_one_global_identity_namespace(self):
        from concorde.spec.validation import validate_repository

        path = self.root / "specs/transfer/obligations.md"
        path.write_text(
            path.read_text().replace("scenario.transfer.debit", "scenario.ledger.read")
        )
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("invalid", report.status)
        self.assertIn(
            "CHK.defines.once", {finding.rule_id for finding in report.findings}
        )

    @verifies("scenario.harness.context-freeze")
    def test_code_is_digest_only_and_only_in_implementation_snapshot(self):
        repo = SpecRepository(self.root)
        plain = resolve_context(repo, "service.transfer").value
        impl = resolve_context(repo, "service.transfer", phase="implementation").value
        self.assertEqual([], plain["implementation_artifacts"])
        self.assertTrue(impl["implementation_artifacts"])
        self.assertNotIn("def transfer", json.dumps(impl))

    @verifies("scenario.harness.context-invalid-input")
    def test_unsupported_phase_or_blank_task_yields_no_snapshot(self):
        repo = SpecRepository(self.root)
        snapshots = []
        for arguments, code in (
            ({"phase": "audit"}, "invalid_phase"),
            ({"phase": "route"}, "invalid_phase"),
            ({"task": ""}, "invalid_input"),
            ({"task": "  \n"}, "invalid_input"),
        ):
            with self.subTest(**arguments):
                invalid_input: dict[str, Any] = dict(arguments)
                with self.assertRaises(SpecError) as raised:
                    snapshots.append(
                        resolve_context(repo, "service.transfer", **invalid_input)
                    )
                self.assertEqual(code, raised.exception.code)
        # Nothing partial is returned, and the refusal precedes Module selection, so nothing was resolved.
        self.assertEqual([], snapshots)
        with self.assertRaises(SpecError) as raised:
            resolve_context(repo, "module.absent", phase="audit")
        self.assertEqual("invalid_phase", raised.exception.code)

    def test_unknown_stage_input_cannot_be_a_hidden_read_channel(self):
        with self.assertRaises(ValueError):
            resolve_context(
                SpecRepository(self.root),
                "service.transfer",
                stage_inputs=(
                    {
                        "type_id": "opaque",
                        "schema_version": 1,
                        "data": {"code": "secret"},
                    },
                ),
            )

    def test_protocol_tampering_invalidates_binding(self):
        from concorde.distribution.build import write_build

        package = self.root / "package"
        shutil.copytree(PACKAGE / "prompts", package / "prompts")
        shutil.copytree(PACKAGE / "agents", package / "agents")
        shutil.copytree(PACKAGE / "operations", package / "operations")
        shutil.copytree(PACKAGE / "protocol", package / "protocol")
        write_build(package)
        SpecRepository(self.root, package)
        # The project's accepted copy is what is admitted and granted; tampering with it is a mismatch.
        (self.root / ".concorde/protocol/kinds/module.md").write_text("changed")
        with self.assertRaises(SpecError) as raised:
            SpecRepository(self.root, package)
        self.assertEqual("protocol_mismatch", raised.exception.code)

    def test_configuration_cannot_replace_initialized_authority(self):
        other = typed(
            "concorde-operation-configuration",
            {"model": CONFIGURATION["data"]["model"], "thinking": "high"},
        )
        result = run_operation(
            "concorde-context-solve",
            other,
            typed("concorde-context-solve-request", self.task),
            host_context=OperationHost(self.root, PACKAGE),
        )
        self.assertEqual("configuration_mismatch", result["errors"][0]["code"])

    @verifies("scenario.harness.typed-reject")
    def test_wrong_version_and_extra_fields_are_rejected(self):
        for value in [
            dict(
                typed("concorde-context-solve-request", self.task), schema_version=True
            ),
            dict(typed("concorde-context-solve-request", self.task), schema_version=7),
            {
                "type_id": "concorde-context-solve-request",
                "schema_version": 1,
                "data": {**self.task, "read_paths": ["secret.py"]},
            },
        ]:
            with self.subTest(value=value), self.assertRaises(TypedDataError):
                validate_typed(value, "concorde-context-solve-request")

    def test_atomic_replacements_rollback_after_failed_verification(self):
        original = (self.root / "specs/transfer/module.md").read_bytes()
        changes = [
            file_change(self.root, "specs/transfer/module.md", "changed"),
            file_change(self.root, "new.md", "new"),
        ]

        def reject():
            raise ValueError("invalid target")

        with self.assertRaises(ValueError):
            apply_files(
                self.root,
                changes,
                {"specs/transfer/module.md", "new.md"},
                verify=reject,
            )
        self.assertEqual(
            original, (self.root / "specs/transfer/module.md").read_bytes()
        )
        self.assertFalse((self.root / "new.md").exists())

    def test_stale_file_proposal_never_overwrites_newer_content(self):
        change = file_change(self.root, "specs/transfer/module.md", "proposed")
        (self.root / "specs/transfer/module.md").write_text("user change")
        with self.assertRaises(ValueError):
            apply_files(self.root, [change], {"specs/transfer/module.md"})
        self.assertEqual(
            "user change", (self.root / "specs/transfer/module.md").read_text()
        )

    def test_unsupported_and_malformed_contract_schemas_fail_admission(self):
        for schema in [
            {"type": "object", "unevaluatedProperties": False},
            {"$ref": "https://example.invalid/schema"},
            {"minLength": True},
            {"enum": []},
            {"minimum": 3, "maximum": 1},
        ]:
            with self.subTest(schema=schema), self.assertRaises(ContractError):
                admit(schema)

    def downgrade_to_profile7(self):
        config = json.loads((self.root / ".concorde/config.json").read_text())
        config = {
            "profile_version": 7,
            "specification_root": "specs",
            "root_module_id": "module.old",
            "operation_configuration": config["operation_configuration"],
        }
        (self.root / ".concorde/config.json").write_text(json.dumps(config))

    def test_profile7_cannot_be_silently_used_by_new_agent_runtime(self):
        self.downgrade_to_profile7()
        result = self.call_operation("concorde-context-solve")
        self.assertEqual("blocked", result["status"])
