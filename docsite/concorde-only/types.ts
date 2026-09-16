export type Graph = {nodes: string[]; edges: {source: string; target: string; conditional: boolean}[]};
export type CapabilityInfo = {public: boolean; context_selection: 'discover' | 'bound' | 'none'; deterministic: boolean; uses: string[]; state: {input: string[]; output: string[]}};
export type FlowData = {loops: (Graph & {label: string})[]; capabilities: Record<string, Graph>; capability_info: Record<string, CapabilityInfo>; flows: Record<string, Graph>; factory_sources: string[];
  policy: {max_repair_iterations: number}; sources: {path: string; digest: string}[]};
