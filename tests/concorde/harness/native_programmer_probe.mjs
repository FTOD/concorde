/** Actual candidate Pi entry + native file-Agent discovery/executor. Only model events are scripted. */
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { EventEmitter } from "node:events";
import { execFileSync } from "node:child_process";
const [subagents, sdk, candidate, scenario = "success"] = process.argv.slice(2);
const root = fs.mkdtempSync(
  path.join(os.tmpdir(), "concorde-programmer-public-"),
);
const python = path.join(candidate, ".venv/bin/python");
execFileSync(python, [
  "-c",
  `import sys;sys.path.insert(0,${JSON.stringify(candidate + "/src")});sys.path.insert(0,${JSON.stringify(candidate)})
from pathlib import Path
from tests.concorde.spec.support import project
project(Path(${JSON.stringify(root)}))
import subprocess
r=Path(${JSON.stringify(root)})
def git(*a):subprocess.run(['git',*a],cwd=r,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
git('init');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid');git('add','.');git('commit','-m','Fixture');git('worktree','add','-b','programmer',str(r/'candidate'))
from concorde.harness.change_worktree import ensure_change,bind_owner,target_state,save_target_state
from concorde.harness.host import OperationHost
from concorde.harness.invocation import Invocation
from concorde.harness.configuration import load_configuration
from concorde.planning.plan import persist_plan_result
from concorde.planning.tasks import persist_tasks
r=r/'candidate';task={'target_id':'service.transfer','task':'Implement the transfer contract'}
ensure_change(r,task=task);bind_owner(r,task)
run=Invocation('concorde-implement',load_configuration(r),task,OperationHost(r,Path(${JSON.stringify(candidate)})))
persist_plan_result(run,{'plan':'Implement transfer','answer':'Seed accepted plan'})
state=target_state(r,'service.transfer',None)
tasks=[{'id':'task.implement','target_id':'service.transfer','description':'Implement transfer','acceptance':'Valid inputs subtract and invalid inputs raise ValueError','complete':False}]
persist_tasks(run,{'tasks':tasks,'answer':'Seed accepted tasks'},state,None,None)
if ${JSON.stringify(scenario)} in ('feedback','tampered-feedback'):
 from concorde.review.review import inputs,_persist
 from concorde.spec.typed_data import typed
 from concorde.issues.store import report_issue
 info,_=inputs(run,'code')
 receipt=report_issue(r,{'report_key':'repair','type':'bug','subtype':None,'title':'Repair input','description':'Fixture repair finding','impact':'Task repair','basis':'Selected contract','owner_target_id':'service.transfer','evidence':[]},{'invocation_id':'fixture-review','agent':'code_reviewer','operation':'concorde-code-review','phase':'code-review','target_id':'service.transfer','context_id':'sha256:'+'a'*64,'change_id':run.change_id,'head':None})
 value=typed('concorde-review-result',{'context_id':'sha256:'+'a'*64,'input_digest':info['input_digest'],'review_mode':'code','status':'findings','representative_tasks':['Transfer repair'],'issues':[{**receipt,'severity':'blocking','affected_task':'Transfer repair'}],'answer':'Repair required','target_id':'service.transfer','focus_id':None,'revision':info['revision'],'semantic_completeness':'not_proven'})
 reference=_persist(run,value)
 state=target_state(r,'service.transfer',None);state['repair_review']=reference;save_target_state(r,state)

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
  ["missing-components", "missing-tasks", "stale-before"].includes(scenario)
) {
  const projectRoot = path.join(root, "candidate");
  execFileSync(python, [
    "-c",
    "from pathlib import Path;from concorde.harness.change_worktree import read_change,save_change;r=Path(" +
      JSON.stringify(projectRoot) +
      ");s=read_change(r);t=s['targets']['service.transfer'];" +
      (scenario === "missing-components"
        ? "t['tasks'][0]['target_id']='module.ledger'"
        : scenario === "missing-tasks"
          ? "t['tasks']=[]"
          : "t['spec_digest']='sha256:'+'0'*64") +
      ";save_change(r,s)",
  ]);
  if (scenario === "missing-components") {
    const response = await tools.get("concorde").execute(
      "prepare",
      {
        operation: "concorde-implement",
        action: "run",
        input: {
          target_id: "service.transfer",
          task: "Implement the transfer contract",
        },
      },
      undefined,
      undefined,
      ctx,
    );
    assert.equal(response.details.state, "not-run");
    assert.equal(response.details.result.output.data.outcome, "unsupported");
  } else
    await assert.rejects(
      () =>
        tools.get("concorde").execute(
          "prepare",
          {
            operation: "concorde-implement",
            action: "run",
            input: {
              target_id: "service.transfer",
              task: "Implement the transfer contract",
            },
          },
          undefined,
          undefined,
          ctx,
        ),
      /missing_tasks|stale_context/,
    );
  console.log(
    JSON.stringify({ scenario, root, scriptedCalls: 0, realModelCalls: 0 }),
  );
  process.exit(0);
}
const preparedTool = await tools.get("concorde").execute(
  "prepare",
  {
    operation: "concorde-implement",
    action: "run",
    input: {
      target_id: "service.transfer",
      task: "Implement the transfer contract",
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
    assert.equal(launch.cwd, call.cwd);
    assert.equal(launch.ambientExtensions, false);
    assert.equal(launch.noSkills, true);
    assert.equal(launch.noContextFiles, true);
    assert(
      launch.tools.includes("write") &&
        launch.tools.includes("edit") &&
        launch.tools.includes("run_checks"),
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
          fs.readFileSync(path.join(call.cwd, "context.json"), "utf8"),
        );
        let toolSequence = 0;
        const actualTool = async (name, args, execute) => {
          const id = "actual-" + ++toolSequence;
          const message = {
            role: "assistant",
            content: [{ type: "toolCall", id, name, arguments: args }],
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
            toolCallId: id,
            toolName: name,
            args,
          });
          const result = await execute(id, args);
          messages.push({
            role: "toolResult",
            toolCallId: id,
            toolName: name,
            ...result,
            isError: false,
            timestamp: Date.now(),
          });
          send({
            type: "tool_execution_end",
            toolCallId: id,
            toolName: name,
            result,
            isError: false,
          });
          return result;
        };
        const { createWriteTool, createEditTool } = await import(
          path.join(sdk, "dist/index.js")
        );
        const implementation = path.join(
          snapshot.native_workspace,
          "app/transfer.py",
        );
        await actualTool(
          "write",
          {
            path: implementation,
            content:
              "def transfer(balance, amount):\n    if amount <= 0 or amount > balance: raise ValueError('invalid')\n    return balance - amount\n",
          },
          (id, args) => createWriteTool(launch.cwd).execute(id, args),
        );
        await actualTool(
          "edit",
          {
            path: implementation,
            edits: [{ oldText: "'invalid'", newText: "'invalid amount'" }],
          },
          (id, args) => createEditTool(launch.cwd).execute(id, args),
        );
        const checks = await actualTool("run_checks", {}, (id, args) =>
          childTools.get("run_checks").execute(id, args),
        );
        assert(
          checks.details.checks.every((item) => item.status === "passed"),
          JSON.stringify(checks),
        );
        assert(
          !fs.existsSync(path.join(launch.cwd, "app/transfer.py")),
          "code written into capsule",
        );
        if (
          ["stale-plan", "stale-tasks", "stale-feedback"].includes(scenario)
        ) {
          execFileSync(python, [
            "-c",
            "from pathlib import Path;from concorde.harness.change_worktree import read_change,save_change;r=Path(" +
              JSON.stringify(snapshot.native_workspace) +
              ");s=read_change(r);t=s['targets']['service.transfer'];" +
              (scenario === "stale-plan"
                ? "t['plan']='changed plan'"
                : scenario === "stale-tasks"
                  ? "t['tasks'][0]['acceptance']='changed acceptance'"
                  : "t['repair_review']={'id':'review','path':'.concorde/work/foreign.json','digest':'sha256:'+'0'*64}") +
              ";save_change(r,s)",
          ]);
        }
        if (["feedback", "tampered-feedback"].includes(scenario)) {
          assert.equal(
            snapshot.stage_inputs.filter(
              (v) => v.type_id === "concorde-issue-context",
            ).length,
            1,
          );
          if (scenario === "tampered-feedback")
            execFileSync(python, [
              "-c",
              "from pathlib import Path;from concorde.harness.change_worktree import read_change;from concorde.harness.status_store import run_path;r=Path(" +
                JSON.stringify(snapshot.native_workspace) +
                ");p=run_path(r,read_change(r)['targets']['service.transfer']['repair_review']['path']);p.write_bytes(p.read_bytes()+b' ')",
            ]);
        }
        const expected = snapshot.stage_inputs.find(
          (value) => value.type_id === "concorde-implementation-task",
        ).data.tasks;
        const data = {
          context_id: snapshot.context_id,
          outcome: "completed",
          answer: "Scripted assessment",
          blockers: [],
          documents: [],
          plan: "",
          tasks: expected.map((task) => ({ ...task, complete: true })),
        };
        if (scenario === "incomplete") data.tasks[0].complete = false;
        if (scenario === "foreign-task") data.tasks[0].id = "task.foreign";
        if (scenario === "malformed")
          data.tasks[0].acceptance = "changed acceptance";
        if (scenario === "stale-spec")
          fs.appendFileSync(
            path.join(snapshot.native_workspace, "specs/transfer/module.md"),
            "\nChanged contract\n",
          );

        const value = {
          invocation_id: scenario === "foreign" ? "foreign" : prepared.ticket,
          result: {
            type_id: "concorde-agent-stage-result",
            schema_version:
              call.outputSchema.properties.result.properties.schema_version
                .const,
            data,
          },
        };

        if (scenario === "gap-result") {
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
const toolId = "native-context-call";
if (scenario === "shadow") {
  const dir = path.join(process.env.PI_CODING_AGENT_DIR, "agents");
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(
    path.join(dir, "concorde-context-assessor.md"),
    "---\nname: concorde-context-assessor\ndescription: foreign shadow\ntools: bash\n---\nWrong global Agent",
  );
}
if (scenario === "agent-tamper")
  fs.appendFileSync(
    path.join(call.cwd, ".pi/agents/concorde-context-assessor.md"),
    "\nTampered role",
  );
if (scenario === "extension-tamper")
  fs.appendFileSync(
    path.join(path.dirname(call.cwd), "capture.ts"),
    "\n// Changed capture",
  );
if (scenario === "missing-capsule")
  fs.renameSync(call.cwd, call.cwd + "-expired");
const admission = emit("tool_call", {
  toolName: "subagent",
  toolCallId: toolId,
  input: call,
});
if (scenario === "duplicate-launch") {
  const duplicate = await emit("tool_call", {
    toolName: "subagent",
    toolCallId: toolId + "-duplicate",
    input: call,
  });
  assert(duplicate.block, "parallel duplicate launch was admitted");
}
const admitted = await admission;

if (
  ["agent-tamper", "extension-tamper", "missing-capsule"].includes(scenario)
) {
  assert(admitted.block, JSON.stringify(admitted));
  assert.equal(scriptedCalls, 0);
  console.log(
    JSON.stringify({ scenario, root, realModelCalls: 0, scriptedCalls }),
  );
  process.exit(0);
}
assert(!admitted.block, JSON.stringify(admitted));
const native = await executor.executePublic(
  toolId,
  call,
  new AbortController().signal,
  undefined,
  ctx,
);
fs.writeFileSync(path.join(root, "native.json"), JSON.stringify(native));
if (scenario === "stale")
  fs.appendFileSync(
    path.join(root, "candidate/specs/transfer/module.md"),
    "\nChanged before acceptance.\n",
  );
const final = await emit("tool_result", {
  toolName: "subagent",
  toolCallId: toolId,
  input: call,
  ...native,
});
fs.writeFileSync(path.join(root, "final.json"), JSON.stringify(final));
const acceptance = final.details.concorde_context;
assert(acceptance, JSON.stringify(final));
assert.equal(
  acceptance.accepted,
  ["success", "feedback"].includes(scenario),
  JSON.stringify(acceptance),
);
assert(
  fs
    .readFileSync(path.join(root, "candidate/app/transfer.py"), "utf8")
    .includes("invalid amount"),
  "partial edits disappeared",
);

if (scenario === "cancel")
  assert.equal(acceptance.state, "cancelled", JSON.stringify(acceptance));
if (scenario === "stale")
  assert.equal(acceptance.state, "stale", JSON.stringify(acceptance));
assert.equal(scriptedCalls, 1);
if (["native-failure", "proposal-tamper"].includes(scenario))
  assert.equal(native.details.results[0].acceptance.status, "verified");
if (scenario === "success") assert.equal(acceptance.result.status, "succeeded");
if (["unsupported", "gap-result"].includes(scenario))
  assert.equal(acceptance.result.status, "blocked");
await emit("session_shutdown", {});
console.log(
  JSON.stringify({
    scenario,
    root,
    accepted: acceptance.accepted,
    scriptedCalls,
    realModelCalls: 0,
  }),
);
