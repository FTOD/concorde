/** Native read-only leaf transport. No session tool, delegation or Python model worker. */
import { spawn } from "node:child_process";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { observeNativeProposal } from "../native-proposal.ts";

export interface NativeBinding {
	argv: string[];
	descriptor: string;
	digest: string;
	root: string;
	reportSchema?: Record<string, unknown>;
	checks?: boolean;
	checksTimeoutMs?: number;
}

export function nativeCommand(
	binding: NativeBinding,
	action: string,
	value: unknown,
	signal?: AbortSignal,
): Promise<any> {
	return new Promise((resolve, reject) => {
		const child = spawn(
			binding.argv[0],
			[...binding.argv.slice(1), action, binding.descriptor, binding.digest],
			{
				cwd: binding.root,
				stdio: ["pipe", "pipe", "pipe"],
			},
		);
		let expired = false;
		const timer = setTimeout(
			() => {
				expired = true;
				child.kill("SIGKILL");
			},
			action === "checks" ? (binding.checksTimeoutMs ?? 30_000) : 30_000,
		);
		const abort = () => child.kill("SIGTERM");
		signal?.addEventListener("abort", abort, { once: true });
		if (signal?.aborted) abort();
		let text = "";
		child.stdout.on("data", (chunk) => {
			text += chunk;
			if (Buffer.byteLength(text) > 2 * 1024 * 1024) child.kill();
		});
		child.stderr.resume();
		child.on("error", (error) => {
			clearTimeout(timer);
			signal?.removeEventListener("abort", abort);
			reject(error);
		});
		child.on("close", (code) => {
			clearTimeout(timer);
			signal?.removeEventListener("abort", abort);
			try {
				if (expired)
					throw new Error(
						"Native Host command timed out; inspect retained evidence before retrying",
					);
				const result = JSON.parse(text);
				if (code !== 0)
					throw Object.assign(new Error(JSON.stringify(result)), {
						response: result,
					});
				resolve(result);
			} catch (error) {
				reject(error);
			}
		});
		child.stdin.on("error", () => {});
		child.stdin.end(JSON.stringify(value));
	});
}

export function nativeContextChild(binding: NativeBinding) {
	return (pi: ExtensionAPI) => {
		observeNativeProposal(
			pi,
			async (value) => {
				await nativeCommand(binding, "submit", value);
			},
			async (reason) => {
				await nativeCommand(binding, "invalidate", { reason });
			},
		);
		if (binding.checks)
			pi.registerTool({
				name: "run_checks",
				label: "Configured checks",
				description:
					"Run the selected Module's Host-configured checks under the enforced check subprocess boundary; no caller command/paths.",
				parameters: Type.Object({}),
				async execute(_id, _params, signal) {
					const value = await nativeCommand(binding, "checks", {}, signal);
					return {
						content: [{ type: "text", text: JSON.stringify(value) }],
						details: value,
					};
				},
			});
		pi.registerTool({
			name: "report_issue",
			label: "Report Issue",
			description:
				"Report a Spec gap or conflict through the scoped Host. Reporting is not context acceptance.",
			parameters: Type.Object({
				report: Type.Unsafe<Record<string, unknown>>(
					binding.reportSchema ?? { type: "object" },
				),
			}),
			async execute(_id, args) {
				const value = await nativeCommand(binding, "report", args.report);
				return {
					content: [{ type: "text", text: JSON.stringify(value) }],
					details: value,
				};
			},
		});
	};
}
