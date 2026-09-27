/**
 * The pure part of the worker model picker of Concorde's pi extension.
 *
 * The `configure_workers` Operation lists the models pi offers workers and what the worktree
 * configures for every worker of every Operation, by worker id; these functions turn its output
 * into the choices the picker shows and a chosen row back into a `concorde run configure_workers`
 * command line. The extension owns the dialogs and runs the Operation; the Operation validates and
 * writes the configuration. A worker whose configuration puts it on Claude Code is not the pi
 * picker's to choose, so it offers only the workers that run on pi.
 */

export interface ModelEntry {
  id: string;
  reasoning: boolean;
  levels: string[];
  note?: string;
  context?: string;
}

export interface Chosen {
  backend?: string | null;
  backend_source?: string;
  model: string | null;
  reasoning: string | null;
  model_source: string;
  reasoning_source: string;
}

interface Choice {
  backend?: string;
  model?: string;
  reasoning?: string;
}

/** The `output` of a `configure_workers` result. */
export interface Listing {
  backend: string;
  config: string;
  candidates: { models: ModelEntry[]; reasoning_levels: string[] } | null;
  effective: Record<string, Record<string, Chosen>>;
  configured: {
    default?: Choice;
    operations?: Record<
      string,
      { default?: Choice; workers?: Record<string, Choice> }
    >;
  };
}

/** What a row configures: the default (no Operation) or one worker of an Operation, by id. */
export interface Scope {
  operation: string | null;
  worker: string | null;
}

export const DONE = "Done";
export const USE_FALLBACK = "Remove this setting (use the more general one)";
export const KEEP = "Keep the current value";

function describe(model: string | null, reasoning: string | null): string {
  return `${model ?? "pi's default model"}, ${reasoning ?? "default reasoning"}`;
}

/** The file's own entry for a scope, when it has one. */
function ownEntry(listing: Listing, scope: Scope): Choice | undefined {
  if (scope.operation === null) return listing.configured.default;
  const entry = listing.configured.operations?.[scope.operation];
  if (scope.worker === null) return entry?.default;
  return entry?.workers?.[scope.worker];
}

/**
 * One row per scope: the default, then every worker of every Operation, by its id, with what it
 * runs on now. A worker whose effective backend is another program than the listing's has no row.
 */
export function scopeRows(
  listing: Listing,
): { label: string; scope: Scope | null }[] {
  const base = listing.configured.default ?? {};
  const rows: { label: string; scope: Scope | null }[] = [
    {
      label: `Every worker (default): ${describe(base.model ?? null, base.reasoning ?? null)}`,
      scope: { operation: null, worker: null },
    },
  ];
  for (const [operation, workers] of Object.entries(listing.effective)) {
    for (const [worker, chosen] of Object.entries(workers)) {
      const scope = { operation, worker };
      if (chosen.backend && chosen.backend !== listing.backend) continue;
      rows.push({
        label:
          `${operation} ${worker}: ` +
          describe(chosen.model, chosen.reasoning) +
          (ownEntry(listing, scope) ? " (own setting)" : ""),
        scope,
      });
    }
  }
  rows.push({ label: DONE, scope: null });
  return rows;
}

/** The model rows for a scope: keep, removing its own setting when it has one, then each model. */
export function modelRows(
  listing: Listing,
  scope: Scope,
): { label: string; model: string | null; action: "keep" | "unset" | "set" }[] {
  const rows: {
    label: string;
    model: string | null;
    action: "keep" | "unset" | "set";
  }[] = [{ label: KEEP, model: null, action: "keep" }];
  if (scope.operation !== null && ownEntry(listing, scope))
    rows.push({ label: USE_FALLBACK, model: null, action: "unset" });
  for (const model of listing.candidates?.models ?? []) {
    const extra = [
      model.context ? `${model.context} context` : "",
      model.reasoning ? "" : "no reasoning",
    ]
      .filter(Boolean)
      .join(", ");
    rows.push({
      label: extra ? `${model.id} (${extra})` : model.id,
      model: model.id,
      action: "set",
    });
  }
  return rows;
}

/** The reasoning levels offered for a model, after the choice to keep the current one. */
export function levelRows(listing: Listing, model: string | null): string[] {
  const found = listing.candidates?.models.find((item) => item.id === model);
  return [
    KEEP,
    ...(found ? found.levels : (listing.candidates?.reasoning_levels ?? [])),
  ];
}

/** The model a scope currently resolves to, which decides the levels offered. */
export function currentModel(listing: Listing, scope: Scope): string | null {
  if (scope.operation === null)
    return listing.configured.default?.model ?? null;
  const workers = listing.effective[scope.operation] ?? {};
  const worker = scope.worker ?? Object.keys(workers)[0];
  return workers[worker]?.model ?? null;
}

export interface CommandOutcome {
  code: number;
  value: Record<string, unknown> | null;
  text: string;
}

/** The error a refused command printed, as text naming each link of the chain. */
export function refusalText(outcome: CommandOutcome): string {
  const error = outcome.value?.error as Record<string, unknown> | undefined;
  if (!error) return outcome.text || `exit status ${outcome.code}`;
  const lines: string[] = [];
  const walk = (link: Record<string, unknown>, depth: number) => {
    const unhandled = link.unhandled as Record<string, string> | undefined;
    lines.push(
      `${"  ".repeat(depth)}${link.actor}: ${link.code}: ${link.detail}` +
        (unhandled ? ` (not handled: ${unhandled.explanation})` : ""),
    );
    for (const option of (link.options as string[]) ?? [])
      lines.push(`${"  ".repeat(depth + 1)}option: ${option}`);
    for (const cause of (link.causes as Record<string, unknown>[]) ?? [])
      walk(cause, depth + 1);
  };
  walk(error, 0);
  return lines.join("\n");
}

/** The `concorde` arguments of the listing run of pi's models, for a worktree or one task's copy. */
export function listingCommand(task: string | null): string[] {
  return [
    "run",
    "configure_workers",
    "--candidates",
    "pi",
    ...(task ? ["--task", task] : []),
  ];
}

/** The `concorde` arguments that name a worktree or one task's copy, and nothing to list. */
function targetCommand(task: string | null): string[] {
  return ["run", "configure_workers", ...(task ? ["--task", task] : [])];
}

/** The `concorde` arguments that apply a choice, or null when nothing changes. */
export function commandFor(
  scope: Scope,
  action: "keep" | "unset" | "set",
  model: string | null,
  level: string | null,
  task: string | null,
): string[] | null {
  const target = [
    ...targetCommand(task),
    ...(scope.operation ? ["--operation", scope.operation] : []),
    ...(scope.worker ? ["--worker", scope.worker] : []),
  ];
  if (action === "unset") return [...target, "--unset"];
  const values = [
    ...(action === "set" && model ? ["--model", model] : []),
    ...(level && level !== KEEP ? ["--reasoning", level] : []),
  ];
  return values.length ? [...target, ...values] : null;
}
