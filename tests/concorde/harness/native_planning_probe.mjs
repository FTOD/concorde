/** Actual candidate Pi entry + native file-Agent discovery/executor. Only model events are scripted. */
import assert from "node:assert/strict";
import { executeWithSdkValidation } from "./native_sdk_validation.mjs";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { EventEmitter } from "node:events";
import { execFileSync } from "node:child_process";
const [subagents, sdk, candidate, scenario = "normal"] = process.argv.slice(2);
const root = fs.mkdtempSync(
  path.join(os.tmpdir(), "concorde-planning-public-"),
);
const python = path.join(candidate, ".venv/bin/python");
execFileSync(python, [
  "-c",
  `import sys;sys.path.insert(0,${JSON.stringify(candidate + "/src")});sys.path.insert(0,${JSON.stringify(candidate)})
from pathlib import Path
from tests.concorde.spec.support import project
project(Path(${JSON.stringify(root)}))
import json
if ${JSON.stringify(scenario)} in ('references','stale-reference'):
 r=Path(${JSON.stringify(root)})
 (r/'reference/lib').mkdir(parents=True);(r/'reference/lib/api.md').write_text('ADMITTED_LIBRARY_API')
 (r/'reference/foreign').mkdir();(r/'reference/foreign/api.md').write_text('UNGRANTED_LIBRARY_API')
 file=r/'.concorde/specs.json';data=json.loads(file.read_text())
 next(t for t in data['targets'] if t['id']=='service.transfer')['references'].append({'kind':'external','path':'reference/lib/'})
 file.write_text(json.dumps(data))
import subprocess
r=Path(${JSON.stringify(root)})
def git(*args): subprocess.run(['git',*args],cwd=r,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
git('init');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid');git('add','.');git('commit','-m','Fixture baseline')
git('worktree','add','-b','native-planning',str(r/'candidate'))
`,
]);
process.env.PI_CODING_AGENT_DIR = path.join(root, "operator-agent");
process.env.PI_SUBAGENTS_TEMP_ROOT = path.join(root, "native");
process.env.PI_SUBAGENTS_LLM_INTENT_ARBITER = "0";
process.env.PI_SUBAGENTS_PI_CODING_AGENT_PACKAGE_ROOT = sdk;
process.env.CONCORDE_NATIVE_SUBAGENTS_ROOT = subagents;
process.env.CONCORDE_NATIVE_PROJECT_ROOT =
  scenario === "primary" ? root : path.join(root, "candidate");
