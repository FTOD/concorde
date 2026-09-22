import { describe, expect, it } from "vitest";
import { injectAnchors } from "../../plugins/scoped-content/render";

describe("published definition titles", () => {
  // verifies: scenario.views.id-anchors
  it.each(
    ["req", "scenario"].flatMap((kind) =>
      [2, 3, 4, 5].flatMap((level) =>
        ["—", "–", "-"].map((separator) => ({ kind, level, separator })),
      ),
    ),
  )(
    "keeps the ID for $kind at level $level with $separator",
    ({ kind, level, separator }) => {
      const marks = "#".repeat(level);
      const id = `${kind}.example.stable`;
      const title = "A **readable** `title` — with punctuation";
      const expected = `${marks} ${title} {#${id}}`;
      for (const suffix of ["", ` {#${id}}`, " ###", ` {#${id}} ###`]) {
        expect(
          injectAnchors(`${marks} ${id} ${separator} ${title}${suffix}`),
        ).toBe(expected);
      }
      expect(injectAnchors(expected)).toBe(expected);
    },
  );

  // verifies: scenario.views.id-anchors
  it("keeps duplicate titles independently addressable and title changes link-stable", () => {
    expect(
      injectAnchors(
        [
          "### scenario.example.first — Same title",
          "### scenario.example.second — Same title",
        ].join("\n"),
      ),
    ).toBe(
      [
        "### Same title {#scenario.example.first}",
        "### Same title {#scenario.example.second}",
      ].join("\n"),
    );
    expect(injectAnchors("### scenario.example.first — Renamed title")).toBe(
      "### Renamed title {#scenario.example.first}",
    );
  });

  // verifies: scenario.views.id-anchors
  it("does not transform ordinary headings, prose, inline code or fenced examples", () => {
    const content = [
      "# Document title",
      "## Ordinary title {#ordinary}",
      "A reference to scenario.example.first — Same title.",
      "`### req.example.inline — Inline example`",
      "```markdown",
      "### req.example.fenced — Fenced example",
      "```",
      "~~~~markdown",
      "### scenario.example.fenced — Another example",
      "```",
      "~~~",
      "### req.example.still-fenced — Not a definition",
      "~~~~",
    ].join("\n");
    expect(injectAnchors(content)).toBe(content);
  });
});
