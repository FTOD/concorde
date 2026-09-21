/** One prepared, foreground native context-assessor; no workflow or model scheduler. */
import { createRequire } from "node:module";
import * as path from "node:path";
import type {
	ExtensionAPI,
	ExtensionContext,
} from "@earendil-works/pi-coding-agent";
import { nativeCommand, type NativeBinding } from "./concorde-native-child.ts";

const AGENT = "concorde-context-assessor";
function canonical(value: any): string {
	if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
	if (value && typeof value === "object")
		return (
			"{" +
			Object.keys(value)
				.sort()
				.map((key) => JSON.stringify(key) + ":" + canonical(value[key]))
				.join(",") +
			"}"
		);
	return JSON.stringify(value);
}

export function nativeContext(
	pi: ExtensionAPI,
	options: {
		root: string;
		python: string;
		launcher: string;
		verify: () => void;
		prepare: (value: unknown, signal?: AbortSignal) => Promise<any>;
	},
) {
	let pending: any;
	let preparing = false;
	let active: { id: string; session: string; digest: string } | undefined;
	const binding = (): NativeBinding => ({
		argv: [options.python, options.launcher, "--native-context"],
		descriptor: pending.descriptor,
		digest: pending.digest,
		root: options.root,
	});
	pi.on("tool_call", async (event, ctx) => {
		if (event.toolName !== "subagent" || (event.input as any).agent !== AGENT)
			return;
		let reserved = false;
		try {
			options.verify();
			if (
				!pending ||
				preparing ||
				active ||
				canonical(event.input) !== canonical(pending.call)
			)
				throw new Error(
					"Use exactly the prepared native call once; no overrides or fallback",
				);
			// Reserve synchronously before any await: parallel tool calls cannot launch twice.
			active = {
				id: event.toolCallId,
				session: ctx.sessionManager.getSessionId(),
				digest: "",
			};
			reserved = true;
			await nativeCommand(binding(), "check", {});
			const root = process.env.CONCORDE_NATIVE_SUBAGENTS_ROOT;
			if (!root)
				throw new Error(
					"Set CONCORDE_NATIVE_SUBAGENTS_ROOT to the selected native installation",
				);
			// Resolve the documented export, not an installed private implementation path.
			const require = createRequire(path.join(root, "package.json"));
			const { resolveSubagentLaunchContract } = await import(
				require.resolve("pi-subagents/preflight")
			);
			const preflight = await resolveSubagentLaunchContract({
				...pending.call,
				availableModels: ctx.modelRegistry.getAvailable(),
				parentSessionId: ctx.sessionManager.getSessionId(),
				parentSessionFile: ctx.sessionManager.getSessionFile(),
			});
			if (!preflight.ok) throw new Error(preflight.message);
			if (
				preflight.contract.agent.source !== "project" ||
				preflight.contract.agent.filePath !==
					path.join(pending.call.cwd, ".pi/agents/" + AGENT + ".md") ||
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
			];
			if (
				preflight.contract.tools.effectiveAllowlist.some(
					(tool: string) => !allowed.includes(tool),
				)
			)
				throw new Error(
					"Native assessor launch exceeds its terminal read policy",
				);
			if (
				preflight.contract.context !== "fresh" ||
				preflight.contract.inheritProjectContext ||
				preflight.contract.inheritGlobalContext ||
				preflight.contract.inheritSkills ||
				preflight.contract.skills.resolved.length ||
				preflight.contract.intercomBridge.active
			)
				throw new Error(
					"Native assessor inherited ungranted context or Skills",
				);
			active = {
				id: event.toolCallId,
				session: ctx.sessionManager.getSessionId(),
				digest: preflight.contract.launchContractDigest,
			};
		} catch (error) {
			if (reserved && active?.id === event.toolCallId) active = undefined;
			return { block: true, reason: String(error) };
		}
	});
	pi.on("tool_result", async (event, ctx) => {
		if (
			event.toolName !== "subagent" ||
			!active ||
			event.toolCallId !== active.id
		)
			return;
		const owner = active;
		let value: any;
		try {
			options.verify();
			if (ctx.sessionManager.getSessionId() !== owner.session)
				throw new Error("Native parent session changed");
			const native = event.details as any;
			// Correlation does not transport model prose, transcripts or the proposal again.
			// Preserve native fields verbatim; absent/foreign fields still fail Host validation.
			const fields = [
				"agent",
				"exitCode",
				"error",
				"detached",
				"interrupted",
				"stopped",
				"terminalOutcome",
				"timedOut",
				"metadataSaveError",
				"outputSaveError",
				"transcriptError",
				"launchContractDigest",
				"artifactPaths",
				"structuredOutputPath",
			];
			const details = {
				mode: native?.mode,
				runId: native?.runId,
				results: native?.results?.map((row: any) =>
					Object.fromEntries(
						fields.filter((key) => key in row).map((key) => [key, row[key]]),
					),
				),
			};
			value = await nativeCommand(binding(), "accept", {
				details,
				isError: Boolean(event.isError),
				tool_call_id: event.toolCallId,
				session_id: owner.session,
				launch_contract_digest: owner.digest,
				gate_command: pending.call.gate.command,
			});
		} catch (error) {
			const response = (error as { response?: any }).response;
			const row = (event.details as any)?.results?.[0];
			const codes =
				response?.result?.errors?.map((item: any) => item.code) ?? [];
			value = {
				state:
					row?.interrupted || row?.stopped
						? "cancelled"
						: row?.detached
							? "not-terminal"
							: codes.some((code: string) =>
										[
											"stale_context",
											"stale_evidence",
											"configuration_mismatch",
										].includes(code),
								  )
								? "stale"
								: codes.some((code: string) =>
											[
												"invalid_completion",
												"incompatible_handoff",
												"invalid_field",
												"permission_denied",
											].includes(code),
									  )
									? "rejected"
									: "failed",
				accepted: false,
				result: response?.result,
				error: String(error),
			};
			try {
				await nativeCommand(binding(), "invalidate", {});
			} catch {}
		} finally {
			active = undefined;
			pending = undefined;
		}
		return {
			content: [{ type: "text", text: JSON.stringify(value) }],
			details: { ...(event.details as any), concorde_context: value },
			isError: !value.accepted,
		};
	});
	pi.on("session_shutdown", async () => {
		if (pending) {
			try {
				await nativeCommand(binding(), "invalidate", {});
			} catch {}
		}
		pending = undefined;
		active = undefined;
	});
	return async (
		invocation: unknown,
		ctx: ExtensionContext,
		signal?: AbortSignal,
	) => {
		if (active || preparing)
			throw new Error(
				"One native context assessment is still active; finish or cancel it before preparing another",
			);
		preparing = true;
		try {
			if (pending) {
				try {
					await nativeCommand(binding(), "invalidate", {});
				} catch {}
				pending = undefined;
			}
			const nativeRoot = process.env.CONCORDE_NATIVE_SUBAGENTS_ROOT;
			const value = await options.prepare(
				{
					invocation,
					native_root: nativeRoot,
					session_id: ctx.sessionManager.getSessionId(),
				},
				signal,
			);
			if (value.state === "prepared") {
				pending = value;
			}
			return {
				...value,
				definition: undefined,
				instruction:
					value.state === "prepared"
						? "Call the native subagent tool with the exact call object. Its structuredOutput is a proposal; only concorde_context.accepted after the Host hook is acceptance."
						: undefined,
			};
		} finally {
			preparing = false;
		}
	};
}
