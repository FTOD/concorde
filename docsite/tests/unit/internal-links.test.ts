import {mkdtemp, mkdir, writeFile, rm, readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve, dirname} from 'node:path';
import {afterEach, beforeEach, expect, it} from 'vitest';
import {validateInternalLinks} from '../../plugins/scoped-content/internal-links';

let root: string;
const site = {url: 'https://example.test', baseUrl: '/project/'};
const aliases = new Map([['/specs/old/alias', '/specs/current']]);
async function put(path: string, html: string) {
  await mkdir(dirname(resolve(root, path)), {recursive: true});
  await writeFile(resolve(root, path), html);
}
const validate = () => validateInternalLinks(root, site, aliases, ['/specs/current']);
beforeEach(async () => {
  root = await mkdtemp(resolve(tmpdir(), 'concorde-links-'));
  await put('specs/current.html', '<h1 id="entity.current">Current</h1><a id="a&amp;b"></a>');
});
afterEach(async () => { await rm(root, {recursive: true, force: true}); });

it('scenario.views.publish-legacy-redirect: resolves cross-collection, alias, query and encoded fragment navigation', async () => {
  await put('protocol/chapter.html', `<a href="../specs/current?view=full#entity.current">Relative</a>
    <a href="/project/specs/old/alias?x=1&amp;y=2#entity.current">Alias</a>
    <a href="https://example.test/project/specs/current#a%26b">Absolute</a>
    <a href="https://other.test/missing">External</a><a href="/outside/missing">Outside base</a>
    <a href="mailto:reader@example.test">Mail</a>`);
  const before = await readFile(resolve(root, 'protocol/chapter.html'));
  await validate();
  expect(await readFile(resolve(root, 'protocol/chapter.html'))).toEqual(before);
});

it('scenario.views.validate-candidate-mismatch: rejects missing pages and anchors on all retained navigation forms', async () => {
  for (const href of ['#missing', '/project/missing', '/project/specs/current#missing',
    '/project/specs/old/alias#missing', '/project/specs/removed/alias',
    'https://example.test/project/missing?q=1', '../specs/current#missing']) {
    await put('protocol/chapter.html', `<a href="${href}">Retained reference</a>`);
    await expect(validate()).rejects.toThrow(/protocol\/chapter.html.*to /);
  }
  await rm(resolve(root, 'protocol/chapter.html'));
  await rm(resolve(root, 'specs/current.html'));
  await expect(validate()).rejects.toThrow(/build-manifest.json.*current/);
});

it('scenario.views.validate-candidate-mismatch: follows redirect fragments and rejects cycles and unresolved redirects', async () => {
  await put('index.html', '<meta http-equiv="refresh" content="0; url=/project/specs/current">');
  await put('protocol/chapter.html', '<a href="/project/#entity.current">Redirect fragment</a>');
  await validate();
  await put('index.html', '<meta http-equiv="refresh" content="0; url=/project/">');
  await expect(validate()).rejects.toThrow(/Unresolved internal navigation/);
  await put('index.html', '<meta http-equiv="refresh" content="0; url=/project/missing">');
  await expect(validate()).rejects.toThrow(/Unresolved internal navigation/);
});

it.each(['/文档/', '/%E6%96%87%E6%A1%A3/'])(
  'scenario.views.validate-candidate-mismatch: checks navigation and required pages under Unicode base %s', async baseUrl => {
    const validateUnicode = () => validateInternalLinks(root, {...site, baseUrl}, aliases, ['/specs/current']);
    await put('protocol/chapter.html', `<a href="../specs/current?q=1#entity.current">Relative</a>
      <a href="/文档/specs/old/alias?q=1#a%26b">Alias</a>
      <a href="https://example.test/%E6%96%87%E6%A1%A3/specs/current#entity.current">Encoded</a>
      <a href="https://other.test/文档/missing">External origin</a>
      <a href="/文档外/missing">Outside base</a><a href="mailto:reader@example.test">Mail</a>`);
    await validateUnicode();
    for (const href of ['/文档/missing?q=1', '/%E6%96%87%E6%A1%A3/specs/current#missing',
      '/文档/specs/old/alias#missing', '../specs/missing']) {
      await put('protocol/chapter.html', `<a href="${href}">Unresolved</a>`);
      await expect(validateUnicode()).rejects.toThrow(/protocol\/chapter.html.*to /);
    }
    await rm(resolve(root, 'protocol/chapter.html'));
    await rm(resolve(root, 'specs/current.html'));
    await expect(validateUnicode()).rejects.toThrow(/build-manifest.json.*current/);
  });

