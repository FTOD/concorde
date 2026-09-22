/** Actual public SDK argument validation against native double-wrapped result schemas. Zero models. */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { validateSdkArguments } from "./native_sdk_validation.mjs";
import { issueCall } from "../../../pi/issue-call.mjs";

const [producer, sdk, source] = process.argv.slice(2);
const { createJiti } = createRequire(path.join(sdk, "package.json"))("jiti");
const jiti = createJiti(import.meta.url, { interopDefault: true });
const { createStructuredOutputToolParameters } = await jiti.import(
  path.join(producer, "src/runs/shared/structured-output.ts"),
);
const f = JSON.parse(
  fs.readFileSync(
    new URL("./fixtures/issue-sdk-rejections.json", import.meta.url),
    "utf8",
  ),
);
const schemas = JSON.parse(
  execFileSync(
    path.join(source, ".venv/bin/python"),
    [
      "-c",
      `import json;from concorde.harness.native_context import native_output_schema;print(json.dumps({k:native_output_schema(k) for k in ['concorde-agent-stage-result','concorde-review-stage-result']}))`,
    ],
    {
      env: { ...process.env, PYTHONPATH: path.join(source, "src") },
      encoding: "utf8",
    },
  ),
);
const valid = {
  invocation_id: f.ticket,
  result: {
    type_id: "concorde-agent-stage-result",
    schema_version: 3,
    data: {
      context_id: f.context_id,
      outcome: "completed",
      answer: "A bounded decision",
      blockers: [],
      documents: [],
      plan: "",
      tasks: [],
      issue_decision: {
        action: "verify",
        intent: "Increment correctly",
        rationale: "Request current review",
        duplicate_of: null,
      },
    },
  },
};
const tool = (schema) => ({
  name: "structured_output",
  description: "Actual native schema wrapped by its producer",
  parameters: createStructuredOutputToolParameters(schema),
});
const errors = { before: [], after: [] };
// Even a complete valid result failed at the SDK layer under the preserved broken issued schema.
for (const args of [{ value: valid }, ...f.invalid_arguments]) {
  await assert.rejects(
    () =>
      validateSdkArguments(
        sdk,
        tool(f.issued_schema_before_fix),
        "before",
        args,
      ),
    (error) => {
      assert.match(error.message, /value\.result\.data: schema is false/);
      errors.before.push(error.message.split("Received arguments:")[0]);
      return true;
    },
  );
}
const fixed = structuredClone(schemas["concorde-agent-stage-result"]);
fixed.properties.invocation_id = { const: f.ticket };
for (const action of ["verify", "resolved"]) {
  const value = structuredClone(valid);
  value.result.data.issue_decision.action = action;
  assert.deepEqual(
    await validateSdkArguments(sdk, tool(fixed), "valid", { value }),
    { value },
  );
}
for (const args of f.invalid_arguments) {
  await assert.rejects(
    () => validateSdkArguments(sdk, tool(fixed), "retained-invalid", args),
    (error) => {
      // The old unresolved root rejected data itself, even for valid values.
      // SDK 0.87 also uses "schema is false" for a legitimately forbidden extra
      // issue_decision.issue_id property; that is not the old composition defect.
      assert(!error.message.includes("value.result.data: schema is false"));
      assert.match(error.message, /context_id.*outcome/);
      errors.after.push(error.message.split("Received arguments:")[0]);
      return true;
    },
  );
}
assert.match(errors.after[0], /plan: must be string/);
assert.match(
  errors.after[1],
  /issue_decision: must not have additional properties/,
);
// Match actual Issue call construction for decisions and both verification modes.
const root = {
  ticket: "issued",
  directory: "/fixture",
  gatePrefix: "host-only",
  stageSchema: schemas["concorde-agent-stage-result"],
  reviewSchema: schemas["concorde-review-stage-result"],
};
for (const key of ["d-0", "v-0-0-0", "v-0-1-0"]) {
  const call = issueCall(root, key),
    isReview = key.startsWith("v-");
  const value = isReview
    ? {
        invocation_id: root.ticket + ":" + key,
        result: {
          type_id: "concorde-review-stage-result",
          schema_version: 2,
          data: {
            context_id: f.context_id,
            input_digest: f.context_id,
            review_mode: key === "v-0-0-0" ? "spec" : "code",
            status: "no_findings",
            representative_tasks: ["Verify increment"],
            issues: [],
            answer: "Scoped evidence",
          },
        },
      }
    : { ...valid, invocation_id: root.ticket + ":" + key };
  assert.deepEqual(
    await validateSdkArguments(sdk, tool(call.outputSchema), "slot", { value }),
    { value },
  );
  const direct = structuredClone(schemas[value.result.type_id]);
  direct.properties.invocation_id = { const: value.invocation_id };
  assert.deepEqual(call.outputSchema, direct);
  assert.deepEqual(
    await validateSdkArguments(sdk, tool(direct), "direct", { value }),
    { value },
  );
  // Preserve closed wrappers and required fields through BOTH result and native value wrapping.
  const extra = structuredClone(value);
  extra.foreign = true;
  await assert.rejects(
    () => validateSdkArguments(sdk, tool(direct), "extra", { value: extra }),
    /additional properties/,
  );
  const missing = structuredClone(value);
  delete missing.result.data.context_id;
  await assert.rejects(
    () =>
      validateSdkArguments(sdk, tool(direct), "missing", { value: missing }),
    /context_id/,
  );
  function checkRefs(node, document) {
    if (Array.isArray(node)) return node.forEach((v) => checkRefs(v, document));
    if (node && typeof node === "object") {
      if (node.$ref) {
        assert(node.$ref.startsWith("#/"));
        let target = document;
        for (const key of node.$ref.slice(2).split("/"))
          target = target?.[key.replace(/~1/g, "/").replace(/~0/g, "~")];
        assert(target, "Unresolved " + node.$ref);
      }
      Object.values(node).forEach((v) => checkRefs(v, document));
    }
  }
  const wrapped = tool(call.outputSchema).parameters;
  checkRefs(wrapped, wrapped);
}
console.log(
  JSON.stringify({
    validDecisions: ["verify", "resolved"],
    validReviews: ["spec", "code"],
    directAndIssueSchemasEqual: true,
    realModelCalls: 0,
    ...errors,
  }),
);
