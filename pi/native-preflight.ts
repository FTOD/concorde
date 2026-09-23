import { errorFeedback, executionError } from "./execution-error.mjs";
import * as fs from "node:fs";
import { createRequire } from "node:module";
import * as path from "node:path";

/** The `tools` of a prepared Agent definition file's front matter. */
export function definitionTools(file: string): string[] {
	const [, header] = fs.readFileSync(file, "utf8").split("---", 3);
	const line = (header ?? "")
		.split("\n")
		.find((entry) => entry.startsWith("tools: "));
	if (!line) throw new Error("The prepared Agent definition file lists no tools");
	return line
		.slice("tools: ".length)
		.split(",")
		.map((tool) => tool.trim())
		.filter(Boolean);
}

export async function nativePreflight(
	root: string,
	call: any,
	options: any = {},
) {
	const require = createRequire(path.join(root, "package.json"));
	const { resolveSubagentLaunchContract } = await import(
		require.resolve("pi-subagents/preflight")
	);
	const preflight = await resolveSubagentLaunchContract({
		...call,
		availableModels: options.availableModels,
		parentSessionId: options.parentSessionId,
		parentSessionFile: options.parentSessionFile,
	});
	if (!preflight.ok)
		throw executionError(
			errorFeedback(preflight, {
				layer: "native-preflight",
				category: "host-refusal",
			}),
		);
	const agentFile = path.join(call.cwd, ".pi/agents/" + call.agent + ".md");
	if (
		preflight.contract.agent.source !== "project" ||
		preflight.contract.agent.filePath !== agentFile ||
		!preflight.contract.tools.disableAmbientExtensions ||
		preflight.contract.tools.fanoutAuthorized
	)
		throw new Error(
			"Native Agent discovery did not resolve the exact capsule role",
		);
	// The allowlist is the prepared Agent definition file's own tool list plus structured output.
	const allowed = [...definitionTools(agentFile), "structured_output"];
	if (
		preflight.contract.tools.effectiveAllowlist.some(
			(tool: string) => !allowed.includes(tool),
		)
	)
		throw new Error("Native Agent launch exceeds its definition's tool list");
	if (
		preflight.contract.context !== "fresh" ||
		preflight.contract.inheritProjectContext ||
		preflight.contract.inheritGlobalContext ||
		preflight.contract.inheritSkills ||
		preflight.contract.skills.resolved.length ||
		preflight.contract.intercomBridge.active
	)
		throw new Error("Native Agent inherited ungranted context or Skills");
	return preflight.contract;
}
