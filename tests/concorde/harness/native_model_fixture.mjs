/** Script only model task events; execute the actual native structured-output tool. */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

export function modelFixture({
  onCreate = () => {},
  interrupt = () => {},
} = {}) {
  return {
    async create(launch) {
      onCreate();
      const tools = new Map();
      const hookApi = {
        on() {},
        registerTool(tool) {
          tools.set(tool.name, tool);
        },
        events: {
          on() {
            return () => {};
          },
          emit() {},
        },
        getAllTools() {
          return [...tools.values()];
        },
        getActiveTools() {
          return [...tools.keys()];
        },
      };
      for (const hook of launch.hooks) hook.factory(hookApi);
      const output = tools.get("structured_output");
      assert(output, "native structured_output tool was not registered");
      assert.deepEqual(
        output.parameters.required,
        ["value"],
        "unexpected second model-authored acceptance report requirement",
      );
      const require = createRequire(
        path.join(process.env.CONCORDE_NATIVE_FIXTURE_SDK, "package.json"),
      );
      const { createJiti } = require("jiti");
      const jiti = createJiti(import.meta.url, { interopDefault: true });
      const { observeNativeProposal } = await jiti.import(
        path.join(
          process.env.CONCORDE_NATIVE_FIXTURE_CANDIDATE,
          "pi/native-proposal.ts",
        ),
      );
      const proposalHandlers = [];
      let index;
      observeNativeProposal(
        {
          on(name, handler) {
            assert.equal(name, "tool_result");
            proposalHandlers.push(handler);
          },
        },
        async (value) => {
          fs.writeFileSync(
            path.join(
              process.env.CONCORDE_NATIVE_FIXTURE_ROOT,
              `raw-proposal-${index}.json`,
            ),
            JSON.stringify(value),
          );
        },
        async (reason) => {
          fs.writeFileSync(
            path.join(
              process.env.CONCORDE_NATIVE_FIXTURE_ROOT,
              `invalid-proposal-${index}`,
            ),
            reason,
          );
        },
      );
      if (launch.processEnv) {
        const bindings = JSON.parse(
          launch.processEnv.PI_SUBAGENT_EXTENSION_BINDINGS ?? "null",
        );
        assert.equal(bindings?.["concorde-fixture/1"]?.token, "fixture-token");
      }
      const listeners = new Set();
      const messages = [];
      const emit = (event) => {
        for (const listener of listeners) listener(event);
      };
      return {
        messages,
        sessionId: "fixture-child-session",
        sessionFile:
          launch.storage.kind === "file"
            ? launch.storage.sessionFile
            : undefined,
        modelId: "fixture/model",
        subscribe(listener) {
          listeners.add(listener);
          return () => listeners.delete(listener);
        },
        async prompt(task) {
          const scenario = process.env.CONCORDE_NATIVE_FIXTURE_SCENARIO;
          index = Number(task.match(/Fixture (\d+)/)?.[1]);
          assert(Number.isSafeInteger(index));
          fs.appendFileSync(
            process.env.CONCORDE_NATIVE_FIXTURE_CALLS,
            "model-seam\n",
          );
          if (scenario === "interrupted-child") interrupt();
          const value = {
            invocation_id: `invocation-${index}`,
            verdict: scenario === "business-invalid" ? "invalid" : "valid",
          };
          const args = { value };
          const message = {
            role: "assistant",
            content: [
              {
                type: "toolCall",
                id: "structured-1",
                name: "structured_output",
                arguments: args,
              },
            ],
            api: "fixture",
            provider: "fixture",
            model: "model",
            stopReason: "toolUse",
            timestamp: Date.now(),
            usage: {
              input: 1,
              output: 1,
              cacheRead: 0,
              cacheWrite: 0,
              totalTokens: 2,
              cost: {
                input: 0,
                output: 0,
                cacheRead: 0,
                cacheWrite: 0,
                total: 0,
              },
            },
          };
          if (scenario === "duplicate-output")
            message.content.push({
              type: "toolCall",
              id: "structured-2",
              name: "structured_output",
              arguments: { value: { ...value, verdict: "invalid" } },
            });
          messages.push(message);
          emit({ type: "agent_start" });
          emit({ type: "message_end", message });
          emit({
            type: "tool_execution_start",
            toolCallId: "structured-1",
            toolName: "structured_output",
            args,
          });
          const result = await output.execute("structured-1", args);
          assert.equal(result.terminate, true);
          const event = {
            toolName: "structured_output",
            input: args,
            content: result.content,
            details: result.details,
            isError: false,
          };
          for (const handler of proposalHandlers)
            Object.assign(event, await handler(event));
          assert.equal(event.isError, false, "Host proposal capture failed");
          if (scenario === "duplicate-output") {
            const duplicateArgs = { value: { ...value, verdict: "invalid" } };
            emit({
              type: "tool_execution_start",
              toolCallId: "structured-2",
              toolName: "structured_output",
              args: duplicateArgs,
            });
            const duplicateResult = await output.execute(
              "structured-2",
              duplicateArgs,
            );
            const duplicate = { ...event, input: duplicateArgs };
            for (const handler of proposalHandlers)
              Object.assign(duplicate, await handler(duplicate));
            assert.equal(duplicate.isError, true);
            emit({
              type: "tool_execution_end",
              toolCallId: "structured-2",
              toolName: "structured_output",
              result: duplicateResult,
              isError: true,
            });
          }

          messages.push({
            role: "toolResult",
            toolCallId: "structured-1",
            toolName: "structured_output",
            ...result,
            isError: false,
            timestamp: Date.now(),
          });
          emit({
            type: "tool_execution_end",
            toolCallId: "structured-1",
            toolName: "structured_output",
            result,
            isError: false,
          });
          emit({ type: "agent_end", messages });
          if (scenario === "failed-child")
            throw new Error(
              "fixture model execution failed after structured submission",
            );
          emit({ type: "agent_settled" });
        },
        async abort() {},
        async dispose() {},
        async steer() {},
        async followUp() {},
      };
    },
    async dispose() {},
  };
}
export default () => modelFixture();
