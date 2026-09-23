/** Actual candidate Pi entry + native file-Agent discovery/executor. Only model events are scripted. */
import assert from "node:assert/strict";
import { executeWithSdkValidation } from "./native_sdk_validation.mjs";
import { nativeObservation } from "./native_observation.mjs";
import { exportDiagnostic } from "./structured_diagnostic.mjs";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire, syncBuiltinESMExports } from "node:module";
import { EventEmitter } from "node:events";
import { execFileSync } from "node:child_process";
const [subagents, sdk, candidate, scenario = "needs-decision"] =
  process.argv.slice(2);
const root = fs.mkdtempSync(path.join(os.tmpdir(), "concorde-issue-public-"));
const python = path.join(candidate, ".venv/bin/python");
const observation = nativeObservation(path.join(root, "observation"));
execFileSync(python, [
  "-c",
  `import sys;sys.path.insert(0,${JSON.stringify(candidate + "/src")});sys.path.insert(0,${JSON.stringify(candidate)})
from pathlib import Path
from concorde.operations.catalog import register_types
register_types()
from tests.concorde.spec.support import project
project(Path(${JSON.stringify(root)}))
import json
r=Path(${JSON.stringify(root)})
if ${JSON.stringify(scenario)} in ('shared','many','missing','budget'):
 from tests.concorde.spec.support import add_consumers
 add_consumers(r, 19 if ${JSON.stringify(scenario)}=='many' else 2)
`,
]);
execFileSync(python, [
  "-c",
  `import sys;sys.path.insert(0,${JSON.stringify(candidate + "/src")})
from concorde.operations.catalog import register_types
register_types()
from pathlib import Path
import subprocess,json
from concorde.harness.change_worktree import ensure_change,bind_owner
from concorde.issues.store import report_issue
r=Path(${JSON.stringify(root)})
(r/'app/transfer.py').write_text('def transfer(balance, amount):'+chr(10)+'    if amount <= 0 or amount > balance: raise ValueError("invalid")'+chr(10)+'    return balance - amount'+chr(10))
def git(*args):subprocess.run(['git',*args],cwd=r,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
git('init');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid');git('add','.');git('commit','-m','Fixture');git('worktree','add','-b','issue',str(r/'candidate'))
r=r/'candidate';task={'target_id':'service.transfer','task':'Resolve selected Issue'};ensure_change(r,task=task);bind_owner(r,task)
receipt=report_issue(r,{'report_key':'selected','type':'bug','subtype':None,'title':'Transfer problem','description':'Verify the transfer contract','impact':'Selected behavior','basis':'Contract','owner_target_id':'service.transfer','evidence':[]},{'invocation_id':'fixture','agent':'host','operation':'concorde-issues','phase':'report','target_id':'service.transfer','context_id':'sha256:'+'a'*64,'change_id':None,'head':None})
(r/'selected.json').write_text(json.dumps(receipt))
if ${JSON.stringify(scenario)} in ('duplicate','stale-duplicate'):
 other=report_issue(r,{'report_key':'duplicate','type':'bug','subtype':None,'title':'Transfer problem','description':'Another transfer observation','impact':'Selected behavior','basis':'Contract','owner_target_id':'service.transfer','evidence':[]},{'invocation_id':'other','agent':'host','operation':'concorde-issues','phase':'report','target_id':'service.transfer','context_id':'sha256:'+'b'*64,'change_id':None,'head':None})
 (r/'duplicate.json').write_text(json.dumps(other))
if ${JSON.stringify(scenario)}=='final-failure':
 (r/'checks/transfer_check.py').write_text('raise AssertionError("fixture final check failure")'+chr(10))
# Only a committed Issue can be solved.
subprocess.run(['git','add','.concorde/issues'],cwd=r,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['git','commit','-m','Issues'],cwd=r,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

`,
]);
process.env.PI_CODING_AGENT_DIR = path.join(root, "operator-agent");
process.env.PI_SUBAGENTS_TEMP_ROOT = path.join(root, "native");
process.env.PI_SUBAGENTS_LLM_INTENT_ARBITER = "0";
process.env.PI_SUBAGENTS_PI_CODING_AGENT_PACKAGE_ROOT = sdk;
process.env.CONCORDE_NATIVE_SUBAGENTS_ROOT = subagents;
process.env.CONCORDE_NATIVE_PROJECT_ROOT = path.join(root, "candidate");
process.env.CONCORDE_SESSION_SELECTION = path.join(
  candidate,
  ".concorde/work/pi-first-context-selection.json",
);
// Guard every real Python command, including native gates. No Graph import or hidden worker.
if (scenario === "missing") {
  const hostFs = createRequire(import.meta.url)("node:fs"),
    write = hostFs.writeFileSync;
  hostFs.writeFileSync = function (file, ...args) {
    if (String(file).startsWith(root) && String(file).endsWith("_meta.json"))
      throw Object.assign(
        new Error("fixture native metadata publication failure"),
        { code: "EIO" },
      );
    return write.call(this, file, ...args);
  };
  syncBuiltinESMExports();
}
const guard = path.join(root, "guard");
fs.mkdirSync(guard);
fs.writeFileSync(
  path.join(guard, "sitecustomize.py"),
  `import builtins
original=builtins.__import__
def guarded(name,*args,**kwargs):
 if name=='langgraph' or name.startswith('langgraph.'): raise AssertionError('Native path imported LangGraph')
 return original(name,*args,**kwargs)
builtins.__import__=guarded

import os,json
from pathlib import Path
scenario=os.environ.get('CONCORDE_ISSUE_FAULT')
if scenario in {'slot-change','missing-slot','call-mismatch'}:
 from concorde.issue_solving import native
 original_issue=native._issue
 def injected(driver,layout,key,*args,**kwargs):
  value=original_issue(driver,layout,key,*args,**kwargs)
  if key=='d-0':
   f=Path(driver.directory)/'bindings/d-0.json';v=json.loads(f.read_text())
   if scenario=='slot-change': Path(v['descriptor']).write_text(Path(v['descriptor']).read_text()+' ')
   elif scenario=='missing-slot': Path(v['descriptor']).unlink()
   else: v['call']['task']='foreign task';f.write_text(json.dumps(v))
  return value
 native._issue=injected
if scenario in {'control-extra','control-large'}:
 from concorde.issue_solving import native
 real_step=native.IssuesWorkflowHook.step
 def bad_control(self,run,driver,name):
  value=real_step(self,run,driver,name)
  if name=='next-0':value['foreign']='x'*(5000 if scenario=='control-large' else 1)
  return value
 native.IssuesWorkflowHook.step=bad_control
if scenario=='journal':
 from concorde.issue_solving.solve import IssueSolve
 real=IssueSolve.ready
 def interrupted(self,state):
  marker=self.root/'journal-interrupted'
  if not marker.exists():marker.write_text('once');raise KeyboardInterrupt('fixture interrupted after closing write')
  return real(self,state)
 IssueSolve.ready=interrupted
`,
);
process.env.CONCORDE_ISSUE_FAULT = scenario;
process.env.PYTHONPATH = guard + path.delimiter + path.join(candidate, "src");
process.chdir(root);
const require = createRequire(path.join(sdk, "package.json"));
const { createJiti } = require("jiti");
const jiti = createJiti(import.meta.url, { interopDefault: true });
const load = (relative) => jiti.import(path.join(subagents, "src", relative));
const { createSubagentExecutor } = await load(
  "runs/foreground/subagent-executor.ts",
);
const { setChildSessionFactory } = await load("runs/shared/child-session.ts");
const { createChildSafeState } = await load("extension/fanout-child.ts");
const { discoverAgents } = await load("agents/agents.ts");
const handlers = new Map(),
  tools = new Map(),
  bus = new EventEmitter();
