/** Load the exact tester extension through the real SDK and invoke one tool, never a model.
 * Caller owns a disposable governing fixture; source entry/runtime remain canonical/read-only.
 */
import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
import { validateSdkArguments } from "./native_sdk_validation.mjs";

const [source, sdkRoot, cwd, agentDir] = process.argv.slice(2);
const request = JSON.parse(fs.readFileSync(0, "utf8"));
const sdk = await import(
  pathToFileURL(path.join(sdkRoot, "dist/index.js")).href
);
const settingsManager = sdk.SettingsManager.inMemory({
  packages: [],
  compaction: { enabled: false },
  retry: { enabled: false },
});
const loader = new sdk.DefaultResourceLoader({
  cwd,
  agentDir,
  settingsManager,
  noExtensions: true,
  noContextFiles: true,
  noSkills: true,
  noPromptTemplates: true,
  noThemes: true,
  additionalExtensionPaths: [
    path.join(source, "generated/session/pi/concorde-session.ts"),
    path.join(source, "pi/extensions/concorde-tester.ts"),
  ],
  appendSystemPromptOverride: () => [],
});
await loader.reload();
assert.deepEqual(loader.getExtensions().errors, []);
const modelRuntime = await sdk.ModelRuntime.create({
  authPath: path.join(agentDir, "auth.json"),
  modelsPath: path.join(agentDir, "models.json"),
  modelsStorePath: path.join(agentDir, "models-store.json"),
  allowModelNetwork: false,
});
const { session } = await sdk.createAgentSession({
  cwd,
  agentDir,
  resourceLoader: loader,
  settingsManager,
  sessionManager: sdk.SessionManager.inMemory(cwd),
  modelRuntime,
  tools: [],
});
await session.bindExtensions({ mode: "print" });
const runner = session.extensionRunner;
const tool = runner.getToolDefinition("test_command");
assert(tool, "actual SDK did not register test_command");
const controller = new AbortController();
const timer =
  request.abortAfterMs === undefined
    ? null
    : setTimeout(() => controller.abort(), request.abortAfterMs);
let result;
try {
  const admitted = await validateSdkArguments(
    sdkRoot,
    tool,
    "tester-evidence-fixture",
    request.params,
  );
  const gate = await runner.emitToolCall({
    type: "tool_call",
    toolName: "test_command",
    toolCallId: "tester-evidence-fixture",
    input: admitted,
  });
  assert(!gate?.block, gate?.reason);
  const value = await tool.execute(
    "tester-evidence-fixture",
    admitted,
    controller.signal,
    undefined,
    runner.createContext(),
  );
  result = { isError: false, response: value.details };
} catch (error) {
  result = { isError: true, response: JSON.parse(error.message) };
} finally {
  if (timer) clearTimeout(timer);
  await runner.emit({ type: "session_shutdown" });
  session.dispose();
}
console.log(JSON.stringify({ ...result, sdkLoaded: true, realModelCalls: 0 }));
