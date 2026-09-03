import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

/** Site identity schema 1 — the only project-specific configuration the adapter reads. */
export interface SiteIdentity {
  schemaVersion: 1;
  title: string;
  url: string;
  baseUrl: string;
  organizationName: string;
  projectName: string;
  repository?: string;
  tagline?: string;
}

const SITE_JSON_LABEL = 'docsite/site.json';
const absoluteUrlPattern = /^https?:\/\//i;

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function invalid(rule: string): never {
  throw new Error(`${SITE_JSON_LABEL} is invalid: ${rule}`);
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

  return {
    schemaVersion: 1,
    title: (record.title as string).trim(),
    url: (record.url as string).trim(),
    baseUrl: record.baseUrl as string,
    organizationName: (record.organizationName as string).trim(),
    projectName: (record.projectName as string).trim(),
    ...(record.repository !== undefined ? {repository: (record.repository as string).trim()} : {}),
    ...(record.tagline !== undefined ? {tagline: (record.tagline as string).trim()} : {}),
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
