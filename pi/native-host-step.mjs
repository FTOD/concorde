/** Shared Host-step helper of every workflow: binding wait, one Python step, slot preflight.
 *
 * A provider's Host-step script is `node <script> <step> <descriptor> <digest>`. The helper waits
 * for the Workflow's launch binding, runs the Python step `workflow-<step>` with a 2 MiB output
 * bound, and then, for every issued slot without a recorded preflight, runs the slot's prelaunch
 * `check` and pi-subagents' launch preflight, recording the resolved contract as `preflight.json`
 * in the slot directory. It never starts or waits for a model.
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { installHostErrors } from "./native-host-error.mjs";

const OUTPUT_BOUND = 2 * 1024 * 1024;
const BINDING_WAIT_MS = 15000;

function python(context, argv, timeout) {
  const { descriptor } = context;
  return JSON.parse(
    execFileSync(
      descriptor.python,
      [
        path.join(descriptor.package_root, "scripts/run-operation.py"),
        "--native-context",
        ...argv,
      ],
      {
        cwd: descriptor.project_root,
        input: "{}",
        encoding: "utf8",
        maxBuffer: OUTPUT_BOUND,
        timeout,
      },
    ),
  );
}

async function waitForBinding(descriptor) {
  const file = path.join(descriptor.directory, "workflow-binding.json");
  const deadline = Date.now() + BINDING_WAIT_MS;
  while (!fs.existsSync(file) && Date.now() < deadline)
    await new Promise((resolve) => setTimeout(resolve, 20));
  if (!fs.existsSync(file))
    throw new Error("Native workflow launch binding did not arrive");
}

function bindings(descriptor) {
  const directory = path.join(descriptor.directory, "bindings");
  if (!fs.existsSync(directory)) return [];
  return fs
    .readdirSync(directory)
    .filter((name) => name.endsWith(".json"))
    .sort()
    .map((name) =>
      JSON.parse(fs.readFileSync(path.join(directory, name), "utf8")),
    );
}

async function preflightSlots(context, verify) {
  const { descriptor } = context;
  const runtime = descriptor.runtime.package_root;
  const require = createRequire(path.join(runtime, "package.json"));
  const { createJiti } = require("jiti");
  const jiti = createJiti(import.meta.url, { interopDefault: true });
  const { nativePreflight } = await jiti.import(
    path.join(descriptor.package_root, "pi/native-preflight.ts"),
  );
  for (const binding of bindings(descriptor)) {
    const slot = path.dirname(binding.descriptor);
    if (fs.existsSync(path.join(slot, "preflight.json"))) continue;
    if (verify) verify(binding, context);
    const checked = python(
      context,
      ["check", binding.descriptor, binding.digest],
      60000,
    );
    if (checked.state !== "prepared")
      throw new Error("Slot " + binding.key + " failed prelaunch admission");
    const contract = await nativePreflight(runtime, binding.call);
    fs.writeFileSync(
      path.join(slot, "preflight.json"),
      JSON.stringify(contract),
      {
        flag: "wx",
      },
    );
  }
}

/**
 * Run the Host step named on the command line and return its answer, after preflighting the
 * slots it issued. `verify(binding, context)` lets a provider check each new slot's call first.
 */
export async function runHostStep({ timeout, verify } = {}) {
  const [step, file, checksum] = process.argv.slice(2);
  const descriptor = JSON.parse(fs.readFileSync(file, "utf8"));
  installHostErrors(descriptor.directory, step, descriptor.ticket);
  const context = { step, file, checksum, descriptor };
  await waitForBinding(descriptor);
  const value = python(context, ["workflow-" + step, file, checksum], timeout);
  await preflightSlots(context, verify);
  return { value, context };
}
