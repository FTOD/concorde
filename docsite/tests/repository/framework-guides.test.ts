import {resolve} from 'node:path';
import {describe,it,expect} from 'vitest';
import {loadScopedRegistry} from '../../plugins/scoped-content/model';
const root=resolve(__dirname,'../../..');
describe('Explicit Concorde self specification',()=>{
 it('publishes every registered member and no ambient control/README source',()=>{
  const r=loadScopedRegistry(root);expect(r.pages.map(p=>p.sourcePath)).toEqual(r.targets.flatMap(t=>t.documents));
  expect(r.pages.some(p=>p.sourcePath==='README.md'||p.sourcePath.startsWith('.concorde/'))).toBe(false);
 });
 it('contains independently complete public Operation and business scope descriptions',()=>{
  const r=loadScopedRegistry(root);const host=r.pages.filter(p=>p.targetId==='service.workflow-host').map(p=>p.content).join('\n');
  expect(host).toContain('concorde-context-solve-request');expect(host).toContain('concorde-operation-invocation');
  const domain=r.pages.find(p=>p.targetId==='domain.workflow')!;expect(domain.content).toContain('Spec incomplete');
 });
});
