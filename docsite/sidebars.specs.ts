import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  publicationMode,
  stagingDirectory,
} from "./plugins/scoped-content/staging";

// The Module documents sidebar the running mode staged beside its pages.
export default JSON.parse(
  readFileSync(
    resolve(
      __dirname,
      stagingDirectory(publicationMode()),
      "specs-sidebar.json",
    ),
    "utf8",
  ),
);
