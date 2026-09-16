/**
 * Concorde worker extension.
 *
 * Every Concorde Pi worker loads this extension with `-e`, and pi-subagents loads it again into
 * every child session through its required-child-extension registry. The host writes one policy
 * file per launch and names it in CONCORDE_WORKER_POLICY. The extension:
 *
 * - replaces the worker's system prompt with the host-rendered common rules and role prompt;
 * - registers `submit_result`, whose parameters are the worker's output contract and which ends
 *   the run, `run_checks`, which asks the host to run the configured checks, and the optional
 *   nonterminating `report_issue`, which persists an observation through a scoped host service;
 * - gates every tool call against the policy: only granted tools, reads under the read grant,
 *   edits and writes under the write grant, and no delegation from a child session;
 * - bounds delegation to one level by registering a pi-subagents capability ceiling (only the
 *   declared children, only their tools) and this extension as a required child extension.
 *
 * This is an in-process policy gate, not an operating-system sandbox: shell commands are not
 * confined by it.
 */
import * as fs from "node:fs";
import * as net from "node:net";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

interface WorkerPolicy {
	schema_version: 1;
	worker: string;
	workspace: string;
	read_paths: string[];
	write_paths: string[];
	tools: string[];
	child_tools: string[];
	children: string[];
	system_prompt_path: string;
	result_schema: Record<string, unknown>;
	report_schema: Record<string, unknown> | null;
	host_socket: string | null;
	extension_path: string;
	scrub_environment: string[];
}

const READ_TOOLS = new Set(["read", "grep", "find", "ls"]);
const WRITE_TOOLS = new Set(["edit", "write"]);
const PARENT_SESSION = Symbol.for("concorde.worker.parent-session");

function loadPolicy(): WorkerPolicy {
	const location = process.env.CONCORDE_WORKER_POLICY;
	if (!location) throw new Error("CONCORDE_WORKER_POLICY is not set; this extension runs only inside a Concorde worker");
	try {
		const policy = JSON.parse(fs.readFileSync(location, "utf8")) as WorkerPolicy;
		if (policy.schema_version !== 1) throw new Error("unsupported Concorde worker policy version");
		return policy;
	} catch (error) {
		throw new Error("Cannot load the host-issued Concorde worker policy", { cause: error });
	}
}

/** The canonical absolute path of `target`, resolving symlinks in its longest existing prefix. */
function canonical(workspace: string, target: string): string {
	let current = path.resolve(workspace, target);
	const missing: string[] = [];
	for (;;) {
		try {
			return path.join(fs.realpathSync(current), ...missing);
		} catch {
			const parent = path.dirname(current);
			if (parent === current) return path.join(current, ...missing);
			missing.unshift(path.basename(current));
			current = parent;
		}
	}
}

function within(target: string, root: string): boolean {
	return target === root || target.startsWith(root.endsWith(path.sep) ? root : root + path.sep);
}

function hostRequest(socket: string, body: Record<string, unknown>): Promise<unknown> {
	return new Promise((resolve, reject) => {
		const chunks: Buffer[] = [];
		const connection = net.createConnection(socket, () => connection.end(JSON.stringify(body) + "\n"));
		connection.on("data", (chunk) => chunks.push(chunk));
		connection.on("error", reject);
		connection.on("end", () => {
			try {
				resolve(JSON.parse(Buffer.concat(chunks).toString("utf8")));
			} catch (error) {
				reject(error);
			}
		});
	});
}

