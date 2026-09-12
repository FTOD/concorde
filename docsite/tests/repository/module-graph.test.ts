import {resolve} from 'node:path';
import {describe,it,expect} from 'vitest';
import {loadScopedRegistry} from '../../plugins/scoped-content/model';
const root=resolve(__dirname,'../../..');
describe('Module navigation metadata',()=>{
 it('scenario.views.load-registry: retains relationships without a graph projection',()=>{
  const a=loadScopedRegistry(root),b=loadScopedRegistry(root);
  expect(a.schema_version).toBe(19);
  expect(a).not.toHaveProperty('edges');
  expect(a.targets.some(t=>t.parent!==null)).toBe(true);
  expect(a.targets.some(t=>t.uses.length>0)).toBe(true);
  expect(a.sourceDigest).toBe(b.sourceDigest);
  expect(a.targets).toEqual(b.targets);
  expect(new Set(a.targets.map(t=>t.id)).size).toBe(a.targets.length);
 });
});
