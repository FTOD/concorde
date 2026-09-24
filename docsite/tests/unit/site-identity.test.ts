import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve } from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import {
  loadSiteIdentity,
  parseSiteIdentity,
  type SiteIdentity,
} from "../../plugins/scoped-content/site-identity";

const validValue = {
  schema_version: 1,
  title: "Atlas",
  url: "https://example.com",
  baseUrl: "/",
  organizationName: "atlas-org",
  projectName: "atlas",
  repository: "https://github.com/atlas-org/atlas",
  tagline: "A specified project",
};

const roots: string[] = [];
afterEach(async () =>
  Promise.all(
    roots.splice(0).map((root) => rm(root, { recursive: true, force: true })),
  ),
);

async function siteDirWith(content: unknown): Promise<string> {
  const root = await mkdtemp(resolve(tmpdir(), "concorde-site-identity-"));
  roots.push(root);
  await writeFile(resolve(root, "site.json"), JSON.stringify(content), "utf8");
  return root;
}

describe("site identity schema 1", () => {
  it("parses a complete valid identity", () => {
    expect(parseSiteIdentity(validValue)).toEqual<SiteIdentity>({
      schemaVersion: 1,
      title: "Atlas",
      url: "https://example.com",
      baseUrl: "/",
      organizationName: "atlas-org",
      projectName: "atlas",
      repository: "https://github.com/atlas-org/atlas",
      tagline: "A specified project",
    });
  });

  it("treats repository and tagline as optional", () => {
    const {
      repository: _repository,
      tagline: _tagline,
      ...minimal
    } = validValue;
    expect(parseSiteIdentity(minimal)).toEqual<SiteIdentity>({
      schemaVersion: 1,
      title: "Atlas",
      url: "https://example.com",
      baseUrl: "/",
      organizationName: "atlas-org",
      projectName: "atlas",
    });
  });

  it("loads a valid docsite/site.json from disk", async () => {
    const siteDir = await siteDirWith(validValue);
    expect(loadSiteIdentity(siteDir)).toMatchObject({
      title: "Atlas",
      organizationName: "atlas-org",
    });
  });

  it.each([true, false, "true"])(
    "rejects retired protocolDocs with migration guidance: %s",
    (value) => {
      expect(() =>
        parseSiteIdentity({ ...validValue, protocolDocs: value }),
      ).toThrow(/Migrate to customDocs/);
    },
  );

  it("supports independent custom docs", () => {
    const customDocs = [
      {
        id: "guides",
        label: "Guides",
        path: "./custom-docs/guides",
        routeBasePath: "guides",
      },
    ];
    expect(parseSiteIdentity({ ...validValue, customDocs }).customDocs).toEqual(
      customDocs,
    );
  });

  // verifies: scenario.views.user-docs-invalid
  it("reads user documents with a default label", () => {
    expect(parseSiteIdentity(validValue).userDocs).toBeUndefined();
    expect(
      parseSiteIdentity({ ...validValue, userDocs: { path: "../docs" } })
        .userDocs,
    ).toEqual({ path: "../docs", label: "User documents" });
    expect(
      parseSiteIdentity({
        ...validValue,
        userDocs: { path: "../guide", label: " Guide " },
      }).userDocs,
    ).toEqual({ path: "../guide", label: "Guide" });
  });

  // verifies: scenario.views.user-docs-invalid
  it.each([
    ["null", null, /userDocs must be an object/],
    ["no path", {}, /userDocs.path/],
    ["absolute path", { path: "/docs" }, /userDocs.path must be relative/],
    ["blank label", { path: "../docs", label: " " }, /userDocs.label/],
  ])("rejects invalid user documents: %s", (_label, userDocs, field) => {
    expect(() => parseSiteIdentity({ ...validValue, userDocs })).toThrow(
      /docsite\/site\.json is invalid/,
    );
    expect(() => parseSiteIdentity({ ...validValue, userDocs })).toThrow(field);
  });

  // verifies: scenario.views.user-docs-invalid
  it("refuses the removed homepage field and points to user documents", () => {
    expect(() =>
      parseSiteIdentity({ ...validValue, homepage: { title: "Atlas" } }),
    ).toThrow(/homepage was removed.*userDocs/);
  });

  it.each(["specs", "specs/extra", "../guides", "/guides", "guides//extra"])(
    "rejects conflicting or invalid custom route %s",
    (routeBasePath) => {
      expect(() =>
        parseSiteIdentity({
          ...validValue,
          customDocs: [
            { id: "guides", label: "Guides", path: "guides", routeBasePath },
          ],
        }),
      ).toThrow(/routeBasePath/);
    },
  );

  it("reports a missing file by its project-relative name", async () => {
    const root = await mkdtemp(
      resolve(tmpdir(), "concorde-site-identity-missing-"),
    );
    roots.push(root);
    expect(() => loadSiteIdentity(root)).toThrow(/docsite\/site\.json/);
  });

  it("reports invalid JSON by the file name", async () => {
    const root = await mkdtemp(
      resolve(tmpdir(), "concorde-site-identity-badjson-"),
    );
    roots.push(root);
    await writeFile(resolve(root, "site.json"), "{not json", "utf8");
    expect(() => loadSiteIdentity(root)).toThrow(/docsite\/site\.json/);
  });

  it.each([
    ["schema_version", { ...validValue, schema_version: 2 }, /schema_version/],
    ["empty title", { ...validValue, title: "" }, /title/],
    ["non-absolute url", { ...validValue, url: "example.com" }, /url/],
    [
      "baseUrl missing leading slash",
      { ...validValue, baseUrl: "atlas/" },
      /baseUrl/,
    ],
    [
      "baseUrl missing trailing slash",
      { ...validValue, baseUrl: "/atlas" },
      /baseUrl/,
    ],
    [
      "non-string organizationName",
      { ...validValue, organizationName: 42 },
      /organizationName/,
    ],
    [
      "non-string projectName",
      { ...validValue, projectName: {} },
      /projectName/,
    ],
    [
      "non-absolute repository",
      { ...validValue, repository: "not-a-url" },
      /repository/,
    ],
  ])(
    "rejects %s with a message naming docsite/site.json and the violated rule",
    (_label, value, rulePattern) => {
      expect(() => parseSiteIdentity(value)).toThrow(/docsite\/site\.json/);
      expect(() => parseSiteIdentity(value)).toThrow(rulePattern);
    },
  );
});