const pi = {
  on(name, handler) {
    const list = handlers.get(name) ?? [];
    list.push(handler);
    handlers.set(name, list);
  },
  registerTool(tool) {
    tools.set(tool.name, tool);
  },
  events: {
    on(name, fn) {
      bus.on(name, fn);
      return () => bus.off(name, fn);
    },
    emit(name, value) {
      bus.emit(name, value);
    },
  },
  appendEntry() {},
  sendMessage() {},
  getActiveTools: () => [...tools.keys()],
  getAllTools: () => [...tools.values()],
  getThinkingLevel: () => "off",
  getSessionName: () => "native-context-fixture",
};
const session = "context-fixture-parent";
const ctx = {
  cwd: root,
  hasUI: false,
  mode: "print",
  isIdle: () => true,
  sessionManager: {
    getSessionId: () => session,
    getSessionFile: () => undefined,
    getLeafId: () => undefined,
    getBranch: () => [],
    getEntries: () => [],
    getHeader: () => ({ id: session, cwd: root }),
  },
  modelRegistry: {
    getAvailable: () => [],
    getRegisteredProviderIds: () => [],
    getRegisteredProviderConfig: () => undefined,
    getRegisteredNativeProvider: () => undefined,
  },
  ui: { notify() {}, setStatus() {}, setWidget() {} },
};
const emit = async (name, event) => {
  for (const handler of handlers.get(name) ?? []) {
    const value = await handler(event, ctx);
    if (value) Object.assign(event, value);
  }
  return event;
};
const entry = await jiti.import(
  path.join(candidate, "generated/session/pi/concorde-session.ts"),
);
entry.default(pi);
await emit("session_start", {});
if (scenario === "preflight-gap") {
  const file = path.join(root, "specs/transfer/module.md.json");
  const value = JSON.parse(fs.readFileSync(file, "utf8"));
  value.dependencies = [];
  fs.writeFileSync(file, JSON.stringify(value));
}
const preparedTool = await tools.get("concorde").execute(
  "prepare",
  {
    operation: "concorde-issues",
    action: "run",
    input: {
      target_id: "service.transfer",
      action: "solve",
      issue_id: JSON.parse(
        fs.readFileSync(path.join(root, "candidate/selected.json"), "utf8"),
      ).issue_id,
      task: "Resolve selected Issue",
    },
    ...(scenario === "describe" ? { mode: "describe-policy" } : {}),
  },
  undefined,
  undefined,
  ctx,
);
const prepared = preparedTool.details;
fs.writeFileSync(path.join(root, "prepared.json"), JSON.stringify(prepared));
if (scenario === "describe") {
  assert.equal(prepared.state, "described", JSON.stringify(prepared));
  assert.equal(prepared.call, undefined);
  console.log(
    JSON.stringify({ scenario, root, realModelCalls: 0, scriptedCalls: 0 }),
  );
  process.exit(0);
}
if (scenario === "preflight-gap") {
  assert.equal(prepared.state, "not-run", JSON.stringify(prepared));
  assert.equal(prepared.result.output.data.outcome, "spec_incomplete");
  assert.equal(prepared.call, undefined);
  console.log(
    JSON.stringify({ scenario, root, realModelCalls: 0, scriptedCalls: 0 }),
  );
  process.exit(0);
}
assert.equal(prepared.state, "prepared", JSON.stringify(prepared));
const call = prepared.call;
const state = createChildSafeState();
state.currentSessionId = session;
let scriptedCalls = 0;
const { createDefaultChildSessionFactory } = await load(
  "runs/shared/child-session.ts",
);
const inspectionFactory = createDefaultChildSessionFactory({
  loadPiCodingAgent: async () =>
    observation.sdk(await jiti.import(path.join(sdk, "dist/index.js"))),
});
setChildSessionFactory({
  async create(launch) {
    scriptedCalls++;
    if (["prose-only", "observe-resolved"].includes(scenario)) {
      const inspected = await inspectionFactory.create(launch);
      observation.refresh();
      await inspected.dispose();
    }
    const slot = JSON.parse(
      fs.readFileSync(
        path.join(path.dirname(launch.cwd), "descriptor.json"),
        "utf8",
      ),
    );
    assert.equal(launch.ambientExtensions, false);
    assert.equal(launch.noSkills, true);
    assert.equal(launch.noContextFiles, true);
    assert(
      !launch.tools.some((t) =>
        ["bash", "write", "edit", "subagent", "concorde"].includes(t),
      ),
    );
    const childTools = new Map(),
      childHandlers = new Map();
    const childPi = {
      ...pi,
      on(name, handler) {
        const list = childHandlers.get(name) ?? [];
        list.push(handler);
        childHandlers.set(name, list);
      },
      registerTool(tool) {
        childTools.set(tool.name, tool);
      },
      getActiveTools: () => [...childTools.keys()],
      getAllTools: () => [...childTools.values()],
    };
    for (const extension of launch.extensionPaths) {
      const module = await jiti.import(extension);
      module.default(childPi);
    }
    for (const hook of launch.hooks) hook.factory(childPi);
    const listeners = new Set(),
      messages = [];
    const send = (event) => {
      for (const fn of listeners) fn(event);
    };
    observation.observeSession(
      {
        sessionId: "scripted-" + scriptedCalls,
        getAllTools: () => [...childTools.values()],
        getActiveToolNames: () => [...childTools.keys()],
        get systemPrompt() {
          return launch.systemPrompt ?? "";
        },
        subscribe(fn) {
          listeners.add(fn);
        },
      },
      { cwd: launch.cwd, origin: "scripted-factory" },
    );
    return {
      messages,
      sessionId: "scripted-child",
      sessionFile:
        launch.storage.kind === "file" ? launch.storage.sessionFile : undefined,
      modelId: "fixture/model",
      subscribe(fn) {
        listeners.add(fn);
        return () => listeners.delete(fn);
      },
      async prompt() {
        if (scenario === "prose-only") {
          const message = {
            role: "assistant",
            content: [
              {
                type: "text",
                text: "Decision: verify. Request fresh reviews.",
              },
            ],
            stopReason: "stop",
            provider: "fixture",
            model: "model",
            usage: { input: 1, output: 1, totalTokens: 2, cost: { total: 0 } },
            timestamp: Date.now(),
          };
          messages.push(message);
          send({ type: "agent_start" });
          send({ type: "message_end", message });
          send({ type: "agent_end", messages });
          send({ type: "agent_settled" });
          return;
        }
        const index = JSON.parse(
          fs.readFileSync(path.join(launch.cwd, "context.json"), "utf8"),
        );
        const snapshot = index.snapshot?.data ?? index;
        let data, type;
        if (slot.phase === "issue-solve") {
          type = "concorde-agent-stage-result";
          const selection = snapshot.stage_inputs[0].data;
          const action = [
            "resolved",
            "observe-resolved",
            "final-failure",
            "incomplete-review",
            "many",
            "journal",
            "review-native-failure",
            "review-cancel",
            "budget",
          ].includes(scenario)
            ? selection.verification
              ? "resolved"
              : "verify"
            : scenario === "exhaustion"
              ? "verify"
              : scenario === "stale-duplicate"
                ? "duplicate"
                : [
                      "stale-issue",
                      "stale-input",
                      "native-failure",
                      "diagnostic-attempts",
                      "schema-correction",
                      "retained-invalid-1",
                      "retained-invalid-2",
                      "missing",
                      "cancel",
                      "slot-change",
                      "missing-slot",
                      "call-mismatch",
                    ].includes(scenario)
                  ? "needs-decision"
                  : scenario;
          data = {
            context_id: snapshot.context_id,
            outcome: "completed",
            answer: "Scripted Issue decision",
            blockers: [],
            documents: [],
            plan: "",
            tasks: [],
            issue_decision: {
              action,
              intent: "Resolve selected Issue",
              rationale: "Scripted evidence judgment",
              duplicate_of:
                action === "duplicate"
                  ? selection.duplicates[0].issue_id
                  : null,
            },
          };
        } else {
          type = "concorde-review-stage-result";
          const info = index.review.data;
          data = {
            context_id: snapshot.context_id,
            input_digest: info.input_digest,
            review_mode: info.review_mode,
            status: "no_findings",
            representative_tasks: ["Scripted verification"],
            issues: [],
            answer: "Scripted independent verification",
          };
          if (scenario === "incomplete-review") {
            data.status = "incomplete";
            data.representative_tasks = [];
          }
        }
        if (
          slot.phase === "issue-solve" &&
          ["stale-issue", "stale-duplicate"].includes(scenario)
        ) {
          const receipt = JSON.parse(
            fs.readFileSync(
              path.join(
                slot.project_root,
                scenario === "stale-issue" ? "selected.json" : "duplicate.json",
              ),
              "utf8",
            ),
          );
          fs.appendFileSync(path.join(slot.project_root, receipt.path), "\n");
        }
        if (slot.phase === "issue-solve" && scenario === "stale-input")
          fs.appendFileSync(
            path.join(slot.project_root, "specs/transfer/module.md"),
            "\nChanged contract\n",
          );
        const value = {
          invocation_id: slot.ticket,
          result: {
            type_id: type,
            schema_version:
              slot.launch.outputSchema.properties.result.properties
                .schema_version.const,
            data,
          },
        };
        if (
          [
            "diagnostic-attempts",
            "schema-correction",
            "retained-invalid-1",
            "retained-invalid-2",
          ].includes(scenario)
        ) {
          const schemaInvalid = structuredClone(value);
          delete schemaInvalid.result.data.documents;
          const businessInvalid = structuredClone(value);
          businessInvalid.result.data.context_id = "sha256:" + "f".repeat(64);
          const values = scenario.startsWith("retained-invalid-")
            ? [
                JSON.parse(
                  fs.readFileSync(
                    new URL(
                      "./fixtures/issue-sdk-rejections.json",
                      import.meta.url,
                    ),
                    "utf8",
                  ),
                ).invalid_arguments[Number(scenario.at(-1)) - 1].value,
              ]
            : scenario === "diagnostic-attempts"
              ? [schemaInvalid, businessInvalid, value]
              : [schemaInvalid, value];
          // Rebind only this test's issued ticket. The preserved model result.data is not repaired.
          if (scenario.startsWith("retained-invalid-"))
            values[0].invocation_id = slot.ticket;
          send({ type: "agent_start" });
          for (let n = 0; n < values.length; n++) {
            const id = "attempt-" + (n + 1),
              args = { value: values[n] };
            const assistant = {
              role: "assistant",
              content: [
                {
                  type: "toolCall",
                  id,
                  name: "structured_output",
                  arguments: args,
                },
              ],
              api: "fixture",
              provider: "fixture",
              model: "model",
              stopReason: "toolUse",
              timestamp: Date.now(),
              usage: {
                input: 1,
                output: 1,
                totalTokens: 2,
                cost: { total: 0 },
              },
            };
            messages.push(assistant);
            send({ type: "message_end", message: assistant });
            send({
              type: "tool_execution_start",
              toolCallId: id,
              toolName: "structured_output",
              args,
            });
            let result;
            try {
              result = await executeWithSdkValidation(
                sdk,
                childTools.get("structured_output"),
                id,
                args,
              );
            } catch (error) {
              result = {
                isError: true,
                content: [{ type: "text", text: String(error.message) }],
              };
            }
            const event = {
              toolName: "structured_output",
              toolCallId: id,
              input: args,
              content: result.content,
              details: result.details,
              isError: Boolean(result.isError),
            };
            for (const handler of childHandlers.get("tool_result") ?? [])
              Object.assign(event, await handler(event, ctx));
            const toolResult = {
              role: "toolResult",
              toolCallId: id,
              toolName: "structured_output",
              content: event.content,
              isError: event.isError,
              timestamp: Date.now(),
            };
            messages.push(toolResult);
            send({ type: "message_end", message: toolResult });
            send({
              type: "tool_execution_end",
              toolCallId: id,
              toolName: "structured_output",
              isError: event.isError,
            });
          }
          send({ type: "agent_end", messages });
          send({ type: "agent_settled" });
          return;
        }
        const args = { value };
        const message = {
          role: "assistant",
          content: [
            {
              type: "toolCall",
              id: "structured-1",
              name: "structured_output",
              arguments: args,
            },
          ],
          api: "fixture",
          provider: "fixture",
          model: "model",
          stopReason: "toolUse",
          timestamp: Date.now(),
          usage: {
            input: 1,
            output: 1,
            cacheRead: 0,
            cacheWrite: 0,
            totalTokens: 2,
            cost: {
              input: 0,
              output: 0,
              cacheRead: 0,
              cacheWrite: 0,
              total: 0,
            },
          },
        };
        messages.push(message);
        send({ type: "agent_start" });
        send({ type: "message_end", message });
        send({
          type: "tool_execution_start",
          toolCallId: "structured-1",
          toolName: "structured_output",
          args,
        });
        const result = await executeWithSdkValidation(
          sdk,
          childTools.get("structured_output"),
          "structured-1",
          args,
        );
        const event = {
          toolName: "structured_output",
          input: args,
          content: result.content,
          details: result.details,
          isError: Boolean(result.isError),
        };
        for (const handler of childHandlers.get("tool_result") ?? [])
          Object.assign(event, await handler(event, ctx));
        messages.push({
          role: "toolResult",
          toolCallId: "structured-1",
          toolName: "structured_output",
          ...result,
          isError: event.isError,
          timestamp: Date.now(),
        });
        send({ type: "message_end", message: messages.at(-1) });
        send({
          type: "tool_execution_end",
          toolCallId: "structured-1",
          toolName: "structured_output",
          result,
          isError: event.isError,
        });
        if (scenario === "proposal-tamper") {
          const file = path.join(path.dirname(call.cwd), "proposal.json");
          const altered = JSON.parse(fs.readFileSync(file, "utf8"));
          altered.result.data.answer = "Changed captured proposal";
          fs.writeFileSync(file, JSON.stringify(altered));
        }
        if (
          scenario === "cancel" ||
          (scenario === "review-cancel" && slot.phase !== "issue-solve")
        ) {
          const control = [...state.foregroundControls.values()][0];
          assert(control.interrupt());
        }
        send({ type: "agent_end", messages });
        if (
          ["native-failure", "proposal-tamper"].includes(scenario) ||
          (scenario === "review-native-failure" && slot.phase !== "issue-solve")
        )
          throw new Error("Scripted native execution failure after proposal");
        send({ type: "agent_settled" });
      },
      async abort() {},
      async dispose() {},
      async steer() {},
      async followUp() {},
    };
  },
  async dispose() {},
});
const executor = createSubagentExecutor({
  pi,
  state,
  config: {
    missions: { enabled: false },
    maxSubagentSpawnsPerRun: scenario === "budget" ? 1 : 100,
    maxSubagentDepth: 1,
    artifactDir: "session",
    artifacts: { enabled: true, includeMetadata: true },
    intercomBridge: { mode: "off" },
  },
  asyncByDefault: false,
  tempArtifactsDir: path.join(root, "artifacts"),
  getSubagentSessionRoot: () => path.join(root, "sessions"),
  expandTilde: (value) => value,
  discoverAgents,
});

