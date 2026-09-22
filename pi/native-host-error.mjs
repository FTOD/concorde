/** Fixed Host-step failure adapter. Retains selected diagnostics before native previews clip. */
import fs from "node:fs";
import path from "node:path";
import { errorFeedback, failure } from "./execution-error.mjs";

export function installHostErrors(directory, action, attempt) {
  process.once("uncaughtException", (error) => {
    let response;
    try {
      response = JSON.parse(String(error.stdout));
    } catch {}
    const feedback = failure(`Native Host step ${action} failed`, {
      layer: "workflow-host",
      attempt,
      category:
        error.code === "ETIMEDOUT"
          ? "timeout"
          : error.status != null
            ? "native-exit"
            : "transport",
      causes: [errorFeedback(response ? { response } : error)],
      diagnostics: JSON.stringify({
        exitCode: error.status,
        signal: error.signal,
        stderr: error.stderr == null ? null : String(error.stderr),
        stdout: response
          ? undefined
          : error.stdout == null
            ? null
            : String(error.stdout),
      }),
      complete: error.code !== "ENOBUFS",
    });
    const file = path.join(
      directory,
      "host-failure-" + action.replace(/[^a-z0-9-]/gi, "_") + ".json",
    );
    try {
      fs.writeFileSync(file, JSON.stringify(feedback), {
        flag: "wx",
        mode: 0o600,
      });
      console.error(
        JSON.stringify({
          message: feedback.message,
          reference: file,
          complete: false,
          retention: "invocation scratch; archive before cleanup",
        }),
      );
    } catch (saveError) {
      console.error(
        JSON.stringify({
          ...feedback,
          observation_error: errorFeedback(saveError),
        }),
      );
    }
    process.exitCode = 3;
  });
}
