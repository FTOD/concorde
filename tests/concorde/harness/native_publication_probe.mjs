/** Dependency contract probe, not a production import surface.
 * Uses pi-subagents' actual executor, native foreground completion, typed gate,
 * metadata writer, asynchronous workflow publication and finite host commands.
 * Only the child model-execution factory and the enclosing Pi UI facade are
 * scripted. No model/provider, external agent runner or network is invoked.
 *
 * node native_publication_probe.mjs <pi-subagents root> <Pi SDK root> <candidate>
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire, syncBuiltinESMExports } from "node:module";
import { EventEmitter } from "node:events";
import { execFileSync } from "node:child_process";
import { modelFixture } from "./native_model_fixture.mjs";

const [subagents, sdk, candidate, scenario = "success"] = process.argv.slice(2);
const count =
  scenario === "success" || scenario === "session-file"
    ? 60
    : scenario === "async-child"
      ? 40
      : scenario === "failed-child"
        ? 2
        : 1;
assert(subagents && sdk && candidate, "three absolute roots required");
execFileSync(path.join(candidate, ".venv/bin/python"), [
  "-c",
  "import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from concorde.harness.native_runtime import admit_native_runtime; admit_native_runtime(Path(sys.argv[2]))",
  path.join(candidate, "src"),
  subagents,
]);
const root = fs.mkdtempSync(
  path.join(os.tmpdir(), "concorde-native-publication-"),
);
// All dependency state goes to the disposable fixture, never operator settings.
process.env.PI_CODING_AGENT_DIR = path.join(root, "agent");
process.env.PI_SUBAGENTS_TEMP_ROOT = path.join(root, "native-tmp");
process.env.PI_SUBAGENTS_LLM_INTENT_ARBITER = "0";
process.env.PI_SUBAGENTS_PI_CODING_AGENT_PACKAGE_ROOT = sdk;
process.env.CONCORDE_NATIVE_FIXTURE_CALLS = path.join(
  root,
  "background-model-calls.log",
);
process.env.CONCORDE_NATIVE_FIXTURE_ROOT = root;
process.env.CONCORDE_NATIVE_FIXTURE_SCENARIO = scenario;
process.env.CONCORDE_NATIVE_FIXTURE_SDK = sdk;
process.env.CONCORDE_NATIVE_FIXTURE_CANDIDATE = candidate;
process.chdir(root);
// Faults target actual producer writes; serialization remains package-owned.
const hostFs = createRequire(import.meta.url)("node:fs");
const writeFile = hostFs.writeFileSync;
const rename = hostFs.renameSync;
let statusFaultActivated = false;
hostFs.writeFileSync = function (file, ...args) {
  if (
    scenario === "metadata-write-failure" &&
    String(file).startsWith(root) &&
    String(file).endsWith("_meta.json")
  )
    throw Object.assign(new Error("fixture metadata I/O failure"), {
      code: "EIO",
    });
  return writeFile.call(this, file, ...args);
};
hostFs.renameSync = function (source, destination) {
  if (
    scenario === "status-write-failure" &&
    String(destination).startsWith(root) &&
    path.basename(String(destination)) === "status.json"
  ) {
    const value = JSON.parse(fs.readFileSync(source, "utf8"));
    statusFaultActivated ||=
      value.steps?.some((step) => step.status === "completed") === true;
    if (
      statusFaultActivated &&
      !fs.existsSync(path.join(root, "rejected.json"))
    )
      throw Object.assign(new Error("fixture status I/O failure"), {
        code: "EIO",
      });
  }
  return rename.call(this, source, destination);
};
syncBuiltinESMExports();
const require = createRequire(path.join(sdk, "package.json"));
const { createJiti } = require("jiti");
const jiti = createJiti(import.meta.url, { interopDefault: true });
const load = (relative) => jiti.import(path.join(subagents, "src", relative));
const { createSubagentExecutor } = await load(
  "runs/foreground/subagent-executor.ts",
);
const { setChildSessionFactory, setChildSessionFactoryModule } = await load(
  "runs/shared/child-session.ts",
);
const { registerWorkflowResource } = await load("api/workflow-resources.ts");
const { createChildSafeState } = await load("extension/fanout-child.ts");

const events = new EventEmitter();
const pi = {
  events: {
    on(name, handler) {
      events.on(name, handler);
      return () => events.off(name, handler);
    },
    emit(name, value) {
      events.emit(name, value);
    },
  },
  on() {},
  registerTool() {},
  sendMessage() {},
  appendEntry() {},
  getActiveTools() {
    return [];
  },
  getAllTools() {
    return [];
  },
  getThinkingLevel() {
    return "off";
  },
  getSessionName() {
    return "fixture-parent";
  },
};
const sessionId = "fixture-session-id";
const sessionFile =
  scenario === "session-file" ? path.join(root, "parent.jsonl") : undefined;
if (sessionFile)
  fs.writeFileSync(
    sessionFile,
    JSON.stringify({
      type: "session",
      version: 3,
      id: sessionId,
      cwd: root,
      timestamp: new Date().toISOString(),
    }) + "\n",
  );
const nativeSessionId = sessionFile ?? sessionId;
const ctx = {
  cwd: root,
  hasUI: false,
  mode: "print",
  isIdle: () => true,
  sessionManager: {
    getSessionId: () => sessionId,
    getSessionFile: () => sessionFile,
    getLeafId: () => undefined,
    getBranch: () => [],
    getEntries: () => [],
    getHeader: () => ({ id: sessionId, cwd: root }),
  },
  modelRegistry: { getAvailable: () => [] },
  ui: { notify() {}, setStatus() {}, setWidget() {} },
};
const agent = {
  name: "fixture-reviewer",
  description: "Deterministic model-execution seam",
  systemPrompt: "Fixture only",
  source: "runtime",
  tools: [],
  extensions: [],
  systemPromptMode: "replace",
  inheritProjectContext: false,
  inheritGlobalContext: false,
  inheritSkills: false,
  defaultContext: "fresh",
  completionGuard: false,
  ...(scenario === "async-child" ? { defaultAsync: true } : {}),
};
let modelCalls = 0;
setChildSessionFactory(
  modelFixture({
    onCreate() {
      modelCalls++;
    },
    interrupt() {
      const control = [...state.foregroundControls.values()].find(
        (value) => value.workflowKey === "review-0",
      );
      assert(control?.interrupt?.(), "native interrupt control unavailable");
    },
  }),
);
if (scenario === "async-child")
  setChildSessionFactoryModule(
    path.join(
      path.dirname(fileURLToPath(import.meta.url)),
      "native_model_fixture.mjs",
    ),
  );
const state = createChildSafeState();
state.currentSessionId = nativeSessionId;
const executor = createSubagentExecutor({
  pi,
  state,
  config: {
    missions: { enabled: false },
    maxSubagentSpawnsPerRun: 100,
    maxSubagentDepth: 2,
    artifactDir: "session",
    artifacts: { enabled: true, includeMetadata: true },
    intercomBridge: { mode: "off" },
  },
  asyncByDefault: false,
  tempArtifactsDir: path.join(root, "artifacts"),
  getSubagentSessionRoot: () => path.join(root, "sessions"),
  expandTilde: (value) => value,
  discoverAgents: () => ({ agents: [agent] }),
});
const quote = (value) => "'" + value.replaceAll("'", "'\\''") + "'";
const gate = path.join(root, "gate.py");
fs.writeFileSync(
  gate,
  `import json,sys,pathlib
sys.path.insert(0,${JSON.stringify(path.join(candidate, "src"))})
from concorde.harness.native_result import NativeResultGate
from concorde.spec.typed_data import canonical
root=pathlib.Path(${JSON.stringify(root)})
i=sys.argv[1]
value=json.loads((root/('raw-proposal-'+i+'.json')).read_text())
assert not (root/('invalid-proposal-'+i)).exists(), 'proposal capture invalidated'
def validate(value):
 if value['verdict']!='valid': raise ValueError('schema-valid but business-invalid proposal')
def no_commit(value): raise AssertionError('a gate cannot commit')
gate=NativeResultGate('invocation-'+i,root/('staged-proposal-'+i+'.json'),ticket='fixture-ticket',recheck=lambda:None,validate=validate,persist=no_commit,verify_execution=lambda:None)
gate.submit('invocation-'+i,value)
control=canonical(gate.stage('invocation-'+i))
if ${JSON.stringify(scenario)}=='gate-mixed-output': print('not control JSON')
if ${JSON.stringify(scenario)}=='gate-truncated-output': print('x'*14000)
print(control)
`,
);

const python = path.join(candidate, ".venv/bin/python");
const gatePrefix = quote(python) + " " + quote(gate);
const check = path.join(root, "check.py");
fs.writeFileSync(
  check,
  `import json,pathlib,sys,time\nsys.path.insert(0,${JSON.stringify(path.join(candidate, "src"))})\nfrom concorde.harness.native_evidence import NativeChildEvidence,verify_native_children\nfrom concorde.harness.native_runtime import admit_native_runtime\nfrom concorde.spec.repository import digest\nroot=pathlib.Path(${JSON.stringify(root)})\nfor _ in range(500):\n if (root/'binding.json').is_file(): break\n time.sleep(.01)\nb=json.loads((root/'binding.json').read_text())\nchildren=tuple(NativeChildEvidence('review-'+str(i),'fixture-reviewer','invocation-'+str(i),digest({'invocation_id':'invocation-'+str(i),'verdict':'valid'}),${JSON.stringify(gatePrefix)}+' '+str(i)) for i in range(${count}))\nif ${JSON.stringify(scenario)}=='malformed-metadata':\n s=json.loads((pathlib.Path(b['asyncDir'])/'status.json').read_text())\n p=pathlib.Path(s['workflow']['emits'][0]['metadata'])\n m=json.loads(p.read_text());m['acceptance']=[];p.write_text(json.dumps(m))\nif ${JSON.stringify(scenario)}=='cancel-before-commit':\n (root/'final-barrier').write_text('before')\n time.sleep(60)\ntry:\n records=verify_native_children(pathlib.Path(b['asyncDir']),run_id=b['runId'],session_id=${JSON.stringify(nativeSessionId)},ticket='fixture-ticket',children=children,runtime=admit_native_runtime(pathlib.Path(${JSON.stringify(subagents)})))\nexcept Exception as error:\n (root/'rejected.json').write_text(json.dumps({'error':str(error)}))\n raise\nreport={'children':len(records),'nativeStatus':json.loads((pathlib.Path(b['asyncDir'])/'status.json').read_text()),'metadata':records}\n(root/'verified.json').write_text(json.dumps(report))\nif ${JSON.stringify(scenario)}=='cancel-after-commit':\n import os\n with (root/'commit.tmp').open('w') as stream:\n  stream.write(json.dumps({'domain':'committed','run_id':b['runId']}));stream.flush();os.fsync(stream.fileno())\n os.replace(root/'commit.tmp',root/'committed.json')\n descriptor=os.open(root,os.O_RDONLY);os.fsync(descriptor);os.close(descriptor)\n (root/'final-barrier').write_text('after')\n time.sleep(60)\nprint(json.dumps({'verified':len(records)}))\n`,
);
const command = quote(python) + " " + quote(check);
const bindScript = path.join(root, "bind.py");
fs.writeFileSync(
  bindScript,
  `import pathlib,time,json\nr=pathlib.Path(${JSON.stringify(root)})\n(r/'bind-started').write_text('waiting')\nfor _ in range(500):\n if (r/'binding.json').is_file(): break\n time.sleep(.01)\nb=json.loads((r/'binding.json').read_text())\ns=json.loads((pathlib.Path(b['asyncDir'])/'status.json').read_text())\nassert s['runId']==b['runId'] and s['sessionId']==${JSON.stringify(nativeSessionId)}\nprint(json.dumps({'bound':True}))\n`,
);
const bindCommand = quote(python) + " " + quote(bindScript);
const registration = registerWorkflowResource({
  sessionId,
  definition: {
    name: "concorde.fixture-publication",
    version: 1,
    resolve() {
      return {
        hostCommands: [
          { key: "bind", command: bindCommand },
          { key: "finalize", command },
        ],
        script: `
    await runs.host("bind", { kind: "command", command: ${JSON.stringify(bindCommand)}, timeoutMs: 10000 });
    for (let i = 0; i < ${count}; i++) {
      const child = await runs.run("review-" + i, { agent: "fixture-reviewer", task: "Fixture " + i, ...${scenario === "async-child" ? "{}" : "{ async: false }"}, extensionBindings: { "concorde-fixture/1": { token: "fixture-token" } }, context: "fresh", intercomBridge: { mode: "off" }, agentContract: { version: 1 }, outputSchema: { type: "object", properties: { invocation_id: { const: "invocation-"+i }, verdict: { enum: ["valid","invalid"] } }, required: ["invocation_id","verdict"], additionalProperties: false }, gate: { command: ${JSON.stringify(gatePrefix)} + " " + i } });
      if (!child.ok || child.detached || child.interrupted || child.stopped || child.terminalOutcome || child.results.length !== 1 || child.results.some(row => row.exitCode !== 0 || row.metadataSaveError || row.outputSaveError || row.transcriptError || row.error)) throw new Error("native child not complete: " + JSON.stringify(child));
      const acceptance = child.results[0].acceptance;
      if (acceptance?.status !== "verified" || acceptance.verifyRuns.length !== 1 || acceptance.verifyRuns[0].status !== "passed") throw new Error("Host staging gate failed");
      const raw = acceptance.verifyRuns[0].stdout;
      if (typeof raw !== "string" || raw.length > 8000 || /[^\\x00-\\x7f]/.test(raw)) throw new Error("Missing or oversized Host control");
      const staged = JSON.parse(raw);
      const fields = ["accepted","invocation_id","proposal_digest","schema_version","state","ticket"];
      if (JSON.stringify(Object.keys(staged).sort()) !== JSON.stringify(fields) || staged.schema_version !== 1 || staged.ticket !== "fixture-ticket" || staged.invocation_id !== "invocation-"+i || staged.state !== "staged" || staged.accepted !== false || !/^sha256:[0-9a-f]{64}$/.test(staged.proposal_digest)) throw new Error("Foreign Host control");
      // All fixture control values are ASCII. Canonical matching also rejects
      // duplicate fields and any non-document or truncated stdout.
      if (JSON.stringify(staged, fields) !== raw.trim()) throw new Error("Noncanonical Host control");
      if (child.structuredOutput.verdict !== "valid") throw new Error("Model proposal is not the Host control DTO");
      emit({ kind: "concorde.child-terminal", ticket: "fixture-ticket", key: child.key, runId: child.runId, invocation_id: staged.invocation_id, proposal_digest: staged.proposal_digest, metadata: child.results[0].artifactPaths.metadataPath });
    }
    return await runs.host("finalize", { kind: "command", command: ${JSON.stringify(command)}, timeoutMs: 10000 });
  `,
      };
    },
  },
});
try {
  const response = await executor.executePublic(
    "fixture-tool-call",
    {
      workflow: "concorde.fixture-publication",
      args: {},
      async: true,
      mission: false,
      cwd: root,
      sessionDir: path.join(root, "sessions"),
    },
    new AbortController().signal,
    undefined,
    ctx,
  );
  fs.writeFileSync(path.join(root, "launch.json"), JSON.stringify(response));
  assert(!response.isError, JSON.stringify(response));
  const binding = {
    asyncDir: response.details.asyncDir,
    runId: response.details.runId ?? response.details.asyncId,
  };
  assert(binding.asyncDir && binding.runId, JSON.stringify(response));
  // Deliberately let the first real Host command reach its wait before the Pi
  // facade delivers the launch tool_result. No early binding is assumed.
  const bindDeadline = Date.now() + 5000;
  while (
    !fs.existsSync(path.join(root, "bind-started")) &&
    Date.now() < bindDeadline
  )
    await new Promise((resolve) => setTimeout(resolve, 10));
  assert(
    fs.existsSync(path.join(root, "bind-started")),
    "initial Host step did not start",
  );
  assert.equal(modelCalls, 0, "model advanced before native run binding");
  if (scenario !== "missing-binding")
    fs.writeFileSync(path.join(root, "binding.json"), JSON.stringify(binding));
  if (scenario.startsWith("cancel-")) {
    const barrierDeadline = Date.now() + 5000;
    while (
      !fs.existsSync(path.join(root, "final-barrier")) &&
      Date.now() < barrierDeadline
    )
      await new Promise((resolve) => setTimeout(resolve, 10));
    assert(
      fs.existsSync(path.join(root, "final-barrier")),
      "finalization barrier not reached",
    );
    const stopped = await executor.executePublic(
      "fixture-stop",
      { action: "stop", id: binding.runId },
      new AbortController().signal,
      undefined,
      ctx,
    );
    assert(!stopped.isError, JSON.stringify(stopped));
  }
  const deadline = Date.now() + 180000;
  let status;
  while (Date.now() < deadline) {
    status = JSON.parse(
      fs.readFileSync(path.join(binding.asyncDir, "status.json"), "utf8"),
    );
    if (!["queued", "running"].includes(status.state)) break;
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
  fs.writeFileSync(path.join(root, "terminal.json"), JSON.stringify(status));
  if (scenario.startsWith("cancel-")) {
    assert.equal(status.state, "stopped", JSON.stringify(status));
    assert.equal(
      fs.existsSync(path.join(root, "committed.json")),
      scenario === "cancel-after-commit",
    );
    if (scenario === "cancel-before-commit")
      assert(!fs.existsSync(path.join(root, "verified.json")));
    console.log(
      JSON.stringify({
        root,
        scenario,
        state: status.state,
        domainCommitted: fs.existsSync(path.join(root, "committed.json")),
      }),
    );
  } else if (
    [
      "failed-child",
      "missing-binding",
      "metadata-write-failure",
      "status-write-failure",
      "malformed-metadata",
      "business-invalid",
      "duplicate-output",
      "gate-mixed-output",
      "gate-truncated-output",
      "interrupted-child",
    ].includes(scenario)
  ) {
    assert.equal(status.state, "failed", JSON.stringify(status));
    assert(
      !fs.existsSync(path.join(root, "verified.json")),
      "failed child became accepted",
    );
    if (
      [
        "failed-child",
        "business-invalid",
        "gate-mixed-output",
        "gate-truncated-output",
        "duplicate-output",
      ].includes(scenario)
    ) {
      assert.equal(modelCalls, 1, "dependent child launched after failure");
      const files = fs
        .readdirSync(path.join(root, "native-tmp/artifacts"), {
          recursive: true,
        })
        .filter((x) => x.endsWith("_meta.json"));
      assert.equal(files.length, 1);
      const metadata = JSON.parse(
        fs.readFileSync(
          path.join(root, "native-tmp/artifacts", files[0]),
          "utf8",
        ),
      );
      assert.equal(metadata.exitCode, scenario === "failed-child" ? 1 : 0);
      assert.equal(
        metadata.acceptance.status,
        ["business-invalid", "duplicate-output"].includes(scenario)
          ? "rejected"
          : "verified",
      );
      if (scenario === "gate-truncated-output")
        assert.equal(metadata.acceptance.verifyRuns[0].stdout.length, 12015);
      if (scenario === "gate-truncated-output")
        assert(
          metadata.acceptance.verifyRuns[0].stdout.endsWith("\n...[truncated]"),
        );
      assert(
        !("structuredOutput" in metadata.acceptance.verifyRuns[0]),
        "a plain gate must not replace the native model proposal",
      );
    }
    console.log(
      JSON.stringify({
        root,
        scenario,
        scriptedForegroundSessions: modelCalls,
        realModelCalls: 0,
        state: status.state,
        accepted: false,
      }),
    );
    process.exitCode = 0;
  } else {
    assert.equal(status.state, "complete", JSON.stringify(status));
    const verified = JSON.parse(
      fs.readFileSync(path.join(root, "verified.json"), "utf8"),
    );
    assert.equal(verified.children, count);
    const scriptedExecutions = fs
      .readFileSync(process.env.CONCORDE_NATIVE_FIXTURE_CALLS, "utf8")
      .trim()
      .split("\n").length;
    assert.equal(scriptedExecutions, count);
    assert(
      verified.metadata.every(
        (record) =>
          record.acceptance.status === "verified" &&
          !record.acceptance.childReport,
      ),
      "no second model-authored acceptance report is required",
    );
    console.log(
      JSON.stringify({
        root,
        scriptedForegroundSessions: modelCalls,
        realModelCalls: 0,
        verified: verified.children,
        stateAtVerification: verified.nativeStatus.state,
        state: status.state,
        scenario,
        scriptedTaskExecutions: fs.existsSync(
          process.env.CONCORDE_NATIVE_FIXTURE_CALLS,
        )
          ? fs
              .readFileSync(process.env.CONCORDE_NATIVE_FIXTURE_CALLS, "utf8")
              .trim()
              .split("\n").length
          : 0,
        rememberedRuns: state.foregroundRuns.size,
      }),
    );
  }
} catch (error) {
  console.error("Fixture artifacts:", root);
  throw error;
} finally {
  hostFs.writeFileSync = writeFile;
  hostFs.renameSync = rename;
  syncBuiltinESMExports();
  registration.dispose();
  setChildSessionFactory(undefined);
  setChildSessionFactoryModule(undefined);
  for (const controller of state.workflowControllers?.values() ?? [])
    controller.abort();
}
