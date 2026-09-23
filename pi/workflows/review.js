// Authored native review order. No business scope cap; native configured budgets still apply.
function stop(message, child, key) {
  const feedback = failure(message, {
    layer: "workflow",
    attempt: key,
    causes: child ? [nativeFeedback(child, { attempt: key })] : [],
  });
  emit({ kind: "concorde.failure", key, feedback });
  throw new Error(
    message +
      "; full causal feedback: workflow status concorde.failure emission for " +
      key,
  );
}
const request = __CONCORDE_WORKFLOW__;
await runs.host("bind", {
  kind: "command",
  command: request.commands.bind,
  timeoutMs: 1800000,
});
for (let index = 0; index < request.members.length; index++) {
  const member = request.members[index];
  const schema = {
    ...request.schema,
    properties: {
      ...request.schema.properties,
      invocation_id: { const: member.ticket },
    },
  };
  const child = await runs.run("review-" + index, {
    ...member.call,
    outputSchema: schema,
  });
  if (
    !child.ok ||
    child.detached ||
    child.interrupted ||
    child.stopped ||
    child.terminalOutcome ||
    child.results?.length !== 1
  )
    stop("Native reviewer incomplete", child, "review-" + index);
  const row = child.results[0];
  if (
    row.exitCode !== 0 ||
    row.error ||
    row.metadataSaveError ||
    row.outputSaveError ||
    row.transcriptError
  )
    stop("Native reviewer failed or lost evidence", child, "review-" + index);
  const gates = row.acceptance?.verifyRuns;
  if (
    row.acceptance?.status !== "verified" ||
    gates?.length !== 1 ||
    gates[0].status !== "passed"
  )
    stop("Reviewer staging gate rejected", child, "review-" + index);
  const raw = gates[0].stdout;
  if (typeof raw !== "string" || raw.length > 8000)
    stop("Reviewer control unavailable", child, "review-" + index);
  const staged = JSON.parse(raw);
  if (
    staged.ticket !== member.ticket ||
    staged.invocation_id !== member.ticket ||
    staged.state !== "staged" ||
    staged.accepted !== false
  )
    stop("Foreign reviewer staging", child, "review-" + index);
  const result = {};
  for (const field of [
    "agent",
    "exitCode",
    "error",
    "detached",
    "interrupted",
    "stopped",
    "terminalOutcome",
    "timedOut",
    "metadataSaveError",
    "outputSaveError",
    "transcriptError",
    "launchContractDigest",
    "artifactPaths",
    "structuredOutputPath",
  ])
    if (field in row) result[field] = row[field];
  emit({
    kind: "concorde.child-terminal",
    ticket: request.ticket,
    key: "review-" + index,
    agent: child.agent,
    runId: child.runId,
    invocation_id: member.ticket,
    proposal_digest: staged.proposal_digest,
    metadata: row.artifactPaths.metadataPath,
    result,
  });
}
// One aggregate Host commit after every native child; never one runs.host grant per reviewer.
return JSON.parse(
  (
    await runs.host("finalize", {
      kind: "command",
      command: request.commands.finalize,
      timeoutMs: 1800000,
    })
  ).stdout,
);
