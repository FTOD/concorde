import {resolve} from 'node:path';
import {describe,it,expect} from 'vitest';
import {loadScopedRegistry} from '../../plugins/scoped-content/model';
const root=resolve(__dirname,'../../..');
describe('Module/Implementation relationship graph',()=>{
 it('separates Module composition, dependency and implementation reuse',()=>{
  const r=loadScopedRegistry(root);const kinds=new Set(r.edges.map(e=>e.kind));
  expect(kinds.has('composes')).toBe(true);expect(kinds.has('uses')).toBe(true);expect(kinds.has('implemented_by')).toBe(true);
  for(const edge of r.edges.filter(e=>e.kind==='composes'))expect(r.targets.find(t=>t.id===edge.source)?.kind).toBe('module');
  expect(r.edges.filter(e=>e.kind==='implemented_by'&&e.target==='implementation.worktree-lifecycle').length).toBeGreaterThan(1);
 });
 it('keeps one identity for each shared implementation',()=>{
  const a=loadScopedRegistry(root),b=loadScopedRegistry(root);expect(a.sourceDigest).toBe(b.sourceDigest);expect(a.edges).toEqual(b.edges);
  expect(new Set(a.targets.map(t=>t.id)).size).toBe(a.targets.length);
 });
});
