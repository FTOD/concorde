// Drives the native call extension, the workflow registrar and the Host-step transport with a
// scripted Host command and a stand-in pi-subagents package; no Pi process or model runs.
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const [repository, section = "all"] = process.argv.slice(2);
const want = (name) => section === "all" || section === name;
const root = fs.mkdtempSync(
  path.join(os.tmpdir(), "concorde-native-extension-"),
);
const log = path.join(root, "host.log");
const responses = path.join(root, "responses.json");

// --- a scripted Host command: logs each action and answers from the responses file -----------
const host = path.join(root, "host.mjs");
fs.writeFileSync(
  host,
  `import fs from "node:fs";
const args = process.argv.slice(2).filter((item) => item !== "--native-context");
const [action, descriptor] = args;
const input = fs.readFileSync(0, "utf8");
fs.appendFileSync(${JSON.stringify(log)}, JSON.stringify({ action, descriptor, input: input ? JSON.parse(input) : null }) + "\\n");
const table = JSON.parse(fs.readFileSync(${JSON.stringify(responses)}, "utf8"));
const answer = table[action] ?? { stdout: { state: "prepared", accepted: false } };
if (answer.sleep) await new Promise((resolve) => setTimeout(resolve, answer.sleep));
if (answer.flood) process.stdout.write("x".repeat(answer.flood));
if (answer.raw !== undefined) process.stdout.write(answer.raw);
if (answer.stdout !== undefined) process.stdout.write(JSON.stringify(answer.stdout));
process.exitCode = answer.exit ?? 0;
`,
);
const respond = (table) => fs.writeFileSync(responses, JSON.stringify(table));
const actions = () =>
  fs.existsSync(log)
    ? fs
        .readFileSync(log, "utf8")
        .trim()
        .split("\n")
        .filter(Boolean)
        .map((line) => JSON.parse(line))
    : [];
respond({});

// --- a stand-in pi-subagents package with the two public entries the plumbing resolves ---------
const subagents = path.join(root, "node_modules/pi-subagents");
fs.mkdirSync(subagents, { recursive: true });
fs.writeFileSync(
  path.join(subagents, "package.json"),
  JSON.stringify({
    name: "pi-subagents",
    type: "module",
    exports: {
      "./preflight": "./preflight.mjs",
      "./workflow-resources": "./workflow-resources.mjs",
    },
  }),
);
fs.writeFileSync(
  path.join(subagents, "preflight.mjs"),
  `import path from "node:path";
export async function resolveSubagentLaunchContract(call) {
  globalThis.preflights = (globalThis.preflights ?? 0) + 1;
  return { ok: true, contract: {
    agent: { source: "project", filePath: path.join(call.cwd, ".pi/agents", call.agent + ".md") },
    tools: { disableAmbientExtensions: true, fanoutAuthorized: false, effectiveAllowlist: ["read"] },
    context: "fresh", inheritProjectContext: false, inheritGlobalContext: false, inheritSkills: false,
    skills: { resolved: [] }, intercomBridge: { active: false },
    launchContractDigest: "sha256:launch-" + globalThis.preflights } };
}
`,
);
fs.writeFileSync(
  path.join(subagents, "workflow-resources.mjs"),
  `export function registerWorkflowResource(value) {
  const entry = { ...value, disposed: false };
  (globalThis.registrations ??= []).push(entry);
  return { dispose() { entry.disposed = true; } };
}
`,
);
process.env.CONCORDE_NATIVE_SUBAGENTS_ROOT = subagents;

const { nativeContext } = await import(
  path.join(repository, "pi/extensions/concorde-native-context.ts")
);
const { nativeCommand } = await import(
  path.join(repository, "pi/extensions/concorde-native-child.ts")
);

// --- a minimal Pi extension surface -------------------------------------------------------
const handlers = new Map();
const emitted = [];
const pi = {
  on(name, handler) {
    handlers.set(name, handler);
  },
  appendEntry() {},
  events: {
    emit(name, value) {
      emitted.push({ name, value });
    },
  },
};
const session = "parent-session";
const ctx = {
  sessionManager: {
    getSessionId: () => session,
    getSessionFile: () => undefined,
  },
  modelRegistry: { getAvailable: () => [] },
};
const emit = (name, event) => handlers.get(name)(event, ctx);
let prepareAnswer;
let preparations = 0;
const prepare = nativeContext(pi, {
  root,
  python: process.execPath,
  launcher: host,
  verify: () => {},
  prepare: async () => {
    preparations += 1;
    return prepareAnswer;
  },
});

