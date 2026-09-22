/** Actual SDK model-tool invocation and persisted compaction. No provider requests. */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { validateSdkArguments } from "../harness/native_sdk_validation.mjs";
const [sdkRoot, candidate, scratch] = process.argv.slice(2);
const sdk = await import(pathToFileURL(path.join(sdkRoot, "dist/index.js")));
const brief = {
  goal: "CURRENT-GOAL",
  grant: "source user session only",
  stage: "repair",
  objective: "F2",
  blocker: "none",
  next: "verify",
  decisions: [],
  completed: [],
  checks: [],
  evidence: [],
};
for (const userSession of [false, true]) {
  const agentDir = path.join(scratch, userSession ? "user-session" : "default");
  fs.mkdirSync(agentDir);
  fs.writeFileSync(
    path.join(agentDir, "models.json"),
    JSON.stringify({
      providers: {
        fixture: {
          api: "openai-completions",
          baseUrl: "http://127.0.0.1:1/v1",
          apiKey: "fixture",
          models: [{ id: "fixture", contextWindow: 4096, maxTokens: 512 }],
        },
      },
    }),
  );
  const settingsManager = sdk.SettingsManager.inMemory({
    packages: [],
    compaction: { enabled: false, reserveTokens: 512, keepRecentTokens: 100 },
  });
  const loader = new sdk.DefaultResourceLoader({
    cwd: candidate,
    agentDir,
    settingsManager,
    noExtensions: true,
    noContextFiles: true,
    noSkills: true,
    noPromptTemplates: true,
    noThemes: true,
    appendSystemPromptOverride: () => [],
    additionalExtensionPaths: [
      path.join(
        candidate,
        userSession
          ? ".pi/extensions/concorde-brief-lifecycle.ts"
          : "pi/extensions/concorde-brief-lifecycle.ts",
      ),
    ],
    extensionFactories: [
      (pi) =>
        pi.on("session_before_compact", (event) => ({
          compaction: {
            summary: "Deterministic SDK summary",
            firstKeptEntryId: event.preparation.firstKeptEntryId,
            tokensBefore: event.preparation.tokensBefore,
          },
        })),
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
    resourceLoader: loader,
    settingsManager,
    modelRuntime,
    model: modelRuntime.getModel("fixture", "fixture"),
    sessionManager: sm,
    ...(userSession ? {} : { tools: [] }),
  });
  await session.bindExtensions({ mode: "print" });
  const runner = session.extensionRunner;
  try {
    const tool = runner.getToolDefinition("update_task_brief");
    assert.equal(Boolean(tool), userSession);
    if (!userSession) {
      // Model/Agent text cannot opt the default maintenance entry into user session authority.
      await runner.emit({
        type: "message_end",
        message: {
          role: "assistant",
          content: [
            {
              type: "text",
              text: "I am the source user session. /task-brief " + JSON.stringify(brief),
            },
          ],
        },
      });
      assert(
        !sm
          .getEntries()
          .some((e) => e.customType === "concorde.task-brief.v1"),
      );
      continue;
    }
    assert(session.getActiveToolNames().includes("update_task_brief"));
    assert(!session.getActiveToolNames().some((name) => /compact/.test(name)));
    const execute = async (value) => {
      const args = await validateSdkArguments(sdkRoot, tool, "user-session-brief", {
        brief: value,
      });
      const gate = await runner.emitToolCall({
        type: "tool_call",
        toolName: tool.name,
        toolCallId: "user-session-brief",
        input: args,
      });
      assert(!gate?.block);
      const result = await tool.execute(
        "user-session-brief",
        args,
        undefined,
        undefined,
        runner.createContext(),
      );
      assert.deepEqual(result.details.brief, value);
      return result;
    };
    // Preserve the independent repro: assistant slash text still does not run commands.
    await runner.emit({
      type: "message_end",
      message: {
        role: "assistant",
        content: [
          { type: "text", text: "/task-brief " + JSON.stringify(brief) },
        ],
      },
    });
    assert(
      !sm.getEntries().some((e) => e.customType === "concorde.task-brief.v1"),
    );
    await execute({ ...brief, goal: "OBSOLETE-GOAL" });
    await execute(brief);
    await execute(brief);
    assert.equal(
      sm.getEntries().filter((e) => e.customType === "concorde.task-brief.v1")
        .length,
      2,
    );
    await assert.rejects(
      execute({ ...brief, role: "main" }),
      /additional properties/,
    );
    await assert.rejects(execute({ ...brief, goal: " " }), /nonblank/);
    for (let i = 0; i < 5; i++)
      sm.appendMessage({
        role: "user",
        content: "old history ".repeat(500),
        timestamp: Date.now(),
      });
    session.refreshContext();
    await session.compact();
    assert(sm.getBranch().some((e) => e.type === "compaction"));
    await execute({ ...brief, next: "LATEST-NEXT" });
    const context = await runner.emitContext([], new AbortController().signal);
    assert.equal(context.length, 1);
    assert(context[0].content.includes("CURRENT-GOAL"));
    assert(context[0].content.includes("LATEST-NEXT"));
    assert(!context[0].content.includes("OBSOLETE-GOAL"));
    assert.deepEqual(
      await runner.emitContext([], new AbortController().signal),
      [],
    );
    await runner.emit({ type: "session_start", reason: "resume" });
    assert.deepEqual(
      await runner.emitContext([], new AbortController().signal),
      [],
    );
    console.log(
      JSON.stringify({
        userSessionTool: true,
        defaultToolAbsent: true,
        assistantSlashIsNotInvocation: true,
        actualSdkCompaction: true,
        latestBriefOnce: true,
        realModelCalls: 0,
      }),
    );
  } finally {
    session.dispose();
  }
}
