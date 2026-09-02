from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from tests.concorde.support.paths import CONTEXT_PROJECT, REPOSITORY_ROOT


class StandaloneReleaseJourneyAcceptance(unittest.TestCase):
    def test_build_verify_extract_install_and_run_native_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            dist = base / "dist"
            build = subprocess.run(
                [sys.executable, str(REPOSITORY_ROOT / "scripts/release/build-release.py"), "--output", str(dist), "--base-url", "https://example.test/v1.0.0"],
                text=True, capture_output=True,
            )
            self.assertEqual(build.returncode, 0, build.stdout)
            verify = subprocess.run(
                [sys.executable, str(REPOSITORY_ROOT / "scripts/release/verify-release.py"), "--dist", str(dist), "--expect-version", "1.0.0", "--expect-base-url", "https://example.test/v1.0.0"],
                text=True, capture_output=True,
            )
            self.assertEqual(verify.returncode, 0, verify.stdout)
            extracted = base / "extracted"
            with zipfile.ZipFile(dist / "concorde-1.0.0.zip") as archive:
                archive.extractall(extracted)
            target = base / "project"
            install = subprocess.run(
                [
                    sys.executable, str(extracted / "concorde/scripts/install-concorde.py"),
                    "--checkout", str(extracted / "concorde"), "--target", str(target),
                    "--integration", "codex", "--apply", "--format", "json",
                ], text=True, capture_output=True,
            )
            self.assertEqual(install.returncode, 0, install.stderr or install.stdout)
            self.assertEqual(json.loads(install.stdout)["status"], "installed")
            shutil.copytree(CONTEXT_PROJECT / ".concorde", target / ".concorde", dirs_exist_ok=True)
            shutil.copytree(CONTEXT_PROJECT / "specs", target / "specs")
            validate = subprocess.run(
                [sys.executable, str(target / ".concorde/framework/scripts/concorde.py"), "--project-root", str(target), "validate"],
                text=True, capture_output=True,
            )
            self.assertEqual(validate.returncode, 0, validate.stdout)
            self.assertEqual(json.loads(validate.stdout)["status"], "success")
            self.assertFalse((target / ".specify").exists())


if __name__ == "__main__":
    unittest.main()
