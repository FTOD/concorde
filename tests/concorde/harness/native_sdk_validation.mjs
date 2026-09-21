/** The public SDK argument validator, using the selected SDK's own pi-ai dependency.
 * Every scripted native tool call must cross this boundary BEFORE tool.execute.
 * No model/provider is called; errors are the actual SDK errors, never fabricated schema checks.
 */
import path from "node:path";
import { pathToFileURL } from "node:url";

export async function validateSdkArguments(sdkRoot, tool, id, args) {
  const { validateToolArguments } = await import(
    pathToFileURL(
      path.join(sdkRoot, "node_modules/@earendil-works/pi-ai/dist/index.js"),
    ).href
  );
  return validateToolArguments(tool, {
    type: "toolCall",
    id,
    name: tool.name,
    arguments: args,
  });
}

export async function executeWithSdkValidation(sdkRoot, tool, id, args) {
  const admitted = await validateSdkArguments(sdkRoot, tool, id, args);
  return tool.execute(id, admitted);
}
