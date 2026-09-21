// Authored native control flow. Substituted only with Host-issued JSON/constants.
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
const request = __CONCORDE_PLAN__;
function control(text) {
  if (typeof text !== "string" || text.length > 30000)
    throw new Error("Invalid Host planning control");
  return JSON.parse(text);
}
function childEvidence(child, key, ticket) {
  if (
    !child.ok ||
    child.detached ||
    child.interrupted ||
    child.stopped ||
    child.terminalOutcome ||
    child.results?.length !== 1
  )
    stop("Native planning child did not complete", child, key);
  const row = child.results[0];
  if (
    row.exitCode !== 0 ||
    row.error ||
    row.metadataSaveError ||
    row.outputSaveError ||
    row.transcriptError
  )
    stop("Native planning child failed or lost evidence", child, key);
  const acceptance = row.acceptance;
  if (
    acceptance?.status !== "verified" ||
    acceptance.verifyRuns?.length !== 1 ||
    acceptance.verifyRuns[0].status !== "passed"
  )
    stop("Planning staging gate failed", child, key);
  const staged = control(acceptance.verifyRuns[0].stdout);
  if (
    staged.schema_version !== 1 ||
    staged.ticket !== ticket ||
    staged.invocation_id !== ticket ||
    staged.state !== "staged" ||
    staged.accepted !== false
  )
    stop("Foreign planning stage", child, key);
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
    key,
    agent: child.agent,
    runId: child.runId,
    invocation_id: ticket,
    proposal_digest: staged.proposal_digest,
    metadata: row.artifactPaths.metadataPath,
    result,
  });
}
await runs.host("bind", {
  kind: "command",
  command: request.bind,
  timeoutMs: 30000,
});
const assessment = await runs.run("assessor", request.assessor);
childEvidence(assessment, "assessor", request.ticket);
// Native child completion and independent Host acceptance precede dependency advance.
const advance = control(
  (
    await runs.host("advance", {
      kind: "command",
      command: request.advance,
      timeoutMs: 60000,
    })
  ).stdout,
);
if (advance.state !== "prepared") return advance;
const planning = await runs.run("planner", advance.call);
childEvidence(planning, "planner", advance.ticket);
return control(
  (
    await runs.host("finalize", {
      kind: "command",
      command: request.finalize,
      timeoutMs: 60000,
    })
  ).stdout,
);