const toolId = "issue-workflow";
const admitted = await emit("tool_call", {
  toolName: "subagent",
  toolCallId: toolId,
  input: call,
});
assert(!admitted.block, JSON.stringify(admitted));
const response = await executor.executePublic(
  toolId,
  call,
  new AbortController().signal,
  undefined,
  ctx,
);
assert(!response.isError, JSON.stringify(response));
await emit("tool_result", {
  toolName: "subagent",
  toolCallId: toolId,
  input: call,
  ...response,
});
let final;
for (let i = 0; i < 2400; i++) {
  final = (
    await tools
      .get("concorde")
      .execute(
        "result",
        { operation: "concorde-issues", action: "result" },
        undefined,
        undefined,
        ctx,
      )
  ).details;
  if (final.native_state !== "running") break;
  await new Promise((r) => setTimeout(r, 100));
}
fs.writeFileSync(path.join(root, "final.json"), JSON.stringify(final));
observation.refresh();
const observationSummary = observation.collect(prepared.descriptor, {
  artifactRoots: [path.join(root, "native/artifacts")],
});
const diagnostic = JSON.parse(
  fs.readFileSync(
    path.join(root, "observation/child-0-structured.json"),
    "utf8",
  ),
);
const evidence =
  process.env.CONCORDE_DIAGNOSTIC_REPORT === "1"
    ? exportDiagnostic(diagnostic)
    : null;
