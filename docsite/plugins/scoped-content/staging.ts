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
