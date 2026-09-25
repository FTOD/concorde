import { dirname, resolve } from "node:path";

import type { ScopedRegistry } from "../plugins/scoped-content/model";

/** The running Docusaurus preview, as much of a child process as the supervisor needs. */
export interface PreviewProcess {
  kill(signal: NodeJS.Signals): void;
  once(
    event: "exit",
    listener: (code: number | null, signal: NodeJS.Signals | null) => void,
  ): void;
}

export interface PreviewDependencies {
  /** Stage the current Specs and return the model they were staged from. */
  prepare(): Promise<ScopedRegistry>;
  /** Start `docusaurus start` with these arguments. */
  launch(args: string[]): PreviewProcess;
  /** Watch one directory, non-recursively, reporting the name of each entry that changed. */
  watch(
    directory: string,
    listener: (name: string | null) => void,
  ): { close(): void };
  log(message: string): void;
}

/**
 * Every file whose change makes the staged pages stale: the site identity, the configuration, the
 * registry and both members of every registered document.
 */
export function previewInputs(
  registry: ScopedRegistry,
  siteDir: string,
): string[] {
  const root = registry.projectRoot;
  return [
    resolve(siteDir, "site.json"),
    resolve(root, ".concorde/config.json"),
    resolve(root, registry.registryPath),
    ...registry.pages.flatMap((page) => [
      resolve(root, page.sourcePath),
      resolve(root, page.metadataPath),
    ]),
  ];
}

function describe(error: unknown): string {
  return error instanceof Error
    ? (error.stack ?? error.message)
    : String(error);
}

/**
 * Keeps the Docusaurus preview on the current Specs. The content plugin refuses staged pages whose
 * source digest differs from the sources, so a running Docusaurus can never show a Spec edit; the
 * supervisor instead stops it, stages again and starts it anew whenever an input changes.
 * Directories are watched rather than files, so editors that save by replacing a file are seen.
 */
export class PreviewSupervisor {
  private child: PreviewProcess | undefined;
  private childExited: Promise<void> = Promise.resolve();
  private inputs = new Set<string>();
  private watchers = new Map<string, { close(): void }>();
  private failed = false;
  private timer: NodeJS.Timeout | undefined;
  private cycle: Promise<void> | undefined;
  private pending: string[] = [];
  private stopped = false;
  private launches = 0;

  constructor(
    private readonly siteDir: string,
    private readonly args: string[],
    private readonly dependencies: PreviewDependencies,
    private readonly debounceMs = 300,
  ) {}

  /** Stage and launch the first preview; a failure here is the command's failure. */
  async start(): Promise<void> {
    await this.restart();
    if (this.failed)
      throw new Error(
        "The docsite preview could not be staged; see the error above.",
      );
  }

  /** Resolves once a scheduled restart, if any, has finished. */
  async settled(): Promise<void> {
    while (this.timer || this.cycle) {
      if (this.cycle) await this.cycle;
      else await new Promise((accept) => setTimeout(accept, this.debounceMs));
    }
  }

  async stop(): Promise<void> {
    this.stopped = true;
    clearTimeout(this.timer);
    this.timer = undefined;
    for (const watcher of this.watchers.values()) watcher.close();
    this.watchers.clear();
    if (this.cycle) await this.cycle;
    await this.stopChild();
  }

  private changed(directory: string, name: string | null): void {
    if (this.stopped) return;
    const path = name ? resolve(directory, name) : directory;
    // After a failed staging the model may name a document that does not exist yet, so a new
    // document in a watched directory retries too. Other entries, such as the generated
    // directories staging itself replaces beside `site.json`, never do.
    if (
      name &&
      !this.inputs.has(path) &&
      !(this.failed && /\.md(?:\.json)?$/.test(name))
    )
      return;
    this.pending.push(path);
    clearTimeout(this.timer);
    this.timer = setTimeout(() => {
      this.timer = undefined;
      void this.restart();
    }, this.debounceMs);
  }

  private restart(): Promise<void> {
    // Changes that arrive during a restart are handled by one more restart right after it.
    if (this.cycle) return this.cycle;
    const changes = this.pending.splice(0);
    this.cycle = this.run(changes).finally(() => {
      this.cycle = undefined;
      if (this.pending.length && !this.timer && !this.stopped)
        void this.restart();
    });
    return this.cycle;
  }

  private async run(changes: string[]): Promise<void> {
    if (this.stopped) return;
    if (changes.length)
      this.dependencies.log(
        `Spec sources changed (${[...new Set(changes)].join(", ")}); restarting the docsite preview.`,
      );
    await this.stopChild();
    let registry: ScopedRegistry;
    try {
      registry = await this.dependencies.prepare();
    } catch (error) {
      this.failed = true;
      this.dependencies.log(
        `The docsite preview could not stage the Specs, so no preview is running:\n${describe(error)}\n` +
          (this.watchers.size
            ? "Waiting for a change to a registered input, or a new Spec document beside one, to try again."
            : "Nothing is watched yet; fix the error and run `npm run start` again."),
      );
      return;
    }
    if (this.stopped) return;
    this.failed = false;
    this.inputs = new Set(previewInputs(registry, this.siteDir));
    this.rewatch();
    this.launch();
  }

  private rewatch(): void {
    const directories = new Set([...this.inputs].map((path) => dirname(path)));
    for (const [directory, watcher] of this.watchers)
      if (!directories.has(directory)) {
        watcher.close();
        this.watchers.delete(directory);
      }
    for (const directory of directories)
      if (!this.watchers.has(directory))
        this.watchers.set(
          directory,
          this.dependencies.watch(directory, (name) =>
            this.changed(directory, name),
          ),
        );
  }

  private launch(): void {
    // Only the first launch may open a browser; later ones reuse the page already open.
    const args =
      this.launches++ && !this.args.includes("--no-open")
        ? [...this.args, "--no-open"]
        : this.args;
    const child = this.dependencies.launch(args);
    this.child = child;
    this.childExited = new Promise((accept) =>
      child.once("exit", (code, signal) => {
        if (this.child === child) {
          this.child = undefined;
          if (!this.stopped)
            this.dependencies.log(
              `The Docusaurus preview exited on its own (${signal ? `signal ${signal}` : `status ${code}`}); ` +
                "it starts again on the next change to a watched Spec source.",
            );
        }
        accept();
      }),
    );
  }

  private async stopChild(): Promise<void> {
    const child = this.child;
    if (!child) return this.childExited;
    this.child = undefined;
    child.kill("SIGTERM");
    const forced = setTimeout(() => child.kill("SIGKILL"), 10_000);
    await this.childExited;
    clearTimeout(forced);
  }
}
