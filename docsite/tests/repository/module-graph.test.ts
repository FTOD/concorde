import {resolve} from 'node:path';
import {describe,it,expect} from 'vitest';
import {loadScopedRegistry} from '../../plugins/scoped-content/model';
const root=resolve(__dirname,'../../..');
describe('Module relationship graph',()=>{
 it('separates Module composition from dependency edges',()=>{
  const r=loadScopedRegistry(root);const kinds=new Set(r.edges.map(e=>e.kind));
  expect(kinds.has('composes')).toBe(true);expect(kinds.has('uses')).toBe(true);
  for(const edge of r.edges)expect(['composes','uses','requires']).toContain(edge.kind);
  for(const edge of r.edges.filter(e=>e.kind==='composes'))expect(r.targets.find(t=>t.id===edge.source)?.kind).toBe('module');
 });
 it('keeps one stable identity for each Module and a reproducible edge set',()=>{
  const a=loadScopedRegistry(root),b=loadScopedRegistry(root);expect(a.sourceDigest).toBe(b.sourceDigest);expect(a.edges).toEqual(b.edges);
  expect(new Set(a.targets.map(t=>t.id)).size).toBe(a.targets.length);
 });
});