// verifies: scenario.views.custom-docs
describe("collection admission", () => {
  const collection = {
    id: "guides",
    label: "Guides",
    path: "../guides",
    routeBasePath: "guides",
  };
  it.each(["default", "Uppercase", "has_space", ""])(
    "rejects invalid ID %s",
    (id) => {
      expect(() =>
        parseSiteIdentity({
          ...validValue,
          customDocs: [{ ...collection, id }],
        }),
      ).toThrow(/id/);
    },
  );
  it.each(["label", "path", "sidebarPath"])("rejects empty %s", (field) => {
    expect(() =>
      parseSiteIdentity({
        ...validValue,
        customDocs: [{ ...collection, [field]: "" }],
      }),
    ).toThrow(new RegExp(field));
  });
  it.each(["path", "sidebarPath"])("requires docsite-relative %s", (field) => {
    for (const path of ["/absolute", "C:\\docs", "C:/docs"]) {
      expect(() =>
        parseSiteIdentity({
          ...validValue,
          customDocs: [{ ...collection, [field]: path }],
        }),
      ).toThrow(/relative to docsite/);
    }
  });
  it("rejects duplicate IDs and overlapping route bases in either order", () => {
    expect(() =>
      parseSiteIdentity({
        ...validValue,
        customDocs: [collection, collection],
      }),
    ).toThrow(/id/);
    for (const routes of [
      ["guides", "guides/api"],
      ["guides/api", "guides"],
      ["guides", "guides"],
    ]) {
      expect(() =>
        parseSiteIdentity({
          ...validValue,
          customDocs: routes.map((routeBasePath, index) => ({
            ...collection,
            id: "guide-" + index,
            routeBasePath,
          })),
        }),
      ).toThrow(/routeBasePath/);
    }
  });
});
