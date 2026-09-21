/** Finite review preflight/aggregation; no model calls. */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
const [action, file, checksum] = process.argv.slice(2);
const base = JSON.parse(fs.readFileSync(file, "utf8"));
const invoke = (step) =>
  JSON.parse(
    execFileSync(
      base.python,
      [
        path.join(base.package_root, "scripts/run-operation.py"),
        "--native-context",
        step,
        file,
        checksum,
      ],
      {
        cwd: base.project_root,
        input: "{}",
        encoding: "utf8",
        maxBuffer: 2 * 1024 * 1024,
        timeout: 1800000,
      },
    ),
  );
if (action === "bind") {
  const binding = path.join(base.directory, "workflow-binding.json");
  const deadline = Date.now() + 15000;
  while (!fs.existsSync(binding) && Date.now() < deadline)
    await new Promise((r) => setTimeout(r, 20));
  if (!fs.existsSync(binding))
    throw new Error("Native review launch binding did not arrive");
  invoke("workflow-check");
  const require = createRequire(
    path.join(base.runtime.package_root, "package.json"),
  );
  const { createJiti } = require("jiti");
  const jiti = createJiti(import.meta.url, { interopDefault: true });
  const { nativePreflight } = await jiti.import(
    path.join(base.package_root, "pi/native-preflight.ts"),
  );
  const scope = JSON.parse(
    fs.readFileSync(path.join(base.directory, "review-scope.json"), "utf8"),
  );
  for (const entry of scope.slots) {
    const slot = JSON.parse(fs.readFileSync(entry.descriptor, "utf8"));
    const contract = await nativePreflight(
      base.runtime.package_root,
      entry.call,
    );
    fs.writeFileSync(
      path.join(slot.directory, "preflight.json"),
      JSON.stringify(contract),
      { flag: "wx" },
    );
  }
  console.log(JSON.stringify({ state: "ready" }));
} else if (action === "finalize")
  console.log(JSON.stringify(invoke("workflow-finalize")));
else throw new Error("Unknown fixed review step");
