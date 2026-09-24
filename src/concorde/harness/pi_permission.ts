/**
 * The Concorde permission extension for pi workers.
 *
 * The Operation host copies this file into a run's `control/` directory, embeds the run's policy
 * in `POLICY` and the sandbox-runtime entry point in the import below, and loads it as the only
 * extension of `pi -p`. It replaces pi's file tools with checked versions (`read`, `write`, `edit`),
 * runs every command and search (`bash`, `grep`, `find`, `ls`) inside the sandbox-runtime sandbox
 * with the grant's filesystem lists and no network, stops the run at its turn and budget limits,
 * and receives the worker result through `concorde_result`. See the Workers Module's pi run
 * mechanics for the tables it follows.
 */

import { spawn } from "node:child_process";
import { stat } from "node:fs/promises";
import { homedir } from "node:os";
import { relative } from "node:path";
import { SandboxManager } from "@concorde/sandbox-runtime";
import { Type } from "typebox";
import {
  type BashOperations,
  createBashTool,
  createEditToolDefinition,
  createFindToolDefinition,
  createGrepToolDefinition,
  createLsToolDefinition,
  createReadToolDefinition,
  createWriteToolDefinition,
  type ExtensionAPI,
} from "@earendil-works/pi-coding-agent";
import {
  type Policy,
  readDecision,
  resolveLikePi,
  searchDecision,
  writeDecision,
} from "./pi_policy.ts";

const POLICY: Policy = {} as Policy;

const LIMIT_ENTRY = "concorde-limit";
const PREFIX = "Concorde grant: ";
const MAX_OUTPUT = 50 * 1024;

let sandboxReady: Promise<void> | undefined;
let sandboxStarted = false;

function sandbox(): Promise<void> {
  sandboxReady ??= (async () => {
    await SandboxManager.initialize({
      network: { allowedDomains: [], deniedDomains: [], strictAllowlist: true },
      filesystem: { ...POLICY.sandbox, denyWrite: [] },
    } as never);
    sandboxStarted = true;
  })();
  return sandboxReady;
}