it('scenario.views.validate-candidate-mismatch: parses HTML entities, unquoted attributes, base URLs and ignores script examples', async () => {
  await put('protocol/chapter.html', `<base href="/project/specs/"><a href=current#a%26b>Entity</a>
    <script>const example = '<a href="/project/not-a-link">';</script>
    <!-- <a href="/project/not-a-link"> -->`);
  await validate();
  await put('protocol/chapter.html', '<area href="/project/missing">');
  await expect(validate()).rejects.toThrow(/protocol\/chapter.html/);
});

it.each([
  ['<base href="/project/specs/">', 'current'],
  ['<base href="specs/">', 'current'],
  ['', 'specs/current'],
])('scenario.views.validate-candidate-mismatch: incoming redirects use their effective base (%s)', async (base, destination) => {
  await put('incoming.html', '<a href="/project/jump.html?from=reader#entity.current">Jump</a>');
  await put('jump.html', `${base}<meta http-equiv="refresh" content="0; url=${destination}?view=full&amp;x=2">`);
  await validate();
  await put('incoming.html', '<a href="/project/jump.html?from=reader#missing">Jump</a>');
  await expect(validate()).rejects.toThrow('from incoming.html to /project/jump.html?from=reader#missing');
});

it.each(['missing?view=full', '../jump.html'])(
  'scenario.views.validate-candidate-mismatch: incoming base redirects reject missing destinations and cycles (%s)', async destination => {
    await put('incoming.html', '<a href="/project/jump.html#entity.current">Jump</a>');
    await put('jump.html', `<base href="/project/specs/"><meta http-equiv="refresh" content="0; url=${destination}">`);
    const before = await readFile(resolve(root, 'jump.html'));
    await expect(validate()).rejects.toThrow('from incoming.html to /project/jump.html#entity.current');
    expect(await readFile(resolve(root, 'jump.html'))).toEqual(before);
  });

it.each(['https://other.test/specs/', '/outside/'])(
  'scenario.views.validate-candidate-mismatch: redirect bases retain external classification (%s)', async base => {
    await put('incoming.html', '<a href="/project/jump.html#missing">Jump</a>');
    await put('jump.html', `<base href="${base}"><meta http-equiv="refresh" content="0; url=missing?q=1">`);
    await validate();
  });

const encodedBases = ['/%E6%96%87%E6%A1%A3/', '/%e6%96%87%e6%a1%a3/', '/%e6%96%87%E6%a1%A3/'];
const equivalentBases = [
  ['/docs/', '/%64ocs/'],
  ['/AZaz09-._~/', '/%41%5a%61%7A%30%39%2d%2E%5f%7e/'],
  ['/docs/文档~/', '/%64oc%73/%e6%96%87%E6%a1%A3%7e/'],
].flatMap(([literal, encoded]) => [[literal, encoded], [encoded, literal]]);
it.each(equivalentBases)(
  'scenario.views.validate-candidate-mismatch: unreserved paths are equivalent from base %s to %s', async (baseUrl, linkBase) => {
    const validateEquivalent = () => validateInternalLinks(root, {...site, baseUrl}, aliases, ['/specs/current']);
    for (const prefix of ['', site.url]) {
      for (const path of ['specs/current?q=1#a%26b', '%73pecs/current#entity.current', 'specs/old/alias#entity.current']) {
        await put('incoming.html', `<a href="${prefix}${linkBase}${path}">Read</a>`);
        await validateEquivalent();
      }
      for (const path of ['missing?q=1', 'specs/current#missing', 'specs/old/alias#missing', 'specs/Current#entity.current']) {
        const href = prefix + linkBase + path;
        await put('incoming.html', `<a href="${href}">Read</a>`);
        const before = await readFile(resolve(root, 'incoming.html'));
        await expect(validateEquivalent()).rejects.toThrow(`from incoming.html to ${href}`);
        expect(await readFile(resolve(root, 'incoming.html'))).toEqual(before);
      }
    }
  });

