/** Actual candidate Pi entry + native file-Agent discovery/executor. Only model events are scripted. */
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire, syncBuiltinESMExports } from "node:module";
import { EventEmitter } from "node:events";
import { execFileSync } from "node:child_process";
const [subagents, sdk, candidate, scenario = "clean"] = process.argv.slice(2);
const root = fs.mkdtempSync(path.join(os.tmpdir(), "concorde-review-public-"));
const python = path.join(candidate, ".venv/bin/python");
execFileSync(python, [
  "-c",
  `import sys;sys.path.insert(0,${JSON.stringify(candidate + "/src")});sys.path.insert(0,${JSON.stringify(candidate)})
from pathlib import Path
from tests.concorde.spec.support import project
project(Path(${JSON.stringify(root)}))
import json
r=Path(${JSON.stringify(root)})
if ${JSON.stringify(scenario)} in ('shared','many','missing','budget'):
 registry=json.loads((r/'.concorde/specs.json').read_text())
 template=next(t for t in registry['targets'] if t['id']=='module.ledger')
 for i in range(39 if ${JSON.stringify(scenario)}=='many' else 2):
  name='consumer'+str(i);member=json.loads(json.dumps(template).replace('ledger',name))
  member['references']=[{'kind':'document','id':'document.transfer.promises'}]
  for old,new in zip(template['documents'],member['documents']):
   dest=r/new;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text((r/old).read_text().replace('ledger',name))
   (r/(new+'.json')).write_text((r/(old+'.json')).read_text().replace('ledger',name))
  registry['targets'].append(member)
 (r/'.concorde/specs.json').write_text(json.dumps(registry))
`,
]);
if (scenario.startsWith("code") || scenario === "managed") {
  execFileSync(python, [
    "-c",
    `from pathlib import Path
import sys;sys.path.insert(0,${JSON.stringify(candidate + "/src")})
import json,subprocess
r=Path(${JSON.stringify(root)})
if ${JSON.stringify(scenario)}=='code-shared':
 file=r/'.concorde/specs.json';v=json.loads(file.read_text());next(t for t in v['targets'] if t['id']=='module.ledger')['files']=['app/transfer.py'];file.write_text(json.dumps(v))
 file=r/'specs/ledger/module.md.json';v=json.loads(file.read_text());next(e for e in v['entities'] if e['id']=='entity.ledger.store')['files']=['app/transfer.py'];file.write_text(json.dumps(v))
def git(*a):subprocess.run(['git',*a],cwd=r,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
git('init');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid');git('add','.');git('commit','-m','Fixture');git('worktree','add','-b','review',str(r/'candidate'))
from concorde.harness.change_worktree import ensure_change,bind_owner,read_change,save_change,target_state,save_target_state
r=r/'candidate';task={'target_id':'scope.bank' if ${JSON.stringify(scenario)}=='code-parent' else 'service.transfer','task':'Assess the transfer contract'}
ensure_change(r,task=task);bind_owner(r,task)
file=r/'app/transfer.py';file.write_text(file.read_text()+chr(10)+'# selected change'+chr(10))
if ${JSON.stringify(scenario)}=='code-parent':
 state=target_state(r,'scope.bank',None,create=True);state['tasks']=[{'id':'task.component','target_id':'service.transfer','description':'Implement transfer','acceptance':'Contract holds','complete':True}];state['component_revisions']={'service.transfer':{'spec':'sha256:'+'0'*64,'implementation':'sha256:'+'0'*64}};save_target_state(r,state)
`,
  ]);
}
process.env.PI_CODING_AGENT_DIR = path.join(root, "operator-agent");
process.env.PI_SUBAGENTS_TEMP_ROOT = path.join(root, "native");
process.env.PI_SUBAGENTS_LLM_INTENT_ARBITER = "0";
process.env.PI_SUBAGENTS_PI_CODING_AGENT_PACKAGE_ROOT = sdk;
process.env.CONCORDE_NATIVE_SUBAGENTS_ROOT = subagents;
process.env.CONCORDE_NATIVE_PROJECT_ROOT =
  scenario.startsWith("code") || scenario === "managed"
    ? path.join(root, "candidate")
    : root;
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
from concorde.harness.worker_executor import WorkerExecutor
def forbidden(*a,**k): raise AssertionError('Native path launched a hidden Pi-RPC worker')
WorkerExecutor.__call__=forbidden
`,
);
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
  modelRegistry: { getAvailable: () => [] },
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
    operation: scenario.startsWith("code")
      ? "concorde-code-review"
      : "concorde-spec-review",
    action: "run",
    input: {
      target_id: scenario === "code-parent" ? "scope.bank" : "service.transfer",
      task: "Assess the transfer contract",
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
setChildSessionFactory({
  async create(launch) {
    scriptedCalls++;
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
        const index = JSON.parse(
          fs.readFileSync(path.join(launch.cwd, "context.json"), "utf8"),
        );
        const snapshot = index.snapshot.data,
          info = index.review.data;
        const data = {
          context_id: snapshot.context_id,
          input_digest: info.input_digest,
          review_mode: info.review_mode,
          status: "no_findings",
          representative_tasks: ["Scripted representative transfer task"],
          issues: [],
          answer: "Scripted review; not model judgment",
        };
        if (scenario === "incomplete") {
          data.status = "incomplete";
          data.representative_tasks = [];
        }
        if (scenario === "wrong-context")
          data.context_id = "sha256:" + "0".repeat(64);
        if (scenario === "wrong-mode")
          data.review_mode = info.review_mode === "spec" ? "code" : "spec";
        if (scenario === "coverage") data.representative_tasks = [];
        if (scenario === "advisory" || scenario === "blocking") {
          const reported = await childTools
            .get("report_issue")
            .execute("issue", {
              report: {
                report_key: "scripted-review",
                type: "bug",
                subtype: null,
                title: "Scripted finding",
                description: "A scripted review finding",
                impact: "Scripted impact",
                basis: "Scripted contract evidence",
                owner_target_id: snapshot.target_id,
                evidence: [],
              },
            });
          data.status = "findings";
          data.issues = [
            {
              ...reported.details.receipt,
              severity: scenario === "blocking" ? "blocking" : "advisory",
              affected_task: "Scripted transfer task",
            },
          ];
        }
        if (scenario === "wrong-receipt") {
          data.status = "findings";
          data.issues = [
            {
              issue_id: "I-" + "0".repeat(32),
              report_id: "sha256:" + "0".repeat(64),
              path: ".concorde/issues/foreign.json",
              severity: "blocking",
              affected_task: "Task",
            },
          ];
        }
        if (info.review_mode === "spec")
          assert.equal(snapshot.implementation_artifacts.length, 0);
        else
          for (const item of snapshot.implementation_artifacts)
            assert(fs.existsSync(path.join(launch.cwd, item.path)));
        if (scenario === "shared" || scenario === "many") {
          for (const doc of snapshot.spec_resolution.sources)
            if (doc.owner !== snapshot.target_id)
              assert.equal(doc.owner, "service.transfer");
        }
        const value = {
          invocation_id: slot.ticket,
          result: {
            type_id: "concorde-review-stage-result",
            schema_version:
              slot.launch.outputSchema.properties.result.properties
                .schema_version.const,
            data,
          },
        };
        if (scenario === "stale")
          fs.appendFileSync(
            path.join(slot.project_root, "specs/transfer/module.md"),
            "\nChanged contract\n",
          );
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
        const result = await childTools
          .get("structured_output")
          .execute("structured-1", args);
        const event = {
          toolName: "structured_output",
          input: args,
          content: result.content,
          details: result.details,
          isError: Boolean(result.isError),
        };
        for (const handler of childHandlers.get("tool_result") ?? [])
          Object.assign(event, await handler(event, ctx));
        if (scenario === "duplicate")
          for (const handler of childHandlers.get("tool_result") ?? [])
            Object.assign(
              event,
              await handler({ ...event, isError: false }, ctx),
            );
        messages.push({
          role: "toolResult",
          toolCallId: "structured-1",
          toolName: "structured_output",
          ...result,
          isError: event.isError,
          timestamp: Date.now(),
        });
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
        if (scenario === "cancel") {
          const control = [...state.foregroundControls.values()][0];
          assert(control.interrupt());
        }
        send({ type: "agent_end", messages });
        if (["native-failure", "proposal-tamper"].includes(scenario))
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

const toolId = "review-scope";
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
    await tools.get("concorde").execute(
      "result",
      {
        operation: scenario.startsWith("code")
          ? "concorde-code-review"
          : "concorde-spec-review",
        action: "result",
      },
      undefined,
      undefined,
      ctx,
    )
  ).details;
  if (final.native_state !== "running") break;
  await new Promise((r) => setTimeout(r, 100));
}
fs.writeFileSync(path.join(root, "final.json"), JSON.stringify(final));
const nativeStatus = JSON.parse(
  fs.readFileSync(path.join(response.details.asyncDir, "status.json"), "utf8"),
);
assert(
  new Set(
    nativeStatus.workflow.trace
      .filter((row) => row.operation === "host")
      .map((row) => row.key),
  ).size <= 2,
  "per-reviewer Host commands were added",
);

const negative = [
  "wrong-context",
  "wrong-mode",
  "wrong-receipt",
  "coverage",
  "native-failure",
  "stale",
  "missing",
  "budget",
];
assert.equal(
  final.accepted,
  !negative.includes(scenario),
  JSON.stringify(final),
);
if (final.accepted) {
  const reviews = final.output.data.reviews;
  assert.equal(
    reviews.length,
    scenario === "many"
      ? 40
      : scenario === "shared"
        ? 3
        : scenario === "code-shared"
          ? 2
          : 1,
  );
  assert.equal(
    new Set(reviews.map((v) => v.data.context_id)).size,
    reviews.length,
  );
  if (scenario === "code-parent")
    assert.equal(reviews[0].data.target_id, "service.transfer");
  if (scenario === "code-shared")
    assert.deepEqual(
      new Set(reviews.map((v) => v.data.target_id)),
      new Set(["service.transfer", "module.ledger"]),
    );
  if (scenario.startsWith("code") || scenario === "managed") {
    assert(fs.existsSync(path.join(root, ".concorde/status")));
    assert(!fs.existsSync(path.join(root, "candidate/.concorde/status")));
    assert(!fs.existsSync(path.join(root, "candidate/.concorde/runs")));
  }
  assert.equal(
    final.output.data.outcome,
    scenario === "incomplete"
      ? "failed"
      : scenario === "blocking"
        ? "conflicting"
        : "completed",
  );
}
await emit("session_shutdown", {});
console.log(
  JSON.stringify({
    scenario,
    root,
    scriptedCalls,
    realModelCalls: 0,
    accepted: final.accepted,
  }),
);
