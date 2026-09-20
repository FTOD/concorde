// Deterministic public pi-subagents preflight; never launches a child or model.
import { createRequire } from "node:module";
import { resolve } from "node:path";
const [subagents, piRoot, cwd] = process.argv.slice(2);
const require = createRequire(resolve(subagents, "package.json"));
const { createJiti } = require("jiti");
const peers = ["pi-coding-agent", "pi-ai", "pi-agent-core", "pi-tui"];
const alias = Object.fromEntries(
  peers.map((name) => [
    `@earendil-works/${name}`,
    name === "pi-coding-agent"
      ? resolve(piRoot, "dist/index.js")
      : resolve(piRoot, "node_modules/@earendil-works", name, "dist/index.js"),
  ]),
);
const jiti = createJiti(import.meta.url, { alias });
const { resolveSubagentLaunchContract } = await jiti.import(
  resolve(subagents, "src/api/preflight.ts"),
);
const results = [];
for (const agent of ["maintenance-worker", "tester"]) {
  results.push(
    await resolveSubagentLaunchContract({
      agent,
      cwd,
      agentScope: "project",
      context: "fresh",
      skill: false,
      intercomBridge: { mode: "off" },
      artifacts: false,
      sessionRoot: process.env.TMPDIR,
    }),
  );
}
console.log(JSON.stringify(results));