process.env.CONCORDE_SESSION_SELECTION = path.join(
  candidate,
  ".concorde/work/pi-first-context-selection.json",
);
// Guard every real Python command, including native gates. No Graph import or hidden worker.
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
if (
  [
    "empty-plan",
    "stale-spec",
    "stale-metadata",
    "stale-intent",
    "stale-reference",
    "review-required",
    "prior-gap",
  ].includes(scenario)
) {
  const dataRoot = path.join(root, "candidate");
  execFileSync(python, [
    "-c",
    `from pathlib import Path
from concorde.harness.change_worktree import ensure_change,bind_owner,read_change,save_change
from concorde.harness.host import OperationHost
from concorde.harness.invocation import Invocation
from concorde.harness.configuration import load_configuration
from concorde.planning.plan import persist_plan_result
r=Path(${JSON.stringify(dataRoot)})
task={'target_id':'service.transfer','task':'Assess the transfer contract'}
ensure_change(r,task=task);bind_owner(r,task)
run=Invocation('concorde-plan',load_configuration(r),task,OperationHost(r,Path(${JSON.stringify(candidate)})))
persist_plan_result(run,{'plan':'PREVIOUS ACCEPTED PLAN','answer':'Fixture precondition'})
if ${JSON.stringify(scenario)}=='prior-gap':
 from concorde.issues.store import report_issue
 from concorde.harness.change_worktree import record_task_gaps
 from concorde.harness.revisions import target_revision
 from concorde.harness.native_context import assessment_context
 context_id=assessment_context(run)[2].id
 receipt=report_issue(r,{'report_key':'prior-gap','type':'gap','subtype':'missing-contract','title':'Prior promise','description':'Prior missing promise','impact':'Blocked planning','basis':'Fixture prior contract','owner_target_id':'service.transfer','evidence':[]},{'invocation_id':'fixture-prior','agent':'host','operation':'concorde-context-solve','phase':'context-solve','target_id':'service.transfer','context_id':context_id,'change_id':run.change_id,'head':None})
 record_task_gaps(r,'service.transfer',task['task'],'context-solve',[{**receipt,'blocked_step':'Assess contract'}],target_revision(run.repository,run.target),spec_resolution=run.repository.spec_context(run.target.id).value)
 file=r/'specs/transfer/module.md';file.write_text(file.read_text()+chr(10)+'The previously missing promise is now explicit.'+chr(10))
if ${JSON.stringify(scenario)}=='review-required':
 c=read_change(r);c.setdefault('review_requirements',{})['service.transfer']={'spec':True,'code':False};save_change(r,c)
`,
  ]);
}
if (scenario === "review-required") {
  await assert.rejects(
    () =>
      tools.get("concorde").execute(
        "review-required",
        {
          operation: "concorde-plan",
          action: "run",
          input: {
            target_id: "service.transfer",
            task: "Assess the transfer contract",
          },
        },
        undefined,
        undefined,
        ctx,
      ),
    /review_required/,
  );
  console.log(
    JSON.stringify({ scenario, root, scriptedCalls: 0, realModelCalls: 0 }),
  );
  process.exit(0);
}
if (scenario === "missing-plan") {
  await assert.rejects(
    () =>
      tools.get("concorde").execute(
        "missing",
        {
          operation: "concorde-tasks",
          action: "run",
          input: {
            target_id: "service.transfer",
            task: "Assess the transfer contract",
          },
        },
        undefined,
        undefined,
        ctx,
      ),
    /missing_plan/,
  );
  console.log(
    JSON.stringify({ scenario, root, scriptedCalls: 0, realModelCalls: 0 }),
  );
  process.exit(0);
}
const preparedTool = await tools.get("concorde").execute(
  "prepare",
  {
    operation: "concorde-plan",
    action: "run",
    input: {
      target_id: "service.transfer",
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
let scriptedCalls = 0,
  taskCalls = 0,
  planCalls = 0;
setChildSessionFactory({
  async create(launch) {
    scriptedCalls++;
    const slot = JSON.parse(
      fs.readFileSync(
        path.join(path.dirname(launch.cwd), "descriptor.json"),
        "utf8",
      ),
    );
    if (slot.phase === "tasks") taskCalls++;
    if (slot.phase === "plan") planCalls++;
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
        const snapshot = JSON.parse(
          fs.readFileSync(path.join(launch.cwd, "context.json"), "utf8"),
        );
        const data = {
          context_id: snapshot.context_id,
          outcome: slot.phase === "context-solve" ? "sufficient" : "completed",
          answer: "Scripted assessment",
          blockers: [],
          documents: [],
          plan: "",
          tasks: [],
        };
        if (slot.phase === "plan")
          data.plan =
            "Implement the specified transfer behavior, preserving its validation contracts.";
        if (slot.phase === "tasks")
          data.tasks = [
            {
              id: "task.native-1",
              target_id: "service.transfer",
              description: "Implement transfer",
              acceptance:
                "Valid transfer subtracts; invalid amount or insufficient funds raises ValueError.",
              complete: false,
            },
          ];
        if (scenario === "assessor-gap" && slot.phase === "context-solve")
          data.outcome = "unsupported";
        if (scenario === "empty-plan" && slot.phase === "plan") data.plan = "";
        assert.deepEqual(snapshot.implementation_artifacts, []);
        assert(
          !fs.existsSync(path.join(launch.cwd, "app/transfer.py")),
          "project code delivered to read-only planning",
        );
        if (["references", "stale-reference"].includes(scenario)) {
          assert(
            !fs.existsSync(path.join(launch.cwd, "reference/foreign/api.md")),
          );
          if (slot.phase !== "context-solve")
            assert.equal(
              fs.readFileSync(
                path.join(launch.cwd, "reference/lib/api.md"),
                "utf8",
              ),
              "ADMITTED_LIBRARY_API",
            );
          else
            assert(
              !fs.existsSync(path.join(launch.cwd, "reference/lib/api.md")),
            );
        }
        if (slot.phase === "tasks" && taskCalls > 1) {
          data.tasks[0].id = "task.native-2";
          if (scenario === "empty-tasks") data.tasks = [];
          if (scenario === "duplicate-tasks")
            data.tasks.push({ ...data.tasks[0] });
          if (scenario === "reserved") data.tasks[0].id = "task.native-1";
          if (scenario === "scope-repair")
            assert(
              snapshot.stage_inputs.some(
                (v) => v.type_id === "concorde-task-scope-feedback",
              ),
            );
        }
        if (scenario === "business-invalid") data.outcome = "spec_incomplete";
        const value = {
          invocation_id: slot.ticket,
          result: {
            type_id: "concorde-agent-stage-result",
            schema_version:
              slot.launch.outputSchema.properties.result.properties
                .schema_version.const,
            data,
          },
        };
        if (scenario === "malformed") delete value.result.data.answer;
        if (scenario === "assessor-gap" && slot.phase === "context-solve") {
          const reported = await childTools
            .get("report_issue")
            .execute("issue", {
              report: {
                report_key: "fixture-gap",
                type: "gap",
                subtype: "missing-contract",
                title: "Missing contract",
                description: "Fixture missing rule",
                impact: "Blocks assessment",
                basis: "Fixture incomplete promise",
                owner_target_id: "service.transfer",
                evidence: [],
              },
            });
          data.outcome = "spec_incomplete";
          data.blockers = [
            { ...reported.details.receipt, blocked_step: "Assess context" },
          ];
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
        if (scenario === "shutdown" && slot.phase === "context-solve")
          await emit("session_shutdown", {});
        if (scenario === "cancel") {
          const control = [...state.foregroundControls.values()][0];
          assert(control.interrupt());
        }
        if (
          slot.phase === "plan" &&
          [
            "stale-spec",
            "stale-metadata",
            "stale-intent",
            "stale-reference",
          ].includes(scenario)
        ) {
          if (scenario === "stale-spec")
            fs.appendFileSync(
              path.join(slot.project_root, "specs/transfer/module.md"),
              "\nChanged contract\n",
            );
          if (scenario === "stale-metadata")
            fs.appendFileSync(
              path.join(slot.project_root, "specs/transfer/module.md.json"),
              "\n",
            );
          if (scenario === "stale-reference")
            fs.appendFileSync(
              path.join(slot.project_root, "reference/lib/api.md"),
              "CHANGED",
            );
          if (scenario === "stale-intent")
            execFileSync(python, [
              "-c",
              "from pathlib import Path; from concorde.harness.change_worktree import read_change,save_change; r=Path(" +
                JSON.stringify(slot.project_root) +
                "); c=read_change(r); c['constraints']=['changed intent']; save_change(r,c)",
            ]);
        }
        send({ type: "agent_end", messages });
        if (scenario === "native-failure" && slot.phase === "context-solve")
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
    maxSubagentSpawnsPerRun: 2,
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

async function nativeCall(call, toolId) {
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
  fs.writeFileSync(path.join(root, toolId + ".json"), JSON.stringify(response));
  const final = await emit("tool_result", {
    toolName: "subagent",
    toolCallId: toolId,
    input: call,
    ...response,
  });
  return { response, final };
}
const { response } = await nativeCall(call, "plan");
assert(!response.isError, JSON.stringify(response));
let result;
for (let n = 0; n < 600; n++) {
  result = (
    await tools
      .get("concorde")
      .execute(
        "result",
        { operation: "concorde-plan", action: "result" },
        undefined,
        undefined,
        ctx,
      )
  ).details;
  if (result.native_state !== "running") break;
  await new Promise((r) => setTimeout(r, 100));
}
fs.writeFileSync(path.join(root, "plan-result.json"), JSON.stringify(result));
assert.notEqual(result.native_state, "running", JSON.stringify(result));
if (
  [
    "assessor-gap",
    "native-failure",
    "cancel",
    "shutdown",
    "empty-plan",
    "stale-spec",
    "stale-metadata",
    "stale-intent",
    "stale-reference",
  ].includes(scenario)
) {
  assert(
    scenario === "assessor-gap"
      ? result.result.status === "blocked"
      : !result.accepted,
    JSON.stringify(result),
  );
  if (
    ["assessor-gap", "native-failure", "cancel", "shutdown"].includes(scenario)
  )
    assert.equal(scriptedCalls, 1);
  if (
    [
      "empty-plan",
      "stale-spec",
      "stale-metadata",
      "stale-intent",
      "stale-reference",
    ].includes(scenario)
  ) {
    const kept = execFileSync(
      python,
      [
        "-c",
        "from pathlib import Path;from concorde.harness.change_worktree import read_change;print(read_change(Path(" +
          JSON.stringify(prepared.binding.root) +
          "))['targets']['service.transfer']['plan'])",
      ],
      { encoding: "utf8" },
    ).trim();
    assert.equal(kept, "PREVIOUS ACCEPTED PLAN");
  }
  if (scenario === "native-failure") {
    const status = JSON.parse(
      fs.readFileSync(
        path.join(response.details.asyncDir, "status.json"),
        "utf8",
      ),
    );
    const artifacts = fs
      .readdirSync(path.join(root, "native/artifacts"), { recursive: true })
      .filter((v) => v.endsWith("_meta.json"));
    const metadata = JSON.parse(
      fs.readFileSync(
        path.join(root, "native/artifacts", artifacts[0]),
        "utf8",
      ),
    );
    assert.equal(metadata.acceptance.status, "verified");
    assert.notEqual(metadata.exitCode, 0);
  }
} else {
  assert(result.accepted, JSON.stringify(result));
  assert.equal(result.result.status, "succeeded", JSON.stringify(result));
  const projectRoot = prepared.binding.root;
  if (scenario === "stale-plan") {
    fs.appendFileSync(
      path.join(projectRoot, "specs/transfer/module.md"),
      "\nChanged before tasks\n",
    );
    await assert.rejects(
      () =>
        tools.get("concorde").execute(
          "stale",
          {
            operation: "concorde-tasks",
            action: "run",
            input: {
              target_id: "service.transfer",
              task: "Assess the transfer contract",
              change_id: result.result.output.data.change_id,
            },
          },
          undefined,
          undefined,
          ctx,
        ),
      /stale_context/,
    );
    console.log(
      JSON.stringify({ scenario, root, scriptedCalls, realModelCalls: 0 }),
    );
    process.exit(0);
  }
  const taskPrepared = (
    await tools.get("concorde").execute(
      "tasks-prepare",
      {
        operation: "concorde-tasks",
        action: "run",
        input: {
          target_id: "service.transfer",
          task: "Assess the transfer contract",
          change_id: result.result.output.data.change_id,
        },
      },
      undefined,
      undefined,
      ctx,
    )
  ).details;
  assert.equal(taskPrepared.state, "prepared", JSON.stringify(taskPrepared));
  const taskRun = await nativeCall(taskPrepared.call, "tasks");
  fs.writeFileSync(
    path.join(root, "tasks-result.json"),
    JSON.stringify(taskRun.final),
  );
  assert.equal(
    taskRun.final.details.concorde_native.accepted,
    true,
    JSON.stringify(taskRun.final),
  );
  function inspect() {
    return JSON.parse(
      execFileSync(
        python,
        [
          "-c",
          "import json; from pathlib import Path; from concorde.harness.change_worktree import read_change; print(json.dumps(read_change(Path(" +
            JSON.stringify(projectRoot) +
            "))))",
        ],
        { encoding: "utf8" },
      ),
    );
  }
  const saved = inspect();
  assert.equal(saved.primary_worktree, root);
  assert.equal(saved.path, projectRoot);
  assert.notEqual(saved.path, root);
  assert.equal(saved.targets["service.transfer"].tasks.length, 1);
  const primaryRecord = path.join(
    root,
    ".concorde/status",
    saved.change_id + ".json",
  );
  assert(fs.existsSync(primaryRecord), "status is not in primary");
  assert(
    !fs.existsSync(
      path.join(projectRoot, ".concorde/status", saved.change_id + ".json"),
    ),
    "candidate duplicated status authority",
  );
  if (scenario === "replan") {
    const next = (
      await tools.get("concorde").execute(
        "replan",
        {
          operation: "concorde-plan",
          action: "run",
          input: {
            target_id: "service.transfer",
            task: "Assess the transfer contract",
            change_id: saved.change_id,
          },
        },
        undefined,
        undefined,
        ctx,
      )
    ).details;
    await nativeCall(next.call, "replan");
    let observed;
    for (let n = 0; n < 600; n++) {
      observed = (
        await tools
          .get("concorde")
          .execute(
            "replan-result",
            { operation: "concorde-plan", action: "result" },
            undefined,
            undefined,
            ctx,
          )
      ).details;
      if (observed.native_state !== "running") break;
      await new Promise((r) => setTimeout(r, 100));
    }
    assert(observed.accepted, JSON.stringify(observed));
    const current = inspect().targets["service.transfer"];
    assert.deepEqual(current.tasks, []);
    assert(
      current.task_history.some((entry) =>
        entry.tasks.some((task) => task.id === "task.native-1"),
      ),
    );
  }
  if (
    [
      "empty-tasks",
      "duplicate-tasks",
      "reserved",
      "scope-repair",
      "stale-scope",
      "stale-review",
    ].includes(scenario)
  ) {
    const tasks = saved.targets["service.transfer"].tasks;
    const taskDigest = execFileSync(
      python,
      [
        "-c",
        "import json; from concorde.spec.repository import digest; from concorde.spec.typed_data import canonical; print(digest(canonical(json.loads(" +
          JSON.stringify(JSON.stringify(tasks)) +
          ")).encode()))",
      ],
      { encoding: "utf8" },
    ).trim();
    const request = {
      target_id: "service.transfer",
      task: "Assess the transfer contract",
      change_id: saved.change_id,
    };
    if (["scope-repair", "stale-scope"].includes(scenario))
      request.repair_task_scope = {
        tasks_digest:
          scenario === "stale-scope" ? "sha256:" + "0".repeat(64) : taskDigest,
      };
    if (scenario === "stale-review")
      request.repair_review = {
        id: "review",
        path: ".concorde/work/foreign.json",
        digest: "sha256:" + "0".repeat(64),
      };
    if (["stale-scope", "stale-review"].includes(scenario)) {
      await assert.rejects(
        () =>
          tools
            .get("concorde")
            .execute(
              "repair",
              { operation: "concorde-tasks", action: "run", input: request },
              undefined,
              undefined,
              ctx,
            ),
        /incompatible_handoff|stale_evidence/,
      );
      assert.deepEqual(inspect().targets["service.transfer"].tasks, tasks);
    } else {
      const repair = (
        await tools
          .get("concorde")
          .execute(
            "repair",
            { operation: "concorde-tasks", action: "run", input: request },
            undefined,
            undefined,
            ctx,
          )
      ).details;
      const repaired = await nativeCall(repair.call, "repair-tasks");
      assert.equal(
        repaired.final.details.concorde_native.accepted,
        scenario === "scope-repair",
        JSON.stringify(repaired.final),
      );
      if (scenario !== "scope-repair")
        assert.deepEqual(inspect().targets["service.transfer"].tasks, tasks);
      else
        assert.equal(
          inspect().targets["service.transfer"].tasks[0].id,
          "task.native-2",
        );
    }
  }
}
console.log(
  JSON.stringify({
    scenario,
    root,
    scriptedCalls,
    realModelCalls: 0,
    accepted: result.accepted,
    native_state: result.native_state,
  }),
);
await emit("session_shutdown", {});
