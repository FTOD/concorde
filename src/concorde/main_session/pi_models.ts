/**
 * The pure part of the worker model picker of Concorde's pi extension.
 *
 * `concorde workers models --backend pi` lists the models pi offers workers and what the worktree
 * configures now; these functions turn that listing into the choices the picker shows and a
 * chosen row back into a `concorde workers set` or `unset` command line. The extension owns the
 * dialogs and runs the commands; the command validates and writes the configuration.
 */

export interface ModelEntry {
  id: string;
  reasoning: boolean;
  levels: string[];
  note?: string;
  context?: string;
}

export interface Chosen {
  model: string | null;
  reasoning: string | null;
  model_source: string;
  reasoning_source: string;
}

export interface Listing {
  backend: string;
  config: string;
  models: ModelEntry[];
  reasoning_levels: string[];
  effective: Record<string, Chosen>;
  configured: {
    default?: { model?: string; reasoning?: string };
    task_types?: Record<string, { model?: string; reasoning?: string }>;
  };
}

export const DEFAULT_SCOPE = "default";
export const DONE = "Done";
export const USE_DEFAULT = "Use the default for this task type";
export const KEEP = "Keep the current value";

function describe(model: string | null, reasoning: string | null): string {
  return `${model ?? "pi's default model"}, ${reasoning ?? "default reasoning"}`;
}

/** One row per scope: the default, then each task type with what it runs on now. */
export function scopeRows(
  listing: Listing,
): { label: string; scope: string }[] {
  const base = listing.configured.default ?? {};
  const rows = [
    {
      label: `All task types (default): ${describe(base.model ?? null, base.reasoning ?? null)}`,
      scope: DEFAULT_SCOPE,
    },
  ];
  for (const [taskType, chosen] of Object.entries(listing.effective)) {
    const own = listing.configured.task_types?.[taskType];
    rows.push({
      label: `${taskType}: ${describe(chosen.model, chosen.reasoning)}${own ? " (own setting)" : ""}`,
      scope: taskType,
    });
  }
  rows.push({ label: DONE, scope: DONE });
  return rows;
}

/** The model rows for a scope: keep, the task type's fallback to the default, then each model. */
export function modelRows(
  listing: Listing,
  scope: string,
): { label: string; model: string | null; action: "keep" | "unset" | "set" }[] {
  const rows: {
    label: string;
    model: string | null;
    action: "keep" | "unset" | "set";
  }[] = [{ label: KEEP, model: null, action: "keep" }];
  if (scope !== DEFAULT_SCOPE && listing.configured.task_types?.[scope])
    rows.push({ label: USE_DEFAULT, model: null, action: "unset" });
  for (const model of listing.models) {
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
  const found = listing.models.find((item) => item.id === model);
  return [KEEP, ...(found ? found.levels : listing.reasoning_levels)];
}

/** The model a scope currently resolves to, which decides the levels offered. */
export function currentModel(listing: Listing, scope: string): string | null {
  if (scope === DEFAULT_SCOPE) return listing.configured.default?.model ?? null;
  return listing.effective[scope]?.model ?? null;
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

/** The `concorde workers` arguments that apply a choice, or null when nothing changes. */
export function commandFor(
  scope: string,
  action: "keep" | "unset" | "set",
  model: string | null,
  level: string | null,
  task: string | null,
): string[] | null {
  const target = [
    "--backend",
    "pi",
    ...(scope === DEFAULT_SCOPE ? [] : ["--task-type", scope]),
    ...(task ? ["--task", task] : []),
  ];
  if (action === "unset") return ["workers", "unset", ...target];
  const values = [
    ...(action === "set" && model ? ["--model", model] : []),
    ...(level && level !== KEEP ? ["--reasoning", level] : []),
  ];
  return values.length ? ["workers", "set", ...target, ...values] : null;
}