export default function concordeWorker(pi: ExtensionAPI): void {
	const policy = loadPolicy();
	const readRoots = policy.read_paths.map((entry) => canonical(policy.workspace, entry));
	const writeRoots = policy.write_paths.map((entry) => canonical(policy.workspace, entry));
	const store = globalThis as typeof globalThis & { [PARENT_SESSION]?: string };
	const isChild = (sessionId: string) => store[PARENT_SESSION] !== undefined && store[PARENT_SESSION] !== sessionId;
	let submitted = false;

	pi.on("session_start", async (_event, ctx) => {
		const sessionId = ctx.sessionManager.getSessionId();
		store[PARENT_SESSION] ??= sessionId;
		if (isChild(sessionId) || policy.children.length === 0) return;
		const { registerSubagentCapabilityCeiling } = await import("pi-subagents/capability-ceiling");
		const { registerRequiredChildExtensions } = await import("pi-subagents/required-child-extensions");
		registerSubagentCapabilityCeiling({
			sessionId,
			source: "concorde-worker",
			ceiling: { allowedAgents: policy.children, allowedTools: policy.child_tools },
		});
		registerRequiredChildExtensions({
			sessionId,
			extensions: [{ id: "concorde-worker", path: policy.extension_path }],
		});
	});

	pi.on("before_agent_start", async (_event, ctx) => {
		if (isChild(ctx.sessionManager.getSessionId())) return undefined;
		return { systemPrompt: fs.readFileSync(policy.system_prompt_path, "utf8") };
	});

	pi.on("tool_call", async (event, ctx) => {
		const child = isChild(ctx.sessionManager.getSessionId());
		const deny = (reason: string) => ({ block: true, reason: `Concorde worker policy: ${reason}` });
		const name = event.toolName;
		if (!(child ? policy.child_tools : policy.tools).includes(name)) return deny(`the ${name} tool is not granted`);
		const input = event.input as Record<string, unknown>;
		if (READ_TOOLS.has(name)) {
			const target = typeof input.path === "string" && input.path ? input.path : ".";
			const resolved = canonical(policy.workspace, target);
			if (![...readRoots, ...writeRoots].some((root) => within(resolved, root))) {
				return deny(`${target} is outside the read grant`);
			}
		} else if (WRITE_TOOLS.has(name)) {
			if (typeof input.path !== "string" || !writeRoots.some((root) => within(canonical(policy.workspace, input.path as string), root))) {
				return deny(`${String(input.path)} is outside the write grant`);
			}
		} else if (name === "bash" && typeof input.command === "string" && policy.scrub_environment.length > 0) {
			input.command = `unset ${policy.scrub_environment.join(" ")}\n${input.command}`;
		} else if (name === "subagent" && child) {
			return deny("a child session cannot delegate");
		} else if (name === "submit_result" && child) {
			return deny("only the worker itself submits its result");
		}
		return undefined;
	});

	pi.registerTool({
		name: "submit_result",
		label: "Submit result",
		description:
			"Submit this worker's final result as the JSON object its output contract requires. Call it exactly once, as your last action; the run ends when it returns.",
		promptSnippet: "Submit the final structured result and end the run",
		parameters: Type.Unsafe<Record<string, unknown>>(policy.result_schema),
		async execute(_toolCallId, params) {
			if (submitted) throw new Error("submit_result was already called in this run");
			submitted = true;
			return { content: [{ type: "text", text: "Result submitted." }], details: params, terminate: true };
		},
	});

	if (policy.report_schema) {
		pi.registerTool({
			name: "report_issue",
			label: "Report issue",
			description:
				"Persist a classified bug, gap or limitation through the host and return its immutable receipt. " +
				"Use one stable report_key for each observation; retry identical input after an uncertain reply. " +
				"Reporting neither ends this run nor approves a repair. Use admitted evidence only; do not copy raw logs or secrets. " +
				"A report is limited to 64 KiB. Only the parent worker reports issues, not its helper children.",
			parameters: Type.Unsafe<Record<string, unknown>>(policy.report_schema),
			async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
				if (isChild(ctx.sessionManager.getSessionId())) throw new Error("only the worker reports verified observations");
				if (!policy.host_socket) throw new Error("this worker has no host reporting service");
				const reply = await hostRequest(policy.host_socket, { tool: "report_issue", report: params });
				if (reply && typeof reply === "object" && "error" in reply) throw new Error(String(reply.error));
				return { content: [{ type: "text", text: JSON.stringify(reply) }], details: reply };
			},
		});
	}

	pi.registerTool({
		name: "run_checks",
		label: "Run checks",
		description:
			"Run the selected Module's configured deterministic checks on the host, read-only, and return each check's status and bounded output.",
		parameters: Type.Object({}),
		async execute() {
			if (!policy.host_socket) throw new Error("this worker has no host check service");
			const reply = await hostRequest(policy.host_socket, { tool: "run_checks" });
			if (reply && typeof reply === "object" && "error" in reply) throw new Error(String(reply.error));
			return { content: [{ type: "text", text: JSON.stringify(reply, null, 2) }], details: reply };
		},
	});
}
