import { resolve } from "node:path";

import {
  loadScopedRegistry,
  requireScoped,
} from "../plugins/scoped-content/model";
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
  registry.pages.forEach((page) => renderPage(registry, page));
  process.stdout.write(
    `Validated publication: ${registry.modules.length} Modules, ${registry.pages.length} documents.\n`,
  );
}

void main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