function quote(value: string): string {
  return `'${value.replace(/'/g, `'\\''`)}'`;
}

interface Completed {
  stdout: string;
  stderr: string;
  code: number | null;
}

/** Run a shell command inside the sandbox, streaming or collecting its output. */
async function inSandbox(
  command: string,
  cwd: string,
  options: {
    signal?: AbortSignal;
    timeout?: number;
    onData?: (data: Buffer) => void;
  } = {},
): Promise<Completed> {
  await sandbox();
  const wrapped = await SandboxManager.wrapWithSandbox(command, undefined, {
    filesystem: { ...POLICY.sandbox, denyWrite: [] },
  } as never);
  return new Promise((resolve, reject) => {
    const child = spawn("bash", ["-c", wrapped], {
      cwd,
      detached: true,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    let timedOut = false;
    const kill = () => {
      try {
        process.kill(-(child.pid as number), "SIGKILL");
      } catch {
        child.kill("SIGKILL");
      }
    };
    const timer = options.timeout
      ? setTimeout(() => ((timedOut = true), kill()), options.timeout * 1000)
      : undefined;
    options.signal?.addEventListener("abort", kill, { once: true });
    child.stdout.on("data", (chunk: Buffer) => {
      if (options.onData) options.onData(chunk);
      else if (stdout.length < 8 * MAX_OUTPUT) stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk: Buffer) => {
      if (options.onData) options.onData(chunk);
      else if (stderr.length < MAX_OUTPUT) stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (timer) clearTimeout(timer);
      options.signal?.removeEventListener("abort", kill);
      if (options.signal?.aborted) reject(new Error("aborted"));
      else if (timedOut) reject(new Error(`timeout:${options.timeout}`));
      else resolve({ stdout, stderr, code });
    });
  });
}

/** Decide with `decision`; any failure inside the decision denies. */
function check(decision: () => string | null): void {
  let reason: string | null;
  try {
    reason = decision();
  } catch (error) {
    reason = `the extension could not decide: ${error instanceof Error ? error.message : String(error)}`;
  }
  if (reason !== null) throw new Error(PREFIX + reason);
}

function target(value: unknown, cwd: string): string {
  return resolveLikePi(
    typeof value === "string" && value ? value : ".",
    cwd,
    homedir(),
  );
}

const sandboxedBash: BashOperations = {
  async exec(command, cwd, { onData, signal, timeout }) {
    const completed = await inSandbox(command, cwd, {
      onData,
      signal,
      timeout,
    });
    return { exitCode: completed.code };
  },
};

function truncated(text: string): string {
  return text.length > MAX_OUTPUT
    ? `${text.slice(0, MAX_OUTPUT)}\n\n[${MAX_OUTPUT / 1024}KB limit reached]`
    : text;
}

export default function (pi: ExtensionAPI) {
  const cwd = process.cwd();
  let turns = 0;
  let cost = 0;
  let stopped: string | null = null;

  const read = createReadToolDefinition(cwd);
  pi.registerTool({
    ...read,
    async execute(id, params, signal, onUpdate, ctx) {
      check(() => readDecision(POLICY, target(params.path, ctx.cwd)));
      return read.execute(id, params, signal, onUpdate, ctx);
    },
  });

  for (const original of [
    createWriteToolDefinition(cwd),
    createEditToolDefinition(cwd),
  ]) {
    pi.registerTool({
      ...original,
      async execute(id, params: { path?: unknown }, signal, onUpdate, ctx) {
        check(() => writeDecision(POLICY, target(params.path, ctx.cwd)));
        return (original.execute as typeof original.execute)(
          id,
          params as never,
          signal,
          onUpdate,
          ctx,
        );
      },
    } as typeof original);
  }

  pi.registerTool(createBashTool(cwd, { operations: sandboxedBash }));

  const find = createFindToolDefinition(cwd, {
    operations: {
      exists: () => true,
      async glob(pattern, root, options) {
        const fullPath = pattern.includes("/");
        const glob =
          fullPath && !pattern.startsWith("/") && !pattern.startsWith("**")
            ? `**/${pattern}`
            : pattern;
        const completed = await inSandbox(
          [
            `cd ${quote(root)} &&`,
            quote(POLICY.programs.fd),
            "--glob --hidden --color=never --no-require-git",
            fullPath ? "--full-path" : "",
            ...options.ignore.map(
              (entry) =>
                `--exclude ${quote(entry.replace(/^\*\*\//, "").replace(/\/\*\*$/, ""))}`,
            ),
            `--max-results ${options.limit}`,
            "--",
            quote(glob),
          ].join(" "),
          POLICY.own[0],
        );
        if (completed.code !== 0 && !completed.stdout) {
          throw new Error(
            completed.stderr.trim() || `fd exited with code ${completed.code}`,
          );
        }
        return completed.stdout.split("\n").filter((line) => line.length > 0);
      },
    },
  });
  pi.registerTool({
    ...find,
    async execute(id, params, signal, onUpdate, ctx) {
      check(() => searchDecision(POLICY, target(params.path, ctx.cwd)));
      return find.execute(id, params, signal, onUpdate, ctx);
    },
  });

  const ls = createLsToolDefinition(cwd, {
    operations: {
      exists: () => true,
      // Entries come from the sandboxed listing, so a host stat reveals nothing new.
      stat: (path) => stat(path),
      async readdir(path) {
        const completed = await inSandbox(
          `ls -1A -- ${quote(path)}`,
          POLICY.own[0],
        );
        if (completed.code !== 0)
          throw new Error(
            completed.stderr.trim() || "the directory cannot be listed",
          );
        return completed.stdout.split("\n").filter((line) => line.length > 0);
      },
    },
  });
  pi.registerTool({
    ...ls,
    async execute(id, params, signal, onUpdate, ctx) {
      check(() => searchDecision(POLICY, target(params.path, ctx.cwd)));
      return ls.execute(id, params, signal, onUpdate, ctx);
    },
  });

  const grep = createGrepToolDefinition(cwd);
  pi.registerTool({
    ...grep,
    async execute(_id, params, signal, _onUpdate, ctx) {
      const root = target(params.path, ctx.cwd);
      check(() => searchDecision(POLICY, root));
      const limit = Math.max(1, params.limit ?? 100);
      const context =
        params.context && params.context > 0 ? Math.floor(params.context) : 0;
      const completed = await inSandbox(
        [
          quote(POLICY.programs.rg),
          "--json --line-number --color=never --hidden",
          params.ignoreCase ? "--ignore-case" : "",
          params.literal ? "--fixed-strings" : "",
          context ? `--context ${context}` : "",
          params.glob ? `--glob ${quote(params.glob)}` : "",
          "--",
          quote(params.pattern),
          quote(root),
        ].join(" "),
        POLICY.own[0],
        { signal },
      );
      if (completed.code !== 0 && completed.code !== 1) {
        throw new Error(
          completed.stderr.trim() ||
            `ripgrep exited with code ${completed.code}`,
        );
      }
      const lines: string[] = [];
      let matches = 0;
      let limited = false;
      for (const line of completed.stdout.split("\n")) {
        if (!line.trim()) continue;
        let event: {
          type?: string;
          data?: {
            path?: { text?: string };
            line_number?: number;
            lines?: { text?: string };
          };
        };
        try {
          event = JSON.parse(line);
        } catch {
          continue;
        }
        if (event.type !== "match" && event.type !== "context") continue;
        if (event.type === "match" && matches >= limit) {
          limited = true;
          break;
        }
        const file = event.data?.path?.text ?? "";
        const shown = relative(root, file) || file;
        const text = (event.data?.lines?.text ?? "").replace(/\r?\n$/, "");
        if (event.type === "match") {
          matches++;
          lines.push(`${shown}:${event.data?.line_number}: ${text}`);
        } else {
          lines.push(`${shown}-${event.data?.line_number}- ${text}`);
        }
      }
      if (matches === 0)
        return {
          content: [{ type: "text", text: "No matches found" }],
          details: undefined,
        };
      let output = truncated(lines.join("\n"));
      if (limited)
        output += `\n\n[${limit} matches limit reached. Use limit=${limit * 2} for more, or refine pattern]`;
      return { content: [{ type: "text", text: output }], details: undefined };
    },
  });

  pi.registerTool({
    name: "concorde_result",
    label: "Concorde result",
    description:
      "End the task with your structured result. Call it exactly once, as your last action; the session ends when it returns.",
    parameters: Type.Unsafe(POLICY.resultSchema),
    async execute(_id, params) {
      return {
        content: [
          { type: "text", text: "Result recorded; the session ends now." },
        ],
        details: params,
        terminate: true,
      };
    },
  });

  function stop(
    limit: string,
    value: number,
    maximum: number,
    ctx: { abort(): void },
  ): void {
    if (stopped) return;
    stopped = limit;
    pi.appendEntry(LIMIT_ENTRY, { limit, value, maximum });
    ctx.abort();
  }

  pi.on("tool_call", async () => {
    if (stopped)
      return {
        block: true,
        reason: `${PREFIX}the run reached its ${stopped} limit`,
      };
    return undefined;
  });

  pi.on("turn_end", async (_event, ctx) => {
    turns++;
    if (turns > POLICY.limits.maxTurns)
      stop("turns", turns, POLICY.limits.maxTurns, ctx);
  });

  pi.on("message_end", async (event, ctx) => {
    const message = (
      event as {
        message?: { role?: string; usage?: { cost?: { total?: number } } };
      }
    ).message;
    if (message?.role !== "assistant") return undefined;
    cost += message.usage?.cost?.total ?? 0;
    const budget = POLICY.limits.maxBudgetUsd;
    if (budget !== null && cost > budget) stop("budget", cost, budget, ctx);
    return undefined;
  });

  pi.on("session_shutdown", async () => {
    if (sandboxStarted) {
      try {
        await SandboxManager.reset();
      } catch {
        // The process ends anyway; a failed reset changes nothing the host relies on.
      }
    }
  });
}