if (scenario === "diagnostic-attempts") {
  const a = diagnostic.attempts;
  assert.equal(a.length, 3);
  assert(a.every((x) => x.argumentsComplete && x.errorComplete && x.isError));
  const schemaFailure = JSON.parse(a[0].resultRecords[0].text);
  assert.equal(schemaFailure.category, "schema-rejection");
  assert.equal(schemaFailure.attempt, "attempt-1");
  assert.match(
    schemaFailure.diagnostics.text,
    /Validation failed for tool "structured_output"/,
  );
  assert.match(schemaFailure.diagnostics.text, /documents/);
  const hostFailure = JSON.parse(a[1].resultRecords[0].text);
  assert.equal(hostFailure.attempt, "attempt-2");
  assert.match(JSON.stringify(hostFailure), /incompatible_handoff/);
  assert.match(
    JSON.stringify(hostFailure),
    /agent returned a different context identity/,
  );
  assert.match(a[2].resultRecords[0].text, /duplicate structured submissions/);
  assert(!Object.hasOwn(a[0].arguments.value.result.data, "documents"));
  assert.equal(
    a[1].arguments.value.result.data.context_id,
    "sha256:" + "f".repeat(64),
  );
  assert.notEqual(
    a[2].arguments.value.result.data.context_id,
    a[1].arguments.value.result.data.context_id,
  );
  assert.equal(final.accepted, false);
}
if (
  scenario === "diagnostic-attempts" ||
  scenario.startsWith("retained-invalid-")
)
  execFileSync(python, [
    "-c",
    "from concorde.operations.catalog import register_types;register_types();from pathlib import Path;from concorde.harness.change_worktree import read_change;from concorde.issues.store import read_issue;import json;r=Path(" +
      JSON.stringify(path.join(root, "candidate")) +
      ");s=read_change(r);i=json.loads((r/'selected.json').read_text())['issue_id'];v=s['sections']['issue-solving']['data']['solutions'][i];assert v['attempts']==1 and not v['history'] and not v.get('verification') and not v.get('pending_disposition') and s['status']!='ready';assert read_issue(r,i)[0]['status']=='open'",
  ]);
