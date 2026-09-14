import {execFileSync} from 'node:child_process';
import {resolve} from 'node:path';
import {expect, it} from 'vitest';
import {filterNavigation, flowNavigation, selectionFromHash} from '../../concorde-only/navigation';
import type {FlowData} from '../../concorde-only/types';

const root = resolve(__dirname, '../../..');
const data: FlowData = JSON.parse(execFileSync(process.env.CONCORDE_PYTHON || 'python3',
  [resolve(root, 'docsite/concorde-only/flows.py')], {encoding: 'utf8'}));
const groups = flowNavigation(data);
const entries = groups.flatMap(group => group.entries);

it('scenario.views.agent-flows: every exported Capability and shared Flow has a unique selectable link', () => {
  expect(new Set(entries.map(entry => entry.id)).size).toBe(entries.length);
  for (const [kind, graphSet] of [['capability', data.capabilities], ['flow', data.flows]] as const) {
    expect(entries.filter(entry => entry.kind === kind).map(entry => entry.key).sort()).toEqual(Object.keys(graphSet).sort());
  }
  for (const entry of entries) expect(selectionFromHash(`#${entry.id}`, groups)).toBe(entry.id);
  expect(entries.find(entry => entry.key === 'concorde-dev-loop')?.id).toBe('development');
  expect(entries.find(entry => entry.key === 'concorde-specify')?.id).toBe('capability-concorde-specify');
});

it('scenario.views.agent-flows: search finds both the enclosing loop and its composed Capability', () => {
  const matches = filterNavigation(groups, 'specify').flatMap(group => group.entries);
  expect(matches.map(entry => entry.key)).toEqual(['concorde-specify-loop', 'concorde-specify']);
  expect(filterNavigation(groups, '  CAPABILITIES specify  ').flatMap(group => group.entries).map(entry => entry.key))
    .toEqual(['concorde-specify-loop', 'concorde-specify']);
  expect(filterNavigation(groups, 'no-such-flow')).toEqual([]);
  expect(filterNavigation(groups, '')).toEqual(groups);
});

it('scenario.views.agent-flows: old detail links select their containing flow and malformed links fall back safely', () => {
  for (const hash of ['#spec-stage-review_spec', '#specify-studio']) expect(selectionFromHash(hash, groups)).toBe('specify');
  for (const hash of ['#stage-tasks', '#handoffs', '#stages', '#studio', '#unknown', '#%']) {
    expect(selectionFromHash(hash, groups)).toBe('development');
  }
  for (const hash of ['#stage-flow-concorde-specify', '#internal-stage-concorde-specify'])
    expect(selectionFromHash(hash, groups)).toBe('capability-concorde-specify');
  expect(selectionFromHash('#flow-catalog', groups)).toBe(groups[1].entries[0].id);
});
