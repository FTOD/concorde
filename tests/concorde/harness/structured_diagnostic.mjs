/** Selected structured-tool evidence only: no auth/env/provider registries or unrelated reads. */
import crypto from "node:crypto";
import { gzipSync, gunzipSync } from "node:zlib";

const hash = (bytes) =>
  "sha256:" + crypto.createHash("sha256").update(bytes).digest("hex");
const secretKey =
  /^(?:api[_-]?key|authorization|password|access[_-]?token|refresh[_-]?token|auth|credentials|env|processEnv|providerRegistry)$/i;
export function sanitize(value) {
  if (typeof value === "string")
    return value
      .replace(/Bearer\s+[^\s"']+/gi, "Bearer [redacted]")
      .replace(
        /((?:api[_-]?key|authorization|password|access[_-]?token|refresh[_-]?token)\s*[:=]\s*)[^\s,"'}]+/gi,
        "$1[redacted]",
      );
  if (Array.isArray(value)) return value.map(sanitize);
  if (value && typeof value === "object")
    return Object.fromEntries(
      Object.entries(value).map(([key, v]) => [
        key,
        secretKey.test(key) ? "[redacted]" : sanitize(v),
      ]),
    );
  return value;
}
export function structuredAttempts(text, runId) {
  const attempts = new Map();
  let transcriptTruncated = false,
    malformedRecords = 0,
    unrelatedToolStarts = 0;
  const terminal = { stopReason: null, errorMessage: null, model: null };
  const attempt = (id) => {
    if (!id) {
      malformedRecords++;
      return null;
    }
    if (!attempts.has(id))
      attempts.set(id, {
        callId: id,
        arguments: null,
        argumentSources: [],
        startObserved: false,
        endObserved: false,
        isError: null,
        resultRecords: [],
        argumentsTruncated: false,
        resultTruncated: false,
      });
    return attempts.get(id);
  };
  const args = (row, value, source) => {
    if (!row) return;
    row.argumentSources.push({
      source,
      present: value !== undefined,
      value: sanitize(value),
    });
    // Full assistant tool-call arguments are preferred to the bounded argsPayload preview.
    if (row.arguments === null || source === "assistant.toolCall")
      row.arguments = sanitize(value);
  };
  for (const line of text.split("\n").filter(Boolean)) {
    let r;
    try {
      r = JSON.parse(line);
    } catch {
      malformedRecords++;
      continue;
    }
    if (!r || typeof r !== "object" || Array.isArray(r)) {
      malformedRecords++;
      continue;
    }
    if (r.runId && r.runId !== runId)
      throw new Error("foreign child transcript");
    if (r.recordType === "truncated") {
      transcriptTruncated = true;
      continue;
    }
    const m = r.message;
    if (r.recordType === "message" && r.role === "assistant") {
      terminal.stopReason =
        r.stopReason ?? m?.stopReason ?? terminal.stopReason;
      terminal.errorMessage = sanitize(
        r.errorMessage ?? m?.errorMessage ?? null,
      );
      if (m?.provider || r.model)
        terminal.model = {
          provider: m?.provider ?? null,
          id: r.model ?? m?.model ?? null,
        };
      for (const c of m?.content ?? [])
        if (c.type === "toolCall" && c.name === "structured_output")
          args(attempt(c.id), c.arguments, "assistant.toolCall");
    }
    if (r.recordType === "tool_start") {
      if (r.toolName !== "structured_output") {
        unrelatedToolStarts++;
        continue;
      }
      const a = attempt(r.toolCallId);
      if (!a) continue;
      a.startObserved = true;
      if (r.argsPayload !== undefined) {
        try {
          args(a, JSON.parse(r.argsPayload), "tool_start.argsPayload");
        } catch {
          a.argumentsTruncated = true;
        }
      }
    }
    if (r.recordType === "tool_end" && r.toolName === "structured_output") {
      const a = attempt(r.toolCallId);
      if (!a) continue;
      a.endObserved = true;
      if (typeof r.isError === "boolean") a.isError = r.isError;
      // Some producer versions include a result here; current v1 transcript uses toolResult messages.
      if (r.result)
        a.resultRecords.push({
          source: "tool_end.result",
          isError: r.isError ?? null,
          text: sanitize(
            (r.result.content ?? [])
              .filter((x) => x.type === "text")
              .map((x) => x.text)
              .join("\n"),
          ),
        });
    }
    if (
      r.recordType === "message" &&
      r.role === "toolResult" &&
      (r.toolName ?? m?.toolName) === "structured_output"
    ) {
      const a = attempt(r.toolCallId ?? m?.toolCallId);
      if (!a) continue;
      const isError = r.isError ?? m?.isError ?? null;
      if (typeof isError === "boolean") a.isError = isError;
      const content =
        r.text ??
        (m?.content ?? [])
          .filter((x) => x.type === "text")
          .map((x) => x.text)
          .join("\n");
      a.resultRecords.push({
        source: "message.toolResult",
        isError,
        text: sanitize(content),
      });
      a.resultTruncated ||=
        r.outputTruncated === true || content.includes("… payload truncated");
    }
  }
  return {
    terminal,
    transcriptTruncated,
    malformedRecords,
    unrelatedToolStarts,
    attempts: [...attempts.values()].map((a) => ({
      ...a,
      status:
        a.isError === true
          ? "rejected"
          : a.isError === false
            ? "tool-succeeded"
            : "unknown",
      argumentsComplete: a.argumentSources.some(
        (s) =>
          s.present &&
          (s.source === "assistant.toolCall" || !a.argumentsTruncated),
      ),
      errorComplete:
        a.isError === true
          ? a.resultRecords.some(
              (r) => r.isError === true && r.text.length > 0,
            ) && !a.resultTruncated
          : null,
    })),
  };
}
export function selectedDiagnostic({
  workflowRunId,
  key,
  ticket,
  schema,
  metadata,
  expected = null,
  transcript,
}) {
  const parsed =
    transcript === null
      ? {
          terminal: null,
          transcriptTruncated: null,
          malformedRecords: 0,
          unrelatedToolStarts: null,
          attempts: [],
        }
      : structuredAttempts(transcript, metadata?.runId);
  return sanitize({
    schema_version: 1,
    workflowRunId,
    key,
    ticket,
    issuedSchema: schema,
    issuedSchemaDigest: hash(JSON.stringify(schema)),
    expected,
    native: {
      runId: metadata?.runId ?? null,
      agent: metadata?.agent ?? null,
      exitCode: metadata?.exitCode ?? null,
      error: metadata?.error ?? null,
      launchContractDigest: metadata?.launchContractDigest ?? null,
      gateStatus: metadata?.acceptance?.status ?? null,
    },
    sourceRecords: transcript === null ? "absent" : "present",
    effectiveStart: "unknown",
    ...parsed,
  });
}
export function packDiagnostic(diagnostic) {
  const fields = new Set([
    "schema_version",
    "workflowRunId",
    "key",
    "ticket",
    "issuedSchema",
    "issuedSchemaDigest",
    "expected",
    "native",
    "sourceRecords",
    "effectiveStart",
    "terminal",
    "transcriptTruncated",
    "malformedRecords",
    "unrelatedToolStarts",
    "attempts",
  ]);
  if (Object.keys(diagnostic).some((k) => !fields.has(k)))
    throw new Error(
      "only selected structured-tool diagnostic fields may be exported",
    );
  const full = sanitize(diagnostic);
  const encode = (data) => {
    const bytes = Buffer.from(JSON.stringify(data));
    if (bytes.length > 256 * 1024)
      throw new Error("selected diagnostic exceeds 256 KiB raw bound");
    const compressed = gzipSync(bytes, { level: 9 });
    return {
      encoding: "gzip+base64",
      sha256: hash(bytes),
      decodedBytes: bytes.length,
      compressedBytes: compressed.length,
      data: compressed.toString("base64"),
    };
  };
  const envelope = {
    schema_version: 1,
    kind: "concorde-structured-tool-diagnostic",
    summary: {
      key: full.key,
      nativeExitCode: full.native?.exitCode,
      attemptCount: full.attempts.length,
      rejected: full.attempts.filter((a) => a.isError === true).length,
      sourceRecords: full.sourceRecords,
      sourceTruncated: full.transcriptTruncated,
      effectiveStart: "unknown",
    },
    omittedCallIds: [],
    payload: encode(full),
  };
  // Never replace the first actual failure's complete available argument/error with a count.
  const firstFailed = full.attempts.find((a) => a.isError === true);
  if (Buffer.byteLength(JSON.stringify(envelope)) >= 6800 && firstFailed) {
    envelope.omittedCallIds = full.attempts
      .filter((a) => a !== firstFailed)
      .map((a) => a.callId);
    envelope.payload = encode({
      ...full,
      attempts: [firstFailed],
      reportingOmittedCallIds: envelope.omittedCallIds,
    });
  }
  if (Buffer.byteLength(JSON.stringify(envelope)) >= 7000)
    throw new Error(
      "diagnostic envelope exceeds 7000-byte reserved diagnostic bound; first failure not silently discarded",
    );
  return envelope;
}
export function unpackDiagnostic(envelope) {
  if (
    envelope?.kind !== "concorde-structured-tool-diagnostic" ||
    envelope.payload.encoding !== "gzip+base64"
  )
    throw new Error("unsupported diagnostic envelope");
  const compressed = Buffer.from(envelope.payload.data, "base64");
  if (compressed.length !== envelope.payload.compressedBytes)
    throw new Error("compressed diagnostic size mismatch");
  const raw = gunzipSync(compressed, { maxOutputLength: 256 * 1024 });
  if (
    raw.length !== envelope.payload.decodedBytes ||
    hash(raw) !== envelope.payload.sha256
  )
    throw new Error("diagnostic checksum/size mismatch");
  return JSON.parse(raw.toString("utf8"));
}
