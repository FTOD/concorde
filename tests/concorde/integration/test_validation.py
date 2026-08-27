import shutil
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.concorde.support.paths import REPOSITORY_ROOT, RUNTIME_ROOT, VALID_PROJECT

sys.path.insert(0, str(RUNTIME_ROOT))

from concorde.diagnostics import canonical_json, operation_envelope  # noqa: E402
from concorde.validate import validate_project  # noqa: E402


class ValidationIntegrationTests(unittest.TestCase):
    def test_five_surfaces_do_not_expand_runtime_dispatch_or_leave_current_inventory_stale(self):
        manifest = (REPOSITORY_ROOT / "extensions/concorde/extension.yml").read_text(encoding="utf-8")
        self.assertEqual(manifest.count('- name: "speckit.concorde.'), 5)
        self.assertEqual(manifest.count('runtime: "'), 4)
        cli = (REPOSITORY_ROOT / "extensions/concorde/runtime/concorde/cli.py").read_text(encoding="utf-8")
        self.assertNotIn('add_parser("ask")', cli)

        current_authorities = (
            REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/spec.md",
            REPOSITORY_ROOT / "specs/concorde/features/001-concorde-workflow/contracts/agent-commands.md",
            REPOSITORY_ROOT / "specs/concorde/features/003-install-concorde-speckit/spec.md",
            REPOSITORY_ROOT / "specs/concorde/features/003-install-concorde-speckit/contracts/installed-command-surfaces.md",
            REPOSITORY_ROOT / "specs/concorde/contracts/spec-kit-installation/contract.md",
            REPOSITORY_ROOT / "README.md",
            REPOSITORY_ROOT / "docs/commands.md",
        )
        for source in current_authorities:
            content = source.read_text(encoding="utf-8")
            with self.subTest(source=source.relative_to(REPOSITORY_ROOT)):
                self.assertNotIn("six Concorde-specific commands", content)
                self.assertIn("ask", content)

    def test_three_runs_are_byte_equivalent_and_non_mutating(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            outputs = [canonical_json(operation_envelope(validate_project(root))) for _ in range(3)]
            after = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(outputs[1], outputs[2])
            self.assertEqual(before, after)
            self.assertIn('"source_digest":"sha256:', outputs[0])

    def test_bounded_target_and_unknown_evidence_are_supported(self):
        result = validate_project(VALID_PROJECT, "module.example.api")
        self.assertEqual(result.status, "success")
        self.assertGreater(len(result.artifacts), 0)
        self.assertFalse(any(item.severity == "error" for item in result.findings))

    def test_layout_evidence_and_freshness_defects_are_distinct(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            shutil.copytree(VALID_PROJECT, root)
            feature = root / "specs/example/features/001-deliver/spec.md"
            (feature.parent / "plan.md").write_text("invalid root plan")
            feature.write_text(feature.read_text().replace(
                "evidence_status: unknown",
                "evidence_status: disagrees\nevidence:\n  - kind: test\n    target: tests/missing.py\n    status: verified\n    producer: unittest",
            ))
            receipt = root / ".concorde/receipts/archify.json"
            receipt.parent.mkdir(parents=True)
            receipt.write_text(json.dumps({
                "producer": "archify",
                "source_paths": ["specs/example/architecture.json"],
                "source_digest": "sha256:" + "0" * 64,
                "output": "generated/architecture/example.html",
            }))
            result = validate_project(root)
            rules = {item.rule_id for item in result.findings}
            self.assertIn("CONCORDE-LAYOUT-001", rules)
            self.assertIn("CONCORDE-EVIDENCE-002", rules)
            self.assertIn("CONCORDE-FRESHNESS-001", rules)
            self.assertEqual(next(item for item in result.findings if item.rule_id == "CONCORDE-EVIDENCE-002").severity, "error")


if __name__ == "__main__":
    unittest.main()
