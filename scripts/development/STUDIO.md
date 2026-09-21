# Optional StateGraph Operation and Studio

Native Agents/workflows and finite Host tools are the default execution architecture. Studio does not
mirror their business control flow and native calls never redirect through a Studio URL.

The genuine optional boundary is `concorde.harness.operation_node.OperationNode`. It compiles a typed
StateGraph with a `terminal_agent` State transition. A trusted caller selects an Agent profile and
supplies its native launch/admission callable; the graph validates typed input/output and never falls
back to a hidden model runner. Runtime authority is not caller-writable State. Parent StateGraphs
can embed it and declare their own reducers. Main/task-Agent callers may select this boundary when
state-centric composition is useful, without recursive task delegation or changing terminal grants.

```python
from concorde.harness.operation_node import OperationNode
from concorde.harness.operation_state import OperationRuntimeContext

operation = OperationNode("context_assessor").graph()
# admitted_context is the Host-prepared typed Agent context; native_service is a trusted
# callable that invokes the real native Agent and returns its independently admitted typed result.
result = await operation.ainvoke(
    admitted_context["data"],
    context=OperationRuntimeContext(launcher=native_service),
)
```

The synchronous `.invoke(context, native_service)` helper is available for synchronous services.
Missing Runtime service refuses; state fields cannot inject one. This API is not a native workflow
scheduler and does not suspend a Python business provider waiting for Pi.

```sh
uv sync --locked --group studio
python3 scripts/concorde.py build
uv run --locked --group studio langgraph dev --config generated/langgraph.json \
  --host 127.0.0.1 --port 2024 --n-jobs-per-worker 1 --no-browser
```

Select `terminal-agent-operation` in Studio. The default server export is inspection-only until a
trusted embedding supplies a service; do not submit credentials or executable callbacks in State.
Installed LangGraph health remains verified. Optional execution is not a claim that dependencies
may be deleted. Source maintenance remains catalog-free authoring, with exact private candidate
selection only for authorized sibling testing. No global configuration, worktree movement, primary
integration or cleanup authority is granted by Studio. Historical screenshots of retired business
Graphs are not current invocation examples.
