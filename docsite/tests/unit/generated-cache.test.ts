import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { runInNewContext } from "node:vm";
import type { ConfigureWebpackUtils } from "@docusaurus/types";
import { afterEach, expect, it, vi } from "vitest";
import webpack, { type Configuration } from "webpack";
import { merge } from "webpack-merge";
import generatedCache from "../../plugins/generated-cache";
import {
  preparePublication,
  productionGeneratedDirectory,
} from "../../scripts/prepare-publication";

vi.mock("../../plugins/scoped-content/model", () => ({
  requireScoped: vi.fn(),
  loadScopedRegistry: vi.fn(() => ({})),
}));
vi.mock("../../plugins/scoped-content/materialize", () => ({
  materializeScoped: vi.fn(),
}));

const roots: string[] = [];
afterEach(async () => {
  await Promise.all(
    roots.splice(0).map((root) => rm(root, { recursive: true, force: true })),
  );
});

async function temporaryRoot() {
  const root = await mkdtemp(resolve(tmpdir(), "concorde-generated-cache-"));
  roots.push(root);
  return root;
}

function configure(generatedFilesDir: string, config: Configuration) {
  const plugin = generatedCache({ generatedFilesDir });
  return merge(
    config,
    plugin.configureWebpack!(
      config,
      false,
      {} as ConfigureWebpackUtils,
      undefined,
    ) ?? {},
  );
}

it("keeps filesystem cache names, versions and build dependencies", () => {
  const cache = {
    type: "filesystem" as const,
    name: "client-development-en",
    version: "test-version",
    buildDependencies: { config: [__filename] },
  };
  expect(configure("/site/.docusaurus", { cache }).cache).toEqual({
    ...cache,
    cacheDirectory: "/site/.docusaurus/webpack",
  });
});

it.each([undefined, false, true, { type: "memory" as const }])(
  "preserves non-filesystem cache setting %j",
  (cache) => {
    expect(configure("/site/.docusaurus", { cache }).cache).toEqual(cache);
  },
);

it.each(["preview", "build"] as const)(
  "preparation clears only the %s generated modules and compiled cache",
  async (mode) => {
    const root = await temporaryRoot();
    const directories = {
      preview: ".docusaurus",
      build: productionGeneratedDirectory,
    };
    for (const directory of Object.values(directories)) {
      for (const name of [
        "client-development-en",
        "client-production-en",
        "server-production-en",
      ]) {
        const cache = configure(resolve(root, "docsite", directory), {
          cache: { type: "filesystem", name },
        }).cache as webpack.FileCacheOptions;
        const path = resolve(cache.cacheDirectory!, name);
        await mkdir(path, { recursive: true });
        await writeFile(resolve(path, "index.pack"), name);
      }
    }
    await preparePublication(root, { mode });
    for (const [owner, directory] of Object.entries(directories)) {
      const file = resolve(
        root,
        "docsite",
        directory,
        "webpack/client-production-en/index.pack",
      );
      if (owner === mode) await expect(readFile(file)).rejects.toThrow();
      else expect(await readFile(file, "utf8")).toBe("client-production-en");
    }
  },
);

it("recovers stale managed search proxies without suppressing missing-export warnings", async () => {
  const root = await temporaryRoot();
  const generated = resolve(root, "docsite/.docusaurus");
  const packageDir = resolve(
    root,
    "node_modules/@easyops-cn/docusaurus-search-local",
  );
  const utils = resolve(packageDir, "dist/client/client/utils");
  await mkdir(utils, { recursive: true });
  await writeFile(
    resolve(packageDir, "package.json"),
    JSON.stringify({
      name: "@easyops-cn/docusaurus-search-local",
      version: "0.55.3",
    }),
  );
  const proxies = ["proxiedGenerated.js", "proxiedGeneratedConstants.js"];
  for (const proxy of proxies)
    await writeFile(resolve(utils, proxy), "export {};\n");
  await writeFile(
    resolve(root, "entry.js"),
    `
    import {searchContextByPaths} from './node_modules/@easyops-cn/docusaurus-search-local/dist/client/client/utils/proxiedGenerated.js';
    import {searchResultLimits} from './node_modules/@easyops-cn/docusaurus-search-local/dist/client/client/utils/proxiedGeneratedConstants.js';
    export const settings = {searchContextByPaths, searchResultLimits};
  `,
  );
  async function generate(limit: number) {
    const directory = resolve(
      generated,
      "@easyops-cn/docusaurus-search-local/default",
    );
    await mkdir(directory, { recursive: true });
    await writeFile(
      resolve(directory, "generated.js"),
      'export const searchContextByPaths = ["/specs", "/protocol"];',
    );
    await writeFile(
      resolve(directory, "generated-constants.js"),
      `export const searchResultLimits = ${limit};`,
    );
  }
  await generate(8);
  const config: Configuration = {
    mode: "development",
    context: root,
    target: "node",
    entry: "./entry.js",
    output: {
      path: resolve(root, "output"),
      filename: "bundle.cjs",
      library: { type: "commonjs2" },
    },
    resolve: { alias: { "@generated": generated } },
    cache: {
      type: "filesystem",
      name: "client-development-en",
      cacheDirectory: resolve(root, "node_modules/.cache/webpack"),
    },
    snapshot: { managedPaths: [resolve(root, "node_modules")] },
  };
  async function compile(configuration: Configuration) {
    const compiler = webpack(configuration)!;
    try {
      const stats = await new Promise<webpack.Stats>((accept, reject) => {
        compiler.run((error, result) =>
          error ? reject(error) : accept(result!),
        );
      });
      expect(stats.hasErrors(), stats.toString()).toBe(false);
      return stats.toJson({ all: false, warnings: true }).warnings ?? [];
    } finally {
      await new Promise<void>((accept, reject) =>
        compiler.close((error) => (error ? reject(error) : accept())),
      );
    }
  }
  expect(await compile(config)).toHaveLength(2);
  for (const proxy of proxies) {
    // Restore the real installed plugin's reexports; webpack still trusts the managed package snapshot.
    await writeFile(
      resolve(utils, proxy),
      await readFile(
        require.resolve(
          `@easyops-cn/docusaurus-search-local/dist/client/client/utils/${proxy}`,
        ),
      ),
    );
  }
  expect(await compile(config)).toHaveLength(2);
  expect(await compile(configure(generated, config))).toEqual([]);
  await preparePublication(root);
  await generate(12);
  expect(await compile(configure(generated, config))).toEqual([]);
  const module = { exports: {} };
  runInNewContext(await readFile(resolve(root, "output/bundle.cjs"), "utf8"), {
    module,
  });
  expect(JSON.parse(JSON.stringify(module.exports))).toEqual({
    settings: {
      searchContextByPaths: ["/specs", "/protocol"],
      searchResultLimits: 12,
    },
  });
});
