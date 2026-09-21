/** Actual installed SDK loading and compaction; deterministic summaries/events, no model or child launch. */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
const [sdkRoot, candidate, scratch, baseUrl] = process.argv.slice(2);
const sdk = await import(pathToFileURL(path.join(sdkRoot, "dist/index.js")));
const agentDir = path.join(scratch, "agent");
fs.mkdirSync(agentDir);
fs.writeFileSync(
  path.join(agentDir, "models.json"),
  JSON.stringify({
    providers: {
      fixture: {
        api: "openai-completions",
        baseUrl,
        apiKey: "fixture",
        models: [{ id: "fixture", contextWindow: 4096, maxTokens: 512 }],
      },
    },
  }),
);
const settings = sdk.SettingsManager.inMemory({
  packages: [],
  compaction: { enabled: true, reserveTokens: 512, keepRecentTokens: 100 },
  retry: { enabled: false },
});
let cancel = false;
const attempts = [];
const loader = new sdk.DefaultResourceLoader({
  cwd: candidate,
  agentDir,
  settingsManager: settings,
  noExtensions: true,
  noContextFiles: true,
  noSkills: true,
  noPromptTemplates: true,
  noThemes: true,
  appendSystemPromptOverride: () => [],
  additionalExtensionPaths: [
    path.join(candidate, "pi/extensions/concorde-outer-lifecycle.ts"),
    path.join(candidate, "pi/extensions/concorde-maintenance.ts"),
  ],
  extensionFactories: [
    (pi) =>
      pi.on("session_before_compact", (event) => {
        attempts.push({
          reason: event.reason,
          tokens: event.preparation.tokensBefore,
          reserve: event.preparation.settings.reserveTokens,
        });
        if (cancel) return { cancel: true };
        return {
          compaction: {
            summary: "Deterministic summary",
            firstKeptEntryId: event.preparation.firstKeptEntryId,
            tokensBefore: event.preparation.tokensBefore,
          },
        };
      }),
  ],
});
await loader.reload();
assert.deepEqual(loader.getExtensions().errors, []);
const modelRuntime = await sdk.ModelRuntime.create({
  authPath: path.join(agentDir, "auth.json"),
  modelsPath: path.join(agentDir, "models.json"),
  modelsStorePath: path.join(agentDir, "models-store.json"),
  allowModelNetwork: false,
});
const sm = sdk.SessionManager.inMemory(candidate);
const { session } = await sdk.createAgentSession({
  cwd: candidate,
  agentDir,
  modelRuntime,
  model: modelRuntime.getModel("fixture", "fixture"),
  resourceLoader: loader,
  settingsManager: settings,
  sessionManager: sm,
  tools: ["read", "grep", "find", "ls", "bash", "edit", "write"],
});
await session.bindExtensions({ mode: "print" });
const runner = session.extensionRunner;
const tools = session.getActiveToolNames();
assert(!tools.includes("subagent") && !tools.includes("concorde"));
const brief = {
  goal: "CURRENT-GOAL",
  grant: "candidate only; no delegation",
  stage: "component",
  objective: "SDK fixture",
  blocker: "none",
  next: "verify",
  decisions: ["accepted scope"],
  completed: ["extension"],
  checks: ["fixture pending"],
  evidence: ["fixture.mjs"],
};
const report = (value) =>
  runner.emitToolCall({
    type: "tool_call",
    toolCallId: "feedback",
    toolName: "contact_supervisor",
    input: {
      reason: "progress_update",
      message:
        "UPDATE: meaningful evidence\n```task-brief\n" +
        JSON.stringify(value) +
        "\n```",
    },
  });
const projectContext = () =>
  runner.emitContext([], new AbortController().signal);
