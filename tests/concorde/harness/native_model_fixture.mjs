/** Only the model-execution seam is scripted; native launch/publication is real. */
import assert from "node:assert/strict";
import fs from "node:fs";

export default {
  async create(launch) {
    const bindings = JSON.parse(
      launch.processEnv?.PI_SUBAGENT_EXTENSION_BINDINGS ?? "null",
    );
    assert.equal(bindings?.["concorde-fixture/1"]?.token, "fixture-token");
    const listeners = new Set();
    const messages = [];
    const emit = (event) => {
      for (const listener of listeners) listener(event);
    };
    return {
      messages,
      sessionId: "fixture-child-session",
      sessionFile:
        launch.storage.kind === "file" ? launch.storage.sessionFile : undefined,
      modelId: "fixture/model",
      subscribe(listener) {
        listeners.add(listener);
        return () => listeners.delete(listener);
      },
      async prompt() {
        fs.appendFileSync(
          process.env.CONCORDE_NATIVE_FIXTURE_CALLS,
          "model-seam\n",
        );
        const message = {
          role: "assistant",
          content: [{ type: "text", text: "Fixture proposal." }],
          api: "fixture",
          provider: "fixture",
          model: "model",
          stopReason: "stop",
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
        messages.push(message);
        emit({ type: "agent_start" });
        emit({ type: "message_end", message });
        emit({ type: "agent_end", messages });
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
