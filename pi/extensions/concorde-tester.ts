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
			"Run a scoped test in the OS read-only host filesystem. Fresh CONCORDE_CHECK_TMPDIR scratch and its private /tmp backing are writable and removed afterward. Read other preexisting host-/tmp inputs through CONCORDE_TEST_HOST_TMP; governing project/runtime paths stay canonical and read-only. No runtime-asset staging or unrestricted shell fallback. UI tails are 20KB per stream; Host exports bounded output and explicitly named reports from CONCORDE_CHECK_REPORT_DIR to canonical primary run evidence before cleanup. Read the returned manifest; incomplete/export failure is not success. Never put secrets in output or selected reports.",
		parameters: Type.Object(
			{
				command: Type.String({ maxLength: 32768 }),
				timeout: Type.Optional(Type.Number({ minimum: 1, maximum: 3600 })),
				reports: Type.Optional(
					Type.Array(Type.String({ minLength: 1, maxLength: 240 }), {
						maxItems: 16,
						uniqueItems: true,
					}),
				),
			},
			{ additionalProperties: false },
		),
		async execute(id, params, signal, _update, ctx) {
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
							CONCORDE_TEST_TOOL_CALL_ID: id,
						},
						stdio: ["pipe", "pipe", "pipe"],
					},
				);
				let output = "";
				let diagnostics = "";
				let ready = false;
				let overflow = false;
				// Wait for the Host's cancellation handler/evidence identity, even if the
				// turn aborts during Python startup or private-selection verification.
				const abort = () => {
					if (ready) child.kill("SIGTERM");
				};
				signal?.addEventListener("abort", abort, { once: true });
				child.stdout.on("data", (data) => {
					if (overflow) return;
					output += data;
					if (output.length > 1024 * 1024) {
						output = output.slice(0, 1024 * 1024);
						overflow = true;
						child.kill("SIGTERM");
						return;
					}
					if (!ready && output.includes("\n")) {
						try {
							ready =
								JSON.parse(output.split("\n")[0]).tester_check_ready === true;
						} catch {
							/* Invalid bridge output is rejected on close. */
						}
						if (signal?.aborted) abort();
					}
				});
				child.stderr.on("data", (data) => {
					diagnostics = (diagnostics + data).slice(-20000);
				});
				child.on("error", reject);
				child.on("close", (code) => {
					signal?.removeEventListener("abort", abort);
					if (overflow)
						reject(
							new Error(
								"Tester bridge response exceeded 1 MiB; evidence acknowledgement incomplete",
							),
						);
					else if (code !== 0)
						reject(
							new Error(
								`Tester bridge exited ${code}; evidence acknowledgement unavailable. ${diagnostics}; ${output}`,
							),
						);
					else done(output);
				});
				child.stdin.on("error", () => {});
				child.stdin.end(
					JSON.stringify({
						command: params.command,
						timeout: params.timeout ?? 600,
						reports: params.reports ?? [],
					}),
				);
				if (signal?.aborted) abort();
			});
			const result = JSON.parse(response.trim().split("\n").at(-1)!);
			if (signal?.aborted) result.cancellation_requested = true;
			if (
				result.returncode !== 0 ||
				result.cancelled ||
				result.error ||
				!result.evidence?.complete ||
				signal?.aborted
			)
				throw new Error(JSON.stringify(result));
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
