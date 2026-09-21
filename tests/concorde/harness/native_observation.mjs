/** Passive test observation only. Never admission, completion authority, retries or model scheduling. */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { selectedDiagnostic } from "./structured_diagnostic.mjs";

const digest = (value) =>
  "sha256:" +
  crypto
    .createHash("sha256")
    .update(
      typeof value === "string" || Buffer.isBuffer(value)
        ? value
        : JSON.stringify(value),
    )
    .digest("hex");
const schemaDigest = (value, unwrap = false) =>
  digest(
    JSON.stringify(value, function (key, v) {
      if (unwrap && key === "$ref" && typeof v === "string")
        return v.replace(/^#\/properties\/value\//, "#/");
      return v && typeof v === "object" && !Array.isArray(v)
        ? Object.fromEntries(
            Object.keys(v)
              .sort()
              .map((k) => [k, v[k]]),
          )
        : v;
    }),
  );
const clean = (text) =>
  text
    .replace(/(Bearer\s+)[^\s"']+/gi, "$1[redacted]")
    .replace(
      /((?:api[_-]?key|authorization|password|access[_-]?token|refresh[_-]?token)["']?\s*[:=]\s*["']?)[^\s,"'}]+/gi,
      "$1[redacted]",
    );
const json = (file) => JSON.parse(fs.readFileSync(file, "utf8"));

export function nativeObservation(directory) {
  const scratch = process.env.CONCORDE_CHECK_TMPDIR;
  if (
    scratch &&
    !path.resolve(directory).startsWith(path.resolve(scratch) + path.sep)
  )
    throw new Error("Observation output must stay in issued tester scratch");
  fs.mkdirSync(directory, { recursive: true, mode: 0o700 });
  if (fs.realpathSync(directory) !== path.resolve(directory))
    throw new Error("Observation directory must be canonical");
  const sessions = [];
  const refreshers = [];
  const starts = new WeakMap();
  function save(name, value) {
    const text = clean(
      typeof value === "string" ? value : JSON.stringify(value, null, 2),
    );
    if (Buffer.byteLength(text) > 16 * 1024 * 1024)
      throw new Error("Observation exceeds raw artifact bound");
    fs.writeFileSync(path.join(directory, name), text, { mode: 0o600 });
    return { file: name, sha256: digest(text), bytes: Buffer.byteLength(text) };
  }
  function observeSession(session, { cwd, origin = "sdk" }) {
    const row = {
      cwd,
      origin,
      sessionId: session.sessionId,
      executionStarts: 0,
    };
    sessions.push(row);
    const capture = (phase = "created") => {
      const tools = session
        .getAllTools()
        .map(({ name, parameters }) => ({ name, parameters }));
      const active = session.getActiveToolNames();
      const prompt = session.systemPrompt;
      const structured = tools.find((t) => t.name === "structured_output");
      Object.assign(row, {
        active,
        registered: tools.map((t) => t.name),
        structuredParameters: structured?.parameters ?? null,
        promptDigest: digest(prompt),
        promptRequiresStructuredOutput: prompt.includes("structured_output"),
        structuredInstruction: clean(
          prompt
            .split("\n")
            .filter((line) => line.includes("structured_output"))
            .join("\n"),
        ).slice(0, 400),
        model: session.model
          ? { provider: session.model.provider, id: session.model.id }
          : null,
      });
      const snapshot = { ...row, phase, systemPrompt: prompt, tools };
      save(`session-${sessions.indexOf(row)}.json`, snapshot);
      // Never let terminal cleanup overwrite what the model's actual turn received.
      if (phase === "agent_start") {
        starts.set(row, snapshot);
        save(
          `session-${sessions.indexOf(row)}-start-${row.executionStarts}.json`,
          snapshot,
        );
      }
    };
    refreshers.push(capture);
    capture();
    session.subscribe((event) => {
      if (event.type === "agent_start") {
        row.executionStarts++;
        capture("agent_start");
      }
      if (event.type === "agent_end" || event.type === "agent_settled")
        capture(event.type);
    });
    return row;
  }
  // Supply this facade through createDefaultChildSessionFactory({loadPiCodingAgent}).
  // It delegates unchanged options/results and uses documented SDK session observations.
  function sdk(module) {
    return {
      ...module,
      async createAgentSession(options) {
        const result = await module.createAgentSession(options);
        observeSession(result.session, { cwd: options.cwd });
        return result;
      },
    };
  }
  function collect(descriptorFile, { artifactRoots }) {
    const root = json(descriptorFile),
      binding = json(path.join(root.directory, "workflow-binding.json"));
    const status = json(path.join(binding.asyncDir, "status.json"));
    if (status.runId !== binding.runId)
      throw new Error("Foreign observation run");
    save("native-status.json", status);
    const events = path.join(binding.asyncDir, "events.jsonl");
    if (fs.existsSync(events)) {
      if (
        fs.lstatSync(events).isSymbolicLink() ||
        fs.statSync(events).size > 16 * 1024 * 1024
      )
        throw new Error("Unsafe native event artifact");
      save("native-events.jsonl", fs.readFileSync(events, "utf8"));
    }
    // Inventory comes from every exclusively issued binding, not only successful emissions.
    const names = fs
      .readdirSync(path.join(root.directory, "bindings"))
      .filter((n) => /^(d-[0-5]|v-[0-5]-[0-3]-\d+)\.json$/.test(n))
      .sort();
    const metas = [];
    for (const base of artifactRoots) {
      if (!fs.existsSync(base)) continue;
      if (fs.realpathSync(base) !== path.resolve(base))
        throw new Error("Aliased artifact root");
      for (const name of fs
        .readdirSync(base)
        .filter((n) => n.endsWith("_meta.json"))) {
        const file = path.join(base, name);
        if (
          fs.lstatSync(file).isSymbolicLink() ||
          fs.statSync(file).size > 16 * 1024 * 1024
        )
          throw new Error("Unsafe native metadata");
        metas.push({ file, value: json(file) });
      }
    }
    const children = names.map((name, index) => {
      const issued = json(path.join(root.directory, "bindings", name));
      const descriptor = json(issued.descriptor),
        key = issued.key;
      const steps = (status.steps ?? []).filter((s) => s.workflowKey === key);
      if (steps.length > 1) throw new Error("Ambiguous observed slot");
      const step = steps[0];
      const matches = metas.filter(
        (m) =>
          m.value.runId === step?.runId && m.value.agent === issued.call.agent,
      );
      if (matches.length > 1) throw new Error("Ambiguous native metadata");
      const meta = matches[0],
        observed = sessions.filter((s) => s.cwd === issued.call.cwd);
      const files = [
        save(`slot-${index}.json`, {
          issued,
          agentProfile: {
            role: descriptor.role,
            phase: descriptor.phase,
            promptDigest: descriptor.prompt_digest,
            assets: descriptor.assets,
          },
          agentDefinition: fs.readFileSync(
            path.join(issued.call.cwd, ".pi/agents", issued.call.agent + ".md"),
            "utf8",
          ),
          preflight: fs.existsSync(
            path.join(descriptor.directory, "preflight.json"),
          )
            ? json(path.join(descriptor.directory, "preflight.json"))
            : null,
        }),
      ];
      if (meta) {
        files.push(save(`child-${index}-metadata.json`, meta.value));
        const transcript = meta.value.transcriptPath;
        if (transcript) {
          const resolved = fs.realpathSync(transcript);
          if (
            resolved !== transcript ||
            !artifactRoots.some((r) =>
              resolved.startsWith(path.resolve(r) + path.sep),
            ) ||
            fs.statSync(transcript).size > 16 * 1024 * 1024
          )
            throw new Error("Unsafe native transcript");
          files.push(
            save(
              `child-${index}-transcript.jsonl`,
              fs.readFileSync(transcript, "utf8"),
            ),
          );
        }
      }
      const transcript = meta?.value.transcriptPath;
      const diagnostic = selectedDiagnostic({
        workflowRunId: binding.runId,
        key,
        ticket: issued.ticket,
        schema: issued.call.outputSchema,
        expected: {
          contextId: descriptor.snapshot.context_id,
          role: descriptor.role,
          phase: descriptor.phase,
          descriptorDigest: issued.digest,
        },
        metadata: meta?.value ?? {
          runId: step?.runId,
          agent: issued.call.agent,
        },
        transcript: transcript ? fs.readFileSync(transcript, "utf8") : null,
      });
      files.push(save(`child-${index}-structured.json`, diagnostic));
      const latest =
        observed.find((s) => s.origin === "sdk") ?? observed.at(-1);
      const session = latest && (starts.get(latest) ?? latest);
      return {
        key,
        agent: issued.call.agent,
        runId: step?.runId ?? null,
        status: step?.status ?? "not-observed",
        metadataObserved: Boolean(meta),
        exitCode: meta?.value.exitCode ?? null,
        error: clean(String(meta?.value.error ?? "")).slice(0, 400),
        executionObserved: Boolean(
          (step?.turnCount ?? 0) > 0 ||
          observed.some((s) => s.executionStarts > 0),
        ),
        actualSdkObserved: session?.origin === "sdk",
        activeTools: session?.active ?? null,
        registeredTools: session?.registered ?? null,
        structuredInstruction: session?.structuredInstruction ?? null,
        sdkExecutionStarts:
          session?.origin === "sdk" ? session.executionStarts : null,
        structuredRegistered:
          session?.registered.includes("structured_output") ?? null,
        structuredActive: session?.active.includes("structured_output") ?? null,
        outputSchemaDigest: schemaDigest(issued.call.outputSchema),
        registeredValueSchemaDigest: session?.structuredParameters?.properties
          ?.value
          ? schemaDigest(session.structuredParameters.properties.value, true)
          : null,
        promptDigest: session?.promptDigest ?? null,
        promptRequiresStructuredOutput:
          session?.promptRequiresStructuredOutput ?? null,
        model: session?.model ?? null,
        files,
      };
    });
    const result = {
      schema_version: 1,
      workflowRunId: binding.runId,
      nativeState: status.state,
      nativeError: clean(String(status.error ?? "")).slice(0, 400),
      expectedSlots: children.length,
      executionsObserved: children.filter((c) => c.executionObserved).length,
      successfulEmissions: (status.workflow?.emits ?? []).filter(
        (e) => e.kind === "concorde.child-terminal",
      ).length,
      childrenMissingMetadata: children.filter(
        (c) => c.runId && !c.metadataObserved,
      ).length,
      failedChildrenWithMetadata: children.filter(
        (c) => c.exitCode !== null && c.exitCode !== 0,
      ).length,
      children,
    };
    save("observation.json", result);
    const summary = { ...result, rawDirectory: directory, omittedChildren: 0 };
    while (
      Buffer.byteLength(JSON.stringify(summary)) >= 7800 &&
      summary.children.length
    ) {
      summary.children = summary.children.slice(0, -1);
      summary.omittedChildren++;
    }
    if (Buffer.byteLength(JSON.stringify(summary)) >= 8000)
      throw new Error("Observation summary exceeds bound");
    save("summary.json", JSON.stringify(summary));
    return summary;
  }
  return {
    sdk,
    observeSession,
    collect,
    refresh: () => refreshers.forEach((f) => f()),
  };
}
