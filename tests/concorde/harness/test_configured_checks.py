"""Configured checks run in the real read-only sandbox, and their inputs are checked first."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.checks import configured_checks, check_revision
from concorde.harness.check_executor import CheckSandboxError, execute_check
from concorde.spec.repository import SpecError, SpecRepository, digest
from concorde.spec.validation import check_input_findings, validate_repository
from concorde.spec.verification import verifies
from tests.concorde.support.spec_project import PACKAGE, project


class CheckIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        project(self.root)
        self.config = json.loads((self.root / ".concorde/config.json").read_text())

    def save_config(self):
        (self.root / ".concorde/config.json").write_text(json.dumps(self.config))

    def configure(self, code, timeout=10):
        check = self.config["checks"][0]
        check.update(argv=["{python}", "-c", code], timeout_seconds=timeout)
        self.save_config()
        repo = SpecRepository(self.root, PACKAGE)
        return repo, repo.module("service.transfer"), check["id"]

    def test_all_registered_required_check_inputs_are_available_and_safe(self):
        # This assertion needs the full checkout, not the publication-only scratch copy.
        findings = check_input_findings(SpecRepository(PACKAGE))
        self.assertEqual((), findings, "\n".join(f.message for f in findings))

    @verifies("scenario.checks.invalid-input")
    def test_missing_check_input_is_reported_before_execution(self):
        self.config["checks"][0]["inputs"] = ["removed-lock.json"]
        repo, target, check_id = self.configure("print('must not run')")
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("invalid", report.status)
        finding = next(f for f in report.findings if f.source == "removed-lock.json")
        self.assertIn(check_id, finding.message)
        self.assertIn(target.id, finding.message)
        self.assertIn("missing_source", finding.message)
        with (
            patch("concorde.harness.checks.execute_check") as execute,
            self.assertRaises(SpecError) as raised,
        ):
            configured_checks(repo, target, "missing-input")
        execute.assert_not_called()
        self.assertEqual("missing_source", raised.exception.code)
        self.assertEqual("removed-lock.json", raised.exception.field)
        for value in (check_id, target.id, "removed-lock.json"):
            self.assertIn(value, str(raised.exception))
        (self.root / "removed-lock.json").write_text("restored fixture input")
        restored = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("success", restored.status)
        self.assertNotEqual(
            report.result["source_digest"], restored.result["source_digest"]
        )

    def test_regular_files_and_directories_share_revision_and_preflight_rules(self):
        directory = self.root / "check-data"
        directory.mkdir()
        self.config["checks"][0]["inputs"] = ["app/transfer.py", "check-data"]
        repo, target, _ = self.configure("print('safe')")
        empty = check_revision(repo, target)
        (directory / "data.txt").write_text("one")
        populated = check_revision(repo, target)
        self.assertNotEqual(empty, populated)
        (directory / "data.txt").write_text("two")
        self.assertNotEqual(populated, check_revision(repo, target))
        (directory / "cache.pyc").write_bytes(b"ignored")
        before = check_revision(repo, target)
        (directory / "cache.pyc").write_bytes(b"also ignored")
        self.assertEqual(before, check_revision(repo, target))
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertFalse(
            [f for f in report.findings if f.rule_id == "CONCORDE-CHECK-001"]
        )

    @verifies("scenario.checks.invalid-input")
    def test_symlinks_are_unsafe_not_missing_including_excluded_directory_members(self):
        directory = self.root / "check-data"
        directory.mkdir()
        (directory / "__pycache__").mkdir()
        cases = (
            ("alias", "app/transfer.py", "alias", "invalid_field"),
            ("dangling", "absent", "dangling", "invalid_field"),
            ("check-data/link", "../app/transfer.py", "check-data", "unsafe_path"),
            ("check-data/__pycache__/link.pyc", "absent", "check-data", "unsafe_path"),
        )
        for link, destination, entry, code in cases:
            with self.subTest(link=link):
                path = self.root / link
                path.symlink_to(destination)
                try:
                    self.config["checks"][0]["inputs"] = [entry]
                    repo, target, check_id = self.configure("print('must not run')")
                    report = validate_repository(self.root, package_root=PACKAGE)
                    finding = next(
                        f for f in report.findings if f.rule_id == "CONCORDE-CHECK-001"
                    )
                    self.assertEqual(link, finding.source)
                    self.assertIn(code, finding.message)
                    self.assertIn(check_id, finding.message)
                    with self.assertRaises(SpecError) as raised:
                        check_revision(repo, target)
                    self.assertEqual(code, raised.exception.code)
                    self.assertEqual(link, raised.exception.field)
                    self.assertIn(target.id, str(raised.exception))
                finally:
                    path.unlink()

    @verifies("scenario.checks.invalid-input")
    def test_special_input_is_rejected_without_opening_it(self):
        import os

        os.mkfifo(self.root / "pipe")
        self.config["checks"][0]["inputs"] = ["pipe"]
        repo, target, _ = self.configure("print('must not run')")
        with self.assertRaises(SpecError) as raised:
            check_revision(repo, target)
        self.assertEqual("unsafe_path", raised.exception.code)
        self.assertEqual("pipe", raised.exception.field)
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertTrue(any(f.source == "pipe" for f in report.findings))

    @verifies("scenario.checks.invalid-input")
    def test_input_disappearing_during_hashing_still_names_its_owner(self):
        self.config["checks"][0]["inputs"] = ["app/transfer.py"]
        repo, target, check_id = self.configure("print('must not run')")
        with (
            patch(
                "concorde.harness.checks.read_file",
                side_effect=SpecError(
                    "required regular file is missing",
                    "missing_source",
                    "app/transfer.py",
                ),
            ),
            self.assertRaises(SpecError) as raised,
        ):
            check_revision(repo, target)
        self.assertEqual("missing_source", raised.exception.code)
        for value in (check_id, target.id, "app/transfer.py"):
            self.assertIn(value, str(raised.exception))

    @verifies("scenario.checks.invalid-input")
    def test_unsafe_registered_spelling_keeps_owning_check_diagnostics(self):
        self.config["checks"][0]["inputs"] = ["../outside"]
        self.save_config()
        report = validate_repository(self.root, package_root=PACKAGE)
        self.assertEqual("invalid", report.status)
        message = " ".join(f.message for f in report.findings)
        for value in (
            self.config["checks"][0]["id"],
            "service.transfer",
            "../outside",
        ):
            self.assertIn(value, message)

    @verifies("scenario.checks.command-output")
    def test_check_cannot_forge_logs_but_host_persists_private_output_and_digest(self):
        repo, target, check_id = self.configure("""
