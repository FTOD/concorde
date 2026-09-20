/**
 * Concorde worker extension.
 *
 * Every terminal Concorde Pi worker loads only this extension with `-e`. The host writes one policy
 * file per launch and names it in CONCORDE_WORKER_POLICY. The extension:
 *
 * - replaces the worker's system prompt with the host-rendered common rules and role prompt;
 * - registers `submit_result`, whose parameters are the worker's output contract and which ends
 *   the run, `run_checks`, which asks the host to run the configured checks, and the optional
 *   nonterminating `report_issue`, which persists an observation through a scoped host service;
 * - gates every tool call against the policy: only granted tools, reads under the read grant,
 *   edits and writes under the write grant. Workers cannot delegate or call Operations.
 *
 * This is an in-process policy gate over the model's tool calls. The process itself runs inside
 * the host's worker sandbox (`worker_sandbox.py`), which bounds shell commands too.
 */
import * as fs from "node:fs";
import * as net from "node:net";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { fileURLToPath, pathToFileURL } from "node:url";
import type * as TypeBox from "typebox";

interface WorkerPolicy {
	schema_version: 2;
	worker: string;
	workspace: string;
	read_paths: string[];
	write_paths: string[];
	tools: string[];
	system_prompt_path: string;
	result_schema: Record<string, unknown>;
	report_schema: Record<string, unknown> | null;
	host_socket: string | null;
	scrub_environment: string[];
}

const READ_TOOLS = new Set(["read", "grep", "find", "ls"]);
const WRITE_TOOLS = new Set(["edit", "write"]);

