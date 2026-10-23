/**
 * Where each publication mode stages its pages. The preview and a production build each stage
 * into a directory of their own, so neither ever clears or overwrites the other's staged files.
 */
export type PublicationMode = "preview" | "build";

/** The environment variable through which the publisher tells Docusaurus which mode it runs. */
export const PUBLICATION_MODE_VARIABLE = "CONCORDE_PUBLICATION_MODE";

/** The mode Docusaurus runs in: `preview` unless the publisher's build says `build`. */
export function publicationMode(
  environment: NodeJS.ProcessEnv = process.env,
): PublicationMode {
  const value = environment[PUBLICATION_MODE_VARIABLE];
  if (value === undefined || value === "" || value === "preview")
    return "preview";
  if (value === "build") return "build";
  throw new Error(
    `${PUBLICATION_MODE_VARIABLE} is ${JSON.stringify(value)}; it must be "preview" or "build".`,
  );
}

/** The mode's staging directory, relative to `docsite/`. */
export function stagingDirectory(mode: PublicationMode): string {
  return mode === "build" ? ".generated/production" : ".generated/preview";
}

/** The Docusaurus files of a production build, relative to `docsite/`; the preview's are `.docusaurus`. */
export const PRODUCTION_GENERATED_DIRECTORY =
  ".generated/docusaurus-production";
/** Where a production build renders the site before promotion, relative to `docsite/`. */
export const CANDIDATE_DIRECTORY = ".generated/candidate";
/** Where promotion keeps the previous site until the new one is in place, relative to `docsite/`. */
export const BACKUP_DIRECTORY = ".generated/previous-build";

/**
 * Every path below a publication output that publication clears, renames or writes by name,
 * relative to the project root. None of them, and no directory between it and its output, may be a
 * symbolic link, which would send its cleanup or its writes elsewhere.
 */
export const PUBLICATION_CLEARED: readonly string[] = [
  ...(["preview", "build"] as const).flatMap((mode) =>
    ["", "/content", "/scoped-materialization.json", "/specs-sidebar.json"].map(
      (path) => `docsite/${stagingDirectory(mode)}${path}`,
    ),
  ),
  `docsite/${PRODUCTION_GENERATED_DIRECTORY}`,
  `docsite/${CANDIDATE_DIRECTORY}`,
  `docsite/${BACKUP_DIRECTORY}`,
];