from pathlib import Path
import sys
assert Path('app/transfer.py').is_file()
try: Path('.concorde/runs/forged').mkdir(parents=True)
except OSError: pass
else: raise AssertionError('project was writable')
print('PRIVATE_CHECK_OUTPUT')
print('PRIVATE_CHECK_ERROR',file=sys.stderr)
sys.exit(17)
""")
        before = check_revision(repo, target)
        result = configured_checks(repo, target, "test-private")
        log = self.root / f".concorde/runs/test-private/{check_id}.log"
        self.assertEqual(
            b"PRIVATE_CHECK_OUTPUT\n\nPRIVATE_CHECK_ERROR\n", log.read_bytes()
        )
        self.assertFalse((self.root / ".concorde/runs/forged").exists())
        self.assertEqual("failed", result[0]["status"])
        self.assertEqual(17, result[0]["exit_code"])
        self.assertEqual(before, result[0]["source_digest"])
        self.assertEqual(digest(log.read_bytes()), result[0]["log_digest"])
        self.assertNotIn("PRIVATE_CHECK", json.dumps(result))

    @verifies("scenario.checks.unavailable")
    def test_unavailable_sandbox_blocks_without_leaking_private_diagnostics(self):
        repo, target, check_id = self.configure(
            "open('unlisted-new.txt','w').write('unsafe')"
        )
        with patch(
            "concorde.harness.check_executor._bubblewrap",
            side_effect=CheckSandboxError("PRIVATE_STARTUP_ERROR"),
        ):
            with self.assertRaises(SpecError) as caught:
                configured_checks(repo, target, "unavailable")
        self.assertEqual("check_sandbox_unavailable", caught.exception.code)
        self.assertNotIn("PRIVATE_STARTUP_ERROR", str(caught.exception))
        self.assertIn(
            b"PRIVATE_STARTUP_ERROR",
            (self.root / f".concorde/runs/unavailable/{check_id}.log").read_bytes(),
        )
        self.assertFalse((self.root / "unlisted-new.txt").exists())

    @verifies("scenario.checks.timeout")
    def test_timeout_retains_output_and_status(self):
        repo, target, check_id = self.configure(
            "import time; print('partial',flush=True); time.sleep(60)", 1
        )
        result = configured_checks(repo, target, "timeout")[0]
        self.assertEqual(("timeout", -1), (result["status"], result["exit_code"]))
        self.assertIn(
            b"partial",
            (self.root / f".concorde/runs/timeout/{check_id}.log").read_bytes(),
        )

    @verifies("scenario.checks.stale-measurement")
    def test_external_host_change_still_invalidates_post_check_digest(self):
        repo, target, check_id = self.configure("print('read-only check')")

        def concurrent_host_change(*args, **kwargs):
            result = execute_check(*args, **kwargs)
            # Simulates a separate authorized host writer, outside the check's sandbox.
            with (self.root / "app/transfer.py").open("a") as stream:
                stream.write("\n# changed externally\n")
            return result

        with patch("concorde.harness.checks.execute_check", concurrent_host_change):
            with self.assertRaises(SpecError) as caught:
                configured_checks(repo, target, "stale")
        self.assertEqual("stale_evidence", caught.exception.code)
        # The log written before the digest mismatch stays for inspection.
        self.assertIn(
            b"read-only check",
            (self.root / f".concorde/runs/stale/{check_id}.log").read_bytes(),
        )


if __name__ == "__main__":
    unittest.main()
