export type Graph = {nodes: string[]; edges: {source: string; target: string; conditional: boolean}[]};
export type FlowData = {loops: (Graph & {label: string})[]; studio: Record<string, Graph>; flows: Record<string, Graph>; factory_sources: string[];
  policy: {max_repair_iterations: number}; sources: {path: string; digest: string}[]};
