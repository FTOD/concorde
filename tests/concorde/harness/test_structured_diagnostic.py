"""Preserve complete selected structured errors as data, including after real scratch cleanup."""

import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from concorde.spec.verification import verifies
from tests.concorde.support.environment import child_environment
from tests.concorde.support.paths import REPOSITORY_ROOT


class StructuredDiagnosticTests(unittest.TestCase):
    @verifies("scenario.harness.native-context-public")
    def test_codec_limits_whitelist_and_native_record_shapes_without_models(self):
        code = r"""
import assert from 'node:assert/strict';import crypto from 'node:crypto';
import {structuredAttempts,selectedDiagnostic,packDiagnostic,unpackDiagnostic} from './tests/concorde/harness/structured_diagnostic.mjs';
const rows=[{recordType:'message',runId:'r',role:'assistant',message:{provider:'fixture',model:'model',content:[{type:'toolCall',id:'one',name:'structured_output',arguments:{value:{unexpected:1}}}]}},{recordType:'tool_start',runId:'r',toolName:'read',argsPayload:'AUTH_FILE_MUST_NOT_EXPORT'},{recordType:'tool_start',runId:'r',toolName:'structured_output',toolCallId:'one',argsPayload:'{"value":{"unexpected":1}}'},{recordType:'tool_end',runId:'r',toolName:'structured_output',toolCallId:'one',isError:true},{recordType:'message',runId:'r',role:'toolResult',toolName:'structured_output',toolCallId:'one',isError:true,text:'Exact schema validation refusal'}];
const d=selectedDiagnostic({workflowRunId:'w',key:'d-0',ticket:'t',schema:{type:'object'},metadata:{runId:'r',exitCode:1,error:'no successful submission'},transcript:rows.map(JSON.stringify).join('\n')});
const nullArgs=structuredAttempts(JSON.stringify({...rows[0],message:{content:[{type:'toolCall',id:'null',name:'structured_output',arguments:null}]}}),'r');assert.equal(nullArgs.attempts[0].argumentsComplete,true);
assert.equal(d.attempts.length,1);assert.equal(d.attempts[0].errorComplete,true);assert.deepEqual(d.attempts[0].arguments,{value:{unexpected:1}});
const e=packDiagnostic(d);assert.deepEqual(unpackDiagnostic(e),d);assert(Buffer.byteLength(JSON.stringify(e))<8000);assert(!JSON.stringify(d).includes('AUTH_FILE_MUST_NOT_EXPORT'));
assert.throws(()=>packDiagnostic({...d,env:{token:'secret'}}),/only selected/);
const altered=structuredClone(e);altered.payload.sha256='wrong';assert.throws(()=>unpackDiagnostic(altered),/checksum/);
const truncated=structuredAttempts(rows.slice(0,4).concat([{...rows[4],outputTruncated:true,text:'partial … payload truncated'}]).map(JSON.stringify).join('\n'),'r');assert.equal(truncated.attempts[0].errorComplete,false);assert(truncated.attempts[0].resultTruncated);
const absent=selectedDiagnostic({workflowRunId:'w',key:'d-0',ticket:'t',schema:{},metadata:null,transcript:null});assert.equal(absent.sourceRecords,'absent');assert.equal(absent.effectiveStart,'unknown');
const big=structuredClone(d);big.attempts[0].resultRecords[0].text='complete error '.repeat(8000);assert.deepEqual(unpackDiagnostic(packDiagnostic(big)),big);
const overflow=structuredClone(d);overflow.attempts[0].resultRecords[0].text=crypto.randomBytes(20000).toString('base64');assert.throws(()=>packDiagnostic(overflow),/diagnostic bound/);
console.log('Selected arguments/errors roundtrip; secret sources excluded; source truncation and output bounds explicit; zero models');
"""
        result = subprocess.run(
            ["node", "--input-type=module", "-e", code],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(
        os.environ.get("CONCORDE_NATIVE_SUBAGENTS")
        and os.environ.get("CONCORDE_NATIVE_PI"),
        "explicit native roots required",
    )
    @verifies(
        "scenario.harness.native-context-public", "scenario.harness.native-result-gate"
    )
    def test_real_structured_tool_errors_survive_os_scratch_cleanup(self):
        temporary = tempfile.TemporaryDirectory(prefix="concorde-diagnostic-governing-")
        self.addCleanup(temporary.cleanup)
        governing = Path(temporary.name)
        for case in ("diagnostic-attempts", "schema-correction", "prose-only"):
            with self.subTest(case=case):
                command = shlex.join(
                    [
                        "node",
                        str(
                            REPOSITORY_ROOT
                            / "tests/concorde/harness/native_issue_probe.mjs"
                        ),
                        os.environ["CONCORDE_NATIVE_SUBAGENTS"],
                        os.environ["CONCORDE_NATIVE_PI"],
                        str(REPOSITORY_ROOT),
                        case,
                    ]
                )
                environment = child_environment(
                    PYTHONPATH=str(REPOSITORY_ROOT / "src"),
                    CONCORDE_SESSION_SELECTION=str(
                        REPOSITORY_ROOT
                        / ".concorde/work/pi-first-diagnostic-selection.json"
                    ),
                    CONCORDE_DIAGNOSTIC_REPORT="1",
                )
                result = subprocess.run(
                    [sys.executable, "-m", "concorde.distribution.outer_check"],
                    input=json.dumps(
                        {
                            "command": command,
                            "timeout": 120,
                            "reports": ["structured-tool.json"],
                        }
                    ),
                    cwd=governing,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=150,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr[-3000:])
                check = json.loads(result.stdout.splitlines()[-1])
                self.assertEqual(check["returncode"], 0, check)
                self.assertTrue(check["evidence"]["complete"], check)
                manifest = json.loads(
                    Path(check["evidence"]["manifest"]["path"]).read_text()
                )
                [report] = [
                    r
                    for r in manifest["artifacts"]
                    if r["name"] == "reports/structured-tool.json"
                ]
                raw = Path(report["artifact"]["path"]).read_bytes()
                self.assertEqual(
                    "sha256:" + hashlib.sha256(raw).hexdigest(),
                    report["artifact"]["digest"],
                )
                # The report, not a payload squeezed into stdout, survives cleanup.
                d = json.loads(raw)
                a = d["attempts"]
                if case == "diagnostic-attempts":
                    self.assertEqual(len(a), 3)
                    self.assertTrue(
                        all(
                            x["isError"]
                            and x["errorComplete"]
                            and x["argumentsComplete"]
                            for x in a
                        )
                    )
                    self.assertNotIn(
                        "documents", a[0]["arguments"]["value"]["result"]["data"]
                    )
                    self.assertIn("documents", a[0]["resultRecords"][0]["text"])
                    host_failure = json.loads(a[1]["resultRecords"][0]["text"])
                    self.assertEqual(host_failure["attempt"], "attempt-2")
                    self.assertIn("incompatible_handoff", json.dumps(host_failure))
                    self.assertIn(
                        "agent returned a different context identity",
                        json.dumps(host_failure),
                    )
                    self.assertIn(
                        "duplicate structured submissions",
                        a[2]["resultRecords"][0]["text"],
                    )
                    self.assertNotEqual(
                        a[1]["arguments"]["value"]["result"]["data"]["context_id"],
                        a[2]["arguments"]["value"]["result"]["data"]["context_id"],
                    )
                elif case == "schema-correction":
                    self.assertEqual([x["isError"] for x in a], [True, False])
                else:
                    self.assertEqual(a, [])
                    self.assertIn("Missing structured_output", d["native"]["error"])
                print(
                    json.dumps(
                        {
                            "case": case,
                            "reportBytes": len(raw),
                            "attempts": len(a),
                            "reportSha256": report["artifact"]["digest"],
                            "afterScratchCleanup": True,
                            "realModels": 0,
                            "evidence": check["evidence"]["manifest"],
                        }
                    )
                )
