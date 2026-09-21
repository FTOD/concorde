/** Host-side bounded display, preserving full sanitized error details in private scratch. */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createHash } from "node:crypto";
import { safeText } from "./execution-error.mjs";

export function errorDisplay(feedback, limit = 12000) {
  const text = JSON.stringify(feedback, (key, value) =>
    /^(api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret|authorization)$/i.test(
      key,
    )
      ? "[REDACTED]"
      : typeof value === "string"
        ? safeText(value)
        : value,
  );
  if (Buffer.byteLength(text) <= limit) return text;
  try {
    const directory = fs.mkdtempSync(path.join(os.tmpdir(), "concorde-error-"));
    const file = path.join(directory, "feedback.json");
    fs.writeFileSync(file, text, { mode: 0o600, flag: "wx" });
    return JSON.stringify({
      message: safeText(
        feedback.message ??
          feedback.state ??
          feedback.status ??
          "Concorde result",
      ).slice(0, 1000),
      code: feedback.code,
      layer: feedback.layer,
      category: feedback.category,
      attempt: feedback.attempt,
      diagnostics: {
        complete: false,
        reference: file,
        bytes: Buffer.byteLength(text),
        sha256: createHash("sha256").update(text).digest("hex"),
        retention: "local temporary file; archive before cleanup",
        redacted: true,
      },
    });
  } catch (error) {
    // Never replace the original cause with an export failure or claim completeness.
    return JSON.stringify({
      message: safeText(feedback.message).slice(0, 1000),
      code: feedback.code,
      diagnostics: {
        complete: false,
        reference: null,
        export_error: safeText(error.message),
        bytes: Buffer.byteLength(text),
      },
    });
  }
}
