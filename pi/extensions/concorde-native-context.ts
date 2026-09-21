/** One prepared, foreground native context-assessor; no workflow or model scheduler. */
import { nativePreflight } from "../native-preflight.ts";
import { nativePlan } from "./concorde-native-plan.ts";
import type {
	ExtensionAPI,
	ExtensionContext,
} from "@earendil-works/pi-coding-agent";
import { nativeCommand, type NativeBinding } from "./concorde-native-child.ts";

const AGENTS = new Set(["concorde-context-assessor", "concorde-task-author"]);
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
	let planning: Awaited<ReturnType<typeof nativePlan>> | undefined;
	let preparing = false;
	let active: { id: string; session: string; digest: string } | undefined;
	const binding = (): NativeBinding =>
		pending.binding ?? {
			argv: [options.python, options.launcher, "--native-context"],
			descriptor: pending.descriptor,
			digest: pending.digest,
			root: options.root,
		};
	pi.on("tool_call", async (event, ctx) => {
		if (planning?.matches(event)) return planning.before(event);
		if (
			event.toolName !== "subagent" ||
			!AGENTS.has((event.input as any).agent)
		)
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
			const contract = await nativePreflight(root, pending.call, {
				availableModels: ctx.modelRegistry.getAvailable(),
				parentSessionId: ctx.sessionManager.getSessionId(),
				parentSessionFile: ctx.sessionManager.getSessionFile(),
			});
			active = {
				id: event.toolCallId,
				session: ctx.sessionManager.getSessionId(),
				digest: contract.launchContractDigest,
			};
		} catch (error) {
			if (reserved && active?.id === event.toolCallId) active = undefined;
			return { block: true, reason: String(error) };
		}
	});
	pi.on("tool_result", async (event, ctx) => {
		if (planning?.matches(event)) return planning.after(event);
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
			details: {
				...(event.details as any),
				concorde_context: value,
				concorde_native: value,
			},
			isError: !value.accepted,
		};
	});
	pi.on("session_shutdown", async () => {
		await planning?.dispose();
		if (pending) {
			try {
				await nativeCommand(binding(), "invalidate", {});
			} catch {}
		}
		pending = undefined;
		active = undefined;
	});
	const prepare = async (
		invocation: unknown,
		ctx: ExtensionContext,
		signal?: AbortSignal,
	) => {
		if (active || preparing)
			throw new Error(
				"One native context assessment is still active; finish or cancel it before preparing another",
			);
		if (planning) {
			const previous = await planning.result();
			if (previous.native_state === "running")
				throw new Error("Native planning workflow is still running");
			await planning.dispose();
			planning = undefined;
		}
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
					native_session_id:
						ctx.sessionManager.getSessionFile() ??
						ctx.sessionManager.getSessionId(),
				},
				signal,
			);
			if (
				value.state === "prepared" &&
				(invocation as any).operation_id === "concorde-plan"
			) {
				planning = await nativePlan(pi, value, ctx, options.verify);
				return planning.prepared;
			}
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
	return Object.assign(prepare, {
		result: async () =>
			planning ? planning.result() : { state: "not-run", accepted: false },
	});
}
