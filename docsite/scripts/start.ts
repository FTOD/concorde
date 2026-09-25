import { spawn } from "node:child_process";
import { watch } from "node:fs";
import { resolve } from "node:path";

import { preparePublication } from "./prepare-publication";
import { PreviewSupervisor } from "./preview";

const siteDir = resolve(__dirname, "..");
const projectRoot = resolve(siteDir, "..");

async function main(): Promise<void> {
  const cli = resolve(
    siteDir,
    "node_modules/@docusaurus/core/bin/docusaurus.mjs",
  );
  const supervisor = new PreviewSupervisor(siteDir, process.argv.slice(2), {
    prepare: async () => (await preparePublication(projectRoot)).registry,
    launch: (args) => {
      const child = spawn(process.execPath, [cli, "start", ...args], {
        cwd: siteDir,
        stdio: "inherit",
        env: { ...process.env, NODE_ENV: "development" },
      });
      // A process that never started has no exit of its own; report why and count it as exited.
      child.once("error", (error) => {
        console.error(
          `[concorde] Docusaurus could not be started (${process.execPath} ${cli} start): ${error.stack ?? error.message}`,
        );
        child.emit("exit", null, null);
      });
      return child;
    },
    // A watcher error, such as its directory being removed, counts as a change of the directory.
    watch: (directory, listener) =>
      watch(directory, (_event, name) => listener(name)).on("error", () =>
        listener(null),
      ),
    log: (message) => console.error(`[concorde] ${message}`),
  });
  for (const signal of ["SIGINT", "SIGTERM"] as const)
    process.once(
      signal,
      () => void supervisor.stop().then(() => process.exit(0)),
    );
  await supervisor.start();
}

void main().catch((error: unknown) => {
  console.error(error);
  process.exit(1);
});
