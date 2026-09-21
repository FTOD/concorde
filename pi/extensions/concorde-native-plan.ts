/** Register one invocation-bound authored native plan resource; no model execution here. */
import fs from "node:fs";
import { issueCall, issueLayout } from "../issue-call.mjs";
import path from "node:path";
import { createRequire } from "node:module";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { nativeCommand } from "./concorde-native-child.ts";
const quote = (value: string) => "'" + value.replaceAll("'", "'\\''") + "'";
export async function nativePlan(
  pi: ExtensionAPI,
  prepared: any,
  ctx: any,
  verify: () => void,
) {
  const descriptor = JSON.parse(fs.readFileSync(prepared.descriptor, "utf8"));
  const root = descriptor.runtime.package_root;
  const require = createRequire(path.join(root, "package.json"));
  const { registerWorkflowResource } = await import(
    require.resolve("pi-subagents/workflow-resources")
  );
  const review = prepared.workflow_kind === "review";
  const issue = prepared.workflow_kind === "issue";
  const helper = path.join(
    descriptor.package_root,
    issue
      ? "pi/native-issue-host.mjs"
      : review
        ? "pi/native-review-host.mjs"
        : "pi/native-plan-host.mjs",
  );
  const commands: any = {};
  for (const action of issue
    ? Array.from({ length: 6 }, (_, i) => [
        "next-" + i,
        "decision-" + i,
        "verified-" + i,
      ]).flat()
    : review
      ? ["bind", "finalize"]
      : ["bind", "advance", "finalize"])
    commands[action] = [
      process.execPath,
      helper,
      action,
      prepared.descriptor,
      prepared.digest,
    ]
      .map(quote)
      .join(" ");
  let expansion: any = {
    ticket: prepared.ticket,
    assessor: prepared.call,
    ...commands,
  };
  if (review) {
    const scope = JSON.parse(
      fs.readFileSync(
        path.join(descriptor.directory, "review-scope.json"),
        "utf8",
      ),
    );
    expansion = {
      ticket: prepared.ticket,
      ...commands,
      schema: scope.slots[0].call.outputSchema,
      members: scope.slots.map((slot: any) => {
        const { outputSchema, ...call } = slot.call;
        return { ticket: slot.ticket, call };
      }),
    };
  }
  if (issue)
    expansion = {
      ...issueLayout(descriptor, prepared.descriptor, prepared.digest),
      commands,
    };
  const script = fs
    .readFileSync(
      path.join(
        descriptor.package_root,
        issue
          ? "pi/workflows/issues.js"
          : review
            ? "pi/workflows/review.js"
            : "pi/workflows/plan.js",
      ),
      "utf8",
    )
    .replace(
      issue
        ? "__CONCORDE_ISSUE__"
        : review
          ? "__CONCORDE_REVIEW__"
          : "__CONCORDE_PLAN__",
      JSON.stringify(expansion),
    )
    .replace("__ISSUE_CALL__", "(" + issueCall.toString() + ")");
  const name =
    (issue
      ? "concorde.issue."
      : review
        ? "concorde.review."
        : "concorde.plan.") + prepared.ticket;
  const registration = registerWorkflowResource({
    sessionId: ctx.sessionManager.getSessionId(),
    definition: {
      name,
      version: 1,
      resolve(args: any) {
        if (Object.keys(args).length !== 1 || args.ticket !== prepared.ticket)
          return { error: "Use the exact issued planning ticket" };
        return {
          script,
          hostCommands: Object.entries(commands).map(([key, command]) => ({
            key,
            command,
          })),
        };
      },
    },
  });
  const call = {
    workflow: name,
    args: { ticket: prepared.ticket },
    cwd: descriptor.project_root,
    async: true,
    mission: false,
    context: "fresh",
    intercomBridge: { mode: "off" },
  };
  let tool: string | undefined,
    runId: string | undefined,
    terminal = false,
    launched = false;
  const canonical = (value: any): string =>
    Array.isArray(value)
      ? "[" + value.map(canonical).join(",") + "]"
      : value && typeof value === "object"
        ? "{" +
          Object.keys(value)
            .sort()
            .map((key) => JSON.stringify(key) + ":" + canonical(value[key]))
            .join(",") +
          "}"
        : JSON.stringify(value);
  return {
    operation: descriptor.operation,
    prepared: {
      ...prepared,
      call,
      definition: undefined,
      instruction:
        "Invoke this exact named native workflow, then concorde action result to inspect Host acceptance separately from workflow execution.",
    },
    matches(event: any) {
      return (
        event.toolName === "subagent" &&
        (event.input.workflow === name || event.toolCallId === tool)
      );
    },
    async before(event: any) {
      verify();
      if (tool || canonical(event.input) !== canonical(call))
        return {
          block: true,
          reason: "Native plan call is single-use and cannot be overridden",
        };
      tool = event.toolCallId;
    },
    async after(event: any): Promise<any> {
      if (event.toolCallId !== tool || launched) return;
      const details = event.details;
      if (
        event.isError ||
        !details?.asyncDir ||
        !(details.runId ?? details.asyncId)
      )
        throw new Error("Native planning launch returned no binding");
      fs.writeFileSync(
        path.join(descriptor.directory, "workflow-binding.tmp"),
        JSON.stringify({
          asyncDir: details.asyncDir,
          runId: details.runId ?? details.asyncId,
        }),
        { flag: "wx" },
      );
      fs.renameSync(
        path.join(descriptor.directory, "workflow-binding.tmp"),
        path.join(descriptor.directory, "workflow-binding.json"),
      );
      runId = details.runId ?? details.asyncId;
      launched = true;
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              state: "running",
              accepted: false,
              native: details,
              instruction:
                "Use the matching concorde operation action result; this launch receipt is not acceptance.",
            }),
          },
        ],
        details: {
          ...details,
          concorde_native: { state: "running", accepted: false },
        },
      };
    },
    async result() {
      verify();
      if (!launched) return { state: "not-run", accepted: false };
      const result = await nativeCommand(
        prepared.binding,
        "workflow-result",
        {},
      );
      if (result.native_state !== "running") {
        terminal = true;
        registration.dispose();
      }
      return result;
    },
    async dispose() {
      registration.dispose();
      if (launched && !terminal) {
        try {
          await nativeCommand(prepared.binding, "workflow-stop", {});
        } catch {}
        pi.events.emit("subagents:rpc:v1:request", {
          version: 1,
          requestId: crypto.randomUUID(),
          method: "stop",
          params: { id: runId },
        });
      } else if (!launched) {
        try {
          await nativeCommand(prepared.binding, "invalidate", {});
        } catch {}
      }
    },
  };
}
