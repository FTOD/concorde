import { readFileSync } from "node:fs";
import { resolve } from "node:path";

/** Project-owned site identity, user documents and declarative custom collections (schema 1). */
export interface UserDocs {
  path: string;
  label: string;
}
export interface CustomDocs {
  id: string;
  label: string;
  path: string;
  routeBasePath: string;
  sidebarPath?: string;
}
export interface SiteIdentity {
  schemaVersion: 1;
  title: string;
  url: string;
  baseUrl: string;
  organizationName: string;
  projectName: string;
  repository?: string;
  tagline?: string;
  userDocs?: UserDocs;
  customDocs?: CustomDocs[];
}

const SITE_JSON_LABEL = "docsite/site.json";
const absoluteUrlPattern = /^https?:\/\//i;

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function invalid(rule: string): never {
  throw new Error(`${SITE_JSON_LABEL} is invalid: ${rule}`);
}

function object(value: unknown, field: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    invalid(`${field} must be an object.`);
  return value as Record<string, unknown>;
}

function string(value: unknown, field: string): string {
  if (!isNonEmptyString(value)) invalid(`${field} must be a non-empty string.`);
  return value.trim();
}

function relativeToSite(value: unknown, field: string): string {
  const path = string(value, field);
  if (path.startsWith("/") || path.includes("\\") || /^[a-zA-Z]:/.test(path)) {
    invalid(`${field} must be relative to docsite/.`);
  }
  return path;
}

function parseUserDocs(value: unknown): UserDocs {
  const entry = object(value, "userDocs");
  return {
    path: relativeToSite(entry.path, "userDocs.path"),
    label:
      entry.label === undefined
        ? "User documents"
        : string(entry.label, "userDocs.label"),
  };
}

function parseCustomDocs(value: unknown): CustomDocs[] {
  if (!Array.isArray(value)) invalid("customDocs must be an array.");
  const ids = new Set<string>(),
    routes: string[] = [];
  return value.map((value, index) => {
    const field = `customDocs[${index}]`,
      entry = object(value, field);
    const id = string(entry.id, `${field}.id`);
    const routeBasePath = string(entry.routeBasePath, `${field}.routeBasePath`);
    if (!/^[a-z][a-z0-9-]*$/.test(id) || id === "default" || ids.has(id))
      invalid(`${field}.id must be unique and must not be default.`);
    if (
      !/^[a-zA-Z0-9_-]+(?:\/[a-zA-Z0-9_-]+)*$/.test(routeBasePath) ||
      routeBasePath === "specs" ||
      routeBasePath.startsWith("specs/") ||
      routes.some(
        (route) =>
          route === routeBasePath ||
          route.startsWith(routeBasePath + "/") ||
          routeBasePath.startsWith(route + "/"),
      )
    ) {
      invalid(
        `${field}.routeBasePath must be a distinct relative route outside specs/.`,
      );
    }
    ids.add(id);
    routes.push(routeBasePath);
    const relativePath = (value: unknown, name: string) =>
      relativeToSite(value, `${field}.${name}`);
    return {
      id,
      routeBasePath,
      label: string(entry.label, `${field}.label`),
      path: relativePath(entry.path, "path"),
      ...(entry.sidebarPath !== undefined
        ? { sidebarPath: relativePath(entry.sidebarPath, "sidebarPath") }
        : {}),
    };
  });
}

/** Parses and validates a decoded `docsite/site.json` value against site identity schema 1. */
export function parseSiteIdentity(value: unknown): SiteIdentity {
  if (!value || typeof value !== "object" || Array.isArray(value))
    invalid("the document must be a JSON object.");
  const record = value as Record<string, unknown>;

  if (record.schema_version !== 1) invalid("schema_version must be exactly 1.");
  if (!isNonEmptyString(record.title))
    invalid("title must be a non-empty string.");
  if (!isNonEmptyString(record.url) || !absoluteUrlPattern.test(record.url)) {
    invalid("url must be an absolute http(s):// URL.");
  }
  if (
    !isNonEmptyString(record.baseUrl) ||
    !record.baseUrl.startsWith("/") ||
    !record.baseUrl.endsWith("/")
  ) {
    invalid('baseUrl must start and end with "/".');
  }
  if (!isNonEmptyString(record.organizationName))
    invalid("organizationName must be a non-empty string.");
  if (!isNonEmptyString(record.projectName))
    invalid("projectName must be a non-empty string.");
  if (
    record.repository !== undefined &&
    (!isNonEmptyString(record.repository) ||
      !absoluteUrlPattern.test(record.repository))
  ) {
    invalid("repository must be an absolute http(s):// URL when present.");
  }
  if (record.tagline !== undefined && !isNonEmptyString(record.tagline)) {
    invalid("tagline must be a non-empty string when present.");
  }
  if ("homepage" in record) {
    invalid(
      "homepage was removed. The home page is the root page of userDocs: set userDocs.path to a directory whose README.md or index.md introduces the project.",
    );
  }
  if ("protocolDocs" in record) {
    invalid(
      "protocolDocs was removed. Migrate to customDocs with id, label, path, routeBasePath and optional sidebarPath; see docsite/README.md.",
    );
  }

  return {
    schemaVersion: 1,
    title: (record.title as string).trim(),
    url: (record.url as string).trim(),
    baseUrl: record.baseUrl as string,
    organizationName: (record.organizationName as string).trim(),
    projectName: (record.projectName as string).trim(),
    ...(record.repository !== undefined
      ? { repository: (record.repository as string).trim() }
      : {}),
    ...(record.tagline !== undefined
      ? { tagline: (record.tagline as string).trim() }
      : {}),
    ...(record.userDocs !== undefined
      ? { userDocs: parseUserDocs(record.userDocs) }
      : {}),
    ...(record.customDocs !== undefined
      ? { customDocs: parseCustomDocs(record.customDocs) }
      : {}),
  };
}

/** Reads and validates `<siteDir>/site.json`, failing with an error that names the file and the violated rule. */
export function loadSiteIdentity(siteDir: string): SiteIdentity {
  const path = resolve(siteDir, "site.json");
  let text: string;
  try {
    text = readFileSync(path, "utf8");
  } catch {
    throw new Error(
      `${SITE_JSON_LABEL} is missing at ${path}. Create it with site identity schema 1: schema_version (1), ` +
        "title, url, baseUrl, organizationName, projectName, and optional repository, tagline, userDocs and customDocs.",
    );
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch (error) {
    throw new Error(
      `${SITE_JSON_LABEL} is not valid JSON: ${(error as Error).message}`,
    );
  }
  return parseSiteIdentity(parsed);
}
