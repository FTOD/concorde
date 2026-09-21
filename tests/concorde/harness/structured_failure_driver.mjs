/** Deterministic actual SDK validation -> actual native transcript -> selected report export.
 * Testers choose scenarios/assertions; this driver supplies loading/observation mechanics only.
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { validateSdkArguments } from "./native_sdk_validation.mjs";
import {
  selectedDiagnostic,
  exportDiagnostic,
} from "./structured_diagnostic.mjs";

const [sdk, native] = process.argv.slice(2);
const scratch = process.env.CONCORDE_CHECK_TMPDIR;
const { createJiti } = createRequire(path.join(sdk, "package.json"))("jiti");
const jiti = createJiti(import.meta.url, { interopDefault: true });
const { createChildTranscriptWriter } = await jiti.import(
  path.join(native, "src/shared/child-transcript.ts"),
);
const transcriptPath = path.join(scratch, "fixture-transcript.jsonl");
const writer = createChildTranscriptWriter({
  transcriptPath,
  source: "foreground",
  runId: "structured-failure-fixture",
  agent: "fixture",
  cwd: scratch,
});
const parameters = {
  type: "object",
  properties: {
    value: {
      type: "object",
      properties: {
        documents: { type: "array", items: { type: "string" } },
        detail: { type: "string" },
      },
      required: ["documents", "detail"],
      additionalProperties: false,
    },
  },
  required: ["value"],
  additionalProperties: false,
};
const args = {
  value: { detail: "deterministic selected detail ".repeat(700) },
};
writer.writeChildEvent({
  type: "message_end",
  message: {
    role: "assistant",
    content: [
      {
        type: "toolCall",
        id: "missing-documents",
        name: "structured_output",
        arguments: args,
      },
    ],
    stopReason: "toolUse",
  },
});
let actualError;
try {
  await validateSdkArguments(
    sdk,
    { name: "structured_output", parameters },
    "missing-documents",
    args,
  );
  throw new Error("fixture unexpectedly validated");
} catch (error) {
  actualError = String(error.message);
  if (!actualError.includes("documents")) throw error;
}
writer.writeChildEvent({
  type: "message_end",
  message: {
    role: "toolResult",
    toolName: "structured_output",
    toolCallId: "missing-documents",
    isError: true,
    content: [{ type: "text", text: actualError }],
  },
});
// Neither unrelated read contents nor configuration/credentials become selected diagnostics.
writer.writeChildEvent({
  type: "message_end",
  message: {
    role: "toolResult",
    toolName: "read",
    toolCallId: "private-read",
    content: [{ type: "text", text: "SECRET_UNRELATED_READ" }],
  },
});
fs.writeFileSync(path.join(scratch, "auth.json"), "SECRET_AUTH_SCRATCH");
fs.writeFileSync(path.join(scratch, "settings.json"), "SECRET_CONFIG_SCRATCH");
const diagnostic = selectedDiagnostic({
  workflowRunId: "fixture-workflow",
  key: "d-0",
  ticket: "fixture-ticket",
  schema: parameters,
  metadata: { runId: "structured-failure-fixture", exitCode: 17 },
  transcript: fs.readFileSync(transcriptPath, "utf8"),
});
const report = exportDiagnostic(diagnostic);
// Exercise the actual OS write refusal, not a mocked capability observer.
let denied = false;
try {
  fs.writeFileSync(path.join(process.cwd(), "forbidden-write"), "bad");
} catch (error) {
  denied = error.code === "EROFS";
}
if (!denied) throw new Error("governing filesystem was not read-only");
console.error("SDK structured_output rejected: value.documents is required");
console.log(
  JSON.stringify({ report, scratch, readOnly: denied, realModelCalls: 0 }),
);
process.exitCode = 17;
