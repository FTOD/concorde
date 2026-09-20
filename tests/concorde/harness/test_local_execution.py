"""Host-only local install admission, with no dependency acquisition or model in these unit cases."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from concorde.harness.host import OperationHost
from concorde.harness.relay import (
    relay_launcher,
    relay_operation,
    verify_local_execution,
)
from concorde.spec.repository import SpecError
from concorde.spec.verification import verifies


class LocalExecutionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.primary = self.root / "primary"
        self.candidate = self.root / "candidate"
        self.primary.mkdir()
        self.candidate.mkdir()
        self.host = OperationHost(self.primary, self.primary / ".concorde/framework")

    @verifies("scenario.harness.local-installation")
    def test_relay_uses_only_verified_local_paths_and_explicit_bootstrap(self):
        source = object()
        local = SimpleNamespace(
            python=self.candidate / ".concorde/.venv/bin/python",
            launcher=self.candidate / ".concorde/framework/scripts/run-operation.py",
        )
        with (
            patch(
                "concorde.distribution.local_installation.admit_package",
                return_value=source,
            ) as admit,
            patch(
                "concorde.distribution.local_installation.ensure_installation",
                return_value=local,
            ) as ensure,
        ):
            self.assertEqual(
                [str(local.python), str(local.launcher)],
                relay_launcher(self.host, self.candidate),
            )
            admit.assert_called_once_with(self.host.package_root)
            ensure.assert_called_once_with(
                self.candidate, source, bootstrap=False, preserve_project=True
            )
            relay_launcher(self.host, self.candidate, bootstrap=True)
            self.assertTrue(ensure.call_args.kwargs["bootstrap"])

    @verifies("scenario.harness.local-installation-failure")
    def test_failed_install_preserves_candidate_and_blocks_before_spawn(self):
        host = OperationHost(
            self.primary,
            self.host.package_root,
            relay_target={
                "path": str(self.candidate),
                "change_id": "change.fixture",
                "bootstrap_installation": True,
            },
        )
        with (
            patch(
                "concorde.harness.relay.read_change",
                return_value={"change_id": "change.fixture"},
            ),
            patch("concorde.harness.relay.resume_owner"),
            patch("concorde.harness.relay.progress") as progress,
            patch("concorde.distribution.local_installation.admit_package"),
            patch(
                "concorde.distribution.local_installation.ensure_installation",
                side_effect=ValueError("acquisition failed"),
            ),
            patch("subprocess.Popen") as process,
        ):
            with self.assertRaisesRegex(
                SpecError, "explicitly install/update"
            ) as failure:
                relay_operation(
                    host, "concorde-plan", {"input": {"data": {}}}, self.candidate
                )
            self.assertEqual("local_installation_required", failure.exception.code)
            progress.assert_called_once_with(
                self.candidate, status="blocked", outcome="local_installation_required"
            )
            process.assert_not_called()
            self.assertTrue(self.candidate.is_dir())

    @verifies("scenario.harness.local-installation-failure")
    def test_foreign_framework_and_missing_local_receipt_never_use_primary(self):
        with patch(
            "concorde.distribution.local_installation.verify_installation"
        ) as verify:
            with self.assertRaises(SpecError):
                verify_local_execution(
                    OperationHost(self.candidate, self.host.package_root)
                )
            verify.assert_not_called()
            verify.side_effect = ValueError("missing receipt")
            with self.assertRaisesRegex(SpecError, "missing receipt"):
                verify_local_execution(
                    OperationHost(
                        self.candidate, self.candidate / ".concorde/framework"
                    )
                )
        with (
            patch("concorde.distribution.local_installation.admit_package"),
            patch(
                "concorde.distribution.local_installation.ensure_installation",
                side_effect=ValueError("missing receipt"),
            ),
        ):
            with self.assertRaises(SpecError):
                relay_launcher(self.host, self.candidate)

    @verifies("scenario.harness.local-installation-failure")
    def test_verified_receipt_cannot_attest_a_foreign_executing_interpreter(self):
        local = SimpleNamespace(python=self.candidate / ".concorde/.venv/bin/python")
        with patch(
            "concorde.distribution.local_installation.verify_installation",
            return_value=local,
        ):
            with self.assertRaisesRegex(
                SpecError, "executing interpreter or LangGraph"
            ):
                verify_local_execution(
                    OperationHost(
                        self.candidate, self.candidate / ".concorde/framework"
                    )
                )

    @verifies("scenario.harness.local-installation")
    def test_source_private_mode_never_installs_ambient_integration(self):
        (self.candidate / "concorde.json").write_text("{}")
        (self.candidate / "src/concorde").mkdir(parents=True)
        with (
            patch("concorde.distribution.build.verify_fresh"),
            patch(
                "concorde.distribution.local_installation.ensure_installation"
            ) as ensure,
        ):
            with self.assertRaisesRegex(SpecError, "own environment"):
                relay_launcher(self.host, self.candidate, bootstrap=True)
            ensure.assert_not_called()
        self.assertFalse((self.candidate / ".pi").exists())
        # Explicit source-private runtime with disposable external fixture data is supported.
        verify_local_execution(OperationHost(self.primary, self.candidate))


if __name__ == "__main__":
    unittest.main()
