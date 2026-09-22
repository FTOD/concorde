/** Selected causal facts only: no environment, proposal values, prompts or transcripts. */
export function safeText(value) {
  return String(value)
    .replace(
      /\n\nReceived arguments:[\s\S]*$/,
      "\n[Argument values omitted from causal diagnostics]",
    )
    .replace(
      /\n\nOutput:\n[\s\S]*?(?=\n\nOutput artifact:|$)/,
      "\n[Model output omitted from causal diagnostics]",
    )
    .replace(/(bearer\s+)[^\s"',;]+/gi, "$1[REDACTED]")
    .replace(
      /((?:api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret|authorization)\s*["']?\s*[:=]\s*["']?)[^\s"',;}]+/gi,
      "$1[REDACTED]",
    );
}

export function failure(
  message,
  {
    code = "execution_failed",
    layer = "pi",
    category = "unknown",
    attempt = null,
    causes = [],
    references = [],
    diagnostics = null,
    complete = true,
  } = {},
) {
  return {
    schema_version: 1,
    code,
    message: safeText(message),
    layer,
    category,
    attempt,
    causes,
    diagnostics: {
      complete:
        complete &&
        causes.every((cause) => cause.diagnostics?.complete === true),
      redacted: true,
      text: diagnostics === null ? null : safeText(diagnostics),
      references,
    },
  };
}

export function errorFeedback(error, options = {}, seen = new Set()) {
  if (error?.feedback?.schema_version === 1) return error.feedback;
  if (seen.has(error))
    return failure("Cyclic cause; further cause unavailable", options);
  seen.add(error);
  const entries =
    error?.response?.result?.errors ?? error?.result?.errors ?? error?.errors;
  return failure(
    error?.message ??
      (typeof error === "string"
        ? error
        : entries
          ? "Host reported failure"
          : "Unknown lower-level failure"),
    {
      ...options,
      code: error?.code ?? options.code ?? "execution_failed",
      causes: Array.isArray(entries)
        ? entries.map(
            (row) =>
              row.feedback ??
              failure(row.message, {
                code: row.code,
                layer: "host",
                category: "host-refusal",
                attempt: error?.response?.result?.invocation_id ?? null,
              }),
          )
        : error?.cause
          ? [errorFeedback(error.cause, options, seen)]
          : [],
    },
  );
}

export function nativeFeedback(value, options = {}) {
  value = value ?? {};
  const category = value.timedOut
    ? "timeout"
    : value.stopped || value.interrupted || value.state === "stopped"
      ? "cancelled"
      : value.exitCode != null && value.exitCode !== 0
        ? "native-exit"
        : value.metadataSaveError ||
            value.outputSaveError ||
            value.transcriptError
          ? "observation"
          : "unknown";
  const causes = [];
  for (const key of [
    "error",
    "metadataSaveError",
    "outputSaveError",
    "transcriptError",
  ])
    if (value[key])
      causes.push(
        failure(value[key], {
          code: key,
          layer: "native",
          category: key === "error" ? category : "observation",
          attempt: value.runId ?? options.attempt ?? null,
          complete: false,
        }),
      );
  for (const row of value.results ?? [])
    causes.push(
      nativeFeedback(row, { attempt: value.runId ?? options.attempt }),
    );
  const facts = {};
  for (const key of [
    "exitCode",
    "processSignal",
    "timedOut",
    "stopped",
    "interrupted",
    "detached",
    "terminalOutcome",
    "state",
    "status",
  ])
    if (key in value) facts[key] = value[key];
  const references = Object.values(value.artifactPaths ?? {}).filter(
    (v) => typeof v === "string",
  );
  if (value.structuredOutputPath) references.push(value.structuredOutputPath);
  // Native verification stdout is a producer-bounded preview, never claim completeness.
  for (const gate of value.acceptance?.verifyRuns ?? [])
    if (gate.status !== "passed" || gate.exitCode !== 0)
      causes.push(
        failure("Native staging gate " + gate.status, {
          layer: "native-gate",
          category: "host-refusal",
          code: gate.exitCode ?? "gate_failed",
          diagnostics: JSON.stringify({
            stdout: gate.stdout,
            stderr: gate.stderr,
            error: gate.structuredOutputError,
          }),
          complete: false,
          references,
        }),
      );
  return failure("Native execution did not complete successfully", {
    ...options,
    layer: "native",
    category,
    causes,
    references,
    diagnostics: JSON.stringify(facts),
  });
}

export function executionError(feedback, cause) {
  return Object.assign(new Error(JSON.stringify(feedback), { cause }), {
    feedback,
  });
}