if (scenario.startsWith("retained-invalid-")) {
  assert.equal(diagnostic.attempts.length, 1);
  const attempt = diagnostic.attempts[0];
  assert(attempt.isError && attempt.errorComplete);
  assert.match(attempt.resultRecords[0].text, /context_id.*outcome/);
  assert(
    !attempt.resultRecords[0].text.includes(
      "value.result.data: schema is false",
    ),
  );
  assert.equal(final.accepted, false);
}
if (scenario === "schema-correction") {
  assert.equal(diagnostic.attempts.length, 2);
  assert.equal(diagnostic.attempts[0].isError, true);
  assert.equal(diagnostic.attempts[1].isError, false);
  assert.equal(final.accepted, true);
}
if (scenario === "prose-only") assert.equal(diagnostic.attempts.length, 0);
if (scenario === "observe-resolved") {
  assert.equal(observationSummary.expectedSlots, 6);
  const fullObservation = JSON.parse(
    fs.readFileSync(path.join(root, "observation/observation.json"), "utf8"),
  );
  assert.equal(fullObservation.children.length, 6);
  for (const child of fullObservation.children) {
    assert(
      child.actualSdkObserved &&
        child.structuredRegistered &&
        child.structuredActive &&
        child.promptRequiresStructuredOutput,
    );
    assert.equal(child.outputSchemaDigest, child.registeredValueSchemaDigest);
  }
}
if (scenario === "prose-only") {
  assert.equal(scriptedCalls, 1);
  assert.equal(observationSummary.executionsObserved, 1);
  assert.equal(observationSummary.successfulEmissions, 0);
  assert.equal(observationSummary.failedChildrenWithMetadata, 1);
  const child = observationSummary.children[0];
  assert(child.actualSdkObserved);
  assert(child.structuredRegistered && child.structuredActive);
  assert(child.promptRequiresStructuredOutput);
  assert.equal(child.outputSchemaDigest, child.registeredValueSchemaDigest);
  execFileSync(python, [
    "-c",
    "from concorde.operations.catalog import register_types;register_types();from pathlib import Path;from concorde.harness.change_worktree import read_change;from concorde.issues.store import read_issue;import json;r=Path(" +
      JSON.stringify(path.join(root, "candidate")) +
      ");s=read_change(r);i=json.loads((r/'selected.json').read_text())['issue_id'];v=s['sections']['issue-solving']['data']['solutions'][i];assert v['attempts']==1 and not v['history'];assert not v.get('verification') and not v.get('pending_disposition') and s['status']!='ready';assert read_issue(r,i)[0]['status']=='open'",
  ]);
}
if (
  [
    "stale-issue",
    "stale-input",
    "stale-duplicate",
    "native-failure",
    "missing",
    "prose-only",
    "diagnostic-attempts",
    "retained-invalid-1",
    "retained-invalid-2",
    "cancel",
    "review-native-failure",
    "review-cancel",
    "budget",
    "slot-change",
    "missing-slot",
    "call-mismatch",
    "journal",
    "control-extra",
    "control-large",
  ].includes(scenario)
)
  assert.equal(final.accepted, false, JSON.stringify(final));
