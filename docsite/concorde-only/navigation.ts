import type {FlowData} from './types';

export type FlowEntry = {id: string; title: string; key: string; kind: 'capability' | 'flow' | 'guide'};
export type FlowGroup = {title: string; entries: FlowEntry[]};

export function capabilityAnchor(key: string): string {
  return key === 'concorde-dev-loop' ? 'development' : key === 'concorde-specify-loop' ? 'specify' : `capability-${key}`;
}

export function flowNavigation(data: FlowData): FlowGroup[] {
  const first = ['concorde-dev-loop', 'concorde-specify-loop', 'concorde-specify'];
  const capabilities = [...first, ...Object.keys(data.capabilities).filter(name => !first.includes(name)).sort()];
  return [
    {title: 'Capabilities', entries: capabilities.map(key => ({key, kind: 'capability',
      title: key.replace(/^concorde-/, ''), id: capabilityAnchor(key)}))},
    {title: 'Shared flows', entries: Object.keys(data.flows).map(key => ({key, kind: 'flow', title: key,
      id: `flow-${key.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}))},
    {title: 'Guides', entries: [
      {id: 'routing', key: 'routing', title: 'Routing & diagnosis', kind: 'guide'},
      {id: 'coverage', key: 'coverage', title: 'Implementation coverage', kind: 'guide'},
    ]},
  ];
}

export function selectionFromHash(hash: string, groups: FlowGroup[]): string {
  let id: string;
  try { id = decodeURIComponent(hash.replace(/^#/, '')); } catch { return 'development'; }
  if (groups.some(group => group.entries.some(entry => entry.id === id))) return id;
  // Existing section and node-detail links still open their containing flow.
  if (id.startsWith('spec-stage-') || id === 'specify-studio') return 'specify';
  for (const prefix of ['stage-flow-', 'internal-stage-']) {
    if (id.startsWith(prefix)) {
      const capability = capabilityAnchor(id.slice(prefix.length));
      if (groups.some(group => group.entries.some(entry => entry.id === capability))) return capability;
    }
  }
  if (id === 'flow-catalog') return groups.find(group => group.title === 'Shared flows')!.entries[0].id;
  return 'development';
}

export function filterNavigation(groups: FlowGroup[], query: string): FlowGroup[] {
  const words = query.toLowerCase().trim().split(/\s+/);
  return groups.map(group => ({...group, entries: group.entries.filter(entry =>
    words.every(word => `${entry.title} ${entry.key} ${group.title}`.toLowerCase().includes(word)))}))
    .filter(group => group.entries.length > 0);
}
