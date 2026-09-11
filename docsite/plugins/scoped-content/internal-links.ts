import {readdir, readFile} from 'node:fs/promises';
import {resolve, posix} from 'node:path';
import {parse} from 'parse5';

interface Element {
  tagName?: string;
  attrs?: {name: string; value: string}[];
  childNodes?: Element[];
}
interface DocumentLinks {anchors: Set<string>; links: string[]; redirect?: string; base?: string}

function inspect(html: string): DocumentLinks {
  const result: DocumentLinks = {anchors: new Set(), links: []};
  function visit(node: Element) {
    const attrs = Object.fromEntries((node.attrs ?? []).map(({name, value}) => [name, value]));
    if (attrs.id) result.anchors.add(attrs.id);
    if (node.tagName === 'a' && attrs.name) result.anchors.add(attrs.name);
    if (['a', 'area'].includes(node.tagName ?? '') && attrs.href !== undefined) result.links.push(attrs.href);
    if (node.tagName === 'base' && attrs.href !== undefined && result.base === undefined) result.base = attrs.href;
    if (node.tagName === 'meta' && attrs['http-equiv']?.toLowerCase() === 'refresh') {
      const match = attrs.content?.match(/^\s*[\d.]+\s*;\s*url\s*=\s*([\s\S]*)$/i);
      if (match) result.redirect = match[1].replace(/^(['"])([\s\S]*)\1$/, '$2');
    }
    for (const child of node.childNodes ?? []) visit(child);
  }
  visit(parse(html) as Element);
  return result;
}

/** Inspect the completed output, including optional reading collections. Never fetch URLs. */
export async function validateInternalLinks(directory: string, site: {url: string; baseUrl: string},
  aliases: Map<string, string>, requiredRoutes: string[]): Promise<void> {
  const files = new Set<string>();
  const documents = new Map<string, DocumentLinks>();
  async function collect(path: string) {
    for (const entry of await readdir(resolve(directory, path), {withFileTypes: true})) {
      const name = posix.join(path, entry.name);
      if (entry.isDirectory()) await collect(name);
      else if (entry.isFile()) {
        files.add(name);
        if (name.endsWith('.html')) documents.set(name, inspect(await readFile(resolve(directory, name), 'utf8')));
      }
    }
  }
  await collect('');
  const origin = new URL(site.url).origin;
  // Unreserved escapes equal their literal forms; retain path case and encoded separators.
  const normalizePath = (path: string) => path.replace(/%[0-9a-f]{2}/gi, escape => {
    const character = String.fromCharCode(parseInt(escape.slice(1), 16));
    return /^[A-Za-z0-9._~-]$/.test(character) ? character : escape.toUpperCase();
  });
  const base = normalizePath(new URL(site.baseUrl, origin).pathname);
  const routeUrl = (route: string) => new URL(base + route.replace(/^\//, ''), origin);
  const locate = (path: string) => [path, path + '.html', posix.join(path, 'index.html')].find(p => files.has(p));
  const fail = (referrer: string, destination: string): never => {
    throw new Error(`Unresolved internal navigation from ${referrer} to ${destination}`);
  };
  function check(url: URL, referrer: string, destination: string, seen = new Set<string>()) {
    const pathname = normalizePath(url.pathname);
    if (url.origin !== origin || !pathname.startsWith(base)) return;
    let path: string;
    try { path = decodeURIComponent(pathname.slice(base.length)); }
    catch { return fail(referrer, destination); }
    if (path.split('/').some(part => part === '..' || part === '.') || path.includes('\\')) return fail(referrer, destination);
    const key = url.href;
    if (seen.has(key)) return fail(referrer, destination);
    seen.add(key);
    const canonical = aliases.get('/' + path.replace(/\.html$/, '').replace(/\/$/, ''));
    if (canonical) {
      const next = routeUrl(canonical); next.search = url.search; next.hash = url.hash;
      return check(next, referrer, destination, seen);
    }
    const file = locate(path);
    if (!file) return fail(referrer, destination);
    const document = documents.get(file);
    if (document?.redirect) {
      const baseUrl = document.base === undefined ? url : new URL(document.base, url);
      const next = new URL(document.redirect, baseUrl);
      if (!next.hash) next.hash = url.hash;
      return check(next, referrer, destination, seen);
    }
    if (document && url.hash) {
      let anchor: string;
      try { anchor = decodeURIComponent(url.hash.slice(1)); } catch { return fail(referrer, destination); }
      if (!document.anchors.has(anchor)) return fail(referrer, destination);
    }
  }
  for (const route of requiredRoutes) check(routeUrl(route), 'build-manifest.json', route);
  for (const [file, document] of documents) {
    const route = file === 'index.html' ? '' : file.endsWith('/index.html') ? file.slice(0, -10) : file.slice(0, -5);
    const pageUrl = routeUrl(route);
    const baseUrl = document.base === undefined ? pageUrl : new URL(document.base, pageUrl);
    for (const href of [...document.links, ...(document.redirect ? [document.redirect] : [])]) {
      try { check(new URL(href, baseUrl), file, href); }
      catch (error) {
        if (error instanceof TypeError) fail(file, href);
        throw error;
      }
    }
  }
}
