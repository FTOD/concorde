/** Actual SDK tool validation -> notification failure -> native extension-error transcript.
 * Only provider responses are loopback scripted. No live model or child launch.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
const [sdkRoot, nativeRoot, candidate, scratch, baseUrl] =
  process.argv.slice(2);
const sdk = await import(pathToFileURL(path.join(sdkRoot, "dist/index.js")));
const { createJiti } = createRequire(path.join(sdkRoot, "package.json"))(
  "jiti",
);
const jiti = createJiti(import.meta.url, { interopDefault: true });
const { observeNativeProposal } = await jiti.import(
  path.join(candidate, "pi/native-proposal.ts"),
);
const { createChildTranscriptWriter } = await jiti.import(
  path.join(nativeRoot, "src/shared/child-transcript.ts"),
);
const { withChildSessionErrorReporting } = await jiti.import(
  path.join(nativeRoot, "src/runs/shared/child-hooks.ts"),
);
const transcriptPath = path.join(scratch, "native-transcript.jsonl");
const writer = createChildTranscriptWriter({
  transcriptPath,
  source: "foreground",
  runId: "observation-fixture",
  agent: "fixture",
  cwd: scratch,
});
const native = withChildSessionErrorReporting({ hooks: [] }, writer);
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
        models: [{ id: "fixture" }],
      },
    },
  }),
);
const settingsManager = sdk.SettingsManager.inMemory({
  packages: [],
  compaction: { enabled: false },
  retry: { enabled: false },
});
let observationCalls = 0,
  submitted = 0,
  invalidated = 0;
const errors = [],
  ends = [],
  results = [];
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
  extensionFactories: [
    (pi) => {
      pi.registerTool({
        name: "structured_output",
        label: "Fixture structured output",
        description: "Fixture only",
        parameters: {
          type: "object",
          properties: {
            value: {
              type: "object",
              properties: { answer: { type: "string" } },
              required: ["answer"],
              additionalProperties: false,
            },
          },
          required: ["value"],
          additionalProperties: false,
        },
        async execute() {
          return {
            content: [{ type: "text", text: "valid fixture" }],
            details: {},
          };
        },
      });
      observeNativeProposal(
        pi,
        async () => {
          submitted++;
        },
        async () => {
          invalidated++;
        },
        async () => {
          observationCalls++;
          throw Object.assign(
            new Error("independent observe-error persistence denied"),
            { code: "EACCES" },
          );
        },
      );
      pi.on("tool_execution_end", (e) => {
        ends.push(e);
      });
      pi.on("tool_result", (e) => {
        results.push(e);
      });
    },
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
const { session } = await sdk.createAgentSession({
  cwd: candidate,
  agentDir,
  resourceLoader: loader,
  settingsManager,
  modelRuntime,
  model: modelRuntime.getModel("fixture", "fixture"),
  sessionManager: sdk.SessionManager.inMemory(candidate),
  tools: ["structured_output"],
});
await session.bindExtensions({
  mode: "print",
  onError: (error) => {
    errors.push(error);
    native.onExtensionError(error);
  },
});
try {
  await session.prompt(
    "Exercise schema rejection and corrected submission using scripted fixture only",
  );
  assert.equal(observationCalls, 1);
  assert.equal(submitted, 1);
  assert.equal(invalidated, 0);
  assert.equal(
    results.length,
    1,
    "SDK immediate rejection must bypass tool_result",
  );
  assert.equal(ends.length, 2);
  assert.equal(errors.length, 1);
  const f = JSON.parse(errors[0].error);
  assert.equal(f.category, "schema-rejection");
  assert.equal(f.attempt, ends[0].toolCallId);
  assert.match(f.diagnostics.text, /answer/);
  assert.equal(f.diagnostics.complete, false);
  assert.equal(f.causes[0].code, "EACCES");
  assert.equal(f.causes[0].attempt, f.attempt);
  await session.extensionRunner.emit(ends[0]);
  assert.equal(
    observationCalls,
    1,
    "Do not retry unknown persistence side effects",
  );
  assert.equal(errors.length, 2);
  assert.deepEqual(JSON.parse(errors[1].error), f);
  const transcript = fs.readFileSync(transcriptPath, "utf8");
  assert(transcript.includes("EACCES"));
  assert(transcript.includes(f.attempt));
  assert(transcript.includes("answer"));
  fs.writeFileSync(
    path.join(scratch, "observation-feedback.json"),
    JSON.stringify(f, null, 2),
    { mode: 0o600 },
  );
  console.log(
    JSON.stringify({
      actualSdkValidation: true,
      immediateBypassedToolResult: true,
      nativeReportingRetained: true,
      repeatedErrorReported: true,
      observationCalls,
      submitted,
      invalidated,
      feedback: f,
      realModelCalls: 0,
    }),
  );
} finally {
  session.dispose();
}
