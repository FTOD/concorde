import { installHostErrors } from "./native-host-error.mjs";
/** One fixed finite Issue step plus actual public native preflight. No model scheduling. */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { issueCall, issueLayout } from "./issue-call.mjs";
const [action, file, checksum] = process.argv.slice(2);
const root = JSON.parse(fs.readFileSync(file, "utf8"));
installHostErrors(root.directory, action, root.ticket);
const layout = issueLayout(root, file, checksum);
if (action === "next-0") {
  const binding = path.join(root.directory, "workflow-binding.json");
  const deadline = Date.now() + 15000;
  while (!fs.existsSync(binding) && Date.now() < deadline)
    await new Promise((r) => setTimeout(r, 20));
  if (!fs.existsSync(binding)) throw new Error("Issue launch binding missing");
}
const value = JSON.parse(
  execFileSync(
    root.python,
    [
      path.join(root.package_root, "scripts/run-operation.py"),
      "--native-context",
      "workflow-issue-" + action,
      file,
      checksum,
    ],
    {
      cwd: root.project_root,
      input: "{}",
      encoding: "utf8",
      maxBuffer: 2 * 1024 * 1024,
      timeout: 1800000,
    },
  ),
);
const keys = [];
const iteration = Number(action.split("-").at(-1));
if (action.startsWith("next") && value.route === "decide")
  keys.push("d-" + iteration);
if (value.route === "verify")
  for (let group = 0; group < 4; group++)
    for (let member = 0; member < value.groups[group]; member++)
      keys.push(`v-${iteration}-${group}-${member}`);
const require = createRequire(
  path.join(root.runtime.package_root, "package.json"),
);
const { createJiti } = require("jiti");
const jiti = createJiti(import.meta.url, { interopDefault: true });
const { nativePreflight } = await jiti.import(
  path.join(root.package_root, "pi/native-preflight.ts"),
);
for (const key of keys) {
  const binding = JSON.parse(
    fs.readFileSync(
      path.join(root.directory, "bindings", key + ".json"),
      "utf8",
    ),
  );
  const call = issueCall(layout, key);
  const stable = (v) =>
    v && typeof v === "object"
      ? Array.isArray(v)
        ? v.map(stable)
        : Object.fromEntries(
            Object.keys(v)
              .sort()
              .map((k) => [k, stable(v[k])]),
          )
      : v;
  if (JSON.stringify(stable(binding.call)) !== JSON.stringify(stable(call)))
    throw new Error("Issue call differs from exclusive slot binding");
  const checked = JSON.parse(
    execFileSync(
      root.python,
      [
        path.join(root.package_root, "scripts/run-operation.py"),
        "--native-context",
        "check",
        binding.descriptor,
        binding.digest,
      ],
      { cwd: root.project_root, input: "{}", encoding: "utf8", timeout: 60000 },
    ),
  );
  if (checked.state !== "prepared")
    throw new Error("Issue slot failed prelaunch admission");
  const contract = await nativePreflight(root.runtime.package_root, call);
  fs.writeFileSync(
    path.join(root.directory, "slots", key, "preflight.json"),
    JSON.stringify(contract),
    { flag: "wx" },
  );
}
const text = JSON.stringify(value, Object.keys(value).sort());
if (Buffer.byteLength(text) > 2048)
  throw new Error("Issue Host control exceeds its bound");
console.log(text);
