// Drives pi/native-preflight.ts against a scripted pi-subagents preflight; never launches a model.
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const [repository] = process.argv.slice(2);
const root = fs.mkdtempSync(path.join(os.tmpdir(), "concorde-preflight-"));
const packageRoot = path.join(root, "node_modules/pi-subagents");
fs.mkdirSync(packageRoot, { recursive: true });
fs.writeFileSync(
  path.join(packageRoot, "package.json"),
  JSON.stringify({
    name: "pi-subagents",
    type: "module",
    exports: { "./preflight": "./preflight.mjs" },
  }),
);
fs.writeFileSync(
  path.join(packageRoot, "preflight.mjs"),
  "export async function resolveSubagentLaunchContract(call) {\n" +
    "  globalThis.preflightCalls = (globalThis.preflightCalls ?? 0) + 1;\n" +
    "  return globalThis.scriptedPreflight(call);\n" +
    "}\n",
);
const { nativePreflight } = await import(
  path.join(repository, "pi/native-preflight.ts")
);

const cwd = path.join(root, "capsule");
const contract = (agent, change = {}) => ({
  agent: {
    source: "project",
    filePath: path.join(cwd, ".pi/agents", agent + ".md"),
  },
  tools: {
    disableAmbientExtensions: true,
    fanoutAuthorized: false,
    effectiveAllowlist: ["read", "grep", "find", "ls", "structured_output"],
  },
  context: "fresh",
  inheritProjectContext: false,
  inheritGlobalContext: false,
  inheritSkills: false,
  skills: { resolved: [] },
  intercomBridge: { active: false },
  launchContractDigest: "sha256:fixture",
  ...change,
});
const run = (agent, value) => {
  globalThis.scriptedPreflight = () => value;
  return nativePreflight(root, { agent, cwd });
};
const refused = async (agent, value, pattern) => {
  await assert.rejects(run(agent, value), pattern);
};

const assessor = "concorde-context-assessor";
const accepted = await run(assessor, {
  ok: true,
  contract: contract(assessor),
});
assert.equal(accepted.launchContractDigest, "sha256:fixture");
// The programmer's wider tool ceiling is its own, not every Agent's.
const programmerTools = contract("concorde-programmer", {
  tools: {
    disableAmbientExtensions: true,
    fanoutAuthorized: false,
    effectiveAllowlist: ["read", "edit", "write", "bash", "run_checks"],
  },
});
await run("concorde-programmer", { ok: true, contract: programmerTools });
await refused(
  assessor,
  {
    ok: true,
    contract: { ...programmerTools, agent: contract(assessor).agent },
  },
  /exceeds its terminal read policy/,
);

// pi-subagents' own refusal is a Host refusal that keeps its reasons as causes.
let failure;
try {
  await run(assessor, {
    ok: false,
    message: "agent not found",
    errors: [{ message: "no project agent named " + assessor }],
  });
} catch (error) {
  failure = error.feedback;
}
assert.equal(failure.layer, "native-preflight");
assert.equal(failure.category, "host-refusal");
assert.equal(failure.causes[0].message, "no project agent named " + assessor);

const role = /did not resolve the exact capsule role/;
await refused(
  assessor,
  {
    ok: true,
    contract: contract(assessor, {
      agent: { source: "project", filePath: path.join(root, "other.md") },
    }),
  },
  role,
);
await refused(
  assessor,
  {
    ok: true,
    contract: contract(assessor, {
      agent: { ...contract(assessor).agent, source: "user" },
    }),
  },
  role,
);
for (const tools of [
  { disableAmbientExtensions: false, fanoutAuthorized: false },
  { disableAmbientExtensions: true, fanoutAuthorized: true },
])
  await refused(
    assessor,
    {
      ok: true,
      contract: contract(assessor, {
        tools: { ...tools, effectiveAllowlist: ["read"] },
      }),
    },
    role,
  );
const inherited = /inherited ungranted context or Skills/;
for (const change of [
  { context: "fork" },
  { inheritProjectContext: true },
  { inheritGlobalContext: true },
  { inheritSkills: true },
  { skills: { resolved: ["ambient-skill"] } },
  { intercomBridge: { active: true } },
])
  await refused(
    assessor,
    { ok: true, contract: contract(assessor, change) },
    inherited,
  );
fs.rmSync(root, { recursive: true, force: true });
console.log(
  JSON.stringify({ preflightCalls: globalThis.preflightCalls, models: 0 }),
);