// --- one Agent call -----------------------------------------------------------------------
let serial = 0;
function preparedCall() {
  serial += 1;
  const directory = path.join(root, "call-" + serial);
  const cwd = path.join(directory, "context");
  fs.mkdirSync(path.join(cwd, ".pi/agents"), { recursive: true });
  fs.writeFileSync(
    path.join(cwd, ".pi/agents/concorde-context-assessor.md"),
    "---\nname: concorde-context-assessor\ntools: read, report_issue\n---\nBody\n",
  );
  const descriptor = path.join(directory, "descriptor.json");
  return {
    state: "prepared",
    accepted: false,
    descriptor,
    digest: "sha256:call-" + serial,
    ticket: "ticket-" + serial,
    call: {
      agent: "concorde-context-assessor",
      task: "Assess context.json for invocation_id ticket-" + serial,
      cwd,
      agentScope: "project",
      context: "fresh",
      async: false,
      gate: { command: "gate " + serial },
    },
  };
}
const since = (count) => actions().slice(count);
const nameOf = (entry) => entry.action;
const call = async (input, id) =>
  emit("tool_call", { toolName: "subagent", toolCallId: id, input });
const result = async (id, row, input = {}) =>
  emit("tool_result", {
    toolName: "subagent",
    toolCallId: id,
    input,
    isError: false,
    details: {
      mode: "single",
      runId: "run-" + id,
      results: [
        {
          agent: "concorde-context-assessor",
          exitCode: 0,
          transcript: "prose",
          ...row,
        },
      ],
    },
  });

const report = {};

// Foreign call: a different call object never reaches check or preflight; the prepared call stays usable.
if (want("call")) {
  const prepared = preparedCall();
  prepareAnswer = prepared;
  const answer = await prepare({ operation: "concorde-context-solve" }, ctx);
  assert.equal(answer.state, "prepared");
  const before = actions().length;
  const foreign = await call(
    { ...prepared.call, task: "Do something else" },
    "t-foreign",
  );
  assert.equal(foreign.block, true);
  assert.equal(since(before).length, 0);
  assert.equal(globalThis.preflights ?? 0, 0);
  const launched = await call(prepared.call, "t-1");
  assert.equal(launched, undefined);
  assert.deepEqual(since(before).map(nameOf), ["check"]);
  assert.equal(globalThis.preflights, 1);
  const repeated = await call(prepared.call, "t-2");
  assert.equal(repeated.block, true);
  respond({
    accept: {
      stdout: { state: "accepted", accepted: true, outcome: "sufficient" },
    },
  });
  const accepted = await result("t-1", {
    launchContractDigest: "sha256:launch-1",
  });
  assert.equal(accepted.isError, false);
  const acceptance = since(before).find((entry) => entry.action === "accept");
  assert.equal(acceptance.input.launch_contract_digest, "sha256:launch-1");
  assert.equal(acceptance.input.gate_command, prepared.call.gate.command);
  assert.equal(acceptance.input.session_id, session);
  assert.equal("transcript" in acceptance.input.details.results[0], false);
  // Once launched, the same call is never launched again.
  const after = await call(prepared.call, "t-3");
  assert.equal(after.block, true);
  report.foreignCall = true;
}

