// Drives a Concorde Pi extension outside Pi and records every process it starts.
//
//   node session_tool_harness.mjs <extension.ts> <root> [catalog.json]
//
// With a catalog the tracked session extension's `concordeSession(root, catalog)` is bound here;
// without one the module's default export (a rendered entry, or an extension such as the tester
// or maintenance guard) is used as is. The TypeScript sources load through the checkout's jiti,
// exactly as Pi loads them. Every `child_process.spawn`/`spawnSync` is recorded, so a step can
// show which processes it started.
//
// Stdin carries {"steps": [...]}; each step is one of
//   {"call": {params}, "tool": "concorde", "abort_after_ms": 500, "cwd": "/dir"}
//   {"emit": "tool_call", "event": {...}, "cwd": "/dir"}
//   {"env": {"NAME": "value" | null}}
//   {"append": "/path/file", "text": "..."}
//   {"branch": [session entries]}      (what ctx.sessionManager.getBranch() returns from now on)
//   {"command": "task-brief", "args": "..."}
// and stdout receives one JSON object: the load error (if the extension refused to load), the
// appended system prompt, the registered tools, appended session entries and one outcome per step.
import childProcess from "node:child_process";
import fs from "node:fs";
import { createRequire, syncBuiltinESMExports } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const [extensionPath, root, catalogPath] = process.argv.slice(2);
if (!extensionPath || !root) {
  console.error(
    "usage: session_tool_harness.mjs <extension.ts> <root> [catalog.json]",
  );
  process.exit(2);
}
const repository = path.resolve(
  fileURLToPath(new URL("../../../", import.meta.url)),
);
const input = JSON.parse(fs.readFileSync(0, "utf8"));

const spawned = [];
const originalSpawn = childProcess.spawn;
const originalSpawnSync = childProcess.spawnSync;
childProcess.spawn = function (command, args, ...rest) {
  spawned.push([command, ...(Array.isArray(args) ? args : [])]);
  return originalSpawn.call(this, command, args, ...rest);
};
childProcess.spawnSync = function (command, args, ...rest) {
  spawned.push([command, ...(Array.isArray(args) ? args : [])]);
  return originalSpawnSync.call(this, command, args, ...rest);
};
syncBuiltinESMExports();

const setEnv = (changes) => {
  for (const [key, value] of Object.entries(changes ?? {})) {
    if (value === null) delete process.env[key];
    else process.env[key] = value;
  }
};
setEnv(input.env);

const require = createRequire(path.join(repository, "pi/package.json"));
const { createJiti } = require("jiti");
const jiti = createJiti(import.meta.url, {
  fsCache: false,
  moduleCache: false,
});

const handlers = new Map();
const tools = new Map();
const commands = new Map();
const entries = [];
const bus = new Map();
let branch = [];
const pi = {
  on(name, handler) {
    handlers.set(name, [...(handlers.get(name) ?? []), handler]);
  },
  registerTool(definition) {
    tools.set(definition.name, definition);
  },
  registerCommand(name, definition) {
    commands.set(name, definition);
  },
  appendEntry(customType, data) {
    entries.push({ customType, data });
  },
  sendMessage() {},
  events: {
    on(name, handler) {
      bus.set(name, [...(bus.get(name) ?? []), handler]);
      return () =>
        bus.set(
          name,
          (bus.get(name) ?? []).filter((item) => item !== handler),
        );
    },
    emit(name, value) {
      for (const handler of bus.get(name) ?? []) handler(value);
    },
  },
};
const context = (cwd) => ({
  cwd: cwd ?? root,
  hasUI: false,
  mode: "print",
  isIdle: () => true,
  sessionManager: {
    getSessionId: () => "harness-session",
    getSessionFile: () => undefined,
    getBranch: () => branch,
    getEntries: () => branch,
    getHeader: () => ({ id: "harness-session", cwd: cwd ?? root }),
  },
  modelRegistry: { getAvailable: () => [] },
  ui: { notify() {}, setStatus() {}, setWidget() {} },
});
const emit = async (name, event, cwd) => {
  const outcomes = [];
  for (const handler of handlers.get(name) ?? [])
    outcomes.push((await handler(event, context(cwd))) ?? null);
  return outcomes;
};

const output = {
  load_error: null,
  load_spawned: [],
  prompt: null,
  tools: [],
  entries,
  steps: [],
};
try {
  const loaded = await jiti.import(path.resolve(extensionPath));
  const extension = catalogPath
    ? loaded.concordeSession(
        root,
        JSON.parse(fs.readFileSync(catalogPath, "utf8")),
      )
    : (loaded.default ?? loaded);
  extension(pi);
} catch (error) {
  output.load_error = String(error?.message ?? error);
}
output.load_spawned = spawned.splice(0);
output.tools = [...tools.values()].map((tool) => ({
  name: tool.name,
  parameters: tool.parameters,
}));
if (!output.load_error && handlers.has("before_agent_start")) {
  const [started] = await emit("before_agent_start", {
    prompt: "hello",
    systemPrompt: "BASE PROMPT\n",
    systemPromptOptions: {},
  });
  output.prompt = started?.systemPrompt ?? null;
}

for (const step of output.load_error ? [] : (input.steps ?? [])) {
  const startedAt = Date.now();
  const outcome = {};
  if (step.env) setEnv(step.env);
  if (step.append) fs.appendFileSync(step.append, step.text ?? "\n");
  if (step.branch) branch = step.branch;
  if (step.command) {
    try {
      await commands
        .get(step.command)
        .handler(step.args ?? "", context(step.cwd));
      outcome.ok = true;
    } catch (error) {
      Object.assign(outcome, {
        ok: false,
        error: String(error?.message ?? error),
      });
    }
  }
  if (step.emit) {
    const event = JSON.parse(JSON.stringify(step.event ?? {}));
    outcome.results = await emit(step.emit, event, step.cwd);
    outcome.event = event;
  }
  if (step.call) {
    const tool = tools.get(step.tool ?? "concorde");
    const controller = new AbortController();
    let timer;
    if (typeof step.abort_after_ms === "number")
      timer = setTimeout(() => controller.abort(), step.abort_after_ms);
    try {
      const result = await tool.execute(
        step.id ?? "call",
        step.call,
        controller.signal,
        undefined,
        context(step.cwd),
      );
      Object.assign(outcome, {
        ok: true,
        text: result.content.map((item) => item.text).join(""),
        details: result.details,
      });
    } catch (error) {
      Object.assign(outcome, {
        ok: false,
        error: String(error?.message ?? error),
      });
    } finally {
      if (timer) clearTimeout(timer);
    }
  }
  outcome.spawned = spawned.splice(0);
  outcome.elapsed_ms = Date.now() - startedAt;
  output.steps.push(outcome);
}
process.stdout.write(JSON.stringify(output));
process.exit(0);
