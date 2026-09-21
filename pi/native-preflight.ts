import { createRequire } from "node:module";
import * as path from "node:path";

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
	if (!preflight.ok) throw new Error(preflight.message);
	if (
		preflight.contract.agent.source !== "project" ||
		preflight.contract.agent.filePath !==
			path.join(call.cwd, ".pi/agents/" + call.agent + ".md") ||
		!preflight.contract.tools.disableAmbientExtensions ||
		preflight.contract.tools.fanoutAuthorized
	)
		throw new Error(
			"Native Agent discovery did not resolve the exact capsule role",
		);
	const allowed = [
		"read",
		"grep",
		"find",
		"ls",
		"report_issue",
		"structured_output",
		...(call.agent === "concorde-programmer"
			? ["edit", "write", "bash", "run_checks"]
			: call.agent === "concorde-code-reviewer"
				? ["run_checks"]
				: []),
	];
	if (
		preflight.contract.tools.effectiveAllowlist.some(
			(tool: string) => !allowed.includes(tool),
		)
	)
		throw new Error("Native assessor launch exceeds its terminal read policy");
	if (
		preflight.contract.context !== "fresh" ||
		preflight.contract.inheritProjectContext ||
		preflight.contract.inheritGlobalContext ||
		preflight.contract.inheritSkills ||
		preflight.contract.skills.resolved.length ||
		preflight.contract.intercomBridge.active
	)
		throw new Error("Native assessor inherited ungranted context or Skills");
	return preflight.contract;
}
