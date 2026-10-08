import { describe, expect, it } from "vitest";
import {
  rewriteMarkdownLinks,
  type ScopedRegistry,
} from "../../plugins/scoped-content/model";

const registry = {
  pages: [
    { sourcePath: "specs/a/module.md", route: "/specs/a" },
    { sourcePath: "specs/a/topic.md", route: "/specs/a/topic" },
  ],
} as unknown as ScopedRegistry;

const rewrite = (content: string) =>
  rewriteMarkdownLinks(registry, "specs/a/module.md", content);

describe("Markdown link rewriting", () => {
  // verifies: scenario.views.materialize
  it("rewrites registered relative links in prose", () => {
    expect(rewrite("See [the topic](topic.md#x) and ![a map](topic.md).")).toBe(
      "See [the topic](/specs/a/topic#x) and ![a map](/specs/a/topic).",
    );
  });

  // verifies: scenario.views.materialize
  it("leaves links inside inline code spans unchanged", () => {
    for (const line of [
      "A link is written `[label](url)` in Markdown.",
      "An image is ``![label](path) with a ` inside``.",
      "Mixed `[label](missing.md)` and [real](topic.md).",
    ]) {
      expect(rewrite(line)).toBe(
        line.replace("[real](topic.md)", "[real](/specs/a/topic)"),
      );
    }
  });

  // verifies: scenario.views.materialize
  it("leaves a link inside a code span wrapped across lines unchanged", () => {
    const wrapped =
      "An example `[label](missing.md)\nstill code` and\n[real](topic.md).";
    expect(rewrite(wrapped)).toBe(
      wrapped.replace("[real](topic.md)", "[real](/specs/a/topic)"),
    );
    const doubled = "Write ``a ` b\n[label](missing.md)`` here.";
    expect(rewrite(doubled)).toBe(doubled);
  });

  // verifies: scenario.views.materialize
  it("never lets a code span cross a blank line or a fence", () => {
    expect(rewrite("A lone `\n\nthen [link](topic.md) and ` here.")).toBe(
      "A lone `\n\nthen [link](/specs/a/topic) and ` here.",
    );
    expect(
      rewrite("A lone `\n```\ncode\n```\n[link](topic.md) and ` here."),
    ).toBe("A lone `\n```\ncode\n```\n[link](/specs/a/topic) and ` here.");
  });

  // verifies: scenario.views.materialize
  it("rewrites a link whose label contains inline code", () => {
    expect(rewrite("Read [`topic.md`](topic.md).")).toBe(
      "Read [`topic.md`](/specs/a/topic).",
    );
  });

  // verifies: scenario.views.materialize
  it("treats an unmatched backtick as text", () => {
    expect(rewrite("A lone ` then [link](topic.md).")).toBe(
      "A lone ` then [link](/specs/a/topic).",
    );
    expect(() => rewrite("A lone ` then [link](missing.md).")).toThrow(
      /Unregistered local link/,
    );
  });

  // verifies: scenario.views.materialize
  it("leaves links inside fenced code unchanged", () => {
    const fenced = "```markdown\n[label](url)\n```\n~~~\n![x](missing.md)\n~~~";
    expect(rewrite(fenced)).toBe(fenced);
  });
});
