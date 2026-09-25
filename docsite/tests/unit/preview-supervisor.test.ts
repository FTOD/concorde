import { EventEmitter } from "node:events";
import { afterEach, expect, it } from "vitest";

import type { ScopedRegistry } from "../../plugins/scoped-content/model";
import {
  PreviewSupervisor,
  previewInputs,
  type PreviewProcess,
} from "../../scripts/preview";

const root = "/project";
const siteDir = "/project/docsite";

function registry(pages: string[]): ScopedRegistry {
  return {
    projectRoot: root,
    registryPath: ".concorde/specs.json",
    pages: pages.map((sourcePath) => ({
      sourcePath,
      metadataPath: sourcePath + ".json",
    })),
  } as unknown as ScopedRegistry;
}

class FakeChild extends EventEmitter implements PreviewProcess {
  signals: string[] = [];
  constructor(readonly args: string[]) {
    super();
  }
  kill(signal: NodeJS.Signals): void {
    this.signals.push(signal);
    queueMicrotask(() => this.emit("exit", null, signal));
  }
}

function harness(initial: ScopedRegistry) {
  const state = {
    model: initial as ScopedRegistry | Error,
    prepared: 0,
    children: [] as FakeChild[],
    listeners: new Map<string, (name: string | null) => void>(),
    closed: [] as string[],
    logs: [] as string[],
  };
  const supervisor = new PreviewSupervisor(
    siteDir,
    ["--port", "4000"],
    {
      prepare: async () => {
        state.prepared++;
        if (state.model instanceof Error) throw state.model;
        return state.model;
      },
      launch: (args) => {
        const child = new FakeChild(args);
        state.children.push(child);
        return child;
      },
      watch: (directory, listener) => {
        state.listeners.set(directory, listener);
        return {
          close: () => {
            state.closed.push(directory);
            state.listeners.delete(directory);
          },
        };
      },
      log: (message) => state.logs.push(message),
    },
    5,
  );
  const change = (directory: string, name: string | null) =>
    state.listeners.get(directory)!(name);
  return { supervisor, state, change };
}

let active: PreviewSupervisor | undefined;
afterEach(async () => {
  await active?.stop();
  active = undefined;
});

// verifies: scenario.views.preview-restart
it("watches the site identity, configuration, registry and both members of every document", () => {
  expect(previewInputs(registry(["specs/a/module.md"]), siteDir)).toEqual([
    "/project/docsite/site.json",
    "/project/.concorde/config.json",
    "/project/.concorde/specs.json",
    "/project/specs/a/module.md",
    "/project/specs/a/module.md.json",
  ]);
});

// verifies: scenario.views.preview-restart
it("stages again and restarts the preview when a registered input changes", async () => {
  const { supervisor, state, change } = harness(
    registry(["specs/a/module.md"]),
  );
  active = supervisor;
  await supervisor.start();
  expect(state.prepared).toBe(1);
  expect(state.children.map((child) => child.args)).toEqual([
    ["--port", "4000"],
  ]);
  expect([...state.listeners.keys()].sort()).toEqual([
    "/project/.concorde",
    "/project/docsite",
    "/project/specs/a",
  ]);

  // An unrelated file in a watched directory is ignored.
  change("/project/specs/a", "notes.txt");
  change("/project/.concorde", "config.json.tmp");
  await supervisor.settled();
  expect(state.prepared).toBe(1);

  // A new document in a new directory: the registry and metadata change together, once.
  state.model = registry(["specs/a/module.md", "specs/b/module.md"]);
  change("/project/.concorde", "specs.json");
  change("/project/specs/a", "module.md.json");
  await supervisor.settled();
  expect(state.prepared).toBe(2);
  expect(state.children[0].signals).toEqual(["SIGTERM"]);
  expect(state.children[1].args).toEqual(["--port", "4000", "--no-open"]);
  expect(state.listeners.has("/project/specs/b")).toBe(true);
  expect(state.logs[0]).toContain("/project/.concorde/specs.json");

  // Removing the document closes the watcher of its directory.
  state.model = registry(["specs/a/module.md"]);
  change("/project/specs/b", "module.md");
  await supervisor.settled();
  expect(state.closed).toContain("/project/specs/b");
  expect(state.children).toHaveLength(3);
});

// verifies: scenario.views.preview-restart-failure
it("reports a failed staging, keeps watching, and retries on the next change in a watched directory", async () => {
  const { supervisor, state, change } = harness(
    registry(["specs/a/module.md"]),
  );
  active = supervisor;
  await supervisor.start();
  state.model = new Error("Missing Spec: specs/a/topic.md");
  change("/project/specs/a", "module.md.json");
  await supervisor.settled();
  expect(state.children[0].signals).toEqual(["SIGTERM"]);
  expect(state.children).toHaveLength(1);
  expect(state.logs.at(-1)).toMatch(
    /could not stage the Specs, so no preview is running:\n.*Missing Spec: specs\/a\/topic\.md/s,
  );
  expect(state.logs.at(-1)).toContain(
    "Waiting for a change to a registered input",
  );

  // Generated entries beside site.json never retry, even after a failure.
  change("/project/docsite", ".docusaurus");
  await supervisor.settled();
  expect(state.prepared).toBe(2);

  // The missing file is not yet an input, but after a failure a new document retries.
  state.model = registry(["specs/a/module.md", "specs/a/topic.md"]);
  change("/project/specs/a", "topic.md");
  await supervisor.settled();
  expect(state.children).toHaveLength(2);
  expect(state.listeners.has("/project/specs/a")).toBe(true);
});

// verifies: scenario.views.preview-restart-failure
it("fails the command when the first staging fails", async () => {
  const { supervisor, state } = harness(registry([]));
  state.model = new Error("No Concorde configuration");
  await expect(supervisor.start()).rejects.toThrow(/could not be staged/);
  expect(state.logs[0]).toContain("No Concorde configuration");
  expect(state.logs[0]).toContain("run `npm run start` again");
  expect(state.children).toHaveLength(0);
});

// verifies: scenario.views.preview-restart
it("waits for a change after the preview exits on its own and stops cleanly", async () => {
  const { supervisor, state, change } = harness(
    registry(["specs/a/module.md"]),
  );
  await supervisor.start();
  state.children[0].emit("exit", 1, null);
  expect(state.logs.at(-1)).toContain("exited on its own (status 1)");
  change("/project/specs/a", "module.md");
  await supervisor.settled();
  expect(state.children).toHaveLength(2);
  await supervisor.stop();
  expect(state.children[1].signals).toEqual(["SIGTERM"]);
  expect(state.listeners.size).toBe(0);
});
