import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

/** Project-owned site identity and declarative custom collections (schema 1). */
export interface HomepageItem {title: string; description: string}
export interface HomepageTable {
  title: string;
  description: string;
  columns: string[];
  rows: string[][];
}
export interface Homepage {
  eyebrow: string;
  title: string;
  description: string;
  features: {title: string; items: HomepageItem[]};
  workflow: {title: string; description: string; steps: HomepageItem[]};
  quickstart: {title: string; description: string; code: string};
  links?: {label: string; to: string}[];
  reference?: {title: string; description: string; tables: HomepageTable[]};
}

export interface CustomDocs {
  id: string; label: string; path: string; routeBasePath: string; sidebarPath?: string;
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
  customDocs?: CustomDocs[];
  homepage?: Homepage;
}

const SITE_JSON_LABEL = 'docsite/site.json';
const absoluteUrlPattern = /^https?:\/\//i;

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function invalid(rule: string): never {
  throw new Error(`${SITE_JSON_LABEL} is invalid: ${rule}`);
}

function object(value: unknown, field: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) invalid(`${field} must be an object.`);
  return value as Record<string, unknown>;
}

function string(value: unknown, field: string): string {
  if (!isNonEmptyString(value)) invalid(`${field} must be a non-empty string.`);
  return value.trim();
}

function items(value: unknown, field: string): HomepageItem[] {
  if (!Array.isArray(value) || value.length === 0) invalid(`${field} must be a non-empty array.`);
  return value.map((item, index) => {
    const entry = object(item, `${field}[${index}]`);
    return {title: string(entry.title, `${field}[${index}].title`),
      description: string(entry.description, `${field}[${index}].description`)};
  });
}

function strings(value: unknown, field: string): string[] {
  if (!Array.isArray(value) || value.length === 0) invalid(`${field} must be a non-empty array.`);
  return value.map((entry, index) => string(entry, `${field}[${index}]`));
}

function parseLinks(value: unknown): {label: string; to: string}[] {
  if (!Array.isArray(value)) invalid('homepage.links must be an array.');
  return value.map((value, index) => {
    const field = `homepage.links[${index}]`, link = object(value, field);
    const to = string(link.to, `${field}.to`);
    if (!/^\/(?!\/)/.test(to) && !absoluteUrlPattern.test(to)) invalid(`${field}.to must be a local /route or HTTP(S) URL.`);
    return {label: string(link.label, `${field}.label`), to};
  });
}

function parseCustomDocs(value: unknown): CustomDocs[] {
  if (!Array.isArray(value)) invalid('customDocs must be an array.');
  const ids = new Set<string>(), routes: string[] = [];
  return value.map((value, index) => {
    const field = `customDocs[${index}]`, entry = object(value, field);
    const id = string(entry.id, `${field}.id`);
    const routeBasePath = string(entry.routeBasePath, `${field}.routeBasePath`);
    if (!/^[a-z][a-z0-9-]*$/.test(id) || id === 'default' || ids.has(id)) invalid(`${field}.id must be unique and must not be default.`);
    if (!/^[a-zA-Z0-9_-]+(?:\/[a-zA-Z0-9_-]+)*$/.test(routeBasePath) ||
        routeBasePath === 'specs' || routeBasePath.startsWith('specs/') ||
        routes.some(route => route === routeBasePath || route.startsWith(routeBasePath + '/') || routeBasePath.startsWith(route + '/'))) {
      invalid(`${field}.routeBasePath must be a distinct relative route outside specs/.`);
    }
    ids.add(id); routes.push(routeBasePath);
    const relativePath = (value: unknown, name: string) => {
      const path = string(value, `${field}.${name}`);
      if (path.startsWith('/') || path.includes('\\') || /^[a-zA-Z]:/.test(path)) {
        invalid(`${field}.${name} must be relative to docsite/.`);
      }
      return path;
    };
    return {id, routeBasePath, label: string(entry.label, `${field}.label`), path: relativePath(entry.path, 'path'),
      ...(entry.sidebarPath !== undefined ? {sidebarPath: relativePath(entry.sidebarPath, 'sidebarPath')} : {})};
  });
}

