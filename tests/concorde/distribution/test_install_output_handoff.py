"""Explicit source-to-installed fixture provenance, not selection weakening."""

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from concorde.spec.verification import verifies
from tests.concorde.support.environment import (
    child_environment,
    scrub_selection,
    scrubbed_process_environment,
)
from tests.concorde.support.install_output_handoff import (
    install_selected_fixture,
    output_environment,
)
from tests.concorde.support.managed_runtime import (
    NpmSeedError,
    independent_runtime_environment,
    locked_npm_tarballs,
    seed_npm_cache,
)
from tests.concorde.support.paths import REPOSITORY_ROOT


class HandoffPolicyTests(unittest.TestCase):
    def test_environment_separation_is_local_and_narrow(self):
        source = {
            "CONCORDE_SESSION_SELECTION": "source-selection",
            "CONCORDE_NATIVE_PROJECT_ROOT": "source-data",
            "PYTHONPATH": "source-path",
            "PATH": "unchanged",
            "OTHER": "preserved",
            "PI_SUBAGENT_EXTENSION_BINDINGS": json.dumps(
                {
                    "concorde/1": {"selection": "source-selection"},
                    "other/1": {"opaque": "preserve"},
                }
            ),
        }
        child = output_environment(source)
        self.assertEqual(source["CONCORDE_SESSION_SELECTION"], "source-selection")
        self.assertNotIn("CONCORDE_SESSION_SELECTION", child)
        self.assertEqual(child["OTHER"], "preserved")
        self.assertEqual(
            json.loads(child["PI_SUBAGENT_EXTENSION_BINDINGS"]),
            {"other/1": {"opaque": "preserve"}},
        )

    def test_shared_scrub_removes_only_the_ambient_selection(self):
        ambient = {
            "CONCORDE_SESSION_SELECTION": "/elsewhere/selection.json",
            "CONCORDE_NATIVE_PROJECT_ROOT": "/elsewhere",
            "CONCORDE_WORKER_POLICY": "/elsewhere/policy.json",
            "PI_SUBAGENT_EXTENSION_BINDINGS": json.dumps(
                {"concorde/1": {"selection": "/elsewhere/selection.json"}}
            ),
            "PATH": "kept",
            "CONCORDE_CHECK_TMPDIR": "kept-too",
        }
        self.assertEqual(
            {"PATH": "kept", "CONCORDE_CHECK_TMPDIR": "kept-too"},
            scrub_selection(ambient),
        )
        self.assertEqual(
            {"other/1": {"opaque": "preserve"}},
            json.loads(
                scrub_selection(
                    {
                        "PI_SUBAGENT_EXTENSION_BINDINGS": json.dumps(
                            {"concorde/1": {}, "other/1": {"opaque": "preserve"}}
                        )
                    }
                )["PI_SUBAGENT_EXTENSION_BINDINGS"]
            ),
        )
        self.assertEqual(
            {}, scrub_selection({"PI_SUBAGENT_EXTENSION_BINDINGS": "not json"})
        )
        with patch.dict(os.environ, ambient):
            child = child_environment(EXTRA="1")
            self.assertEqual("1", child["EXTRA"])
            self.assertNotIn("CONCORDE_SESSION_SELECTION", child)
            self.assertNotIn("PI_SUBAGENT_EXTENSION_BINDINGS", child)
            with scrubbed_process_environment(EXTRA="1"):
                self.assertNotIn("CONCORDE_SESSION_SELECTION", os.environ)
                self.assertNotIn("CONCORDE_WORKER_POLICY", os.environ)
                self.assertEqual("1", os.environ["EXTRA"])
                self.assertEqual("kept", os.environ["PATH"])
            self.assertEqual(
                "/elsewhere/selection.json", os.environ["CONCORDE_SESSION_SELECTION"]
            )
            self.assertNotIn("EXTRA", os.environ)

    def test_npm_seed_fills_the_cache_in_use_from_local_bytes_or_names_the_gap(self):
        locked = locked_npm_tarballs(REPOSITORY_ROOT)
        self.assertEqual(["typebox@1.1.38"], [spec for spec, _, _ in locked])
        with tempfile.TemporaryDirectory(prefix="concorde-npm-seed-test-") as temporary:
            root = Path(temporary)
            home = root / "home"
            home.mkdir()
            # A populated local cache, produced from this host's own bootstrap material.
            populated = seed_npm_cache(
                {**os.environ, "npm_config_cache": str(root / "populated")},
                REPOSITORY_ROOT,
            )
            self.assertEqual(root / "populated", populated)
            # An empty HOME hides npm's default cache: nothing local is left to seed from.
            empty = {
                **os.environ,
                "HOME": str(home),
                "npm_config_cache": str(root / "empty"),
            }
            with self.assertRaises(NpmSeedError) as missing:
                seed_npm_cache(empty, REPOSITORY_ROOT)
            for expected in ("typebox@1.1.38", str(root / "empty"), str(home / ".npm")):
                self.assertIn(expected, str(missing.exception))
            self.assertFalse(list((root / "empty").glob("_cacache/content-v2/**/*")))
            # An explicit populated cache serves as the source, and workers share one seeding.
            explicit = {**empty, "CONCORDE_TEST_NPM_CACHE": str(populated)}
            with ThreadPoolExecutor(max_workers=4) as pool:
                caches = set(
                    pool.map(
                        lambda _: seed_npm_cache(explicit, REPOSITORY_ROOT), range(4)
                    )
                )
            self.assertEqual({root / "empty"}, caches)
            self.assertEqual(
                1, len(list((root / "empty").glob("_cacache/content-v2/sha512/*/*/*")))
            )
            project = root / "pi"
            project.mkdir()
            for name in ("package.json", "package-lock.json"):
                shutil.copyfile(REPOSITORY_ROOT / "pi" / name, project / name)
            installed = subprocess.run(
                ["npm", "--prefix", str(project), "ci", "--ignore-scripts"],
                env={**explicit, "NPM_CONFIG_OFFLINE": "true"},
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, installed.returncode, installed.stderr)
            self.assertTrue((project / "node_modules/typebox/package.json").is_file())

    def test_outside_scratch_and_missing_governing_selection_refuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            scratch = Path(temporary)
            with patch.dict(
                os.environ,
                {
                    "CONCORDE_CHECK_TMPDIR": str(scratch),
                    "CONCORDE_SESSION_SELECTION": "wrong",
                },
            ):
                for target in (scratch, REPOSITORY_ROOT, scratch / "consumer"):
                    with self.assertRaises(ValueError):
                        install_selected_fixture(target, Path("/not-selected"))

    @unittest.skipUnless(
        os.environ.get("CONCORDE_NATIVE_SUBAGENTS")
        and os.environ.get("CONCORDE_NATIVE_PI"),
        "explicit native roots required",
    )
    @verifies(
        "scenario.harness.native-context-public",
        "scenario.harness.check-read-only",
        "scenario.distribution.install-local-worktree",
    )
    def test_readonly_tester_installs_selected_output_and_runs_native_smoke(self):
        with tempfile.TemporaryDirectory(
            prefix="concorde-install-handoff-input-"
        ) as temporary:
            environment = independent_runtime_environment(
                Path(temporary), REPOSITORY_ROOT
            )
            # Locked acquisition stays offline: install_selected_fixture seeds the tester's
            # issued scratch cache from local bytes, so the only writes are to that scratch.
            environment.update(
                CONCORDE_SESSION_SELECTION=str(
                    REPOSITORY_ROOT / ".concorde/work/pi-first-repair-selection.json"
                ),
                PYTHONPATH=str(REPOSITORY_ROOT / "src"),
            )
            argv = [
                sys.executable,
                str(
                    REPOSITORY_ROOT
                    / "tests/concorde/distribution/installed_output_probe.py"
                ),
                os.environ["CONCORDE_NATIVE_SUBAGENTS"],
                os.environ["CONCORDE_NATIVE_PI"],
            ]
            governing = Path(temporary) / "governing"
            governing.mkdir()
            result = subprocess.run(
                [sys.executable, "-m", "concorde.distribution.tester_check"],
                input=json.dumps({"command": shlex.join(argv), "timeout": 330}),
                cwd=governing,
                env=environment,
                capture_output=True,
                text=True,
                timeout=370,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr[-4000:])
            check = json.loads(result.stdout.splitlines()[-1])
            self.assertEqual(check["returncode"], 0, check)
            self.assertFalse(check["timed_out"])
            self.assertLess(len(check["stdout"].encode()), 8000)
            proof = json.loads(check["stdout"])
            self.assertTrue(proof["native"]["accepted"])
            self.assertTrue(proof["inherited_selection_refused"])
            print(json.dumps(proof))
