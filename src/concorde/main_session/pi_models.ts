/** The pi picker opens Workers' terminal editor, sharing its draft and Save/Cancel behavior. */
import { spawnSync } from "node:child_process";

export interface CommandOutcome {
  code: number;
  value: Record<string, unknown> | null;
  text: string;
}

export const listingCommand = (): string[] => [
  "configure-workers",
  "--show",
  "--json",
];
export const editorCommand = (): string[] => ["configure-workers"];

/** Release pi's terminal for the editor and always restore it, including spawn failures. */
export function runEditor(
  tui: { stop(): void; start(): void; requestRender(force?: boolean): void },
  command: string[],
  cwd: string,
  spawn: typeof spawnSync = spawnSync,
): number {
  tui.stop();
  try {
    const [program, ...args] = command;
    const result = spawn(program, args, {
      cwd,
      stdio: "inherit",
      env: { ...process.env, CONCORDE_CLIENT: "pi" },
    });
    if (result.error) throw result.error;
    return result.status ?? 1;
  } finally {
    tui.start();
    tui.requestRender(true);
  }
}

/** Preserve every command error link in the text shown to the main agent. */
export function refusalText(outcome: CommandOutcome): string {
  const error = outcome.value?.error as Record<string, unknown> | undefined;
  if (!error) return outcome.text || `exit status ${outcome.code}`;
  const lines: string[] = [];
  const walk = (link: Record<string, unknown>, depth: number) => {
    const unhandled = link.unhandled as Record<string, string> | undefined;
    lines.push(
      `${"  ".repeat(depth)}${link.actor}: ${link.code}: ${link.detail}` +
        (unhandled
          ? ` (not handled: ${unhandled.reason}: ${unhandled.explanation})`
          : ""),
    );
    for (const option of (link.options as string[]) ?? [])
      lines.push(`${"  ".repeat(depth + 1)}option: ${option}`);
    for (const cause of (link.causes as Record<string, unknown>[]) ?? [])
      walk(cause, depth + 1);
  };
  walk(error, 0);
  return lines.join("\n");
}