function parseReference(value: unknown): NonNullable<Homepage['reference']> {
  const field = 'homepage.reference';
  const reference = object(value, field);
  if (!Array.isArray(reference.tables) || reference.tables.length === 0) invalid(`${field}.tables must be a non-empty array.`);
  return {
    title: string(reference.title, `${field}.title`),
    description: string(reference.description, `${field}.description`),
    tables: reference.tables.map((value, index) => {
      const path = `${field}.tables[${index}]`;
      const table = object(value, path);
      const columns = strings(table.columns, `${path}.columns`);
      if (!Array.isArray(table.rows) || table.rows.length === 0) invalid(`${path}.rows must be a non-empty array.`);
      const rows = table.rows.map((value, row) => {
        const cells = strings(value, `${path}.rows[${row}]`);
        if (cells.length !== columns.length) invalid(`${path}.rows[${row}] must have one cell per column.`);
        return cells;
      });
      return {title: string(table.title, `${path}.title`),
        description: string(table.description, `${path}.description`), columns, rows};
    }),
  };
}

function parseHomepage(value: unknown): Homepage {
  const page = object(value, 'homepage');
  const features = object(page.features, 'homepage.features');
  const workflow = object(page.workflow, 'homepage.workflow');
  const quickstart = object(page.quickstart, 'homepage.quickstart');
  return {
    eyebrow: string(page.eyebrow, 'homepage.eyebrow'),
    title: string(page.title, 'homepage.title'),
    description: string(page.description, 'homepage.description'),
    features: {title: string(features.title, 'homepage.features.title'), items: items(features.items, 'homepage.features.items')},
    workflow: {title: string(workflow.title, 'homepage.workflow.title'),
      description: string(workflow.description, 'homepage.workflow.description'), steps: items(workflow.steps, 'homepage.workflow.steps')},
    quickstart: {title: string(quickstart.title, 'homepage.quickstart.title'),
      description: string(quickstart.description, 'homepage.quickstart.description'), code: string(quickstart.code, 'homepage.quickstart.code')},
    ...(page.links !== undefined ? {links: parseLinks(page.links)} : {}),
    ...(page.reference !== undefined ? {reference: parseReference(page.reference)} : {}),
  };
}

/** Parses and validates a decoded `docsite/site.json` value against site identity schema 1. */
export function parseSiteIdentity(value: unknown): SiteIdentity {
  if (!value || typeof value !== 'object' || Array.isArray(value)) invalid('the document must be a JSON object.');
  const record = value as Record<string, unknown>;

  if (record.schema_version !== 1) invalid('schema_version must be exactly 1.');
  if (!isNonEmptyString(record.title)) invalid('title must be a non-empty string.');
  if (!isNonEmptyString(record.url) || !absoluteUrlPattern.test(record.url)) {
    invalid('url must be an absolute http(s):// URL.');
  }
  if (!isNonEmptyString(record.baseUrl) || !record.baseUrl.startsWith('/') || !record.baseUrl.endsWith('/')) {
    invalid('baseUrl must start and end with "/".');
  }
  if (!isNonEmptyString(record.organizationName)) invalid('organizationName must be a non-empty string.');
  if (!isNonEmptyString(record.projectName)) invalid('projectName must be a non-empty string.');
  if (record.repository !== undefined && (!isNonEmptyString(record.repository) || !absoluteUrlPattern.test(record.repository))) {
    invalid('repository must be an absolute http(s):// URL when present.');
  }
  if (record.tagline !== undefined && !isNonEmptyString(record.tagline)) {
    invalid('tagline must be a non-empty string when present.');
  }
  if ('protocolDocs' in record) {
    invalid('protocolDocs was removed. Migrate to customDocs with id, label, path, routeBasePath and optional sidebarPath; see docsite/README.md.');
  }

  return {
    schemaVersion: 1,
    title: (record.title as string).trim(),
    url: (record.url as string).trim(),
    baseUrl: record.baseUrl as string,
    organizationName: (record.organizationName as string).trim(),
    projectName: (record.projectName as string).trim(),
    ...(record.repository !== undefined ? {repository: (record.repository as string).trim()} : {}),
    ...(record.tagline !== undefined ? {tagline: (record.tagline as string).trim()} : {}),
    ...(record.customDocs !== undefined ? {customDocs: parseCustomDocs(record.customDocs)} : {}),
    ...(record.homepage !== undefined ? {homepage: parseHomepage(record.homepage)} : {}),
  };
}

/** Reads and validates `<siteDir>/site.json`, failing with an error that names the file and the violated rule. */
export function loadSiteIdentity(siteDir: string): SiteIdentity {
  const path = resolve(siteDir, 'site.json');
  let text: string;
  try {
    text = readFileSync(path, 'utf8');
  } catch {
    throw new Error(
      `${SITE_JSON_LABEL} is missing at ${path}. Create it with site identity schema 1: schema_version (1), ` +
      'title, url, baseUrl, organizationName, projectName, and optional repository/tagline.',
    );
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch (error) {
    throw new Error(`${SITE_JSON_LABEL} is not valid JSON: ${(error as Error).message}`);
  }
  return parseSiteIdentity(parsed);
}
