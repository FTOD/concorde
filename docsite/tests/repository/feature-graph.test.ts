import {resolve} from 'node:path';
import {describe,it,expect} from 'vitest';
import {loadScopedRegistry} from '../../plugins/scoped-content/model';
const root=resolve(__dirname,'../../..');
describe('Profile 8 relationship graph',()=>{
 it('separates scope nesting, composition, overlapping participation and shared contracts',()=>{
  const r=loadScopedRegistry(root);
  expect(new Set(r.edges.map(e=>e.kind))).toEqual(new Set(['scope_contains','composes','participates_in','requires']));
  expect(r.edges.filter(e=>e.source==='service.spec-context'&&e.kind==='participates_in')).toHaveLength(2);
  for(const e of r.edges.filter(e=>e.kind==='composes'))expect(r.targets.find(t=>t.id===e.source)?.kind).not.toBe('domain');
 });
 it('has stable identity and exactly one component identity across scopes',()=>{
  const a=loadScopedRegistry(root),b=loadScopedRegistry(root);expect(a.sourceDigest).toBe(b.sourceDigest);expect(a.edges).toEqual(b.edges);
  expect(new Set(a.targets.map(t=>t.id)).size).toBe(a.targets.length);
 });
});
