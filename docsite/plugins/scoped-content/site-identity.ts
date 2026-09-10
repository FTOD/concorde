import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

/** Site identity schema 1 — the only project-specific configuration the adapter reads. */
export interface HomepageItem {title: string; description: string}
export interface Homepage {
  eyebrow: string;
  title: string;
  description: string;
  features: {title: string; items: HomepageItem[]};
  workflow: {title: string; description: string; steps: HomepageItem[]};
  quickstart: {title: string; description: string; code: string};
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
  protocolDocs?: boolean;
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
  if (record.protocolDocs !== undefined && typeof record.protocolDocs !== 'boolean') {
    invalid('protocolDocs must be a boolean when present.');
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
    ...(record.protocolDocs !== undefined ? {protocolDocs: record.protocolDocs as boolean} : {}),
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
