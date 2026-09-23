/** The generic workflow registrar: registers one prepared Workflow exactly as its plan says.
 *
 * Which script runs, which helpers it inlines, which Host-step commands exist and what they print
 * all come from the prepared workflow plan; the registrar knows no provider. */
import { errorFeedback, failure, nativeFeedback } from "../execution-error.mjs";
import { errorDisplay } from "../error-display.mjs";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { nativeCommand } from "./concorde-native-child.ts";
const quote = (value: string) => "'" + value.replaceAll("'", "'\\''") + "'";
const PLACEHOLDER = "__CONCORDE_WORKFLOW__";
const unexported = (text: string) => text.replace(/^export /gm, "");
export async function nativePlan(
  pi: ExtensionAPI,
  prepared: any,
  ctx: any,
  verify: () => void,
) {
  const descriptor = JSON.parse(fs.readFileSync(prepared.descriptor, "utf8"));
  const plan = prepared.workflow;
  const packageRoot = descriptor.package_root;
  const require = createRequire(
    path.join(descriptor.runtime.package_root, "package.json"),
  );
  const { registerWorkflowResource } = await import(
    require.resolve("pi-subagents/workflow-resources")
  );
  const read = (relative: string) =>
    fs.readFileSync(path.join(packageRoot, relative), "utf8");
  const commands: Record<string, string> = Object.fromEntries(
    Object.entries(plan.commands).map(([step, argv]) => [
      step,
      (argv as string[]).map(quote).join(" "),
    ]),
  );
  const body = read(plan.script);
  if (body.split(PLACEHOLDER).length !== 2)
    throw new Error("A workflow script has exactly one " + PLACEHOLDER);
  const script = [
    unexported(read("pi/execution-error.mjs")),
    ...plan.helpers.map((helper: string) => unexported(read(helper))),
    body.replace(PLACEHOLDER, JSON.stringify(plan.expansion)),
  ].join("\n");
  const name = plan.name;
  const registration = registerWorkflowResource({
    sessionId: ctx.sessionManager.getSessionId(),
    definition: {
      name,
      version: 1,
      resolve(args: any) {
        if (Object.keys(args).length !== 1 || args.ticket !== prepared.ticket)
          return { error: "Use the exact issued workflow ticket" };
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
  let launchFailure: any;
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
          reason:
            "The prepared workflow call is single-use and cannot be overridden",
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
      ) {
        launchFailure = failure("Native workflow launch returned no binding", {
          layer: "workflow-launch",
          attempt: prepared.ticket,
          causes: [nativeFeedback(details)],
          diagnostics: event.content
            ?.filter((p: any) => p.type === "text")
            .map((p: any) => p.text)
            .join("\n"),
        });
        return {
          isError: true,
          content: [{ type: "text", text: errorDisplay(launchFailure) }],
          details: {
            ...details,
            concorde_native: {
              state: "failed",
              accepted: false,
              failure: launchFailure,
            },
          },
        };
      }
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
      if (!launched)
        return launchFailure
          ? { state: "failed", accepted: false, failure: launchFailure }
          : { state: "not-run", accepted: false };
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
        } catch (error) {
          pi.appendEntry(
            "concorde.execution-failure",
            errorFeedback(error, {
              layer: "workflow-stop",
              attempt: prepared.ticket,
            }),
          );
        }
        pi.events.emit("subagents:rpc:v1:request", {
          version: 1,
          requestId: crypto.randomUUID(),
          method: "stop",
          params: { id: runId },
        });
      } else if (!launched) {
        try {
          await nativeCommand(prepared.binding, "invalidate", {});
        } catch (error) {
          pi.appendEntry(
            "concorde.execution-failure",
            errorFeedback(error, {
              layer: "workflow-invalidation",
              attempt: prepared.ticket,
            }),
          );
        }
      }
    },
  };
}
