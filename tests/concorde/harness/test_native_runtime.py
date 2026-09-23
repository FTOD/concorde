"""Compatibility admission is explicit even when native artifacts have no version."""

import json
import tempfile
import unittest
from pathlib import Path

from concorde.harness.native_runtime import FORMAT, admit_native_runtime
from concorde.spec.repository import SpecError, digest
from concorde.spec.verification import verifies


class NativeRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.package = self.root / "package"
        self.package.mkdir()
        self.package.joinpath("package.json").write_text(
            json.dumps({"name": "pi-subagents", "version": "0.69.0"})
        )
        self.package.joinpath("writer.ts").write_text("// pinned test producer\n")
        self.contract = self.root / "contract.json"
        self.expected = {
            "schema_version": 1,
            "package": "pi-subagents",
            "package_version": "0.69.0",
            "format": FORMAT,
            "artifact_version": None,
            "sources": {p.name: digest(p.read_bytes()) for p in self.package.iterdir()},
        }
        self.save()

    def save(self):
        self.contract.write_text(json.dumps(self.expected))

    @verifies("scenario.execution.workflow-coverage")
    def test_known_versionless_producer_is_explicit(self):
        admitted = admit_native_runtime(self.package, contract=self.contract)
        self.assertEqual(admitted.format, FORMAT)
        self.assertIsNone(admitted.artifact_version)
        self.assertEqual(admitted.source_digest, digest(self.expected["sources"]))

    @verifies("scenario.execution.workflow-coverage")
    def test_same_version_with_changed_serialization_is_not_admitted(self):
        self.package.joinpath("writer.ts").write_text("// different format\n")
        with self.assertRaises(SpecError):
            admit_native_runtime(self.package, contract=self.contract)

    @verifies("scenario.execution.workflow-coverage")
    def test_unknown_package_contract_has_no_fallback(self):
        self.expected["package_version"] = "0.70.0"
        self.save()
        with self.assertRaises(SpecError):
            admit_native_runtime(self.package, contract=self.contract)

    @verifies("scenario.execution.workflow-coverage")
    def test_absent_version_is_not_silently_called_schema_three(self):
        self.expected["artifact_version"] = 3
        self.save()
        with self.assertRaises(SpecError):
            admit_native_runtime(self.package, contract=self.contract)

    @verifies("scenario.execution.workflow-coverage")
    def test_missing_source_blocks_compatibility(self):
        self.package.joinpath("writer.ts").unlink()
        with self.assertRaises(SpecError):
            admit_native_runtime(self.package, contract=self.contract)
