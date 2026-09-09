import {resolve} from 'node:path';
import {it,expect} from 'vitest';
import {loadScopedRegistry} from '../../plugins/scoped-content/model';
import {discoverDiagramDeclarations} from '../../plugins/concorde-content/diagrams';
it('declares no external diagram sources under registry schema 3',async()=>{
 const root=resolve(__dirname,'../../..');
 expect(await discoverDiagramDeclarations(root)).toEqual([]);
 expect(loadScopedRegistry(root).targets.length).toBeGreaterThan(0);
});
