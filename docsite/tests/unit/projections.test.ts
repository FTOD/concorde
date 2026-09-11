import {mkdtempSync,mkdirSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';
import {afterEach,beforeEach,describe,expect,it} from 'vitest';
import {
  hasDocsProjections, loadInstructionsProjection, loadWireProjection,
  renderInstructionsPage, renderWirePage, PROJECTION_NOTE,
} from '../../plugins/scoped-content/projections';

let root: string;
beforeEach(() => { root = mkdtempSync(resolve(tmpdir(), 'concorde-projections-')); });
afterEach(() => rmSync(root, {recursive: true, force: true}));

function putDocs(instructions: unknown, wire: unknown) {
  mkdirSync(resolve(root, 'generated/docs'), {recursive: true});
  writeFileSync(resolve(root, 'generated/docs/instructions.json'), JSON.stringify(instructions));
  writeFileSync(resolve(root, 'generated/docs/wire.json'), JSON.stringify(wire));
}

describe('hasDocsProjections', () => {
  it('is false when neither generated/docs file exists', () => {
    expect(hasDocsProjections(root)).toBe(false);
  });
  it('is false when only one of the two files exists', () => {
    mkdirSync(resolve(root, 'generated/docs'), {recursive: true});
    writeFileSync(resolve(root, 'generated/docs/instructions.json'), '{}');
    expect(hasDocsProjections(root)).toBe(false);
  });
  it('is true once both generated/docs files exist', () => {
    putDocs({skills: [], agents: []}, {});
    expect(hasDocsProjections(root)).toBe(true);
  });
});

describe('loadInstructionsProjection and loadWireProjection', () => {
  it('read exactly the generated/docs JSON files, rejecting unsafe paths like every other safeRead call', () => {
    putDocs({skills: [{name: 'concorde-main', description: 'Global entry.', capability: 'main', body: 'Body text.'}], agents: []},
      {'concorde-main-request': {type: 'object'}});
    expect(loadInstructionsProjection(root)).toEqual({
      skills: [{name: 'concorde-main', description: 'Global entry.', capability: 'main', body: 'Body text.'}], agents: [],
    });
    expect(loadWireProjection(root)).toEqual({'concorde-main-request': {type: 'object'}});
  });
});

describe('renderInstructionsPage', () => {
  it('opens with the projection note and renders every Skill and Agent', () => {
    const page = renderInstructionsPage({
      skills: [{name: 'concorde-main', description: 'Global entry.', capability: 'main', body: 'Invoke this capability.'}],
      agents: [{name: 'concorde-coordinator', spec: 'agents/coordinator/spec.md', harness: 'discovery-capsule', instructions: 'Act only as the coordinator.', sources: ['agents/coordinator/spec.md'],
        modes: [{name: 'ask', instructions: 'Answer from the admitted complete Specs.', contract: {phase: 'route', action: 'ask'}}]}],
    });
    expect(page.startsWith('# Agent instructions')).toBe(true);
    expect(page).toContain(PROJECTION_NOTE);
    expect(page).toContain('concorde-main');
    expect(page).toContain('Invoke this capability.');
    expect(page).toContain('concorde-coordinator');
    expect(page).toContain('agents/coordinator/spec.md');
    expect(page).toContain('discovery-capsule');
    expect(page).toContain('Act only as the coordinator.');
    expect(page).toContain('#### concorde-coordinator / ask');
    expect(page).toContain('Answer from the admitted complete Specs.');
    expect(page).toContain('"action": "ask"');
  });
});

describe('renderWirePage', () => {
  it('scenario.views.publish-without-graph: sorts type IDs and displays schemas directly', () => {
    const schemas = {'z.type': {const: 'last'}, 'a.type': {type: 'object', properties: {value: {type: 'string'}}}};
    const page = renderWirePage(schemas);
    expect(page.indexOf('## a.type')).toBeLessThan(page.indexOf('## z.type'));
    for (const schema of Object.values(schemas)) expect(page).toContain(JSON.stringify(schema, null, 2));
  });
  it('opens with the projection note and renders every exported schema under its own heading', () => {
    const page = renderWirePage({'concorde-main-request': {type: 'object', properties: {}}});
    expect(page.startsWith('# Wire contracts')).toBe(true);
    expect(page).toContain(PROJECTION_NOTE);
    expect(page).toContain('## concorde-main-request');
    expect(page).toContain('"type": "object"');
  });
});

it('scenario.views.publish-without-graph: preserves Agent, mode and Skill order and complete mode text', () => {
  const common = 'Common responsibility.';
  const modes = ['z-mode', 'a-mode'].map(name => ({name, instructions: common+'\nSelected '+name,
    contract: {mode: name, authority: {write: false}}}));
  const agents = ['z-agent', 'a-agent'].map(name => ({name, spec: name+'.md', harness: 'bounded',
    sources: ['common.md'], instructions: common, modes}));
  const skills = ['z-skill', 'a-skill'].map(name => ({name, description: name, capability: name, body: 'Body '+name}));
  const page = renderInstructionsPage({agents, skills});
  expect(page.indexOf('### z-skill')).toBeLessThan(page.indexOf('### a-skill'));
  expect(page.indexOf('### z-agent')).toBeLessThan(page.indexOf('### a-agent'));
  for (const agent of agents) {
    expect(page.indexOf('#### '+agent.name+' / z-mode')).toBeLessThan(page.indexOf('#### '+agent.name+' / a-mode'));
    for (const mode of modes) {
      const section = page.split('#### '+agent.name+' / '+mode.name)[1].split('\n###')[0];
      expect(section).toContain(JSON.stringify(mode.contract, null, 2));
      expect(section).toContain(mode.instructions);
      expect(section.split(common)).toHaveLength(2);
    }
  }
});
