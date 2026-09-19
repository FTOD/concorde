/**
 * Concorde session extension.
 *
 * The developer's own Pi session loads this extension through the shim the build renders under
 * `.pi/extensions/`. The shim supplies the project root and the catalog: every public Concorde
 * Operation with its description, guidance and request schema, the launcher to run and the
 * interpreters to try. The extension is the Pi projection of the public Operations, the
 * counterpart of the Skills rendered for Claude Code and Codex:
 *
 * - it registers one `concorde` tool. Action `describe` returns an Operation's guidance and
 *   request schema; action `run` wraps the caller's input in the typed invocation envelope, runs
 *   the launcher with that envelope on stdin in the project root and returns the launcher's JSON
 *   result;
 * - when the turn is aborted it sends the launcher SIGTERM, which the launcher turns into a
 *   cancellation of its running worker, and kills the launcher's whole process group after a
 *   grace period;
 * - it appends a short Concorde section to the system prompt naming the tool and the Operations.
 *
 * Everything the launcher checks (typed request, configuration, worktree lifecycle, permissions)
 * stays with the launcher: this extension grants nothing and knows no internal Operation.
 */
import { spawn } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

export interface SessionOperation {
	/** The public Operation's external name, for example `concorde-main`. */
	name: string;
	description: string;
	/** The rendered Skill guidance for this Operation, without launcher mechanics. */
	guidance: string;
	/** The schema version of `<name>-request`, the `input` the tool wraps. */
	request_version: number;
	/** The self-contained JSON Schema of the typed request. */
	request_schema: Record<string, unknown>;
}

export interface SessionCatalog {
	schema_version: 1;
	/** Project-relative path of the launcher, `scripts/run-operation.py` in a checkout. */
	launcher: string;
	/** Project-relative interpreters tried in order before the ambient `python3`. */
	interpreters: string[];
	/** True in Concorde's own source checkout, where a graph runs only on explicit request. */
	explicit_request_only: boolean;
	operations: SessionOperation[];
}

interface ToolParameters {
	operation: string;
	action: "run" | "describe";
	input?: Record<string, unknown>;
	mode?: "execute" | "describe-policy";
}

const INVOCATION_TYPE = "concorde-operation-invocation";
const INVOCATION_VERSION = 3;
/** How long a terminated launcher may cancel its worker before its process group is killed. */
const GRACE_MS = 5000;
/** The launcher's JSON result is returned whole up to this size; larger results go to a file. */
const RESULT_LIMIT = 48 * 1024;

export function sessionPrompt(catalog: SessionCatalog): string {
	const lines = [
		"## Concorde",
		"",
		"This project uses the Concorde Framework. Its public Operations run only through the " +
			"`concorde` tool: never run the launcher script or an internal stage operation yourself, " +
			'task-authorized edits in your own workspace may include `.concorde` files; preserve scope, evidence and concurrency safety. Call `concorde` with action "describe" ' +
			"before the first use of an Operation to read its guidance and request schema, then " +
			'action "run" with the request data as `input`. Results are typed JSON envelopes whose ' +
			"`status` is succeeded, described, blocked or failed and whose `errors` explain a stop; " +
			"report Spec gaps and blocked steps as returned instead of working around them.",
	];
	if (catalog.explicit_request_only) {
		lines.push(
			"",
			"This is Concorde's own source checkout: run an Operation only when the user explicitly " +
				"asks for it by name. Source maintenance belongs to a fresh Skill-free candidate writer, " +
				"followed by a fresh sibling tester using only candidate-built Skills; never rewrite governing Skills.",
		);
	}
	lines.push("", "Operations:");
	for (const operation of catalog.operations) {
		lines.push(`- ${operation.name}: ${operation.description}`);
	}
	return lines.join("\n") + "\n";
}

function describe(operation: SessionOperation): string {
	// The guidance opens with the Operation's own heading; the description precedes it.
	return (
		`${operation.description}\n\n${operation.guidance.trimEnd()}\n\n` +
		`## Request schema (\`input\` is its \`data\`, schema_version ${operation.request_version})\n\n` +
		"```json\n" +
		JSON.stringify(operation.request_schema, null, 2) +
		"\n```\n"
	);
}

function interpreter(root: string, catalog: SessionCatalog): string {
	for (const candidate of catalog.interpreters) {
		const resolved = path.resolve(root, candidate);
		if (fs.existsSync(resolved)) return resolved;
	}
	return process.platform === "win32" ? "python" : "python3";
}

function usageLine(stderr: string): string | null {
	for (const line of stderr.split("\n")) {
		if (!line.startsWith('{"usage":')) continue;
		try {
			const total = JSON.parse(line).usage?.total ?? {};
			const figure = (key: string) =>
				typeof total[key] === "number" ? total[key] : "?";
			return (
				`usage: input ${figure("input_tokens")}, output ${figure("output_tokens")}, ` +
				`cost ${figure("cost_usd")} USD, ${figure("wall_seconds")} s`
			);
		} catch {
			return null;
		}
	}
	return null;
}

interface LauncherRun {
	code: number | null;
	stdout: string;
	stderr: string;
	aborted: boolean;
}

