import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';

import Ajv2020 from 'ajv/dist/2020.js';
import {describe, expect, it} from 'vitest';

import {deriveFeatureGraph} from '../../plugins/concorde-content/graph';
import {createManifest} from '../../plugins/concorde-content/manifest';
import {buildRegistry} from '../../plugins/concorde-content/registry';

const fixture = resolve(__dirname, '../fixtures/valid-project');
const interfaceRoot = resolve(__dirname, '../fixtures/interfaces');

describe('Feature Graph 1', () => {
  it('accepts the executable representative example under the strict schema', async () => {
    const schema = JSON.parse(await readFile(resolve(interfaceRoot, 'feature-graph.schema.json'), 'utf8'));
    const example = JSON.parse(await readFile(resolve(interfaceRoot, 'feature-graph.example.json'), 'utf8'));
    const validate = new Ajv2020({allErrors: true, strictTypes: true, strictTuples: true}).compile(schema);
    expect(validate(example), JSON.stringify(validate.errors, null, 2)).toBe(true);
    expect(example.schema_version).toBe(1);
  });

  it('validates a graph derived from the valid-project fixture under the strict schema', async () => {
    const schema = JSON.parse(await readFile(resolve(interfaceRoot, 'feature-graph.schema.json'), 'utf8'));
    const validate = new Ajv2020({allErrors: true, strictTypes: true, strictTuples: true}).compile(schema);
    const graph = deriveFeatureGraph(await buildRegistry(fixture), '0.7.0');
    expect(validate(graph), JSON.stringify(validate.errors, null, 2)).toBe(true);
  });

  it('rejects a graph with an extra property or an inverse relation kind', async () => {
    const schema = JSON.parse(await readFile(resolve(interfaceRoot, 'feature-graph.schema.json'), 'utf8'));
    const validate = new Ajv2020({allErrors: true, strictTypes: true, strictTuples: true}).compile(schema);
    const graph = deriveFeatureGraph(await buildRegistry(fixture), '0.7.0') as unknown as Record<string, unknown>;
    expect(validate({...graph, extra: true})).toBe(false);
    const edges = (graph.edges as Array<Record<string, unknown>>).map((edge) => ({...edge}));
    if (edges.length) {
      edges[0].kind = 'composed_by';
      expect(validate({...graph, edges})).toBe(false);
    }
  });

  it('registers feature-graph.json and its counts in Build Manifest 12', async () => {
    const manifest = createManifest(await buildRegistry(fixture));
    expect(manifest.schemaVersion).toBe(12);
    expect(manifest.featureGraph).toBe('feature-graph.json');
    expect(manifest.featureGraphCounts).toEqual({
      features: 2, modules: 2,
      edges_by_kind: {composes: 0, refines: 0, depends_on: 0, relates_to: 1, requires: 0},
    });
  });
});