// Cancellation: replacement and shutdown invalidate a prepared call, a failed acceptance
// invalidates the call, and nothing is retried.
if (want("call")) {
  respond({});
  const first = preparedCall();
  prepareAnswer = first;
  await prepare({}, ctx);
  const second = preparedCall();
  prepareAnswer = second;
  let before = actions().length;
  await prepare({}, ctx);
  assert.deepEqual(
    since(before).map((entry) => [entry.action, entry.descriptor]),
    [["invalidate", first.descriptor]],
  );
  before = actions().length;
  await emit("session_shutdown", {});
  assert.deepEqual(
    since(before).map((entry) => [entry.action, entry.descriptor]),
    [["invalidate", second.descriptor]],
  );
  const cases = [
    ["stale", {}, "stale_context"],
    ["cancelled", { interrupted: true }, "execution_cancelled"],
    ["cancelled", { stopped: true }, "execution_cancelled"],
    ["failed", { exitCode: 1 }, "execution_failed"],
  ];
  for (const [state, row, code] of cases) {
    const prepared = preparedCall();
    prepareAnswer = prepared;
    const count = preparations;
    await prepare({}, ctx);
    const id = "t-" + prepared.ticket;
    assert.equal(await call(prepared.call, id), undefined);
    respond({
      accept: {
        exit: 3,
        stdout: {
          state: "rejected",
          accepted: false,
          result: { errors: [{ code, field: "", message: "refused " + code }] },
        },
      },
    });
    before = actions().length;
    const value = await result(id, {
      launchContractDigest: "sha256:x",
      ...row,
    });
    assert.equal(value.isError, true);
    assert.equal(value.details.concorde_context.state, state);
    assert.equal(value.details.concorde_context.accepted, false);
    assert.deepEqual(since(before).map(nameOf), ["accept", "invalidate"]);
    assert.equal(preparations, count + 1);
    // The invalidated call is not launched again.
    assert.equal((await call(prepared.call, id + "-again")).block, true);
  }
  report.cancelledCall = true;
}

// --- one Workflow -------------------------------------------------------------------------
const packageRoot = path.join(root, "package");
fs.mkdirSync(path.join(packageRoot, "pi"), { recursive: true });
fs.copyFileSync(
  path.join(repository, "pi/execution-error.mjs"),
  path.join(packageRoot, "pi/execution-error.mjs"),
);
fs.writeFileSync(
  path.join(packageRoot, "workflow.mjs"),
  "const plan = __CONCORDE_WORKFLOW__;\nrun(plan);\n",
);
fs.writeFileSync(
  path.join(packageRoot, "helper.mjs"),
  "export function helperStep() {\n  return 1;\n}\n",
);
function preparedWorkflow() {
  serial += 1;
  const directory = path.join(root, "workflow-" + serial);
  fs.mkdirSync(directory, { recursive: true });
  const descriptor = path.join(directory, "descriptor.json");
  const ticket = "wf-ticket-" + serial;
  fs.writeFileSync(
    descriptor,
    JSON.stringify({
      kind: "workflow",
      directory,
      operation: "concorde-spec-review",
      package_root: packageRoot,
      project_root: root,
      runtime: { package_root: subagents },
    }),
  );
  const digest = "sha256:workflow-" + serial;
  return {
    state: "prepared",
    accepted: false,
    descriptor,
    digest,
    ticket,
    binding: { argv: [process.execPath, host], root, descriptor, digest },
    workflow: {
      name: "concorde.spec-review." + ticket,
      script: "workflow.mjs",
      host: "host.mjs",
      steps: ["bind", "finish"],
      helpers: ["helper.mjs"],
      commands: {
        bind: [
          process.execPath,
          "host step's path",
          "bind",
          descriptor,
          digest,
        ],
        finish: [process.execPath, "host.mjs", "finish", descriptor, digest],
      },
      expansion: { ticket, slot_gate: "gate 'it'" },
    },
  };
}
const workflowCall = (prepared) => ({
  workflow: prepared.workflow.name,
  args: { ticket: prepared.ticket },
  cwd: root,
  async: true,
  mission: false,
  context: "fresh",
  intercomBridge: { mode: "off" },
});

