"""Preparation destinations and dependency reuse; real compiler isolation is an integration check."""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT

# The lockfile of the fixture: a compiler, esbuild with its platform packages, an optional
# package for every platform that only a package left out would need, and a platform package that
# only an optional peer dependency reaches.
LOCK = {
    "lockfileVersion": 3,
    "packages": {
        "": {"name": "docsite"},
        "node_modules/typescript": {"version": "5.0.0"},
        "node_modules/esbuild": {"version": "0.25.12"},
        "node_modules/@esbuild/linux-x64": {
            "version": "0.25.12",
            "optional": True,
            "os": ["linux"],
            "cpu": ["x64"],
        },
        "node_modules/@esbuild/darwin-arm64": {
            "version": "0.25.12",
            "optional": True,
            "os": ["darwin"],
            "cpu": ["arm64"],
        },
        "node_modules/@emnapi/core": {"version": "1.0.0", "optional": True},
        "node_modules/vitest/node_modules/@esbuild/linux-x64": {
            "version": "0.28.2",
            "dev": True,
            "optional": True,
            "peer": True,
            "os": ["linux"],
            "cpu": ["x64"],
        },
    },
}
EVERYTHING = ["typescript", "esbuild", "@esbuild/linux-x64"]
OPTIONAL_PEER = "vitest/node_modules/@esbuild/linux-x64"
PLATFORM = "linux x64 glibc\n"


def install(docsite: Path, packages: list[str]) -> None:
    for name in packages:
        path = f"node_modules/{name}"
        folder = docsite / path
        folder.mkdir(parents=True)
        (folder / "package.json").write_text(
            json.dumps({"version": LOCK["packages"][path]["version"]})
        )
    if "typescript" in packages:
        (docsite / "node_modules/typescript/bin").mkdir()
        (docsite / "node_modules/typescript/bin/tsc").write_text("compiler")


class DocsiteTypeCheckTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "check_docsite_types",
            REPOSITORY_ROOT / "scripts/development/check-docsite-types.py",
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def check(self, checkout: list[str] | None, installs: list[list[str]]):
        """Run the check on a checkout whose own install holds ``checkout`` (None: none), each
        npm ci installing the next of ``installs``; answer the exit status, the calls and
        whether the checkout's files stayed unchanged."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docsite = root / "docsite"
            docsite.mkdir()
            for filename in ("package.json", "tsconfig.json"):
                (docsite / filename).write_text("{}")
            (docsite / "package-lock.json").write_text(json.dumps(LOCK))
            (docsite / ".generated").mkdir()
            (docsite / ".generated/specs-sidebar.json").write_text("original")
            if checkout is not None:
                install(docsite, checkout)
            original = {
                str(p.relative_to(root)): p.read_bytes()
                for p in root.rglob("*")
                if p.is_file()
            }
            calls, pending = [], list(installs)

            def run(argv, *, cwd=None, **kwargs):
                if argv[:2] == ["node", "-p"]:
                    return subprocess.CompletedProcess(argv, 0, PLATFORM, "")
                cwd = Path(cwd)
                self.assertFalse(cwd.is_relative_to(root))
                calls.append((argv, cwd))
                if argv[0] == "npm":
                    shutil.rmtree(cwd / "node_modules", ignore_errors=True)
                    install(cwd, pending.pop(0))
                elif "--import" in argv:
                    self.assertEqual(str(root), argv[-1])
                    (cwd / ".generated").mkdir()
                    (cwd / ".generated/specs-sidebar.json").write_text(
                        "temporary sidebar"
                    )
                else:
                    self.assertIn("--noEmit", argv)
                    return subprocess.CompletedProcess(argv, 7)
                return subprocess.CompletedProcess(argv, 0)

            with (
                patch.object(self.module, "ROOT", root),
                patch.object(self.module, "DOCSITE", docsite),
                patch.object(self.module.subprocess, "run", run),
            ):
                status = self.module.main()
            self.assertTrue(all(not cwd.exists() for _, cwd in calls))
            unchanged = original == {
                str(p.relative_to(root)): p.read_bytes()
                for p in root.rglob("*")
                if p.is_file()
            }
            return status, calls, unchanged

    @verifies("scenario.concorde.check-docsite-external")
    def test_preparation_and_dependency_installation_use_only_temporary_copy(self):
        for checkout, installs in ((None, [EVERYTHING]), (EVERYTHING, [])):
            with self.subTest(reused=checkout is not None):
                status, calls, unchanged = self.check(checkout, installs)
                self.assertEqual(7, status)
                self.assertEqual(
                    checkout is None, any(argv[0] == "npm" for argv, _ in calls)
                )
                self.assertTrue(unchanged)

    @verifies("scenario.concorde.check-docsite-complete-install")
    def test_an_install_without_a_package_for_this_platform_is_never_used(self):
        # The checkout's install lacks esbuild's platform package: a fresh one is made, and an
        # npm ci that leaves it out again is retried.
        partial = ["typescript", "esbuild"]
        status, calls, unchanged = self.check(partial, [partial, EVERYTHING])
        self.assertEqual(7, status)
        self.assertEqual(2, sum(argv[0] == "npm" for argv, _ in calls))
        self.assertTrue(unchanged)
        # Every attempt leaves it out: the compiler never runs and the check fails.
        status, calls, _ = self.check(None, [partial] * 3)
        self.assertEqual(1, status)
        self.assertEqual(["npm"] * 3, [argv[0] for argv, _ in calls])

    @verifies("scenario.concorde.check-docsite-complete-install")
    def test_a_package_only_optional_peers_reach_may_be_left_out(self):
        # npm 11 leaves it out and npm 10 installs it: either install is used as it is.
        for checkout in (EVERYTHING, [*EVERYTHING, OPTIONAL_PEER]):
            with self.subTest(with_optional_peer=OPTIONAL_PEER in checkout):
                status, calls, unchanged = self.check(checkout, [])
                self.assertEqual(7, status)
                self.assertFalse(any(argv[0] == "npm" for argv, _ in calls))
                self.assertTrue(unchanged)
        # Present at another version, it is still wrong.
        with tempfile.TemporaryDirectory() as directory:
            docsite = Path(directory)
            install(docsite, [*EVERYTHING, OPTIONAL_PEER])
            (docsite / "node_modules" / OPTIONAL_PEER / "package.json").write_text(
                json.dumps({"version": "0.0.1"})
            )
            platform = dict(zip(("os", "cpu", "libc"), PLATFORM.split(), strict=True))
            self.assertEqual(
                [f"node_modules/{OPTIONAL_PEER}"],
                self.module.lacking(docsite, LOCK, platform),
            )


if __name__ == "__main__":
    unittest.main()
