import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";
const [root, cwd] = process.argv.slice(2);
const { observe, toolSpan } = await import(
	pathToFileURL(`${root}/pi/extensions/concorde-observe.ts`).href
);
const handlers = new Map<string, Function[]>();
const bus = new Map<string, Function[]>();
const records: any[] = [];
const tools: any[] = [];
const pi = {
	on(name: string, f: Function) {
		handlers.set(name, [...(handlers.get(name) ?? []), f]);
	},
	appendEntry(_name: string, record: any) {
		records.push(record);
	},
	registerTool(tool: any) {
		tools.push(tool);
	},
	events: {
		on(name: string, f: Function) {
			bus.set(name, [...(bus.get(name) ?? []), f]);
			return () => bus.delete(name);
		},
		emit(name: string, value: any) {
			for (const f of bus.get(name) ?? []) f(value);
		},
	},
};
const ctx = {
	cwd,
	sessionManager: {
		getSessionId: () => "session-fixture",
		getHeader: () => ({ parentSession: "/private/parent" }),
	},
	getContextUsage: () => ({ tokens: 122000, contextWindow: 872000 }),
	model: { contextWindow: 872000 },
};
const emit = async (name: string, value: any = {}) => {
	const out = [];
	for (const f of handlers.get(name) ?? []) out.push(await f(value, ctx));
	return out;
};
observe(pi, "maintenance-worker");
await emit("session_start", { reason: "resume" });
await emit("turn_start");
await emit("before_provider_request", { payload: { secret: "RAW-PROMPT" } });
await emit("tool_execution_start", {
	toolName: "read",
	toolCallId: "1",
	args: { secret: "RAW-ARGS" },
});
await emit("tool_execution_start", {
	toolName: "contact_supervisor",
	toolCallId: "2",
});
await emit("tool_execution_end", {
	toolCallId: "2",
	isError: false,
	result: "RAW-OUTPUT",
});
await emit("tool_execution_end", { toolCallId: "1", isError: true });
await emit("message_end", {
	message: {
		role: "assistant",
		stopReason: "stop",
		usage: { input: 122000, cacheRead: 110000 },
	},
});
await emit("turn_end");
await emit("session_before_compact", {
	reason: "manual",
	preparation: { tokensBefore: 122000, settings: { reserveTokens: 16384 } },
});
await emit("session_compact_failed", { aborted: true });
await emit("session_shutdown");
assert.equal(tools.length, 0);
assert(records.some((r) => r.name === "outer.supervisor_wait"));
assert(
	records.some(
		(r) => r.name === "outer.compaction" && r.status === "cancelled",
	),
);
assert.equal(
	records.find((r) => r.name === "outer.turn").metadata
		.current_context_estimate,
	122000,
);
assert.equal(
	records.find((r) => r.name === "outer.turn").metadata.context_capacity,
	872000,
);
assert.equal(
	records.find((r) => r.name === "outer.turn").metadata.reserve_tokens,
	null,
);
assert.equal(
	records.find((r) => r.name === "outer.request_roundtrip").metadata
		.output_tokens,
	null,
);
assert(!JSON.stringify(records).includes("RAW-"));
assert(!JSON.stringify(records).includes("/private/parent"));
assert(records.every((r) => r.duration_ns >= 0));
const bad = {
	...pi,
	appendEntry() {
		throw new Error("disk failure");
	},
};
toolSpan(bad, "fixture")("ok");
handlers.clear();
const tester = await import(
	pathToFileURL(`${root}/pi/extensions/concorde-tester.ts`).href
);
tester.default(pi);
assert(
	(await emit("tool_call", { toolName: "bash" })).some((r: any) => r?.block),
);
assert(
	(await emit("tool_call", { toolName: "write" })).some((r: any) => r?.block),
);
assert(
	(await emit("tool_call", { toolName: "subagent" })).some(
		(r: any) => r?.block,
	),
);
const command = tools.find((t) => t.name === "test_command");
const result = await command.execute(
	"test",
	{
		command:
			'echo fixture > "$CONCORDE_CHECK_TMPDIR/example"; cat "$CONCORDE_CHECK_TMPDIR/example"',
	},
	undefined,
	undefined,
	ctx,
);
assert(result.content[0].text.includes("fixture"));
await assert.rejects(
	command.execute(
		"deny",
		{ command: "echo forbidden > governing-canary" },
		undefined,
		undefined,
		ctx,
	),
);
console.log(
	JSON.stringify({ ok: true, spans: records.length, readonly: true }),
);
