/** Explicit source-outer lifecycle support; never loaded by terminal domain Agents or tester.
 * Pi owns measured threshold/overflow compaction. This extension neither schedules tasks nor
 * replaces summarization. Briefs are reported task memory, never an authority or status ledger.
 */
import type {
	ExtensionAPI,
	ExtensionContext,
} from "@earendil-works/pi-coding-agent";

const BRIEF = "concorde.outer-brief.v1";
const INJECTED = "concorde.outer-brief-injected.v1";
const scalar = [
	"goal",
	"grant",
	"stage",
	"objective",
	"blocker",
	"next",
] as const;
const lists = ["decisions", "completed", "checks", "evidence"] as const;
export type TaskBrief = Record<(typeof scalar)[number], string> &
	Record<(typeof lists)[number], string[]>;

export function parseBrief(value: unknown): TaskBrief {
	if (!value || typeof value !== "object" || Array.isArray(value))
		throw new Error("Task brief must be an object");
	const v = value as Record<string, unknown>;
	const keys = [...scalar, ...lists];
	if (
		Object.keys(v).length !== keys.length ||
		Object.keys(v).some((k) => !keys.includes(k as never))
	)
		throw new Error(
			"Task brief requires exactly goal/grant/stage/objective/blocker/next/decisions/completed/checks/evidence",
		);
	const text = (s: unknown) =>
		typeof s === "string" && s.trim().length > 0 && s.length <= 2000;
	if (
		scalar.some((k) => !text(v[k])) ||
		lists.some(
			(k) => !Array.isArray(v[k]) || v[k].length > 16 || !v[k].every(text),
		)
	)
		throw new Error(
			"Task brief fields must be concise nonblank text; lists allow at most 16 entries",
		);
	if (JSON.stringify(v).length > 12000)
		throw new Error("Task brief exceeds 12000 characters");
	return Object.fromEntries(
		keys.map((k) => [k, Array.isArray(v[k]) ? [...v[k]] : v[k]]),
	) as TaskBrief;
}

export default function outerLifecycle(pi: ExtensionAPI) {
	let brief: TaskBrief | undefined;
	let pending: string | undefined;
	let injected = new Set<string>();
	function restore(ctx: ExtensionContext) {
		brief = undefined;
		pending = undefined;
		injected = new Set();
		for (const entry of ctx.sessionManager.getBranch()) {
			if (entry.type === "compaction") pending = entry.id;
			if (entry.type !== "custom") continue;
			if (entry.customType === BRIEF)
				brief = entry.data === null ? undefined : parseBrief(entry.data);
			if (entry.customType === INJECTED && typeof entry.data === "string")
				injected.add(entry.data);
			if (
				entry.customType === "concorde.outer-compaction-failed.v1" ||
				entry.customType === "concorde.outer-brief-missing.v1"
			)
				pending = undefined;
		}
		if (pending && injected.has(pending)) pending = undefined;
	}
	function update(value: unknown) {
		const next = parseBrief(value);
		if (JSON.stringify(next) === JSON.stringify(brief)) return;
		pi.appendEntry(BRIEF, next);
		brief = next;
	}
	pi.on("session_start", (_event, ctx) => {
		restore(ctx);
		pi.events.emit("subagent:acknowledge-extension", {
			id: "concorde-outer-lifecycle-v1",
		});
	});
	pi.on("session_tree", (_event, ctx) => restore(ctx));
	pi.registerCommand("outer-brief", {
		description:
			"Replace current concise task brief (JSON); no task or authority transition",
		handler: async (args) => update(JSON.parse(args)),
	});
	// Reuse the native supervisor transport. Do not rewrite, suppress, duplicate or attest delivery.
	pi.on("tool_call", (event) => {
		if (
			event.toolName !== "contact_supervisor" ||
			event.input.reason !== "progress_update"
		)
			return;
		const message = event.input.message;
		if (typeof message !== "string") return;
		const match = message.match(
			/(?:^|\n)```task-brief\n([\s\S]*?)\n```(?:\n|$)/,
		);
		if (!match) return;
		try {
			update(JSON.parse(match[1]));
		} catch {
			// Never block failure/progress delivery because optional task memory was malformed.
			brief = undefined;
			try {
				pi.appendEntry(BRIEF, null); // Persist invalidation so resume cannot restore stale memory.
				pi.appendEntry("concorde.outer-brief-error.v1", {
					message:
						"Optional task brief invalid or unpersisted; current memory cleared",
				});
			} catch {
				console.error(
					"CONCORDE_OUTER_BRIEF_PERSISTENCE_FAILED; supervisor delivery unchanged",
				);
			}
		}
	});
	pi.registerCommand("outer-compact", {
		description:
			"Run actual Pi compaction; completion/failure observed through native hooks",
		handler: async (_args, ctx) => {
			await ctx.waitForIdle();
			await new Promise<void>((resolve, reject) =>
				ctx.compact({ onComplete: () => resolve(), onError: reject }),
			);
		},
	});
	pi.on("session_compact", (_event, ctx) => {
		// Use the actual latest persisted entry, not summary equality (summaries can repeat).
		const entry = [...ctx.sessionManager.getBranch()]
			.reverse()
			.find((e) => e.type === "compaction");
		if (entry && !injected.has(entry.id)) pending = entry.id;
	});
	pi.on("session_compact_failed", (event) => {
		pending = undefined;
		pi.appendEntry("concorde.outer-compaction-failed.v1", {
			reason: event.reason,
			aborted: event.aborted,
			// Original error remains in native lifecycle evidence; do not duplicate raw diagnostics.
			hasErrorMessage: typeof event.errorMessage === "string",
		});
	});
	pi.on("context", (event) => {
		if (!pending) return;
		if (!brief) {
			pi.appendEntry("concorde.outer-brief-missing.v1", pending);
			pending = undefined;
			return;
		}
		const id = pending;
		// One request-local reinjection, never a queued turn or replay of old launch prompts.
		pi.appendEntry(INJECTED, id);
		injected.add(id);
		pending = undefined;
		return {
			messages: [
				...event.messages,
				{
					role: "custom" as const,
					customType: BRIEF,
					display: false,
					timestamp: Date.now(),
					content:
						"Current task brief (reported memory, not a new grant; frozen launch rules still apply):\n" +
						JSON.stringify(brief),
				},
			],
		};
	});
	pi.on("session_shutdown", () => {
		brief = undefined;
		pending = undefined;
		injected.clear();
	});
}