function runLauncher(
	argv: string[],
	cwd: string,
	envelope: unknown,
	signal: AbortSignal | undefined,
): Promise<LauncherRun> {
	return new Promise((resolve, reject) => {
		const child = spawn(argv[0], argv.slice(1), {
			cwd,
			stdio: ["pipe", "pipe", "pipe"],
			detached: process.platform !== "win32",
		});
		const stdout: Buffer[] = [];
		const stderr: Buffer[] = [];
		let aborted = false;
		let killer: NodeJS.Timeout | undefined;
		const terminate = () => {
			aborted = true;
			// The launcher turns SIGTERM into the cancellation of its running worker and reports
			// it; the whole group is killed only when that does not finish within the grace period.
			try {
				child.kill("SIGTERM");
			} catch {}
			killer = setTimeout(() => {
				try {
					if (process.platform === "win32" || child.pid === undefined)
						child.kill("SIGKILL");
					else process.kill(-child.pid, "SIGKILL");
				} catch {}
			}, GRACE_MS);
		};
		if (signal?.aborted) terminate();
		else signal?.addEventListener("abort", terminate, { once: true });
		child.stdout.on("data", (chunk: Buffer) => stdout.push(chunk));
		child.stderr.on("data", (chunk: Buffer) => stderr.push(chunk));
		child.on("error", (error) => {
			if (killer) clearTimeout(killer);
			signal?.removeEventListener("abort", terminate);
			reject(error);
		});
		child.on("close", (code) => {
			if (killer) clearTimeout(killer);
			signal?.removeEventListener("abort", terminate);
			resolve({
				code,
				stdout: Buffer.concat(stdout).toString("utf8"),
				stderr: Buffer.concat(stderr).toString("utf8"),
				aborted,
			});
		});
		child.stdin.on("error", () => {});
		child.stdin.end(JSON.stringify(envelope));
	});
}

function bounded(text: string, label: string): string {
	if (Buffer.byteLength(text, "utf8") <= RESULT_LIMIT) return text;
	const file = path.join(
		fs.mkdtempSync(path.join(os.tmpdir(), "concorde-result-")),
		`${label}.json`,
	);
	fs.writeFileSync(file, text, "utf8");
	return (
		Buffer.from(text, "utf8").subarray(0, RESULT_LIMIT).toString("utf8") +
		`\n\n[Result truncated to ${RESULT_LIMIT} bytes; the complete result is saved at ${file}]`
	);
}

/**
 * Bind the extension to one project: `root` is the project directory that holds the launcher,
 * `catalog` the operations the build rendered for it.
 */
export function concordeSession(root: string, catalog: SessionCatalog) {
	if (catalog.schema_version !== 1)
		throw new Error("unsupported Concorde session catalog version");
	const operations = new Map(
		catalog.operations.map((item) => [item.name, item]),
	);
	const names = catalog.operations.map((item) => item.name);
	return function extension(pi: ExtensionAPI): void {
		pi.on("before_agent_start", async (event) => ({
			systemPrompt:
				event.systemPrompt.trimEnd() + "\n\n" + sessionPrompt(catalog),
		}));

		pi.registerTool({
			name: "concorde",
			label: "Concorde",
			description:
				'Run a public Concorde Operation or describe one. Action "describe" returns the ' +
				'Operation\'s guidance and the JSON Schema of its request. Action "run" sends `input`, ' +
				"the request data, to the Operation and returns its typed result envelope; `mode` " +
				'"describe-policy" previews the context and permissions an execute run would use ' +
				"without running an agent. A run may take a long time and blocks this turn; aborting " +
				"it cancels the running worker. Results larger than 48 KiB are saved to a file.",
			promptSnippet: "Run or describe a public Concorde Operation",
			parameters: Type.Unsafe<ToolParameters>({
				type: "object",
				properties: {
					operation: {
						type: "string",
						enum: names,
						description: "The public Concorde Operation.",
					},
					action: {
						type: "string",
						enum: ["run", "describe"],
						description: "describe the Operation, or run it with `input`.",
					},
					input: {
						type: "object",
						additionalProperties: true,
						description:
							'The Operation\'s request data for action "run"; describe shows its schema.',
					},
					mode: {
						type: "string",
						enum: ["execute", "describe-policy"],
						description: 'Run mode for action "run"; execute unless given.',
					},
				},
				required: ["operation", "action"],
				additionalProperties: false,
			}),
			async execute(_toolCallId, params, signal) {
				const operation = operations.get(params.operation);
				if (operation === undefined)
					throw new Error(
						`unknown Concorde Operation ${params.operation}; choose one of ${names.join(", ")}`,
					);
				if (params.action === "describe") {
					return {
						content: [{ type: "text", text: describe(operation) }],
						details: { operation: operation.name, action: "describe" },
					};
				}
				const input = params.input;
				if (
					input === undefined ||
					input === null ||
					typeof input !== "object" ||
					Array.isArray(input)
				)
					throw new Error(
						`action "run" needs \`input\`, the ${operation.name}-request data; call describe first`,
					);
				const mode = params.mode ?? "execute";
				const envelope = {
					type_id: INVOCATION_TYPE,
					schema_version: INVOCATION_VERSION,
					operation_id: operation.name,
					mode,
					configuration: null,
					input: {
						type_id: `${operation.name}-request`,
						schema_version: operation.request_version,
						data: input,
					},
				};
				const argv = [
					interpreter(root, catalog),
					path.resolve(root, catalog.launcher),
					operation.name,
				];
				const run = await runLauncher(argv, root, envelope, signal);
				const usage = usageLine(run.stderr);
				const body = run.stdout.trim() || run.stderr.trim();
				if (run.aborted)
					throw new Error(
						`${operation.name} was cancelled` +
							(body ? `\n${bounded(body, operation.name)}` : ""),
					);
				if (run.code !== 0)
					throw new Error(
						(body
							? bounded(body, operation.name)
							: `${operation.name} exited with code ${run.code}`) +
							(usage ? `\n${usage}` : ""),
					);
				return {
					content: [
						{
							type: "text",
							text:
								bounded(run.stdout.trim(), operation.name) +
								(usage ? `\n${usage}` : ""),
						},
					],
					details: {
						operation: operation.name,
						action: "run",
						mode,
						exit_code: run.code,
					},
				};
			},
		});
	};
}
