// Drives the Concorde session extension outside Pi: a fake ExtensionAPI records the tool and the
// system-prompt hook, then every call listed on stdin runs against the tool's execute. Run with
// `node --experimental-strip-types` (Node 22) or plain `node` (Node 23.6+).
//
//   node --experimental-strip-types pi_session_harness.mts <extension-or-shim.ts> <root> [catalog.json]
//
// With a catalog the tracked extension's `concordeSession(root, catalog)` is bound here; without
// one the module's default export (a rendered shim) is used as is. Stdin carries
// {"calls": [{"params": {...}, "abort_after_ms": 500}, ...]} and stdout receives one JSON object
// with the appended system prompt, the tool definition and the outcome of every call.
import * as fs from "node:fs";
import { pathToFileURL } from "node:url";

const [extensionPath, root, catalogPath] = process.argv.slice(2);
if (!extensionPath || !root) {
	console.error("usage: pi_session_harness.mts <extension.ts> <root> [catalog.json]");
	process.exit(2);
}
const loaded = await import(pathToFileURL(extensionPath).href);
const extension = catalogPath
	? loaded.concordeSession(root, JSON.parse(fs.readFileSync(catalogPath, "utf8")))
	: loaded.default;

const handlers: Record<string, (event: any, ctx: any) => Promise<any>> = {};
const tools: any[] = [];
const pi = {
	on(event: string, handler: (event: any, ctx: any) => Promise<any>) {
		handlers[event] = handler;
	},
	registerTool(definition: any) {
		tools.push(definition);
	},
};
extension(pi);
const started = await handlers.before_agent_start(
	{ prompt: "hello", systemPrompt: "BASE PROMPT\n", systemPromptOptions: {} },
	{},
);
const input = JSON.parse(fs.readFileSync(0, "utf8"));
const results: any[] = [];
for (const call of input.calls ?? []) {
	const controller = new AbortController();
	let timer: NodeJS.Timeout | undefined;
	if (typeof call.abort_after_ms === "number")
		timer = setTimeout(() => controller.abort(), call.abort_after_ms);
	const startedAt = Date.now();
	try {
		const result = await tools[0].execute("call", call.params, controller.signal, undefined, {
			cwd: root,
		});
		results.push({
			ok: true,
			text: result.content.map((item: any) => item.text).join(""),
			details: result.details,
			elapsed_ms: Date.now() - startedAt,
		});
	} catch (error: any) {
		results.push({ ok: false, error: String(error?.message ?? error), elapsed_ms: Date.now() - startedAt });
	} finally {
		if (timer) clearTimeout(timer);
	}
}
process.stdout.write(
	JSON.stringify({
		prompt: started.systemPrompt,
		tool: { name: tools[0].name, description: tools[0].description, parameters: tools[0].parameters },
		results,
	}),
);