function loadPolicy(): WorkerPolicy {
	const location = process.env.CONCORDE_WORKER_POLICY;
	if (!location)
		throw new Error(
			"CONCORDE_WORKER_POLICY is not set; this extension runs only inside a Concorde worker",
		);
	try {
		const policy = JSON.parse(
			fs.readFileSync(location, "utf8"),
		) as WorkerPolicy;
		if (policy.schema_version !== 2)
			throw new Error("unsupported Concorde worker policy version");
		const known = new Set([
			"read",
			"grep",
			"find",
			"ls",
			"edit",
			"write",
			"bash",
			"submit_result",
			"run_checks",
			"report_issue",
		]);
		const keys = [
			"schema_version",
			"worker",
			"workspace",
			"read_paths",
			"write_paths",
			"tools",
			"system_prompt_path",
			"result_schema",
			"report_schema",
			"host_socket",
			"scrub_environment",
		];
		if (
			Object.keys(policy).length !== keys.length ||
			keys.some((key) => !(key in policy)) ||
			!Array.isArray(policy.tools) ||
			policy.tools.some((tool) => !known.has(tool)) ||
			new Set(policy.tools).size !== policy.tools.length ||
			!policy.tools.includes("submit_result")
		)
			throw new Error(
				"worker policy must contain only terminal tools and no child definitions",
			);
		return policy;
	} catch (error) {
		throw new Error("Cannot load the host-issued Concorde worker policy", {
			cause: error,
		});
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
	return (
		target === root ||
		target.startsWith(root.endsWith(path.sep) ? root : root + path.sep)
	);
}

function hostRequest(
	socket: string,
	body: Record<string, unknown>,
): Promise<unknown> {
	return new Promise((resolve, reject) => {
		const chunks: Buffer[] = [];
		const connection = net.createConnection(socket, () =>
			connection.end(JSON.stringify(body) + "\n"),
		);
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

export default async function concordeWorker(pi: ExtensionAPI): Promise<void> {
	// Explicit local dependency import avoids Pi's bundled bare-name TypeBox alias.
	const framework = path.resolve(
		path.dirname(fileURLToPath(import.meta.url)),
		"../..",
	);
	const installed =
		path.basename(framework) === "framework" &&
		path.basename(path.dirname(framework)) === ".concorde";
	const dependency = installed
		? path.join(
				framework,
				"../.venv/share/concorde/pi/node_modules/typebox/build/index.mjs",
			)
		: path.join(framework, "pi/node_modules/typebox/build/index.mjs");
	const { Type } = (await import(
		pathToFileURL(dependency).href
	)) as typeof TypeBox;
	const policy = loadPolicy();
	const readRoots = policy.read_paths.map((entry) =>
		canonical(policy.workspace, entry),
	);
	const writeRoots = policy.write_paths.map((entry) =>
		canonical(policy.workspace, entry),
	);
	let submitted = false;
	pi.on("session_start", () => {
		pi.setActiveTools(policy.tools);
	});
	pi.on("before_agent_start", async () => {
		return { systemPrompt: fs.readFileSync(policy.system_prompt_path, "utf8") };
	});

	pi.on("tool_call", async (event) => {
		const deny = (reason: string) => ({
			block: true,
			reason: `Concorde worker policy: ${reason}`,
		});
		const name = event.toolName;
		if (!policy.tools.includes(name))
			return deny(`the ${name} tool is not granted`);
		const input = event.input as Record<string, unknown>;
		if (READ_TOOLS.has(name)) {
			const target =
				typeof input.path === "string" && input.path ? input.path : ".";
			const resolved = canonical(policy.workspace, target);
			if (
				![...readRoots, ...writeRoots].some((root) => within(resolved, root))
			) {
				return deny(`${target} is outside the read grant`);
			}
		} else if (WRITE_TOOLS.has(name)) {
			if (
				typeof input.path !== "string" ||
				!writeRoots.some((root) =>
					within(canonical(policy.workspace, input.path as string), root),
				)
			) {
				return deny(`${String(input.path)} is outside the write grant`);
			}
		} else if (
			name === "bash" &&
			typeof input.command === "string" &&
			policy.scrub_environment.length > 0
		) {
			input.command = `unset ${policy.scrub_environment.join(" ")}\n${input.command}`;
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
			if (submitted)
				throw new Error("submit_result was already called in this run");
			submitted = true;
			return {
				content: [{ type: "text", text: "Result submitted." }],
				details: params,
				terminate: true,
			};
		},
	});

	if (policy.tools.includes("report_issue") && policy.report_schema) {
		pi.registerTool({
			name: "report_issue",
			label: "Report issue",
			description:
				"Persist a classified bug, gap or limitation through the host and return its immutable receipt. " +
				"Use one stable report_key for each observation; retry identical input after an uncertain reply. " +
				"Reporting neither ends this run nor approves a repair. Use admitted evidence only; do not copy raw logs or secrets. " +
				"A report is limited to 64 KiB.",
			parameters: Type.Unsafe<Record<string, unknown>>(policy.report_schema),
			async execute(_toolCallId, params) {
				if (!policy.host_socket)
					throw new Error("this worker has no host reporting service");
				const reply = await hostRequest(policy.host_socket, {
					tool: "report_issue",
					report: params,
				});
				if (reply && typeof reply === "object" && "error" in reply)
					throw new Error(String(reply.error));
				return {
					content: [{ type: "text", text: JSON.stringify(reply) }],
					details: reply,
				};
			},
		});
	}

	if (policy.tools.includes("run_checks"))
		pi.registerTool({
			name: "run_checks",
			label: "Run checks",
			description:
				"Run the selected Module's configured deterministic checks on the host, read-only, and return each check's status and bounded output.",
			parameters: Type.Object({}),
			async execute() {
				if (!policy.host_socket)
					throw new Error("this worker has no host check service");
				const reply = await hostRequest(policy.host_socket, {
					tool: "run_checks",
				});
				if (reply && typeof reply === "object" && "error" in reply)
					throw new Error(String(reply.error));
				return {
					content: [{ type: "text", text: JSON.stringify(reply, null, 2) }],
					details: reply,
				};
			},
		});
}