let requests = 0;
const seedAssistant = (error = false) => {
  sm.appendMessage({
    role: "assistant",
    content: [{ type: "text", text: "fixture" }],
    api: "openai-completions",
    provider: "fixture",
    model: "fixture",
    stopReason: error ? "error" : "stop",
    ...(error ? { errorMessage: "maximum context length exceeded" } : {}),
    usage: {
      input: 3900,
      output: 1,
      cacheRead: 0,
      cacheWrite: 0,
      totalTokens: 3901,
      cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 },
    },
    timestamp: Date.now() + 1,
  });
  session.refreshContext();
};
const seed = () => {
  for (let i = 0; i < 5; i++)
    sm.appendMessage({
      role: "user",
      content: "obsolete history ".repeat(500),
      timestamp: Date.now(),
    });
  session.refreshContext();
};
try {
  await assert.rejects(session.compact(), /Nothing to compact/);
  assert(
    sm
      .getEntries()
      .some(
        (e) =>
          e.customType === "concorde.outer-compaction-failed.v1" &&
          !e.data.aborted &&
          e.data.hasErrorMessage,
      ),
  );
  assert.deepEqual(await projectContext(), []);
  await report({ ...brief, goal: "OBSOLETE-GOAL" });
  await report(brief);
  await report(brief);
  assert.equal(
    sm.getEntries().filter((e) => e.customType === "concorde.outer-brief.v1")
      .length,
    2,
  );
  assert.deepEqual(await projectContext(), []); // A checkpoint is not compaction.
  seed();
  await session.prompt("/outer-compact"); // Actual command -> ctx.compact -> persisted SDK compaction.
  assert.equal(attempts.length, 1);
  assert(sm.getBranch().some((e) => e.type === "compaction"));
  await report({ ...brief, next: "LATEST-NEXT" }); // Update after compaction, before next request.
  let context = await projectContext();
  assert.equal(context.length, 1);
  assert(
    context[0].content.includes("CURRENT-GOAL") &&
      context[0].content.includes("LATEST-NEXT"),
  );
  assert(!context[0].content.includes("OBSOLETE-GOAL"));
  assert.deepEqual(await projectContext(), []);
  await runner.emit({ type: "session_start", reason: "resume" });
  assert.deepEqual(await projectContext(), []);
  // The SDK's automatic threshold path uses measured projected input and the same real compactor.
  seed();
  seedAssistant();
  assert(session.getContextUsage().tokens > 4096 - 512);
  await session.prompt("Threshold fixture request");
  requests++;
  assert.equal(attempts.at(-1).reason, "threshold");
  assert(attempts.at(-1).tokens > 4096 - 512);
  assert.deepEqual(await projectContext(), []); // Real request already consumed new compaction's brief.
  assert.equal(
    sm
      .getEntries()
      .filter((e) => e.customType === "concorde.outer-brief-injected.v1")
      .length,
    2,
  );
  seed();
  seedAssistant(true);
  await session.prompt("Overflow fixture request");
  requests++;
  assert.equal(attempts.at(-1).reason, "overflow");
  assert.deepEqual(await projectContext(), []);
  assert.equal(
    sm
      .getEntries()
      .filter((e) => e.customType === "concorde.outer-brief-injected.v1")
      .length,
    3,
  );
  seed();
  cancel = true;
  // Extension-command errors are reported by Pi, not rethrown by session.prompt.
  await session.prompt("/outer-compact");
  assert(
    sm
      .getEntries()
      .some(
        (e) =>
          e.customType === "concorde.outer-compaction-failed.v1" &&
          e.data.aborted,
      ),
  );
  assert.deepEqual(await projectContext(), []);
  assert(
    sm
      .getEntries()
      .some((e) => e.customType === "concorde.outer-compaction-failed.v1"),
  );
  cancel = false;
  seed();
  await session.compact();
  await report({ goal: "invalid" });
  assert.deepEqual(await projectContext(), []);
  await runner.emit({ type: "session_start", reason: "resume" });
  assert.deepEqual(await projectContext(), []);
  // Real branch navigation restores only memory on that branch, not future reports.
  const oldBrief = sm
    .getEntries()
    .find((e) => e.customType === "concorde.outer-brief.v1");
  await session.navigateTree(oldBrief.id, { summarize: false });
  assert.deepEqual(await projectContext(), []);
  await session.prompt(
    "/outer-brief " + JSON.stringify({ ...brief, goal: "BRANCH-GOAL" }),
  );
  seed();
  await session.compact();
  const branchContext = await projectContext();
  assert.equal(branchContext.length, 1);
  assert(branchContext[0].content.includes("BRANCH-GOAL"));
  assert(!branchContext[0].content.includes("LATEST-NEXT"));
  assert.deepEqual(session.getActiveToolNames(), tools);
  assert(
    (
      await runner.emitToolCall({
        type: "tool_call",
        toolCallId: "denied",
        toolName: "subagent",
        input: {},
      })
    ).block,
  );
  console.log(
    JSON.stringify({
      sdk: JSON.parse(fs.readFileSync(path.join(sdkRoot, "package.json")))
        .version,
      attempts,
      tools,
      fixtureRequests: requests,
      liveModelCalls: 0,
      childLaunches: 0,
    }),
  );
} finally {
  session.dispose();
}
