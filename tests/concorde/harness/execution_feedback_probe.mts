import assert from "node:assert/strict";
import fs from "node:fs";
import { observeNativeProposal } from "../../../pi/native-proposal.ts";
import { nativeCommand } from "../../../pi/extensions/concorde-native-child.ts";
import {
  errorFeedback,
  failure,
  nativeFeedback,
} from "../../../pi/execution-error.mjs";
import { errorDisplay } from "../../../pi/error-display.mjs";

async function test() {
  const envelope = {
    state: "rejected",
    accepted: false,
    result: {
      invocation_id: "host-attempt",
      errors: [
        {
          code: "stale_context",
          field: "/context",
          message: "exact context changed",
        },
      ],
    },
  };
  const binding = {
    argv: [
      process.execPath,
      "-e",
      `console.log(${JSON.stringify(JSON.stringify(envelope))});process.exit(3)`,
      "--",
    ],
    root: process.cwd(),
    descriptor: "descriptor",
    digest: "ticket",
  };
  let hook: any;
  const handlers = new Map<string, any>();
  const pi: any = {
    on(name: string, handler: any) {
      handlers.set(name, handler);
      hook = handler;
    },
  };
  let invalidations = 0;
  observeNativeProposal(
    pi,
    async (value) => {
      await nativeCommand(binding, "submit", value);
    },
    async () => {
      invalidations++;
      throw Object.assign(new Error("cannot revoke transport"), {
        code: "EPIPE",
      });
    },
  );
  const result = await hook({
    toolName: "structured_output",
    toolCallId: "tool-attempt",
    input: { value: {} },
    isError: false,
  });
  assert.equal(result.isError, true);
  assert.equal(invalidations, 1);
  assert.match(result.content[0].text, /exact context changed/);
  assert.match(result.content[0].text, /stale_context/);
  assert.match(result.content[0].text, /EPIPE/);
  assert.equal(result.details.concorde_failure.attempt, "tool-attempt");

  let submitted = 0;
  const observations: any[] = [];
  observeNativeProposal(
    pi,
    async () => {
      submitted++;
    },
    async () => {
      invalidations++;
    },
    async (f) => {
      observations.push(f);
    },
  );
  const rejected = await hook({
    toolName: "structured_output",
    toolCallId: "schema-call",
    input: {},
    isError: true,
    content: [
      {
        type: "text",
        text: 'Validation failed for tool "structured_output": Required property result is missing',
      },
    ],
  });
  assert.equal(rejected.details.concorde_failure.category, "schema-rejection");
  assert.equal(observations.length, 1);
  assert.equal(invalidations, 1);
  await hook({
    toolName: "structured_output",
    toolCallId: "corrected",
    input: { value: {} },
    isError: false,
  });
  assert.equal(submitted, 1);
  await handlers.get("tool_execution_end")({
    toolName: "structured_output",
    toolCallId: "sdk-immediate",
    isError: true,
    result: {
      content: [
        {
          type: "text",
          text: 'Validation failed for tool "structured_output": missing value\n\nReceived arguments:\n{"password":"private"}',
        },
      ],
    },
  });
  assert.equal(observations[1].category, "schema-rejection");
  assert(!JSON.stringify(observations[1]).includes("private"));

  // Exact independent F1 reproduction: an already-known schema cause must not
  // disappear when observe-error persistence refuses, including repeated delivery.
  const edge = {
    toolName: "structured_output",
    toolCallId: "independent-schema-attempt",
    isError: true,
    result: {
      content: [
        {
          type: "text",
          text: 'Validation failed for tool "structured_output": required answer missing',
        },
      ],
    },
  };
  let retentionCalls = 0;
  observeNativeProposal(
    pi,
    async () => {
      submitted++;
    },
    async () => {
      invalidations++;
    },
    async () => {
      retentionCalls++;
      throw Object.assign(
        new Error("independent observe-error persistence denied"),
        { code: "EACCES" },
      );
    },
  );
  for (let i = 0; i < 2; i++) {
    await assert.rejects(handlers.get("tool_execution_end")(edge), (error) => {
      const f = errorFeedback(error);
      assert.equal(f.attempt, edge.toolCallId);
      assert.equal(f.category, "schema-rejection");
      assert.match(f.diagnostics.text, /required answer missing/);
      assert.equal(f.diagnostics.complete, false);
      assert.equal(f.causes[0].code, "EACCES");
      assert.equal(f.causes[0].category, "observation");
      assert.equal(f.causes[0].attempt, edge.toolCallId);
      assert.match(error.message, /required answer missing/);
      return true;
    });
  }
  assert.equal(retentionCalls, 1);
  const ordinary = await handlers.get("tool_result")({
    ...edge,
    input: {},
    content: edge.result.content,
  });
  assert.equal(ordinary.details.concorde_failure.causes[0].code, "EACCES");
  assert.equal(ordinary.details.concorde_failure.diagnostics.complete, false);
  await handlers.get("tool_result")({
    toolName: "structured_output",
    toolCallId: "after-observation-refusal",
    input: { value: {} },
    isError: false,
  });
  assert.equal(submitted, 2); // Observation failure did not invalidate a correctable slot.
  assert.equal(invalidations, 1);
  observeNativeProposal(
    pi,
    async () => {},
    async () => {},
  );
  await handlers.get("tool_execution_end")(edge); // No observer, no fabricated failure.
  await handlers.get("tool_execution_end")(edge);

  for (const [row, category] of [
    [{ timedOut: true }, "timeout"],
    [{ interrupted: true }, "cancelled"],
    [{ exitCode: 3, error: "process refused" }, "native-exit"],
    [{ metadataSaveError: "permission denied" }, "observation"],
    [{}, "unknown"],
  ] as any[])
    assert.equal(nativeFeedback(row).category, category);
  const cases = [
    ["console.error('specific stderr');process.exit(7)", "native-exit"],
    ["console.log('not-json')", "transport"],
    ["setInterval(()=>{},1000)", "timeout"],
  ];
  for (const [script, category] of cases) {
    try {
      await nativeCommand(
        {
          ...binding,
          argv: [process.execPath, "-e", script, "--"],
          checksTimeoutMs: category === "timeout" ? 20 : 1000,
        },
        "checks",
        {},
      );
      assert.fail("failure became success");
    } catch (error) {
      assert.equal(errorFeedback(error).category, category);
      if (category === "native-exit")
        assert.match(JSON.stringify(errorFeedback(error)), /specific stderr/);
    }
  }
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(
    nativeCommand(
      {
        ...binding,
        argv: [process.execPath, "-e", "setInterval(()=>{},1000)", "--"],
      },
      "checks",
      {},
      controller.signal,
    ),
    (e) => errorFeedback(e).category === "cancelled",
  );
  const quoted = JSON.parse(
    errorDisplay(failure('password="private" ordinary error')),
  );
  assert(!quoted.message.includes("private"));
  assert(errorDisplay(failure("x".repeat(30000))).length < 12000);
  const detail = failure("large cause", {
    diagnostics: "x".repeat(30000) + "password=private",
  });
  const display = JSON.parse(errorDisplay(detail));
  assert.equal(display.diagnostics.complete, false);
  const saved = fs.readFileSync(display.diagnostics.reference, "utf8");
  assert(saved.includes("x".repeat(30000)));
  assert(!saved.includes("private"));
  assert.equal(fs.statSync(display.diagnostics.reference).mode & 0o777, 0o600);
  console.log(
    "execution feedback: proposal/Host/SDK/transport/exit/timeout/cancel/display assertions passed",
  );
}
await test();
