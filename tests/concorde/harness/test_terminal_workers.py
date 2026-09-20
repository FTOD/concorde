"""Terminal-node boundaries, without model calls or task delegation."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from concorde.harness.admission import run_operation
from concorde.harness.entry import validate_invocation
from concorde.harness.host import OperationHost
from concorde.harness.worker_executor import build_worker_invocation
from concorde.spec.repository import SpecError
from concorde.spec.typed_data import TypedDataError, typed, validate_typed
from concorde.spec.verification import verifies
from tests.concorde.support.paths import REPOSITORY_ROOT


class TerminalBoundaryTests(unittest.TestCase):
    @verifies("scenario.harness.pi-worker-delegation")
    def test_recursive_entry_and_retired_invocation_fields_fail(self):
        with patch.dict(os.environ, {"CONCORDE_WORKER_POLICY": "/host/policy.json"}):
            with self.assertRaises(SpecError) as error:
                validate_invocation({})
            self.assertEqual("permission_denied", error.exception.code)
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                result = run_operation(
                    "concorde-validate",
                    None,
                    {},
                    host_context=OperationHost(root, REPOSITORY_ROOT),
                )
                self.assertEqual("blocked", result["status"])
                self.assertEqual("permission_denied", result["errors"][0]["code"])
                self.assertEqual([], list(root.iterdir()))
        with self.assertRaisesRegex(TypeError, "child_selections"):
            build_worker_invocation(child_selections=())

    @verifies("scenario.harness.worker-selection-reject")
    def test_configuration_v1_is_not_reinterpreted(self):
        current = typed("concorde-operation-configuration", {"thinking": "high"})
        self.assertEqual(2, current["schema_version"])
        with self.assertRaises(TypedDataError) as error:
            validate_typed({**current, "schema_version": 1})
        self.assertEqual("unsupported_version", error.exception.code)

    @unittest.skipUnless(shutil.which("node"), "Node is required")
    @verifies(
        "scenario.harness.pi-worker-delegation", "scenario.harness.pi-worker-gate"
    )
    def test_extension_exposes_only_granted_services_and_rejects_old_policy(self):
        # Node's type stripping loads the actual candidate extension, not a copied implementation.
        script = """
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
const worker = (await import(pathToFileURL(process.argv[1]).href)).default;
const session = await import(pathToFileURL(process.argv[2]).href);
const policyPath = process.env.CONCORDE_WORKER_POLICY;
const base = JSON.parse(fs.readFileSync(policyPath, 'utf8'));
const tools = [], events = {};
let active;
worker({registerTool: t => tools.push(t), on: (n,h) => events[n] = h,
        setActiveTools: t => active = t});
events.session_start();
const denied = [];
for (const name of ['subagent', 'concorde', 'run_operation']) {
    denied.push(await events.tool_call({toolName: name, input: {}}));
}
const rejected = [];
for (const change of [{schema_version: 1}, {children: []}, {child_tools: []},
                      {tools: ['submit_result', 'subagent']}, {child_definitions: []}]) {
    fs.writeFileSync(policyPath, JSON.stringify({...base, ...change}));
    try { worker({}); rejected.push(false); } catch { rejected.push(true); }
}
let sessionRejected = false;
try { session.concordeSession('.', {schema_version: 1, operations: []}); }
catch { sessionRejected = true; }
console.log(JSON.stringify({tools: tools.map(t => t.name), active, denied, rejected, sessionRejected}));
"""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            policy = root / "policy.json"
            policy.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "worker": "test",
                        "workspace": str(root),
                        "read_paths": [],
                        "write_paths": [],
                        "tools": ["read", "submit_result"],
                        "system_prompt_path": str(root / "prompt.md"),
                        "result_schema": {"type": "object"},
                        "report_schema": None,
                        "host_socket": None,
                        "scrub_environment": [],
                    }
                )
            )
            result = subprocess.run(
                [
                    "node",
                    "--experimental-strip-types",
                    "--input-type=module",
                    "-e",
                    script,
                    str(REPOSITORY_ROOT / "pi/extensions/concorde-worker.ts"),
                    str(REPOSITORY_ROOT / "pi/extensions/concorde-session.ts"),
                ],
                env={**os.environ, "CONCORDE_WORKER_POLICY": str(policy)},
                text=True,
                capture_output=True,
                timeout=20,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(["submit_result"], value["tools"])
        self.assertEqual(["read", "submit_result"], value["active"])
        self.assertTrue(all(item["block"] for item in value["denied"]))
        self.assertEqual([True] * 5, value["rejected"])
        self.assertTrue(value["sessionRejected"])
