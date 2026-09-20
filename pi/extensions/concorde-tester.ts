/** Outer tester command capability; no unrestricted bash/write/edit or delegation. */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";
import { observe } from "./concorde-observe.ts";
import { selectionPath } from "./concorde-selection.ts";

export default function (pi: ExtensionAPI) {
	observe(pi, "tester");
	const selected = selectionPath();
	const framework = fileURLToPath(new URL("../../", import.meta.url));
	const installed = framework.endsWith("/.concorde/framework/");
	const python = resolve(
		framework,
		installed ? "../.venv/bin/python" : ".venv/bin/python",
	);
	pi.registerTool({
		name: "test_command",
		label: "Read-only test command",
		description:
			"Run a scoped test in the OS read-only host filesystem. Fresh CONCORDE_CHECK_TMPDIR scratch and its private /tmp backing are writable and removed afterward. Read other preexisting host-/tmp inputs through CONCORDE_TEST_HOST_TMP; governing project/runtime paths stay canonical and read-only. No runtime-asset staging or unrestricted shell fallback. Output capped at 20KB per stream.",
		parameters: Type.Object({
			command: Type.String({ maxLength: 32768 }),
			timeout: Type.Optional(Type.Number({ minimum: 1, maximum: 3600 })),
		}),
		async execute(_id, params, signal, _update, ctx) {
			if (selectionPath() !== selected)
				throw new Error("Tester selection changed; start a fresh session");
			if (!existsSync(python))
				throw new Error("Exact local tester Python runtime is missing");
			const response = await new Promise<string>((done, reject) => {
				const child = spawn(
					python,
					["-m", "concorde.distribution.outer_check"],
					{
						cwd: ctx.cwd,
						env: {
							...process.env,
							...(selected ? { CONCORDE_SESSION_SELECTION: selected } : {}),
							PYTHONPATH: resolve(framework, "src"),
							PYTHONDONTWRITEBYTECODE: "1",
						},
						stdio: ["pipe", "pipe", "pipe"],
					},
				);
				let output = "";
				let diagnostics = "";
				const abort = () => child.kill("SIGTERM");
				signal?.addEventListener("abort", abort, { once: true });
				child.stdout.on("data", (data) => {
					output = (output + data).slice(-100000);
				});
				child.stderr.on("data", (data) => {
					diagnostics = (diagnostics + data).slice(-20000);
				});
				child.on("error", reject);
				child.on("close", (code) => {
					signal?.removeEventListener("abort", abort);
					if (code !== 0 || signal?.aborted)
						reject(
							new Error(
								signal?.aborted
									? "Test cancelled"
									: `Isolated check unavailable: ${diagnostics}`,
							),
						);
					else done(output);
				});
				child.stdin.on("error", () => {});
				child.stdin.end(
					JSON.stringify({
						command: params.command,
						timeout: params.timeout ?? 600,
					}),
				);
				if (signal?.aborted) abort();
			});
			const result = JSON.parse(response);
			if (result.returncode !== 0) throw new Error(JSON.stringify(result));
			return {
				content: [{ type: "text", text: JSON.stringify(result) }],
				details: result,
			};
		},
	});
	// Defense against accidental effective-profile widening by settings overrides.
	const allowed = new Set([
		"read",
		"grep",
		"find",
		"ls",
		"test_command",
		"structured_output",
		"contact_supervisor",
	]);
	pi.on("tool_call", (event) =>
		allowed.has(event.toolName)
			? undefined
			: {
					block: true,
					reason: "Tester capability is read-only; use isolated test_command",
				},
	);
}
