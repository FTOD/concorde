/** Fixed deterministic workflow steps. Never starts a model or schedules a child. */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
const [action, descriptorPath, checksum] = process.argv.slice(2);
const descriptor = JSON.parse(fs.readFileSync(descriptorPath, "utf8"));
const python = descriptor.python;
const launcher = path.join(descriptor.package_root, "scripts/run-operation.py");
const invoke = (step, file = descriptorPath, hash = checksum) =>
  JSON.parse(
    execFileSync(python, [launcher, "--native-context", step, file, hash], {
      cwd: descriptor.project_root,
      input: "{}",
      encoding: "utf8",
      maxBuffer: 2 * 1024 * 1024,
      timeout: 60000,
    }),
  );
async function preflight(prepared) {
  const slot = JSON.parse(fs.readFileSync(prepared.descriptor, "utf8"));
  const require = createRequire(
    path.join(slot.runtime.package_root, "package.json"),
  );
  const { createJiti } = require("jiti");
  const jiti = createJiti(import.meta.url, { interopDefault: true });
  const { nativePreflight } = await jiti.import(
    path.join(slot.package_root, "pi/native-preflight.ts"),
  );
  const contract = await nativePreflight(
    slot.runtime.package_root,
    prepared.call,
  );
  fs.writeFileSync(
    path.join(slot.directory, "preflight.json"),
    JSON.stringify(contract),
    { flag: "wx" },
  );
}
if (action === "bind") {
  const file = path.join(descriptor.directory, "workflow-binding.json");
  const deadline = Date.now() + 15000;
  while (!fs.existsSync(file) && Date.now() < deadline)
    await new Promise((resolve) => setTimeout(resolve, 20));
  if (!fs.existsSync(file))
    throw new Error("Native workflow launch binding did not arrive");
  invoke("check");
  await preflight({ descriptor: descriptorPath, call: descriptor.launch });
  console.log(JSON.stringify({ state: "ready" }));
} else if (action === "advance") {
  const value = invoke("workflow-advance");
  if (value.state === "prepared") {
    await preflight(value);
    console.log(
      JSON.stringify({
        state: value.state,
        ticket: value.ticket,
        call: value.call,
      }),
    );
  } else console.log(JSON.stringify(value));
} else if (action === "finalize")
  console.log(JSON.stringify(invoke("workflow-finalize")));
else throw new Error("Unknown fixed planning Host step");
