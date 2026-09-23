/** Actual candidate Pi entry + native file-Agent discovery/executor. Only model events are scripted. */
import assert from "node:assert/strict";
import { executeWithSdkValidation } from "./native_sdk_validation.mjs";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { EventEmitter } from "node:events";
import { execFileSync } from "node:child_process";
const [subagents, sdk, candidate, scenario = "sufficient"] =
  process.argv.slice(2);
const root =
  process.env.CONCORDE_NATIVE_PROBE_PROJECT ??
  fs.mkdtempSync(path.join(os.tmpdir(), "concorde-context-public-"));
const python =
  process.env.CONCORDE_NATIVE_PROBE_PYTHON ??
  path.join(candidate, ".venv/bin/python");
const fixtureSource = process.env.CONCORDE_NATIVE_FIXTURE_SOURCE ?? candidate;
execFileSync(python, [
  "-c",
  `import sys;sys.path.insert(0,${JSON.stringify(candidate + "/src")});sys.path.append(${JSON.stringify(fixtureSource)})
from pathlib import Path
from tests.concorde.spec import support
support.PACKAGE=Path(${JSON.stringify(candidate)})
project=support.project
if not (Path(${JSON.stringify(root)})/".concorde/specs.json").exists(): project(Path(${JSON.stringify(root)}))`,
]);
process.env.PI_CODING_AGENT_DIR = path.join(root, "operator-agent");
process.env.PI_SUBAGENTS_TEMP_ROOT = path.join(root, "native");
process.env.PI_SUBAGENTS_LLM_INTENT_ARBITER = "0";
process.env.PI_SUBAGENTS_PI_CODING_AGENT_PACKAGE_ROOT = sdk;
process.env.CONCORDE_NATIVE_SUBAGENTS_ROOT = subagents;
if (!process.env.CONCORDE_NATIVE_PROBE_PROJECT) {
  process.env.CONCORDE_NATIVE_PROJECT_ROOT = root;
  process.env.CONCORDE_SESSION_SELECTION = path.join(
    candidate,
    ".concorde/work/pi-first-context-selection.json",
  );
} else {
  delete process.env.CONCORDE_NATIVE_PROJECT_ROOT;
  delete process.env.CONCORDE_SESSION_SELECTION;
}
// Guard every real Python command, including native gates. No Graph import or hidden worker.
const guard = path.join(root, "guard");
fs.mkdirSync(guard, { recursive: true });
fs.writeFileSync(
  path.join(guard, "sitecustomize.py"),
  `import builtins,sys
if ${process.env.CONCORDE_NATIVE_PROBE_PROJECT ? "True" : "False"}:
 from langgraph.graph import StateGraph
 def no_graph(*a,**k): raise AssertionError('Native installed path compiled a Graph')
 StateGraph.compile=no_graph
original=builtins.__import__
def guarded(name,*args,**kwargs):
 if ${process.env.CONCORDE_NATIVE_PROBE_PROJECT ? "False" : "True"} and '--runtime-check' not in sys.argv and (name=='langgraph' or name.startswith('langgraph.')): raise AssertionError('Native path imported LangGraph')
 return original(name,*args,**kwargs)
builtins.__import__=guarded
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
  process.env.CONCORDE_NATIVE_PROBE_PROJECT
    ? path.join(root, ".pi/extensions/concorde-session.ts")
    : path.join(candidate, "generated/session/pi/concorde-session.ts"),
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
    operation: "concorde-context-solve",
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
let scriptedCalls = 0;
setChildSessionFactory({
  async create(launch) {
    scriptedCalls++;
    assert.equal(launch.cwd, call.cwd);
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
    assert(
      !childTools.has("update_task_brief"),
      "source user session tool leaked into Domain Agent",
    );
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
        const data = {
          context_id: snapshot.context_id,
          outcome: scenario === "unsupported" ? "unsupported" : "sufficient",
          answer: "Scripted assessment",
          blockers: [],
          documents: [],
          plan: "",
          tasks: [],
        };
        if (scenario === "business-invalid") data.outcome = "spec_incomplete";
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
        if (scenario === "malformed") delete value.result.data.answer;
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
        let result;
        try {
          result = await executeWithSdkValidation(
            sdk,
            childTools.get("structured_output"),
            "structured-1",
            args,
          );
        } catch (error) {
          // SDK immediate validation failures bypass tool_result but emit this supported event.
          const ended = {
            type: "tool_execution_end",
            toolName: "structured_output",
            toolCallId: "structured-1",
            result: {
              content: [{ type: "text", text: error.message }],
              details: {},
            },
            isError: true,
          };
          for (const handler of childHandlers.get("tool_execution_end") ?? [])
            await handler(ended, ctx);
          send(ended);
          throw error;
        }
        const event = {
          toolCallId: "structured-1",
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
    path.join(root, "specs/transfer/module.md"),
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
  [
    "sufficient",
    "unsupported",
    "gap-result",
    "shadow",
    "duplicate-launch",
  ].includes(scenario),
  JSON.stringify(acceptance),
);
if (scenario === "business-invalid") {
  const feedback = acceptance.result.errors[0].feedback;
  assert.equal(feedback.layer, "native-slot");
  assert.equal(feedback.causes[0].layer, "host-submit");
  assert.equal(feedback.causes[0].code, "invalid_completion");
  assert.equal(
    feedback.causes[0].message,
    "stage outcome does not match its task blockers",
  );
  assert(feedback.causes[0].attempt);
  assert.equal(final.isError, true);
}
if (scenario === "malformed") {
  const feedback = acceptance.result.errors[0].feedback;
  assert.match(JSON.stringify(feedback), /schema-rejection/);
  assert.match(JSON.stringify(feedback), /Validation failed for tool/);
  assert(!JSON.stringify(feedback).includes("Received arguments:"));
}
if (scenario === "cancel")
  assert.equal(acceptance.state, "cancelled", JSON.stringify(acceptance));
if (scenario === "stale")
  assert.equal(acceptance.state, "stale", JSON.stringify(acceptance));
assert.equal(scriptedCalls, 1);
if (["native-failure", "proposal-tamper"].includes(scenario))
  assert.equal(native.details.results[0].acceptance.status, "verified");
if (scenario === "sufficient")
  assert.equal(acceptance.result.status, "succeeded");
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