it.each([
  ['/docs/', ['/%44ocs/missing', '/%64ocsextra/missing', '/docs%2fmissing', '/%2564ocs/missing']],
  ['/docs%2Fpart/', ['/docs/part/missing', '/docs%252Fpart/missing']],
  ['/docs%25part/', ['/docs%part/missing', '/docs%2525part/missing']],
])('scenario.views.validate-candidate-mismatch: unreserved normalization preserves boundaries under %s', async (baseUrl, outside) => {
  const validateBoundary = () => validateInternalLinks(root, {...site, baseUrl}, aliases, ['/specs/current']);
  await put('incoming.html', outside.map(href => `<a href="${href}">Outside base</a>`).join('') +
    '<a href="https://other.test/%64ocs/missing">Other origin</a>');
  await validateBoundary();
  const href = baseUrl.toLowerCase() + 'missing';
  await put('incoming.html', `<a href="${href}">Internal</a>`);
  await expect(validateBoundary()).rejects.toThrow(`from incoming.html to ${href}`);
});

it('scenario.views.validate-candidate-mismatch: normalized suffixes decode percent signs only once', async () => {
  await put('specs/%64ocument.html', '<h1 id="present">Literal percent escape</h1>');
  await put('incoming.html', '<a href="/%64ocs/specs/%2564ocument#present">Read</a>');
  const validatePercent = () => validateInternalLinks(root, {...site, baseUrl: '/docs/'}, aliases, ['/specs/current']);
  await validatePercent();
  await put('incoming.html', '<a href="/%64ocs/specs/document#present">Missing literal path</a>');
  await expect(validatePercent()).rejects.toThrow('from incoming.html to /%64ocs/specs/document#present');
});

it.each(encodedBases)(
  'scenario.views.validate-candidate-mismatch: escape case is equivalent under base %s', async baseUrl => {
    const validateEncoded = () => validateInternalLinks(root, {...site, baseUrl}, aliases, ['/specs/current']);
    for (const prefix of ['', site.url]) for (const base of encodedBases) {
      for (const path of ['specs/current?q=1#a%26b', 'specs/old/alias?q=1#entity.current']) {
        await put('incoming.html', `<a href="${prefix}${base}${path}">Read</a>`);
        await validateEncoded();
      }
      for (const path of ['missing?q=1', 'specs/current?q=1#missing', 'specs/Current#entity.current']) {
        const href = prefix + base + path;
        await put('incoming.html', `<a href="${href}">Read</a>`);
        const before = await readFile(resolve(root, 'incoming.html'));
        await expect(validateEncoded()).rejects.toThrow(`from incoming.html to ${href}`);
        expect(await readFile(resolve(root, 'incoming.html'))).toEqual(before);
      }
    }
    await put('incoming.html', `<a href="https://other.test/${baseUrl.slice(1)}missing">Other origin</a>
      <a href="${baseUrl.slice(0, -1)}extra/missing">Outside directory</a>
      <a href="/outside/missing">Outside base</a>`);
    await validateEncoded();
  });

it('scenario.views.validate-candidate-mismatch: escape normalization preserves literal base case and encoded boundaries', async () => {
  await put('incoming.html', `<a href="/docs/%e6%96%87/missing">Different case</a>
    <a href="/Docs/%e6%96%87extra/missing">Different directory</a>
    <a href="/Docs/%e6%96%87%2fmissing">Encoded separator</a>`);
  const validateCase = () => validateInternalLinks(root,
    {...site, baseUrl: '/Docs/%E6%96%87/'}, aliases, ['/specs/current']);
  await validateCase();
  await put('incoming.html', '<a href="/Docs/%e6%96%87/missing">Internal</a>');
  await expect(validateCase()).rejects.toThrow('from incoming.html to /Docs/%e6%96%87/missing');
});
