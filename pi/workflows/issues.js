// Authored bounded Issue decide/verify loop. Only real native children do cognition.
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
const root = __CONCORDE_WORKFLOW__;
function control(text, iteration) {
  if (
    typeof text !== "string" ||
    text.length > 2048 ||
    /[^\x00-\x7f]/.test(text)
  )
    throw new Error("Invalid Issue Host control");
  const value = JSON.parse(text),
    keys = ["groups", "iteration", "route", "schema_version", "ticket"];
  if (
    JSON.stringify(Object.keys(value).sort()) !== JSON.stringify(keys) ||
    JSON.stringify(value, keys) !== text.trim() ||
    value.schema_version !== 1 ||
    value.ticket !== root.ticket ||
    value.iteration !== iteration ||
    !["decide", "verify", "finished"].includes(value.route) ||
    !Array.isArray(value.groups) ||
    value.groups.length !== 4 ||
    value.groups.some((n) => !Number.isSafeInteger(n) || n < 0)
  )
    throw new Error("Foreign or malformed Issue control");
  return value;
}
function host(kind, i) {
  return runs
    .host(kind + "-" + i, {
      kind: "command",
      command: root.commands[kind + "-" + i],
      timeoutMs: 1800000,
    })
    .then((result) => control(result.stdout, i));
}
function leaf(key) {
  return runs.run(key, issueCall(root, key)).then((child) => {
    if (
      !child.ok ||
      child.detached ||
      child.interrupted ||
      child.stopped ||
      child.terminalOutcome ||
      child.results?.length !== 1
    )
      stop("Issue child incomplete", child, key);
    const row = child.results[0],
      gates = row.acceptance?.verifyRuns;
    if (
      row.exitCode !== 0 ||
      row.error ||
      row.metadataSaveError ||
      row.outputSaveError ||
      row.transcriptError ||
      row.acceptance?.status !== "verified" ||
      gates?.length !== 1 ||
      gates[0].status !== "passed"
    )
      stop("Issue child failed staging/completion", child, key);
    const staged = JSON.parse(gates[0].stdout),
      ticket = root.ticket + ":" + key;
    if (
      staged.ticket !== ticket ||
      staged.invocation_id !== ticket ||
      staged.state !== "staged" ||
      staged.accepted !== false
    )
      stop("Foreign Issue proposal", child, key);
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
      ticket: root.ticket,
      key,
      agent: child.agent,
      runId: child.runId,
      invocation_id: ticket,
      proposal_digest: staged.proposal_digest,
      metadata: row.artifactPaths.metadataPath,
      result,
    });
  });
}
for (let iteration = 0; iteration < 6; iteration++) {
  const next = await host("next", iteration);
  if (next.route === "finished") return next;
  if (next.route !== "decide")
    throw new Error("Unexpected Issue preparation route");
  await leaf("d-" + iteration);
  const decision = await host("decision", iteration);
  if (decision.route === "finished") return decision;
  if (decision.route !== "verify")
    throw new Error("Issue decision did not select verification or finish");
  for (let group = 0; group < 4; group++)
    for (let member = 0; member < decision.groups[group]; member++)
      await leaf(`v-${iteration}-${group}-${member}`);
  const verified = await host("verified", iteration);
  if (verified.route === "finished") return verified;
  if (verified.route !== "decide")
    throw new Error("Unexpected Issue verification route");
}
throw new Error("Host failed to enforce the Issue decision bound");
