import { resolve } from "node:path";
import type { LoadContext, Plugin } from "@docusaurus/types";

export default function generatedCache({
  generatedFilesDir,
}: Pick<LoadContext, "generatedFilesDir">): Plugin {
  return {
    name: "concorde-generated-cache",
    configureWebpack(config) {
      if (
        typeof config.cache !== "object" ||
        config.cache.type !== "filesystem"
      )
        return {};
      // preparePublication clears this directory before each launch. Keep compiled
      // snapshots with their generated modules, not in the longer-lived node_modules cache.
      return {
        cache: {
          type: "filesystem",
          cacheDirectory: resolve(generatedFilesDir, "webpack"),
        },
      };
    },
  };
}
