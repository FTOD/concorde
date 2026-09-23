"""Real isolated tester export and primary authority; all persistence targets disposable fixtures."""

import hashlib
import json
import os
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.check_evidence import CheckEvidence, report_names
from concorde.harness.check_executor import CheckResult, execute_check
from concorde.spec.verification import verifies
from tests.concorde.support.environment import child_environment
from tests.concorde.support.paths import REPOSITORY_ROOT


class CheckEvidenceTests(unittest.TestCase):
    @verifies("scenario.harness.context-freeze")
    def test_distribution_includes_complete_tester_contract_pair_once(self):
        from concorde.spec.repository import SpecRepository

        sources = (
            SpecRepository(REPOSITORY_ROOT)
            .spec_context("module.distribution")
            .value["sources"]
        )
        paths = [source["path"] for source in sources]
        for suffix in ("", ".json"):
            self.assertEqual(
                1, paths.count("specs/concorde/harness/checks/interfaces.md" + suffix)
            )

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="concorde-evidence-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.storage = self.root / "scratch"
        self.storage.mkdir()
        self.environment = child_environment(
            PYTHONPATH=str(REPOSITORY_ROOT / "src"), TMPDIR=str(self.storage)
        )

    def bridge(self, code, *, reports=(), timeout=10, bootstrap=None):
        command = shlex.join([sys.executable, "-c", code])
        process = subprocess.run(
            (
                [sys.executable, "-c", bootstrap]
                if bootstrap
                else [sys.executable, "-m", "concorde.distribution.tester_check"]
            ),
            input=json.dumps(
                {"command": command, "timeout": timeout, "reports": list(reports)}
            ),
            cwd=self.project,
            env=self.environment,
            capture_output=True,
            text=True,
            timeout=timeout + 20,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        response = json.loads(process.stdout.splitlines()[-1])
        self.assertEqual([], list(self.storage.glob("concorde-check-*")))
        return response

    def manifest(self, response):
        reference = response["evidence"]["manifest"]
        self.assertIsNotNone(reference, response)
        raw = Path(reference["path"]).read_bytes()
        self.assertEqual(
            reference["digest"], "sha256:" + hashlib.sha256(raw).hexdigest()
        )
        self.assertEqual(reference["bytes"], len(raw))
        self.assertEqual(0o600, Path(reference["path"]).stat().st_mode & 0o777)
        return json.loads(raw)

    @verifies(
        "scenario.harness.check-result",
        "scenario.harness.check-read-only",
        "scenario.checks.tester-evidence",
    )
    def test_failure_reports_and_output_survive_cleanup_exactly_without_scratch_secrets(
        self,
    ):
        result = self.bridge(
            """
import os,sys,json
from pathlib import Path
s=Path(os.environ['CONCORDE_CHECK_TMPDIR'])
(s/'auth.json').write_text('SECRET_AUTH');(s/'settings.json').write_text('SECRET_CONFIG')
r=Path(os.environ['CONCORDE_CHECK_REPORT_DIR'])
(r/'ignored.txt').write_text('SECRET_NOT_SELECTED')
(r/'failure.json').write_text(json.dumps({'error':'required value.documents missing','scratch':str(s)}))
try: Path('forbidden').write_text('unsafe')
except OSError as e: assert e.errno==30
else: raise AssertionError('read-only boundary absent')
print('precise failure');print('cause: documents',file=sys.stderr);sys.exit(17)
""",
            reports=["failure.json"],
        )
        self.assertEqual(17, result["returncode"])
        self.assertTrue(result["evidence"]["complete"], result)
        m = self.manifest(result)
        by_name = {r["name"]: r for r in m["artifacts"]}
        self.assertEqual(
            b"precise failure\n",
            Path(by_name["stdout.bin"]["artifact"]["path"]).read_bytes(),
        )
        report = json.loads(
            Path(by_name["reports/failure.json"]["artifact"]["path"]).read_text()
        )
        self.assertFalse(Path(report["scratch"]).exists())
        self.assertEqual("required value.documents missing", report["error"])
        combined = b"".join(
            p.read_bytes()
            for p in (self.project / ".concorde/runs").rglob("*")
            if p.is_file()
        )
        self.assertNotIn(b"SECRET_", combined)
        self.assertFalse((self.project / "forbidden").exists())
        self.assertFalse((self.project / ".concorde/status").exists())

    @verifies("scenario.harness.check-result")
    def test_binary_output_survives_lossy_and_truncated_ui_tail(self):
        result = self.bridge("import os;os.write(1,bytes(range(256))*100)")
        self.assertTrue(result["stdout_truncated"])
        self.assertTrue(result["evidence"]["complete"])
        record = self.manifest(result)["artifacts"][0]
        data = Path(record["artifact"]["path"]).read_bytes()
        self.assertEqual(bytes(range(256)) * 100, data)
        self.assertEqual(
            record["artifact"]["digest"], "sha256:" + hashlib.sha256(data).hexdigest()
        )
        self.assertFalse(record["truncated"])

    @verifies("scenario.harness.check-result")
    def test_output_and_report_limits_are_explicit_not_silent_success(self):
        result = self.bridge(
            """
import os
from pathlib import Path
os.write(1,b'A'*(2*1024*1024+50000)+b'END')
os.write(2,b'B'*(2*1024*1024+1))
r=Path(os.environ['CONCORDE_CHECK_REPORT_DIR'])
for i in range(5): (r/f'{i}.bin').write_bytes(b'R'*(2*1024*1024+1))
""",
            reports=[f"{i}.bin" for i in range(5)],
        )
        self.assertEqual(0, result["returncode"])
        self.assertTrue(result["stdout_truncated"])
        self.assertTrue(result["stdout"].endswith("END"))
        self.assertFalse(result["evidence"]["complete"])
        manifest = self.manifest(result)
        self.assertEqual(2 * 1024 * 1024 + 50003, result["stdout_bytes"])
        self.assertTrue(all(r["truncated"] for r in manifest["artifacts"]))
        self.assertEqual(
            8 * 1024 * 1024,
            sum(
                r["captured_bytes"]
                for r in manifest["artifacts"]
                if r["name"].startswith("reports/")
            ),
        )
        self.assertTrue(
            all(r["captured_bytes"] <= 2 * 1024 * 1024 for r in manifest["artifacts"])
        )

    @verifies("scenario.harness.check-scratch", "scenario.harness.check-unavailable")
    def test_unsafe_report_sources_are_refused_without_hanging_or_following_links(self):
        result = self.bridge(
            """
import os
from pathlib import Path
r=Path(os.environ['CONCORDE_CHECK_REPORT_DIR']);s=r.parent
(s/'secret').write_text('SECRET_NOT_EXPORTED')
(r/'link').symlink_to(s/'secret');(r/'directory').mkdir()
(r/'parent').symlink_to(s,target_is_directory=True)
os.mkfifo(r/'fifo');os.link(s/'secret',r/'hardlink')
(r/'good').write_text('safe')
""",
            reports=[
                "link",
                "directory",
                "parent/secret",
                "fifo",
                "hardlink",
                "absent",
                "good",
            ],
        )
        m = self.manifest(result)
        self.assertEqual(6, len(m["errors"]))
        self.assertFalse(m["complete"])
        self.assertEqual(
            b"safe", Path(m["artifacts"][-1]["artifact"]["path"]).read_bytes()
        )
        for names in (
            ["../secret"],
            ["/absolute"],
            ["a//b"],
            ["a/./b"],
            ["a\\b"],
            ["a", "a"],
            [None],
            ["x"] * 17,
        ):
            with self.subTest(names=names), self.assertRaises(ValueError):
                report_names(names)

    @verifies("scenario.harness.check-scratch")
    def test_report_directory_itself_cannot_be_replaced_by_a_link(self):
        result = self.bridge(
            """
import os
from pathlib import Path
r=Path(os.environ['CONCORDE_CHECK_REPORT_DIR']);r.rmdir()
(r.parent/'secret').write_text('secret');r.symlink_to(r.parent,target_is_directory=True)
""",
            reports=["secret"],
        )
        self.assertFalse(result["evidence"]["complete"])
        self.assertIsNone(self.manifest(result)["artifacts"][-1]["artifact"])

    @verifies("scenario.harness.check-lifetime", "scenario.checks.tester-evidence")
    def test_timeout_keeps_partial_output_and_named_report(self):
        result = self.bridge(
            """
import os,time
from pathlib import Path
Path(os.environ['CONCORDE_CHECK_REPORT_DIR'],'partial.json').write_text('{"step":"before timeout"}')
print('deadline evidence',flush=True);time.sleep(30)
""",
            reports=["partial.json"],
            timeout=0.5,
        )
        self.assertEqual(-1, result["returncode"])
        self.assertTrue(result["timed_out"])
        self.assertFalse(result["evidence"]["complete"])
        self.assertTrue(result["evidence"]["artifacts_complete"])
        self.assertIn("deadline evidence", result["stdout"])
        self.assertTrue(self.manifest(result)["timed_out"])

    @verifies("scenario.harness.check-lifetime", "scenario.checks.tester-evidence")
    def test_cancellation_captures_before_cleanup_and_ignores_repeat_abort(self):
        code = "import os,time;from pathlib import Path;Path(os.environ['CONCORDE_CHECK_REPORT_DIR'],'ready').write_text('cancel detail');print('cancel output',flush=True);time.sleep(30)"
        p = subprocess.Popen(
            [sys.executable, "-m", "concorde.distribution.tester_check"],
            cwd=self.project,
            env=self.environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.addCleanup(lambda: p.kill() if p.poll() is None else None)
        p.stdin.write(
            json.dumps(
                {
                    "command": shlex.join([sys.executable, "-c", code]),
                    "timeout": 30,
                    "reports": ["ready"],
                }
            )
        )
        p.stdin.close()
        deadline = time.monotonic() + 10
        while not list(self.storage.glob("concorde-check-*/reports/ready")):
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0.02)
        p.send_signal(signal.SIGTERM)
        p.send_signal(signal.SIGTERM)
        p.wait(timeout=15)
        stdout, stderr = p.stdout.read(), p.stderr.read()
        p.stdout.close()
        p.stderr.close()
        self.assertEqual(0, p.returncode, stderr)
        result = json.loads(stdout.splitlines()[-1])
        self.assertTrue(result["cancelled"])
        self.assertIn("cancel output", result["stdout"])
        self.assertFalse(result["evidence"]["complete"])
        self.assertTrue(result["evidence"]["artifacts_complete"])
        self.assertTrue(self.manifest(result)["cancelled"])
        self.assertEqual([], list(self.storage.glob("concorde-check-*")))

    @verifies("scenario.harness.check-lifetime")
    def test_abort_during_export_preserves_completed_execution_and_artifact_ack(self):
        result = self.bridge(
            "print('completed before abort')",
            bootstrap="""
import os,signal
from concorde.harness import check_evidence
from concorde.distribution.tester_check import main
original=check_evidence.write_run
sent=False
def interrupt(root,relative,data):
    global sent
    if not sent:
        sent=True;os.kill(os.getpid(),signal.SIGTERM)
    return original(root,relative,data)
check_evidence.write_run=interrupt
main()
""",
        )
        self.assertEqual(0, result["returncode"])
        self.assertFalse(result["cancelled"])
        self.assertTrue(result["cancellation_requested"])
        self.assertTrue(result["evidence"]["complete"])
        self.assertEqual(0, self.manifest(result)["returncode"])

    @verifies("scenario.harness.primary-status", "scenario.checks.tester-evidence")
    def test_missing_primary_authority_never_creates_a_replacement_archive(self):
        missing = self.root / "missing"
        evidence = CheckEvidence(missing, (), command="true", timeout=1)
        evidence.collect(None, CheckResult(b"original cause", b"", 17))
        self.assertIsNone(evidence.reference)
        self.assertFalse(evidence.summary()["complete"])
        self.assertIn("no local fallback", str(evidence.errors))
        self.assertFalse(missing.exists())

    @verifies("scenario.harness.check-unavailable")
    def test_unavailable_isolation_has_manifest_and_no_fallback(self):
        result = self.bridge(
            "open('unsafe','w').write('bad')",
            reports=["missing"],
            bootstrap="import sys;sys.platform='darwin';from concorde.distribution.tester_check import main;main()",
        )
        self.assertIsNone(result["returncode"])
        self.assertIn("no read-only check backend", result["error"])
        self.assertFalse(result["evidence"]["complete"])
        self.assertFalse((self.project / "unsafe").exists())
        self.assertIn("scratch/report unavailable", str(self.manifest(result)))

    @verifies("scenario.harness.primary-status")
    def test_export_refusal_keeps_original_failure_and_has_no_destination_fallback(
        self,
    ):
        (self.project / ".concorde").mkdir()
        outside = self.root / "outside"
        outside.mkdir()
        (self.project / ".concorde/runs").symlink_to(outside, target_is_directory=True)
        result = self.bridge("import sys;print('original cause');sys.exit(23)")
        self.assertEqual(23, result["returncode"])
        self.assertIn("original cause", result["stdout"])
        self.assertIsNone(result["evidence"]["manifest"])
        self.assertFalse(result["evidence"]["complete"])
        self.assertTrue(result["evidence"]["errors"])
        self.assertEqual([], list(outside.iterdir()))

    @verifies("scenario.harness.primary-status", "scenario.checks.tester-evidence")
    def test_partial_export_is_recorded_with_successful_artifacts_still_retrievable(
        self,
    ):
        from concorde.harness import check_evidence

        evidence = CheckEvidence(
            self.project, ("failed",), command="fixture", timeout=1
        )
        (self.storage / "reports").mkdir()
        (self.storage / "reports/failed").write_text("selected")
        original = check_evidence.write_run

        def fail_one(root, relative, data):
            if relative.endswith("/reports/failed"):
                raise OSError("deterministic export disk failure")
            return original(root, relative, data)

        with patch.object(check_evidence, "write_run", fail_one):
            evidence.collect(self.storage, CheckResult(b"cause", b"", 17))
        result = {"evidence": evidence.summary()}
        m = self.manifest(result)
        self.assertFalse(m["complete"])
        self.assertEqual(17, m["returncode"])
        self.assertIn("deterministic export disk failure", str(m["errors"]))
        self.assertEqual(
            b"cause", Path(m["artifacts"][0]["artifact"]["path"]).read_bytes()
        )

    @verifies("scenario.harness.primary-status")
    def test_manifest_export_failure_retains_successful_artifact_references(self):
        from concorde.harness import check_evidence

        evidence = CheckEvidence(self.project, (), command="fixture", timeout=1)
        original = check_evidence.write_run

        def fail_manifest(root, relative, data):
            if relative.endswith("/manifest.json"):
                raise OSError("manifest write refused")
            return original(root, relative, data)

        with patch.object(check_evidence, "write_run", fail_manifest):
            evidence.collect(None, CheckResult(b"specific cause", b"", 17))
        summary = evidence.summary()
        self.assertIsNone(summary["manifest"])
        self.assertFalse(summary["complete"])
        self.assertIn("manifest write refused", str(summary["errors"]))
        self.assertEqual(
            b"specific cause",
            Path(summary["artifacts"][0]["artifact"]["path"]).read_bytes(),
        )

    @verifies("scenario.harness.primary-status", "scenario.checks.tester-evidence")
    def test_linked_fixture_uses_only_primary_authority_and_retains_input_identity(
        self,
    ):
        def git(*args):
            return subprocess.run(
                ["git", "-C", str(self.project), *args],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

        git("init", "-q")
        git("config", "user.name", "Fixture")
        git("config", "user.email", "fixture@example.invalid")
        (self.project / "source").write_text("base")
        git("add", ".")
        git("commit", "-qm", "fixture")
        candidate = self.root / "candidate"
        git("worktree", "add", "-qb", "candidate", str(candidate))
        (candidate / "source").write_text("dirty")
        evidence = CheckEvidence(candidate, (), command="true", timeout=1)
        result = execute_check(
            candidate,
            ["true"],
            timeout=2,
            environment=self.environment,
            evidence=evidence.collect,
        )
        m = self.manifest({"evidence": evidence.summary()})
        self.assertEqual(0, result.returncode)
        self.assertEqual(str(candidate), m["source_worktree"])
        self.assertEqual("candidate", m["branch"])
        self.assertTrue(m["dirty"])
        self.assertTrue(m["input_tree"])
        self.assertFalse((candidate / ".concorde/runs").exists())
        self.assertFalse((candidate / ".concorde/status").exists())
        self.assertTrue(Path(evidence.reference["path"]).is_relative_to(self.project))


@unittest.skipUnless(
    os.environ.get("CONCORDE_NATIVE_PI")
    and os.environ.get("CONCORDE_NATIVE_SUBAGENTS")
    and os.environ.get("CONCORDE_TEST_SELECTION"),
    "explicit SDK/native roots and candidate test selection required",
)
class RegisteredToolEvidenceTests(unittest.TestCase):
    setUp = CheckEvidenceTests.setUp
    manifest = CheckEvidenceTests.manifest

    def drive(self, command, *, reports=(), timeout=30, abort_after=None):
        agent = self.root / "agent"
        agent.mkdir(exist_ok=True)
        environment = {
            **self.environment,
            "CONCORDE_SESSION_SELECTION": os.environ["CONCORDE_TEST_SELECTION"],
            "PI_CODING_AGENT_DIR": str(agent),
            "PI_OFFLINE": "1",
            "PI_SKIP_VERSION_CHECK": "1",
        }
        result = subprocess.run(
            [
                "node",
                str(
                    REPOSITORY_ROOT / "tests/concorde/harness/tester_command_driver.mjs"
                ),
                str(REPOSITORY_ROOT),
                os.environ["CONCORDE_NATIVE_PI"],
                str(self.project),
                str(agent),
            ],
            input=json.dumps(
                {
                    "params": {
                        "command": command,
                        "timeout": timeout,
                        "reports": list(reports),
                    },
                    **(
                        {"abortAfterMs": abort_after} if abort_after is not None else {}
                    ),
                }
            ),
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout.splitlines()[-1])

    @verifies("scenario.harness.check-lifetime")
    def test_abort_during_bridge_startup_keeps_evidence_acknowledgement(self):
        actual = self.drive("sleep 20", abort_after=0)
        self.assertTrue(actual["isError"])
        response = actual["response"]
        self.assertTrue(response["cancellation_requested"])
        self.assertTrue(response["cancelled"], response)
        self.assertFalse(response["evidence"]["complete"])
        self.assertTrue(self.manifest(response)["cancelled"])
        self.assertEqual([], list(self.storage.glob("concorde-check-*")))

    @verifies("scenario.harness.check-result")
    def test_zero_exit_missing_report_is_tool_error_not_success(self):
        actual = self.drive("true", reports=["absent"])
        self.assertTrue(actual["isError"])
        self.assertEqual(0, actual["response"]["returncode"])
        self.assertFalse(self.manifest(actual["response"])["complete"])

    @verifies("scenario.harness.check-result", "scenario.harness.native-result-gate")
    def test_real_sdk_registered_test_command_specific_failure_is_retrievable(self):
        command = shlex.join(
            [
                "node",
                str(
                    REPOSITORY_ROOT
                    / "tests/concorde/harness/structured_failure_driver.mjs"
                ),
                os.environ["CONCORDE_NATIVE_PI"],
                os.environ["CONCORDE_NATIVE_SUBAGENTS"],
            ]
        )
        actual = self.drive(command, reports=["structured-tool.json"])
        self.assertTrue(actual["sdkLoaded"])
        self.assertEqual(0, actual["realModelCalls"])
        self.assertTrue(actual["isError"])
        response = actual["response"]
        self.assertEqual(17, response["returncode"], response)
        self.assertTrue(response["evidence"]["complete"], response)
        m = self.manifest(response)
        self.assertEqual("tester-evidence-fixture", m["tool_call_id"])
        self.assertTrue(m["selection"]["pi_entry"]["catalog_digest"])
        record = next(
            r for r in m["artifacts"] if r["name"] == "reports/structured-tool.json"
        )
        raw = Path(record["artifact"]["path"]).read_bytes()
        self.assertGreater(len(raw), 20000)
        self.assertEqual(
            record["artifact"]["digest"], "sha256:" + hashlib.sha256(raw).hexdigest()
        )
        d = json.loads(raw)
        [attempt] = d["attempts"]
        self.assertTrue(attempt["isError"])
        self.assertTrue(attempt["errorComplete"])
        self.assertIn("documents", attempt["resultRecords"][0]["text"])
        self.assertEqual(
            "deterministic selected detail " * 700,
            attempt["arguments"]["value"]["detail"],
        )
        self.assertNotIn(b"SECRET_", raw)
        summary = json.loads(response["stdout"])
        self.assertFalse(Path(summary["scratch"]).exists())
        self.assertEqual([], list(self.storage.glob("concorde-check-*")))
        self.assertFalse((self.project / "forbidden-write").exists())
        print(
            json.dumps(
                {
                    "sdkLoaded": True,
                    "realModelCalls": 0,
                    "afterScratchCleanup": True,
                    "reportBytes": len(raw),
                    "reportDigest": record["artifact"]["digest"],
                    "manifest": response["evidence"]["manifest"],
                }
            )
        )
