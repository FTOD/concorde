/** One explicitly authorized native Issue attempt. Default is model-free selftest. */
import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { nativeObservation } from "./native_observation.mjs";
import {
  selectedDiagnostic,
  packDiagnostic,
  unpackDiagnostic,
  sanitize,
} from "./structured_diagnostic.mjs";

const { C, S, SDK, NATIVE } = process.env;
const json = (file) => JSON.parse(fs.readFileSync(file, "utf8"));
const { createJiti } = createRequire(path.join(SDK, "package.json"))("jiti");
const jiti = createJiti(import.meta.url, { interopDefault: true });
// Configure before importing any producer module. No child-factory setter or SDK facade is used.
Object.assign(process.env, {
  PI_CODING_AGENT_DIR: path.join(S, "operator"),
  PI_SUBAGENTS_TEMP_ROOT: path.join(S, "native"),
  PI_SUBAGENTS_LLM_INTENT_ARBITER: "0",
  PI_SUBAGENTS_PI_CODING_AGENT_PACKAGE_ROOT: SDK,
  CONCORDE_NATIVE_SUBAGENTS_ROOT: NATIVE,
  CONCORDE_NATIVE_PROJECT_ROOT: path.join(S, "candidate"),
  PI_SUBAGENT_MAX_SPAWNS_PER_RUN: "8",
});
const { createChildTranscriptWriter } = await jiti.import(
  path.join(NATIVE, "src/shared/child-transcript.ts"),
);
function preflight(schema = { type: "object" }, ticket = "selftest") {
  const file = path.join(S, "diagnostic-selftest.jsonl");
  const w = createChildTranscriptWriter({
    transcriptPath: file,
    source: "foreground",
    runId: "selftest",
    agent: "fixture",
    cwd: S,
  });
  w.writeChildEvent({
    type: "message_end",
    message: {
      role: "assistant",
      content: [
        {
          type: "toolCall",
          id: "invalid",
          name: "structured_output",
          arguments: { value: { missingRequired: true } },
        },
      ],
      stopReason: "toolUse",
    },
  });
  w.writeChildEvent({
    type: "tool_execution_start",
    toolName: "structured_output",
    toolCallId: "invalid",
    args: { value: { missingRequired: true } },
  });
  w.writeChildEvent({
    type: "tool_execution_end",
    toolName: "structured_output",
    toolCallId: "invalid",
    isError: true,
  });
  w.writeChildEvent({
    type: "message_end",
    message: {
      role: "toolResult",
      toolName: "structured_output",
      toolCallId: "invalid",
      content: [
        {
          type: "text",
          text: "Complete selected schema error: required value missing",
        },
      ],
      isError: true,
    },
  });
  const d = selectedDiagnostic({
    workflowRunId: "selftest",
    key: "d-0",
    ticket,
    schema,
    metadata: { runId: "selftest", exitCode: 1 },
    transcript: fs.readFileSync(file, "utf8"),
  });
  const e = packDiagnostic(d);
  assert.deepEqual(unpackDiagnostic(e), d);
  assert(d.attempts[0].errorComplete);
  assert.equal(d.attempts[0].arguments.value.missingRequired, true);
  assert(Buffer.byteLength(JSON.stringify(e)) < 8000);
}
preflight();
if (!process.argv.includes("--live")) {
  console.log(
    JSON.stringify({ selftest: true, live: false, realModelCalls: 0 }),
  );
  process.exit(0);
}
assert(
  process.env.CONCORDE_DIAGNOSTIC_MODEL &&
    process.env.CONCORDE_DIAGNOSTIC_AUTH &&
    process.env.CONCORDE_DIAGNOSTIC_MODELS,
  "explicit model and approved credential/model-file paths required",
);
let session, prepared, artifactRoot;
const observation = nativeObservation(path.join(S, "issue-observation"));
const summary = {
  liveAttempt: true,
  coordinatorModelCalls: 0,
  effectiveStart: "unknown",
  result: null,
  diagnosticComplete: false,
  driverError: null,
};
try {
  const sdk = await import(path.join(SDK, "dist/index.js")),
    agentDir = path.join(S, "operator");
  fs.mkdirSync(agentDir, { mode: 0o700 });
  fs.copyFileSync(
    process.env.CONCORDE_DIAGNOSTIC_AUTH,
    path.join(agentDir, "auth.json"),
  );
  fs.chmodSync(path.join(agentDir, "auth.json"), 0o600);
  // Native default child sessions read this scratch settings file, not the parent's in-memory settings.
  fs.writeFileSync(
    path.join(agentDir, "settings.json"),
    JSON.stringify({
      retry: { enabled: false },
      compaction: { enabled: false },
      packages: [],
    }),
    { mode: 0o600 },
  );
  fs.symlinkSync(
    fs.realpathSync(process.env.CONCORDE_DIAGNOSTIC_MODELS),
    path.join(agentDir, "models.json"),
  );
  const [provider, ...idParts] =
      process.env.CONCORDE_DIAGNOSTIC_MODEL.split("/"),
    id = idParts.join("/");
  const settings = sdk.SettingsManager.inMemory({
    defaultProvider: provider,
    defaultModel: id,
    defaultThinkingLevel: "medium",
    compaction: { enabled: false },
    retry: { enabled: false },
    packages: [],
  });
  const loader = new sdk.DefaultResourceLoader({
    cwd: C,
    agentDir,
    settingsManager: settings,
    noExtensions: true,
    noContextFiles: true,
    noSkills: true,
    noPromptTemplates: true,
    noThemes: true,
    additionalExtensionPaths: [
      path.join(C, "generated/session/pi/concorde-session.ts"),
      path.join(NATIVE, "index.ts"),
    ],
    appendSystemPromptOverride: () => [],
  });
  await loader.reload();
  assert.equal(loader.getExtensions().errors.length, 0);
  assert.equal(loader.getSkills().skills.length, 0);
  assert.equal(loader.getAgentsFiles().agentsFiles.length, 0);
  assert.equal(loader.getAppendSystemPrompt().length, 0);
  const modelRuntime = await sdk.ModelRuntime.create({
      authPath: path.join(agentDir, "auth.json"),
      modelsPath: path.join(agentDir, "models.json"),
      modelsStorePath: path.join(S, "models-store.json"),
      allowModelNetwork: false,
    }),
    model = modelRuntime.getModel(provider, id);
  assert(model, "parent model discovery failed");
  const nativeDiscovery = await sdk.ModelRuntime.create({
    allowModelNetwork: false,
  });
  assert(
    nativeDiscovery.getModel(provider, id),
    "native default model discovery failed",
  );
  ({ session } = await sdk.createAgentSession({
    cwd: C,
    agentDir,
    resourceLoader: loader,
    settingsManager: settings,
    sessionManager: sdk.SessionManager.inMemory(C),
    modelRuntime,
    model,
    thinkingLevel: "medium",
    tools: [],
  }));
  await session.bindExtensions({ mode: "print" });
  const { getArtifactsDir } = await jiti.import(
    path.join(NATIVE, "src/shared/artifacts.ts"),
  );
  artifactRoot = getArtifactsDir(
    session.sessionManager.getSessionFile() ?? null,
  );
  const runner = session.extensionRunner;
  let calls = 0;
  async function tool(name, input) {
    const callId = "diagnostic-" + ++calls;
    const gate = await runner.emitToolCall({
      type: "tool_call",
      toolName: name,
      toolCallId: callId,
      input,
    });
    assert(!gate?.block, gate?.reason);
    const result = await runner
      .getToolDefinition(name)
      .execute(
        callId,
        input,
        new AbortController().signal,
        undefined,
        runner.createContext(),
      );
    const observed = await runner.emitToolResult({
      type: "tool_result",
      toolName: name,
      toolCallId: callId,
      input,
      ...result,
      isError: !!result.isError,
    });
    return { ...result, ...observed };
  }
  await tool("concorde", { operation: "concorde-issues", action: "describe" });
  const f = json(path.join(S, "fixture.json"));
  prepared = (
    await tool("concorde", {
      operation: "concorde-issues",
      action: "run",
      input: {
        action: "solve",
        issue_id: f.receipt.issue_id,
        target_id: "module.increment",
        task: "Resolve selected Issue",
        change_id: f.change_id,
        expected_revision: f.revision,
      },
    })
  ).details;
  assert.equal(prepared.state, "prepared");
  const root = json(prepared.descriptor);
  // Exercise actual issued schema/transport roundtrip BEFORE any child model execution.
  const { issueCall, issueLayout } = await import(
    path.join(C, "pi/issue-call.mjs")
  );
  const issued = issueCall(
    issueLayout(root, prepared.descriptor, prepared.digest),
    "d-0",
  );
  preflight(issued.outputSchema, prepared.ticket + ":d-0");
  const launched = await tool("subagent", prepared.call);
  assert(!launched.isError, "native launch refused");
  const deadline = Date.now() + 1100000;
  let result;
  do {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    result = (
      await tool("concorde", { operation: "concorde-issues", action: "result" })
    ).details;
    summary.result = {
      accepted: result.accepted,
      state: result.state,
      native_state: result.native_state,
      decision: result.output?.data?.decision,
      outcome: result.output?.data?.outcome,
    };
    if (result.native_state !== "running") break;
  } while (Date.now() < deadline);
  assert(result.native_state !== "running", "outer diagnostic deadline");
} catch (error) {
  summary.driverError = sanitize(String(error.message ?? error)).slice(0, 400);
} finally {
  try {
    if (prepared?.descriptor && artifactRoot) {
      observation.collect(prepared.descriptor, {
        artifactRoots: [artifactRoot],
      });
      const d = json(path.join(S, "issue-observation/child-0-structured.json"));
      const envelope = packDiagnostic(d);
      assert.deepEqual(unpackDiagnostic(envelope), d);
      fs.writeFileSync(
        path.join(S, "diagnostic-envelope.json"),
        JSON.stringify(envelope),
        { mode: 0o600 },
      );
      summary.diagnosticComplete =
        d.sourceRecords === "present" &&
        !d.transcriptTruncated &&
        d.malformedRecords === 0 &&
        d.attempts.every(
          (a) =>
            a.argumentsComplete &&
            typeof a.isError === "boolean" &&
            (a.isError !== true || a.errorComplete),
        );
    }
  } catch (error) {
    summary.observationError = sanitize(String(error.message ?? error)).slice(
      0,
      400,
    );
  }
  if (session) {
    try {
      await session.extensionRunner.emit({ type: "session_shutdown" });
      session.dispose();
    } catch {
      summary.shutdownError = true;
    }
  }
  fs.writeFileSync(path.join(S, "summary.json"), JSON.stringify(summary), {
    mode: 0o600,
  });
}