else {
  assert(final.accepted, JSON.stringify(final));
  const expected =
    scenario === "schema-correction"
      ? "needs-decision"
      : ["many", "observe-resolved"].includes(scenario)
        ? "resolved"
        : scenario === "exhaustion"
          ? "limit-exhausted"
          : scenario === "final-failure"
            ? "verification-failed"
            : scenario === "incomplete-review"
              ? "failed"
              : scenario;
  assert.equal(final.output.data.decision, expected, JSON.stringify(final));
  if (scenario === "final-failure" || scenario === "incomplete-review")
    assert.equal(final.output.data.issues[0].status, "open");
  if (
    scenario === "resolved" ||
    scenario === "duplicate" ||
    scenario === "not-actionable"
  )
    assert.equal(final.output.data.issues[0].status, "closed");
}

if (
  [
    "slot-change",
    "missing-slot",
    "call-mismatch",
    "control-extra",
    "control-large",
  ].includes(scenario)
)
  assert.equal(scriptedCalls, 0);
if (scenario === "exhaustion") assert.equal(scriptedCalls, 30);
if (scenario === "many") assert.equal(scriptedCalls, 44);
if (scenario === "journal") {
  const check = execFileSync(
    python,
    [
      "-c",
      "from concorde.operations.catalog import register_types;register_types();from pathlib import Path;from concorde.harness.change_worktree import read_change;from concorde.issue_solving.bookkeeping import pending_disposition;from concorde.issue_solving.records import solutions;r=Path(" +
        JSON.stringify(path.join(root, "candidate")) +
        ");c=read_change(r);i=next(iter(solutions(c)));assert pending_disposition(c,i);print(i)",
    ],
    { encoding: "utf8" },
  ).trim();
  const next = (
    await tools.get("concorde").execute(
      "recover",
      {
        operation: "concorde-issues",
        action: "run",
        input: {
          action: "solve",
          issue_id: check,
          target_id: "service.transfer",
          task: "Resolve selected Issue",
        },
      },
      undefined,
      undefined,
      ctx,
    )
  ).details;
  assert.equal(next.state, "prepared");
  const reopened = execFileSync(
    python,
    [
      "-c",
      "from concorde.operations.catalog import register_types;register_types();from pathlib import Path;from concorde.issues.store import read_issue;print(read_issue(Path(" +
        JSON.stringify(path.join(root, "candidate")) +
        ")," +
        JSON.stringify(check) +
        ")[0]['status'])",
    ],
    { encoding: "utf8" },
  ).trim();
  assert.equal(reopened, "open");
}
const attempts = Number(
  execFileSync(
    python,
    [
      "-c",
      "from concorde.operations.catalog import register_types;register_types();from pathlib import Path;from concorde.harness.change_worktree import read_change;s=read_change(Path(" +
        JSON.stringify(path.join(root, "candidate")) +
        ")).get('sections',{}).get('issue-solving',{}).get('data',{}).get('solutions',{});print(next(iter(s.values()))['attempts'])",
    ],
    { encoding: "utf8" },
  ).trim(),
);
assert(
  attempts >= 1 && attempts <= 6,
  "persisted bounded attempts before launch",
);
if (
  [
    "slot-change",
    "missing-slot",
    "call-mismatch",
    "control-extra",
    "control-large",
    "budget",
  ].includes(scenario)
)
  assert.equal(attempts, 1);
if (scenario === "exhaustion") assert.equal(attempts, 6);
await inspectionFactory.dispose();
await emit("session_shutdown", {});
if (process.env.CONCORDE_DIAGNOSTIC_REPORT === "1")
  console.log(JSON.stringify(evidence));
else
  console.log(
    JSON.stringify({
      scenario,
      root,
      scriptedCalls,
      realModelCalls: 0,
      accepted: final.accepted,
      observation: path.join(root, "observation/summary.json"),
      diagnostic: path.join(root, "observation/child-0-structured.json"),
      outcome: final.output?.data.outcome,
    }),
  );
