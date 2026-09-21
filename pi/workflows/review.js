// Authored native review order. No business scope cap; native configured budgets still apply.
const request = __CONCORDE_REVIEW__;
await runs.host("bind", {
  kind: "command",
  command: request.bind,
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
    throw new Error("Native reviewer incomplete");
  const row = child.results[0];
  if (
    row.exitCode !== 0 ||
    row.error ||
    row.metadataSaveError ||
    row.outputSaveError ||
    row.transcriptError
  )
    throw new Error("Native reviewer failed or lost evidence");
  const gates = row.acceptance?.verifyRuns;
  if (
    row.acceptance?.status !== "verified" ||
    gates?.length !== 1 ||
    gates[0].status !== "passed"
  )
    throw new Error("Reviewer staging gate rejected");
  const raw = gates[0].stdout;
  if (typeof raw !== "string" || raw.length > 8000)
    throw new Error("Reviewer control unavailable");
  const staged = JSON.parse(raw);
  if (
    staged.ticket !== member.ticket ||
    staged.invocation_id !== member.ticket ||
    staged.state !== "staged" ||
    staged.accepted !== false
  )
    throw new Error("Foreign reviewer staging");
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
      command: request.finalize,
      timeoutMs: 1800000,
    })
  ).stdout,
);
