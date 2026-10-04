import { resolve } from "node:path";

import {
  loadScopedRegistry,
  requireScoped,
} from "../plugins/scoped-content/model";
import { renderDiagrams } from "../plugins/scoped-content/diagrams";
import { renderPage } from "../plugins/scoped-content/render";

function projectRoot(): string {
  const index = process.argv.indexOf("--project-root");
  return resolve(
    index >= 0 && process.argv[index + 1]
      ? process.argv[index + 1]
      : resolve(__dirname, "../.."),
  );
}

async function main() {
  const root = projectRoot();
  requireScoped(root);
  const registry = loadScopedRegistry(root);
  // Step 2 of staging, diagrams included, in memory: nothing is written.
  for (const page of registry.pages)
    await renderDiagrams(registry, page, renderPage(registry, page), null);
  process.stdout.write(
    `Validated publication: ${registry.modules.length} Modules, ${registry.pages.length} documents.\n`,
  );
}

void main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
