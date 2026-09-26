/**
 * The boundary extension of a pi task session.
 *
 * Tasks copies this file into `.concorde/tasks/<task>.session/boundary.ts`, embeds the session's
 * policy in `POLICY` and the sandbox-runtime entry point in the import below, and the supervisor
 * loads it with `-e` on top of the developer's own pi configuration. It intercepts tool calls
 * rather than replacing tools, so the developer's extensions keep theirs: a `write` or `edit`
 * outside the task worktree and its decision log is blocked with the reason, and every `bash`
 * command is rewritten to run inside sandbox-runtime, writing only the session's writable paths,
 * with every network host allowed. `concorde_report` ends the round with the session report.
 */

import { homedir } from "node:os";
import { SandboxManager } from "@concorde/sandbox-runtime";
import { Type } from "typebox";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { resolveLikePi } from "./pi_policy.ts";
import {
  reportProblem,
  type SessionPolicy,
  sessionWriteDecision,
} from "./pi_session_policy.ts";

const POLICY: SessionPolicy = {} as SessionPolicy;

const PREFIX = "Concorde task session: ";

let sandboxReady: Promise<void> | undefined;
let sandboxStarted = false;

function filesystem() {
  return {
    denyRead: [],
    allowRead: [],
    allowWrite: POLICY.sandbox.allowWrite,
    denyWrite: [],
  };
}

function sandbox(): Promise<void> {
  sandboxReady ??= (async () => {
    await SandboxManager.initialize({
      network: { allowedDomains: ["*"], deniedDomains: [] },
      filesystem: filesystem(),
    } as never);
    sandboxStarted = true;
  })();
  return sandboxReady;
}

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName === "write" || event.toolName === "edit") {
      const input = event.input as { path?: unknown };
      let reason: string | null;
      try {
        const path = resolveLikePi(
          typeof input.path === "string" && input.path ? input.path : ".",
          ctx.cwd,
          homedir(),
        );
        reason = sessionWriteDecision(POLICY, path);
      } catch (error) {
        reason = `the boundary could not decide: ${error instanceof Error ? error.message : String(error)}`;
      }
      if (reason !== null) return { block: true, reason: PREFIX + reason };
    } else if (event.toolName === "bash") {
      const input = event.input as { command?: unknown };
      if (typeof input.command !== "string") return undefined;
      await sandbox();
      input.command = await SandboxManager.wrapWithSandbox(
        input.command,
        undefined,
        { filesystem: filesystem() } as never,
      );
    }
    return undefined;
  });

  pi.registerTool({
    name: "concorde_report",
    label: "Concorde report",
    description:
      "End this round of the task session with your report to the main agent: delivered with " +
      "the delivery commit, or escalated with the numbers of the escalations you recorded. Call " +
      "it exactly once, as your last action; the round ends when it returns.",
    parameters: Type.Unsafe(POLICY.reportSchema),
    async execute(_id, params) {
      const problem = reportProblem(params as Record<string, unknown>);
      if (problem !== null)
        throw new Error(`${PREFIX}the report is incomplete: ${problem}`);
      return {
        content: [
          { type: "text", text: "Report recorded; this round ends now." },
        ],
        details: params,
        terminate: true,
      };
    },
  });

  pi.on("session_shutdown", async () => {
    if (sandboxStarted) {
      try {
        await SandboxManager.reset();
      } catch {
        // The process ends anyway; a failed reset changes nothing the supervisor relies on.
      }
    }
  });
}
