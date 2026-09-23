"""Acceptance: adopting Concorde in a project, accepting its Protocol and configuring Agent calls.

Each test installs Concorde into a fresh temporary consumer project with the real installer and
drives the installed launcher the way the user session's ``concorde`` tool does. The only
stand-ins are the offline package sources (see ``adopt_project``), the injected provisioning
failure, the native pi-subagents package binding (no Agent is launched; the prepared launch
definition is inspected instead) and, for describing capabilities, a Node harness that plays Pi's
extension API around the installed session extension.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from concorde.distribution import installation as installer
from concorde.distribution import managed_runtime
from concorde.harness.host import OperationHost
from concorde.harness.native_driver import execute
from concorde.harness.native_runtime import FORMAT, NativeRuntimeBinding
from concorde.operations.catalog import PUBLIC_OPERATIONS
from concorde.operations.dispatch import run_operation, services
from concorde.spec.repository import digest
from concorde.spec.typed_data import typed
from concorde.spec.verification import verifies
from tests.concorde.acceptance.adopt_project import (
    DEFAULT_CONFIGURATION,
    FRAMEWORK,
    RUNTIME_PYTHON,
    ConsumerProject,
    configuration,
)
from tests.concorde.support.environment import child_environment
from tests.concorde.support.paths import REPOSITORY_ROOT
from tests.concorde.support.session_catalog import shim_catalog

HARNESS = REPOSITORY_ROOT / "tests/concorde/support/pi_session_harness.mts"
SESSION_EXTENSION = "pi/extensions/concorde-session.ts"
TYPEBOX = REPOSITORY_ROOT / "pi/node_modules/typebox/package.json"
LIST_ISSUES = {
    "target_id": "module.project",
    "task": "List the open Issues",
    "action": "list",
}
SELECTION = configuration(
    model="anthropic/claude-sonnet-5", thinking="high", timeout_seconds=2400
)


def node_supports_typescript() -> bool:
    node = shutil.which("node")
    if not node:
        return False
    output = subprocess.run(
        [node, "--version"], capture_output=True, text=True, check=False
    )
    try:
        version = tuple(
            int(x) for x in output.stdout.strip().lstrip("v").split(".")[:2]
        )
    except ValueError:
        return False
    return version >= (22, 6)


def installed_binding(target: Path) -> dict:
    raw = (target / ".concorde/protocol/manifest.json").read_bytes()
    return {"version": json.loads(raw)["version"], "digest": digest(raw)}


class AdoptAcceptance(ConsumerProject, unittest.TestCase):
    """The developer installs Concorde; the user session initializes and inspects the project."""

    def describe_session(self) -> dict:
        """The installed ``concorde`` tool describing every capability of its catalog.

        The installed shim embeds the catalog and binds the installed session extension; Pi
        itself supplies ``typebox`` to extensions, which plain Node cannot resolve from the
        installed tree, so the harness binds the source extension after checking that the
        installed extension is byte for byte the same.
        """
        installed = self.target / FRAMEWORK / SESSION_EXTENSION
        self.assertEqual(
            (REPOSITORY_ROOT / SESSION_EXTENSION).read_bytes(), installed.read_bytes()
        )
        catalog = shim_catalog(
            (self.target / ".pi/extensions/concorde-session.ts").read_bytes()
        )
        catalog_path = self.scratch / "catalog.json"
        catalog_path.write_text(json.dumps(catalog))
        calls = [
            {"params": {"operation": item["name"], "action": "describe"}}
            for item in catalog["operations"]
        ]
        process = subprocess.run(
            [
                "node",
                "--experimental-strip-types",
                str(HARNESS),
                str(REPOSITORY_ROOT / SESSION_EXTENSION),
                str(self.target),
                str(catalog_path),
            ],
            input=json.dumps({"calls": calls}),
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
            env=child_environment(TMPDIR=str(self.tmp)),
            cwd=self.target,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        return {"catalog": catalog, **json.loads(process.stdout)}

    @unittest.skipUnless(node_supports_typescript(), "Node 22.6+ runs the session tool")
    @unittest.skipUnless(
        TYPEBOX.is_file(), "typebox is not installed; npm ci --prefix pi"
    )
    @verifies(
        "scenario.concorde.adopt-initialize",
        "scenario.concorde.describe-capabilities",
    )
    def test_install_initialize_and_describe_the_installed_capabilities(self):
        self.install()
        self.assertTrue((self.target / ".concorde/protocol/manifest.json").is_file())
        self.assertFalse((self.target / ".concorde/config.json").exists())

        # The user session proposes a first Spec, then applies exactly that proposal. The
        # initializer takes its configuration from the request: the envelope carries none.
        proposed = self.call(
            "concorde-init",
            {
                "action": "propose",
                "name": "Consumer",
                "configuration": configuration(
                    model="openai-codex/gpt-6-astra", thinking="medium"
                ),
            },
        )
        self.assertEqual("succeeded", proposed["status"], proposed)
        proposal = proposed["output"]["data"]
        self.assertEqual("proposed", proposal["status"])
        self.assertFalse((self.target / ".concorde/config.json").exists())
        applied = self.call(
            "concorde-init",
            {
                "action": "apply",
                "proposal": proposal["proposal"],
                "proposal_digest": proposal["proposal_digest"],
                "run_in_primary": True,
            },
        )
        self.assertEqual("succeeded", applied["status"], applied)
        self.assertEqual("applied", applied["output"]["data"]["status"])

        # The configuration binds the copy the installer placed under .concorde/protocol/.
        self.assertEqual(
            installed_binding(self.target),
            self.read_json(".concorde/config.json")["protocol"],
        )
        # The project validates without errors, with the installed validator.
        process = subprocess.run(
            [
                str(self.target / RUNTIME_PYTHON),
                str(self.target / FRAMEWORK / "scripts/concorde.py"),
                "--project-root",
                str(self.target),
                "validate",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=child_environment(TMPDIR=str(self.tmp)),
        )
        report = json.loads(process.stdout)
        self.assertEqual(
            [],
            [f for f in report["findings"] if f["severity"] == "error"],
            report,
        )
        self.assertEqual(0, process.returncode, report)
        # The root entry states that purpose and behaviour are not yet specified.
        registry = self.read_json(".concorde/specs.json")
        (root,) = registry["modules"]
        entry = (self.target / root["entry"]).read_text()
        self.assertIn("purpose, its users and the", entry)
        self.assertIn("have not been specified yet", entry)
        self.assertIn("How the project is used is not specified yet", entry)

        # Describing the capabilities admits nothing, creates no worktree, launches no Agent.
        before = self.tree()
        runs, worktrees = self.runs(), self.worktrees()
        described = self.describe_session()
        catalog = described["catalog"]
        names = [item["name"] for item in catalog["operations"]]
        self.assertEqual(list(PUBLIC_OPERATIONS), names)
        self.assertEqual(
            names, described["tool"]["parameters"]["properties"]["operation"]["enum"]
        )
        schemas = json.loads(
            (self.target / FRAMEWORK / "generated/schemas.json").read_text()
        )
        for item, result in zip(catalog["operations"], described["results"]):
            with self.subTest(operation=item["name"]):
                self.assertIn(
                    f"- {item['name']}: {item['description']}", described["prompt"]
                )
                self.assertTrue(result["ok"], result)
                self.assertTrue(result["text"].startswith(item["description"]))
                self.assertIn(f"# {item['name']}", result["text"])
                self.assertEqual(
                    schemas[f"{item['name']}-request"], item["request_schema"]
                )
                self.assertIn(
                    json.dumps(item["request_schema"], indent=2), result["text"]
                )
        self.assertEqual(before, self.tree())
        self.assertEqual(runs, self.runs())
        self.assertEqual(worktrees, self.worktrees())
        self.assertEqual([], [p.name for p in self.tmp.iterdir()])

    @verifies("scenario.concorde.adopt-conflict")
    def test_a_conflicting_installation_changes_nothing(self):
        conflict = self.target / ".pi/extensions/concorde-session.ts"
        conflict.parent.mkdir(parents=True)
        conflict.write_text("// the developer's own extension\n")
        before = self.tree()
        code, payload = self.run_installer()
        self.assertNotEqual(0, code, payload)
        self.assertEqual("conflict", payload["status"], payload)
        self.assertEqual(
            [".pi/extensions/concorde-session.ts"],
            [
                item["path"]
                for item in payload["actions"]
                if item["action"] == "conflict"
            ],
        )
        self.assertEqual(before, self.tree())
        # With nothing installed, a following initialization proposal is refused.
        result = run_operation(
            "concorde-init",
            None,
            typed(
                "concorde-init-request",
                {
                    "action": "propose",
                    "name": "Consumer",
                    "configuration": configuration(thinking="medium"),
                },
            ),
            host_context=OperationHost(self.target, REPOSITORY_ROOT),
        )
        self.assertEqual("blocked", result["status"], result)
        self.assertEqual("not_installed", result["errors"][0]["code"], result)
        # The refused call leaves only its own run record.
        self.assertEqual(before, self.tree(exclude=(".git", ".concorde/runs")))

    @verifies("scenario.concorde.adopt-provision-failure")
    def test_a_failed_upgrade_keeps_the_previous_installation(self):
        self.install()
        self.initialize()
        self.age_installation()
        before = self.tree()
        # Reinstalling the (newer) package fails while it provisions the managed runtime.
        output = io.StringIO()
        with (
            mock.patch.dict(os.environ, self.install_environment(), clear=True),
            mock.patch.object(
                managed_runtime,
                "_verify_operations",
                side_effect=managed_runtime.ManagedRuntimeError(
                    "injected runtime verification failure"
                ),
            ),
            contextlib.redirect_stdout(output),
        ):
            code = installer.main(
                ["--target", str(self.target), "--apply", "--format", "json"]
            )
        report = json.loads(output.getvalue())
        self.assertNotEqual(0, code, report)
        self.assertEqual("failed", report["status"], report)
        self.assertIn("injected runtime verification failure", report["error"])
        # The previous installation's files, receipt and Protocol copy are restored byte for
        # byte; the plan kept the existing runtime (see age_installation), so it is intact too.
        self.assertEqual(before, self.tree())
        # With the runtime kept, capabilities keep running on the previous installation.
        result = self.call("concorde-issues", LIST_ISSUES)
        self.assertEqual("succeeded", result["status"], result)

    def age_installation(self) -> None:
        """Turn the installation into one of an older release whose README differed.

        The receipt then owns the older README and names the older package identity, so the
        current package is a newer release that updates that file.
        """
        framework = self.target / FRAMEWORK
        readme = framework / "README.md"
        readme.write_bytes(readme.read_bytes() + b"\nThe previous release.\n")
        receipt_path = self.target / installer.RECEIPT_PATH
        receipt = json.loads(receipt_path.read_text())
        for item in receipt["outputs"]:
            if item["path"] == f"{FRAMEWORK}/README.md":
                item["sha256"] = installer._sha256(readme.read_bytes())
        manifest = json.loads((framework / "concorde.json").read_text())
        receipt["package"] = installer.package_identity(
            installer.Package(framework, manifest)
        )
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        actions, _, _ = installer.installation_plan(
            self.target, installer.load_package(REPOSITORY_ROOT)
        )
        planned = {item["path"]: item["action"] for item in actions}
        self.assertEqual("update", planned[f"{FRAMEWORK}/README.md"])
        self.assertEqual("unchanged", planned[".concorde/.venv"])


class ProtocolAndConfigurationAcceptance(ConsumerProject, unittest.TestCase):
    """An installed, initialized project whose Protocol binding and Agent configuration change."""

    def setUp(self):
        super().setUp()
        self.install()
        self.initialize()

    @verifies(
        "scenario.concorde.protocol-upgrade-refused",
        "scenario.concorde.protocol-upgrade-accepted",
    )
    def test_a_newer_protocol_is_refused_until_the_session_accepts_it(self):
        # The configuration still binds the Protocol copy of the previous installation, while
        # the installer has placed the newer copy under .concorde/protocol/.
        config = self.read_json(".concorde/config.json")
        previous = {
            "version": config["protocol"]["version"],
            "digest": "sha256:" + "0" * 64,
        }
        config["protocol"] = previous
        (self.target / ".concorde/config.json").write_text(
            json.dumps(config, indent=2) + "\n"
        )
        before = self.tree(exclude=(".git", ".concorde/runs"))
        refused = self.call("concorde-issues", LIST_ISSUES)
        self.assertEqual("blocked", refused["status"], refused)
        self.assertEqual("protocol_mismatch", refused["errors"][0]["code"], refused)
        self.assertEqual(before, self.tree(exclude=(".git", ".concorde/runs")))

        # Accepting the installed Protocol explicitly moves the binding to it.
        proposed = self.call(
            "concorde-configure",
            {
                "action": "propose",
                "configuration": config["operation_configuration"],
                "accept_protocol": True,
                "run_in_primary": True,
            },
        )
        self.assertEqual("succeeded", proposed["status"], proposed)
        proposal = proposed["output"]["data"]
        self.assertEqual(previous, self.read_json(".concorde/config.json")["protocol"])
        applied = self.call(
            "concorde-configure",
            {
                "action": "apply",
                "proposal": proposal["proposal"],
                "proposal_digest": proposal["proposal_digest"],
                "run_in_primary": True,
            },
        )
        self.assertEqual("succeeded", applied["status"], applied)
        self.assertEqual(
            installed_binding(self.target),
            self.read_json(".concorde/config.json")["protocol"],
        )
        listed = self.call("concorde-issues", LIST_ISSUES)
        self.assertEqual("succeeded", listed["status"], listed)

    @verifies(
        "scenario.concorde.configure-reject",
        "scenario.concorde.configure-apply",
    )
    def test_configuring_agent_calls(self):
        path = self.target / ".concorde/config.json"
        before = path.read_bytes()
        unsupported = {
            "type_id": "concorde-operation-configuration",
            "schema_version": DEFAULT_CONFIGURATION["schema_version"],
            "data": {"model": "openai-codex/gpt-6-astra", "thinking": "ultra"},
        }
        rejected = self.call(
            "concorde-configure",
            {
                "action": "propose",
                "configuration": unsupported,
                "run_in_primary": True,
            },
            checked=False,
        )
        self.assertNotEqual("succeeded", rejected["status"], rejected)
        self.assertIn("thinking", rejected["errors"][0]["field"], rejected)
        self.assertEqual(before, path.read_bytes())

        proposed = self.call(
            "concorde-configure",
            {"action": "propose", "configuration": SELECTION, "run_in_primary": True},
        )
        self.assertEqual("succeeded", proposed["status"], proposed)
        proposal = proposed["output"]["data"]
        applied = self.call(
            "concorde-configure",
            {
                "action": "apply",
                "proposal": proposal["proposal"],
                "proposal_digest": proposal["proposal_digest"],
                "run_in_primary": True,
            },
        )
        self.assertEqual("succeeded", applied["status"], applied)
        self.assertEqual(
            SELECTION,
            self.read_json(".concorde/config.json")["operation_configuration"],
        )

        # The next Agent call of a capability is prepared with that model, thinking level and
        # time limit. The launch definition is read from the prepared call; nothing launches.
        agent = self.prepare_agent_call()
        self.assertIn('model: "anthropic/claude-sonnet-5"', agent)
        self.assertIn('thinking: "high"', agent)
        self.assertIn("timeoutMs: 2400000", agent)

    def prepare_agent_call(self) -> str:
        """Prepare a context-solve Agent call on the installed package; return its definition."""
        calls = Path(tempfile.mkdtemp(dir=self.tmp))
        before = Path.cwd()
        self.addCleanup(os.chdir, before)
        os.chdir(self.target)
        with (
            mock.patch.object(tempfile, "tempdir", str(calls)),
            mock.patch(
                "concorde.harness.native_driver.admit_native_runtime",
                return_value=NativeRuntimeBinding(
                    FORMAT, str(self.scratch / "native"), "sha256:" + "0" * 64
                ),
            ),
        ):
            prepared = execute(
                self.target / FRAMEWORK,
                "prepare",
                {
                    "invocation": {
                        "type_id": "concorde-operation-invocation",
                        "schema_version": 3,
                        "operation_id": "concorde-context-solve",
                        "mode": "execute",
                        "configuration": None,
                        "input": typed(
                            "concorde-context-solve-request",
                            {"target_id": "module.project", "task": "Assess"},
                        ),
                    },
                    "native_root": str(self.scratch / "native"),
                    "session_id": "acceptance-session",
                },
                services=services(),
            )
        self.assertEqual("prepared", prepared["state"], prepared)
        call = prepared["call"]
        return (Path(call["cwd"]) / ".pi/agents" / (call["agent"] + ".md")).read_text()


if __name__ == "__main__":
    unittest.main()
