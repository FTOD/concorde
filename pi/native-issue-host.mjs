/** The solve workflow's Host steps (next-i, decision-i, verified-i); provider logic only. */
import fs from "node:fs";
import path from "node:path";
import { issueCall } from "./issue-call.mjs";
import { runHostStep } from "./native-host-step.mjs";

const stable = (value) =>
  value && typeof value === "object"
    ? Array.isArray(value)
      ? value.map(stable)
      : Object.fromEntries(
          Object.keys(value)
            .sort()
            .map((key) => [key, stable(value[key])]),
        )
    : value;

const { value } = await runHostStep({
  timeout: 1800000,
  verify(binding, context) {
    // The call the workflow script launches for this key must be the slot's exclusive binding.
    const layout = JSON.parse(
      fs.readFileSync(
        path.join(context.descriptor.directory, "issue-layout.json"),
        "utf8",
      ),
    );
    const call = issueCall(layout, binding.key);
    if (JSON.stringify(stable(binding.call)) !== JSON.stringify(stable(call)))
      throw new Error("Issue call differs from its exclusive slot binding");
  },
});
const text = JSON.stringify(value, Object.keys(value).sort());
if (Buffer.byteLength(text) > 2048)
  throw new Error("Issue Host control exceeds its bound");
console.log(text);
