export type Graph = {
  nodes: string[];
  edges: { source: string; target: string; conditional: boolean }[];
};
export type OperationInfo = {
  public: boolean;
  context_selection: "discover" | "bound" | "none";
  deterministic: boolean;
  uses: string[];
  state: { input: string[]; output: string[] };
};
export type GraphData = {
  loops: (Graph & { label: string })[];
  operations: Record<string, Graph>;
  operation_info: Record<string, OperationInfo>;
  graphs: Record<string, Graph>;
  factory_sources: string[];
  policy: { max_repair_iterations: number };
  sources: { path: string; digest: string }[];
};
