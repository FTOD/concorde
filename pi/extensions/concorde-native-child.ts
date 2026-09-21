/** Native read-only leaf transport. No session tool, delegation or Python model worker. */
import { spawn } from "node:child_process";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { errorFeedback, failure, executionError } from "../execution-error.mjs";
import { errorDisplay } from "../error-display.mjs";
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
		let overflow = false;
		let stderr = "";
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
			if (Buffer.byteLength(text) > 2 * 1024 * 1024) {
				overflow = true;
				child.kill("SIGKILL");
			}
		});
		child.stderr.on("data", (chunk) => {
			stderr += chunk;
			if (Buffer.byteLength(stderr) > 2 * 1024 * 1024) {
				overflow = true;
				child.kill("SIGKILL");
			}
		});
		child.on("error", (error) => {
			clearTimeout(timer);
			signal?.removeEventListener("abort", abort);
			reject(
				executionError(
					errorFeedback(error, {
						layer: "native-command",
						category: "transport",
						attempt: binding.digest,
					}),
					error,
				),
			);
		});
		child.on("close", (code, processSignal) => {
			clearTimeout(timer);
			signal?.removeEventListener("abort", abort);
			let response: any;
			let parseError: unknown;
			try {
				response = JSON.parse(text);
			} catch (error) {
				parseError = error;
			}
			if (
				expired ||
				signal?.aborted ||
				overflow ||
				code !== 0 ||
				parseError ||
				response?.state === "rejected"
			) {
				const feedback = failure(`Native Host ${action} failed`, {
					layer: "native-command",
					attempt: binding.digest,
					category: expired
						? "timeout"
						: signal?.aborted
							? "cancelled"
							: overflow
								? "observation"
								: response?.result?.errors?.length
									? "host-refusal"
									: code !== 0
										? "native-exit"
										: "transport",
					causes: response?.result?.errors?.length
						? [errorFeedback({ response })]
						: parseError
							? [errorFeedback(parseError)]
							: [],
					diagnostics: JSON.stringify({
						exitCode: code,
						processSignal,
						stdout: response ? undefined : text,
						stderr,
					}),
					complete: !overflow,
				});
				const error = executionError(feedback);
				error.message = errorDisplay(feedback);
				Object.assign(error, { response });
				reject(error);
			} else resolve(response);
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
			async (feedback) => {
				await nativeCommand(binding, "observe-error", { feedback });
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