// Register: the script, helpers and commands come only from the plan.
if (want("workflow")) {
  respond({});
  const prepared = preparedWorkflow();
  prepareAnswer = prepared;
  const answer = await prepare({}, ctx);
  assert.deepEqual(answer.call, workflowCall(prepared));
  assert.equal(answer.ticket, prepared.ticket);
  const registration = globalThis.registrations.at(-1);
  assert.equal(registration.sessionId, session);
  assert.equal(registration.definition.name, prepared.workflow.name);
  const resolved = registration.definition.resolve({ ticket: prepared.ticket });
  assert.equal(resolved.script.includes("__CONCORDE_WORKFLOW__"), false);
  assert.ok(
    resolved.script.includes(
      "const plan = " + JSON.stringify(prepared.workflow.expansion) + ";",
    ),
  );
  assert.ok(resolved.script.includes("\nfunction helperStep()"));
  assert.ok(resolved.script.includes("function failure("));
  assert.equal(/^export /m.test(resolved.script), false);
  assert.ok(
    resolved.script.indexOf("function failure(") <
      resolved.script.indexOf("function helperStep(") &&
      resolved.script.indexOf("function helperStep(") <
        resolved.script.indexOf("const plan ="),
  );
  assert.deepEqual(resolved.hostCommands, [
    {
      key: "bind",
      command: prepared.workflow.commands.bind
        .map((item) => "'" + item.replaceAll("'", "'\\''") + "'")
        .join(" "),
    },
    {
      key: "finish",
      command: prepared.workflow.commands.finish
        .map((item) => "'" + item + "'")
        .join(" "),
    },
  ]);
  assert.ok(
    resolved.hostCommands[0].command.includes("'host step'\\''s path'"),
  );
  report.workflowRegister = true;

  // Foreign workflow calls are blocked and the resource resolves only for the issued ticket.
  for (const args of [
    { ticket: "other" },
    { ticket: prepared.ticket, extra: true },
    {},
  ])
    assert.ok(registration.definition.resolve(args).error);
  const exact = workflowCall(prepared);
  for (const input of [
    { ...exact, args: { ticket: "other" } },
    { ...exact, async: false },
    { ...exact, workflow: "concorde.spec-review.other-ticket" },
  ])
    assert.equal((await call(input, "w-foreign")).block, true);
  assert.equal(await call(exact, "w-1"), undefined);
  assert.equal((await call(exact, "w-2")).block, true);
  report.workflowForeignCall = true;

  // A launch receipt is recorded as the binding; running is not a result.
  const launch = await emit("tool_result", {
    toolName: "subagent",
    toolCallId: "w-1",
    input: exact,
    isError: false,
    details: { asyncDir: path.join(root, "async"), runId: "wf-run-1" },
  });
  assert.equal(launch.details.concorde_native.state, "running");
  assert.deepEqual(
    JSON.parse(
      fs.readFileSync(
        path.join(path.dirname(prepared.descriptor), "workflow-binding.json"),
        "utf8",
      ),
    ),
    { asyncDir: path.join(root, "async"), runId: "wf-run-1" },
  );
  respond({
    "workflow-result": {
      stdout: {
        state: "running",
        accepted: false,
        native_state: "running",
        native_error: null,
        failure: null,
        run_id: "wf-run-1",
      },
    },
  });
  const running = await prepare.result("concorde-spec-review");
  assert.equal(running.state, "running");
  assert.equal(running.accepted, false);
  assert.equal(running.run_id, "wf-run-1");
  assert.equal(registration.disposed, false);
  report.workflowRunning = true;

  // A new preparation never replaces a running Workflow: it is refused and nothing is stopped.
  const beforeReplacement = actions().length;
  const preparedBefore = preparations;
  await assert.rejects(prepare({}, ctx), /still running/);
  assert.equal(preparations, preparedBefore);
  assert.equal(
    since(beforeReplacement).some((entry) => entry.action === "workflow-stop"),
    false,
  );
  assert.equal(registration.disposed, false);
  report.workflowReplacementRefused = true;

  // A receipt is reported and the registration released.
  respond({
    "workflow-result": {
      stdout: {
        state: "accepted",
        accepted: true,
        output: { answer: "done" },
        native_state: "complete",
        native_error: null,
        failure: null,
        run_id: "wf-run-1",
      },
    },
  });
  const accepted = await prepare.result("concorde-spec-review");
  assert.equal(accepted.state, "accepted");
  assert.equal(accepted.accepted, true);
  assert.deepEqual(accepted.output, { answer: "done" });
  assert.equal(registration.disposed, true);
  report.workflowAccepted = true;
}

