import {resolve} from 'node:path';
import {it,expect} from 'vitest';
import {loadScopedRegistry} from '../../plugins/scoped-content/model';
import {discoverDiagramDeclarations} from '../../plugins/concorde-content/diagrams';
it('discovers exactly declared diagrams without filename inference',async()=>{
 const root=resolve(__dirname,'../../..'),r=loadScopedRegistry(root);
 expect((await discoverDiagramDeclarations(root)).map(d=>d.sourcePath).sort()).toEqual(r.targets.flatMap(t=>t.diagrams.map(d=>d.source)).sort());
 expect(loadScopedRegistry(root).sourceDigest).toBe(r.sourceDigest);
});
