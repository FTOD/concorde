import { createHash } from "node:crypto";
import { expect, it } from "vitest";
import { hash, sourceDigestOf } from "../../plugins/scoped-content/model";

// verifies: scenario.views.load-registry
it("serializes the source digest's pairs exactly as the pipeline's example", () => {
  const pairs: [string, string][] = [
    [".concorde/config.json", hash("{}\n")],
    [".concorde/specs.json", hash('{"schema_version": 3}\n')],
  ];
  const text =
    '[[".concorde/config.json","sha256:ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356"],' +
    '[".concorde/specs.json","sha256:feaa30087d2ef50cda938089d9ea5d4dd7f0803b82ec53f10561078a9e9259db"]]';
  expect(JSON.stringify(pairs)).toBe(text);
  expect(sourceDigestOf(pairs)).toBe(
    "sha256:4cf77a4e7432e482a2255f3b172934c97232c6e6c5de74f6b9659719e48287d1",
  );
  // Non-ASCII characters are written as they are and hashed as UTF-8.
  const unicode: [string, string][] = [["specs/文档.md", hash("x")]];
  expect(sourceDigestOf(unicode)).toBe(
    "sha256:" +
      createHash("sha256")
        .update(Buffer.from(`[["specs/文档.md","${hash("x")}"]]`, "utf8"))
        .digest("hex"),
  );
});