// A launch without a binding fails, and a later result reports failed.
if (want("workflow")) {
  respond({});
  const prepared = preparedWorkflow();
  prepareAnswer = prepared;
  await prepare({}, ctx);
  for (const [id, event] of [
    ["l-1", { isError: true, details: { error: "spawn failed" } }],
  ]) {
    assert.equal(await call(workflowCall(prepared), id), undefined);
    const value = await emit("tool_result", {
      toolName: "subagent",
      toolCallId: id,
      input: workflowCall(prepared),
      content: [{ type: "text", text: "spawn failed" }],
      ...event,
    });
    assert.equal(value.isError, true);
    assert.equal(
      value.details.concorde_native.failure.layer,
      "workflow-launch",
    );
  }
  const failed = await prepare.result("concorde-spec-review");
  assert.equal(failed.state, "failed");
  assert.equal(failed.failure.layer, "workflow-launch");
  assert.equal(
    fs.existsSync(
      path.join(path.dirname(prepared.descriptor), "workflow-binding.json"),
    ),
    false,
  );
  // A launch answer without an async directory or run identity is no binding either.
  const other = preparedWorkflow();
  prepareAnswer = other;
  await prepare({}, ctx);
  assert.equal(await call(workflowCall(other), "l-2"), undefined);
  const unbound = await emit("tool_result", {
    toolName: "subagent",
    toolCallId: "l-2",
    input: workflowCall(other),
    isError: false,
    details: { runId: "r" },
  });
  assert.equal(unbound.isError, true);
  assert.equal((await prepare.result("concorde-spec-review")).state, "failed");
  report.workflowLaunchFailure = true;
}

// Shutdown stops a launched, unfinished Workflow.
if (want("workflow")) {
  respond({});
  const prepared = preparedWorkflow();
  prepareAnswer = prepared;
  await prepare({}, ctx);
  assert.equal(await call(workflowCall(prepared), "s-1"), undefined);
  await emit("tool_result", {
    toolName: "subagent",
    toolCallId: "s-1",
    input: workflowCall(prepared),
    isError: false,
    details: { asyncDir: path.join(root, "async-stop"), runId: "wf-run-stop" },
  });
  const before = actions().length;
  const events = emitted.length;
  await emit("session_shutdown", {});
  assert.deepEqual(
    since(before).map((entry) => [entry.action, entry.descriptor]),
    [["workflow-stop", prepared.descriptor]],
  );
  const stop = emitted
    .slice(events)
    .find((item) => item.name === "subagents:rpc:v1:request");
  assert.equal(stop.value.method, "stop");
  assert.deepEqual(stop.value.params, { id: "wf-run-stop" });
  assert.equal(globalThis.registrations.at(-1).disposed, true);
  report.workflowStop = true;
}

// --- Host-step transport ------------------------------------------------------------------
if (want("transport")) {
  const binding = {
    argv: [process.execPath, host],
    descriptor: "d",
    digest: "sha256:t",
    root,
    checksTimeoutMs: 300,
  };
  const failure = async (action) => {
    let caught;
    await nativeCommand(binding, action, {}).then(
      (value) => assert.fail("no answer is used: " + JSON.stringify(value)),
      (error) => {
        caught = error;
      },
    );
    return caught;
  };
  respond({
    exit: { exit: 1, raw: "partial" },
    reject: {
      exit: 3,
      stdout: {
        state: "rejected",
        accepted: false,
        result: {
          errors: [
            { code: "stale_context", field: "", message: "inputs changed" },
          ],
        },
      },
    },
    flood: { flood: 3 * 1024 * 1024 },
    checks: { sleep: 5000, stdout: { state: "late" } },
    zero: { exit: 0, raw: "not json" },
  });
  const exited = await failure("exit");
  assert.equal(exited.feedback.category, "native-exit");
  assert.ok(
    JSON.parse(exited.feedback.diagnostics.text).stdout.includes("partial"),
  );
  const rejected = await failure("reject");
  assert.equal(rejected.feedback.category, "host-refusal");
  assert.ok(
    JSON.stringify(rejected.feedback.causes).includes("inputs changed"),
  );
  assert.equal(rejected.response.state, "rejected");
  const flooded = await failure("flood");
  assert.equal(flooded.feedback.category, "observation");
  assert.equal(flooded.feedback.diagnostics.complete, false);
  const started = Date.now();
  const expired = await failure("checks");
  assert.equal(expired.feedback.category, "timeout");
  assert.ok(Date.now() - started < 4000);
  const malformed = await failure("zero");
  assert.equal(malformed.feedback.category, "transport");
  report.hostStepFailure = true;
}

fs.rmSync(root, { recursive: true, force: true });
console.log(JSON.stringify({ ...report, models: 0 }));
