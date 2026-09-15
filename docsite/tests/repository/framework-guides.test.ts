import {resolve} from 'node:path';
import {describe,it,expect} from 'vitest';
import {loadScopedRegistry} from '../../plugins/scoped-content/model';
const root=resolve(__dirname,'../../..');
describe('Explicit Concorde self specification',()=>{
 it('publishes every registered document exactly once and no ambient control/README source',()=>{
  const r=loadScopedRegistry(root);
  expect(r.pages.map(p=>p.sourcePath)).toEqual([...new Set(r.targets.flatMap(t=>t.documents))]);
  expect(r.pages.some(p=>p.sourcePath==='README.md'||p.sourcePath.startsWith('.concorde/'))).toBe(false);
  expect(r.targets.some(t=>t.id==='module.protocol')).toBe(false);
  expect(r.pages.some(p=>p.sourcePath.startsWith('protocol/')||p.sourcePath.startsWith('specs/concorde/protocol/'))).toBe(false);
 });
 it('contains independently complete public Skill and business scope descriptions',()=>{
  const r=loadScopedRegistry(root);
  const host=r.pages.filter(p=>p.owner==='module.development').map(p=>p.content).join('\n');
  expect(host).toContain('concorde-context-solve-request');expect(host).toContain('concorde-capability-invocation');
  const hostEntry=r.pages.find(p=>p.primaryOf==='module.development')!;
  expect(hostEntry.content).toContain('scenario.development.execute-capability');
  const specFlow=r.pages.find(p=>p.primaryOf==='module.specify-loop')!;
  expect(specFlow.content).toContain('scenario.development.specify-loop');
  for(const module of r.targets.filter(t=>t.kind==='module')) {
   expect(module.documents.some(path=>path.endsWith('/architecture.md')||path.endsWith('/developer-experience.md'))).toBe(false);
   const entry=r.pages.find(p=>p.primaryOf===module.id)!.content;
   for(const section of ['Usage & Contract','Architecture & Realization'])
    expect(entry).toContain(`## ${section}`);
   for(const section of ['Purpose','Usage','Requirements','Scenarios','Design','Entities','Relationships'])
    expect(entry).toContain(`### ${section}`);
   expect(entry.indexOf('## Usage & Contract')).toBeLessThan(entry.indexOf('## Architecture & Realization'));
  }
 });
});
