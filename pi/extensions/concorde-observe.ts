/** Passive outer-session diagnostics. No tools, prompts, settings, network or authority. */
import { createHash, randomUUID } from "node:crypto";
import type {
	ExtensionAPI,
	ExtensionContext,
} from "@earendil-works/pi-coding-agent";

type Status = "ok" | "error" | "cancelled" | "incomplete";
export type Span = {
	schema_version: 1;
	trace_id: string;
	span_id: string;
	parent_id: string | null;
	layer: "A" | "B" | "C";
	name: string;
	process_id: number;
	session_id: string | null;
	task_id: string | null;
	started_at: string;
	start_ns: number;
	duration_ns: number | null;
	status: Status;
	metadata: Record<string, unknown>;
};
const count = (n: unknown): number | null =>
	typeof n === "number" && Number.isFinite(n) && n >= 0 ? n : null;

export function observe(
	pi: ExtensionAPI,
	role: "main" | "maintenance-worker" | "tester" = "main",
) {
	const trace = randomUUID();
	let session: string | null = null;
	let incomplete = 0;
	let reserve: number | null = null;
	let compaction: string | null = null;
	const active = new Map<string, Span>();
	let turn: string | null = null;
	function emit(record: Span) {
		try {
			pi.appendEntry("concorde.timing.v1", {
				...record,
				telemetry_incomplete: incomplete,
			});
		} catch {
			incomplete++;
			if (incomplete === 1) {
				try {
					console.error("CONCORDE_TIMING_INCOMPLETE");
				} catch {}
			}
		} // Never change tool/mutation completion.
		try {
			pi.events.emit("concorde:timing:v1", {
				...record,
				telemetry_incomplete: incomplete,
			});
		} catch {
			incomplete++;
		}
	}
	function start(
		key: string,
		name: string,
		metadata: Record<string, unknown> = {},
		parent = turn,
	) {
		if (active.has(key)) end(key, "incomplete");
		if (active.size >= 1024) {
			incomplete++;
			return;
		}
		active.set(key, {
			schema_version: 1,
			trace_id: trace,
			span_id: randomUUID(),
			parent_id: parent,
			layer: "A",
			name,
			process_id: process.pid,
			session_id: session,
			task_id: null,
			started_at: new Date().toISOString(),
			start_ns: performance.now() * 1e6,
			duration_ns: null,
			status: "incomplete",
			metadata: { role, ...metadata },
		});
	}
	function end(
		key: string,
		status: Status = "ok",
		metadata: Record<string, unknown> = {},
	) {
		const span = active.get(key);
		if (!span) {
			incomplete++;
			return;
		}
		active.delete(key);
		emit({
			...span,
			duration_ns: Math.max(0, performance.now() * 1e6 - span.start_ns),
			status,
			metadata: { ...span.metadata, ...metadata },
		});
	}
	function context(ctx: ExtensionContext) {
		try {
			const usage = ctx.getContextUsage();
			return {
				context_capacity: count(
					usage?.contextWindow ?? ctx.model?.contextWindow,
				),
				current_context_estimate: count(usage?.tokens),
				reserve_tokens: reserve,
				compaction,
			};
		} catch {
			incomplete++;
			return {
				context_capacity: null,
				current_context_estimate: null,
				reserve_tokens: reserve,
				compaction,
			};
		}
	}
	pi.on("session_start", (event, ctx) => {
		session = ctx.sessionManager.getSessionId();
		const parent = ctx.sessionManager.getHeader()?.parentSession;
		start(
			"session",
			"outer.session",
			{
				reason: event.reason,
				parent_session_digest: parent
					? createHash("sha256").update(parent).digest("hex")
					: null,
				...context(ctx),
			},
			null,
		);
		try {
			pi.events.emit("subagent:acknowledge-extension", {
				id: "concorde-observe-v1",
			});
		} catch {
			incomplete++;
		}
	});
	pi.on("turn_start", (_event, ctx) => {
		start(
			"turn",
			"outer.turn",
			context(ctx),
			active.get("session")?.span_id ?? null,
		);
		turn = active.get("turn")?.span_id ?? null;
	});
	pi.on("turn_end", (_event, ctx) => {
		end("turn", ctx.signal?.aborted ? "cancelled" : "ok", context(ctx));
		turn = null;
	});
	pi.on("before_provider_request", () => {
		start("request", "outer.request_roundtrip");
	});
	pi.on("after_provider_response", (event) => {
		start("headers", "outer.response_headers", {
			http_status: count(event.status),
		});
		end("headers");
	});
	pi.on("message_end", (event) => {
		if (event.message.role !== "assistant") return;
		const m = event.message;
		if (active.has("request"))
			end(
				"request",
				m.stopReason === "aborted"
					? "cancelled"
					: m.stopReason === "error"
						? "error"
						: "ok",
				{
					input_tokens: count(m.usage?.input),
					output_tokens: count(m.usage?.output),
					cache_read_tokens: count(m.usage?.cacheRead),
					cache_write_tokens: count(m.usage?.cacheWrite),
				},
			);
	});
	pi.on("tool_execution_start", (event) => {
		// Arbitrary extension names and all arguments/outputs are intentionally omitted.
		const known = [
			"read",
			"grep",
			"find",
			"ls",
			"bash",
			"write",
			"edit",
			"test_command",
			"concorde",
			"contact_supervisor",
		];
		start(
			`tool:${event.toolCallId}`,
			event.toolName === "contact_supervisor"
				? "outer.supervisor_wait"
				: "outer.tool",
			{ tool: known.includes(event.toolName) ? event.toolName : "other" },
		);
	});
	pi.on("tool_execution_end", (event, ctx) => {
		end(
			`tool:${event.toolCallId}`,
			ctx.signal?.aborted ? "cancelled" : event.isError ? "error" : "ok",
		);
	});
	pi.on("session_before_compact", (event) => {
		reserve = count(event.preparation.settings.reserveTokens);
		compaction = "running";
		start("compact", "outer.compaction", {
			reason: event.reason,
			tokens_before: count(event.preparation.tokensBefore),
			reserve_tokens: reserve,
		});
	});
	pi.on("session_compact", () => {
		compaction = "completed";
		end("compact");
	});
	pi.on("session_compact_failed", (event) => {
		compaction = event.aborted ? "cancelled" : "failed";
		end("compact", event.aborted ? "cancelled" : "error");
	});
	pi.on("ui_prompt_start", () => {
		start("wait", "outer.ui_wait");
	});
	pi.on("ui_prompt_end", () => {
		end("wait");
	});
	const childDisposers = [
		pi.events.on("subagent:async-started", (value: any) => {
			const id = value?.runId ?? value?.id;
			if (typeof id !== "string" || id.length > 160) return;
			const key = createHash("sha256").update(id).digest("hex");
			start(
				`child:${key}`,
				"outer.child_interval",
				{ child_run_digest: key },
				active.get("session")?.span_id ?? null,
			);
		}),
		pi.events.on("subagent:async-complete", (value: any) => {
			const id = value?.runId ?? value?.id;
			if (typeof id !== "string" || id.length > 160) return;
			const key = `child:${createHash("sha256").update(id).digest("hex")}`;
			if (active.has(key))
				end(
					key,
					value?.success === true
						? "ok"
						: value?.success === false
							? "error"
							: "incomplete",
				);
		}),
	];
	// Main may annotate facts unavailable in native events. Closed vocabulary; no free text.
	const dispose = pi.events.on("concorde:outer-fact:v1", (value: unknown) => {
		if (!value || typeof value !== "object") return;
		const v = value as Record<string, unknown>;
		if (!["handoff", "test_trigger", "resume"].includes(String(v.kind))) return;
		const reason = [
			"resource",
			"quality",
			"scope",
			"failure",
			"changed-input",
			"stable-final",
			"manual",
		].includes(String(v.reason))
			? v.reason
			: null;
		const scope = ["none", "targeted", "full"].includes(String(v.scope))
			? v.scope
			: null;
		start("fact", `outer.${v.kind}`, { reason, scope });
		end("fact");
	});
	pi.on("session_shutdown", (_event, ctx) => {
		for (const key of [...active.keys()].filter((k) => k !== "session"))
			end(key, "incomplete");
		if (active.has("session")) end("session", "ok", context(ctx));
		dispose();
		for (const stop of childDisposers) stop();
	});
}
export function toolSpan(
	pi: ExtensionAPI,
	name: string,
	layer: "A" | "B" = "B",
) {
	const start = performance.now() * 1e6;
	const record = {
		schema_version: 1,
		trace_id: randomUUID(),
		span_id: randomUUID(),
		parent_id: null,
		layer,
		name,
		process_id: process.pid,
		session_id: null,
		task_id: null,
		started_at: new Date().toISOString(),
		start_ns: start,
	};
	return (status: Status, rootInvocation: string | null = null) => {
		const id =
			rootInvocation && /^[a-f0-9-]{36}$/.test(rootInvocation)
				? rootInvocation
				: null;
		try {
			pi.appendEntry("concorde.timing.v1", {
				...record,
				duration_ns: performance.now() * 1e6 - start,
				status,
				metadata: { root_invocation_id: id },
			});
		} catch {
			/* Native session absence is unknown, never mutation failure. */
		}
	};
}
export default observe;
