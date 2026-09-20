// Source-only explicit child observer; never an Operation catalog or tool provider.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { observe } from "./concorde-observe.ts";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
export default function (pi: ExtensionAPI) {
	observe(pi, "maintenance-worker");
	pi.on("tool_call", (event, ctx) => {
		if (
			!existsSync(resolve(ctx.cwd, "concorde.json")) ||
			!existsSync(resolve(ctx.cwd, "specs/concorde/module.md"))
		)
			return {
				block: true,
				reason:
					"maintenance-worker is restricted to a Concorde source repository",
			};
		if (["subagent", "concorde"].includes(event.toolName))
			return {
				block: true,
				reason:
					"Source maintenance cannot delegate tasks or use Operations to govern its authoring",
			};
	});
}
