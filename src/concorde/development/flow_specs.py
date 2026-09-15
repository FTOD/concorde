"""Flow Specs: node, edge and state diagrams bound to the compiled LangGraph Flows they describe.

A Flow Spec is a Mermaid flowchart in a registered Spec document whose first comment line binds
it to one catalog entry, ``%% flow: <compiled name>``. The diagram follows LangGraph's own
concepts: every node is one executing step, every edge is one routing decision, and every node
label states the state it reads and writes (``name<br/>in: ...<br/>out: ...``). This module
compares each bound diagram with the Flow the catalog compiles from the executable factory:

- the diagram's node identifiers are exactly the compiled nodes, ``__start__`` and ``__end__``
  included;
- the diagram's edges are exactly the compiled edges;
- an edge leaving a node with several successors carries its routing condition as its label,
  and an edge leaving a node with one successor carries none;
- every executing node's label names its input and output state.

It also holds the Graph API rule of the Framework profile: every catalog Flow is a compiled
``StateGraph``, and no Python file under ``src/`` or ``scripts/`` imports LangGraph's Functional
API (``langgraph.func``), which would hide control flow inside ordinary Python. Source files are
parsed for that, never executed.

The findings are deterministic evidence that the authored Flow Spec and the executed topology
agree; they say nothing about whether either is semantically right.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from ..spec.model import Finding
from ..spec.repository import SpecRepository
from ..spec.validation import DiagramError, flowchart_model

BINDING = re.compile(r"^\s*%%\s*flow:\s*([A-Za-z0-9_.-]+)\s*$", re.M)
FENCE = re.compile(r"^```mermaid[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
BOUNDARY = {"__start__", "__end__"}
FUNCTIONAL_API = "langgraph.func"
SOURCE_ROOTS = ("src", "scripts")
EXCLUDED_DIRS = {"node_modules", "__pycache__", ".venv", "build", "dist"}


@dataclass(frozen=True)
class FlowSpec:
    """One bound diagram: where it is, which Flow it names, and its parsed model."""

    path: str
    flow: str
    nodes: dict[str, str]
    edges: tuple[tuple[str, str | None, str], ...]


def flow_specs(repository: SpecRepository) -> tuple[FlowSpec, ...]:
    """Every bound Flow diagram in the registered Spec documents, in path order."""
    result = []
    for path in sorted(repository.document_targets):
        body = repository.document(path).body
        for fence in FENCE.finditer(body):
            text = fence.group(1)
            binding = BINDING.search(text)
            if binding is None:
                continue
            nodes, edges = flowchart_model(text)
            result.append(FlowSpec(path, binding.group(1), nodes, tuple(edges)))
    return tuple(result)


def _state_lines(label: str) -> tuple[str, str | None, str | None]:
    """The node name and its ``in:``/``out:`` lines from a diagram label."""
    text = label.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]
    lines = [line.strip() for line in re.split(r"<br\s*/?>", text)]
    inputs = next((line[len("in:"):].strip() for line in lines if line.startswith("in:")), None)
    outputs = next((line[len("out:"):].strip() for line in lines if line.startswith("out:")), None)
    return lines[0], inputs, outputs


def compare(spec: FlowSpec, topology: dict) -> list[str]:
    """Problems that make ``spec`` disagree with a compiled topology; empty when they agree."""
    problems: list[str] = []
    compiled_nodes = set(topology["nodes"])
    declared_nodes = set(spec.nodes)
    if declared_nodes != compiled_nodes:
        problems.append(f"nodes differ: diagram-only {sorted(declared_nodes - compiled_nodes)}, "
                        f"compiled-only {sorted(compiled_nodes - declared_nodes)}")
    compiled_edges = {(edge["source"], edge["target"]) for edge in topology["edges"]}
    declared_edges = {(source, target) for source, _, target in spec.edges}
    if declared_edges != compiled_edges:
        problems.append(f"edges differ: diagram-only {sorted(declared_edges - compiled_edges)}, "
                        f"compiled-only {sorted(compiled_edges - declared_edges)}")
    successors: dict[str, int] = {}
    for edge in topology["edges"]:
        successors[edge["source"]] = successors.get(edge["source"], 0) + 1
    seen: set[tuple[str, str]] = set()
    for source, label, target in spec.edges:
        if (source, target) in seen:
            problems.append(f"edge {source} -> {target} is declared twice")
        seen.add((source, target))
        if successors.get(source, 0) > 1 and not label:
            problems.append(f"edge {source} -> {target} needs its routing condition as a label")
        if successors.get(source, 0) == 1 and label:
            problems.append(f"edge {source} -> {target} is the node's only transition and carries a label")
    for node_id, label in spec.nodes.items():
        if node_id in BOUNDARY:
            continue
        name, inputs, outputs = _state_lines(label)
        if name != node_id:
            problems.append(f"node {node_id} label must start with its identifier, not {name!r}")
        if not inputs or not outputs:
            problems.append(f"node {node_id} label must state 'in:' and 'out:' state")
    return problems


def _imports_functional_api(node: ast.AST) -> bool:
    """Whether one import statement names ``langgraph.func`` or a member of it."""
    if isinstance(node, ast.Import):
        return any(alias.name == FUNCTIONAL_API or alias.name.startswith(FUNCTIONAL_API + ".")
                   for alias in node.names)
    if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
        if node.module == FUNCTIONAL_API or node.module.startswith(FUNCTIONAL_API + "."):
            return True
        return node.module == "langgraph" and any(alias.name == "func" for alias in node.names)
    return False


def functional_api_imports(root: Path | str, roots: tuple[str, ...] = SOURCE_ROOTS) -> tuple[tuple[str, int, str], ...]:
    """Every import of LangGraph's Functional API below the source roots, found by parsing alone.

    Each hit is ``(path, line, statement)`` with the path relative to ``root``, in root order and
    then path order. Files are parsed, never executed; directories of the Framework's exclusion
    rule and dot-prefixed entries are skipped. A file that cannot be parsed is a hit at the
    failing line, because a check that cannot read a file must not vouch for it.
    """
    root = Path(root)
    hits: list[tuple[str, int, str]] = []
    for relative in roots:
        base = root / relative
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            parts = path.relative_to(root).parts
            if any(part in EXCLUDED_DIRS or part.startswith(".") for part in parts):
                continue
            posix = path.relative_to(root).as_posix()
            try:
                tree = ast.parse(path.read_bytes(), filename=posix)
            except SyntaxError as problem:
                hits.append((posix, problem.lineno or 0, "file cannot be parsed"))
                continue
            for node in ast.walk(tree):
                if _imports_functional_api(node):
                    hits.append((posix, node.lineno, ast.unparse(node)))
    return tuple(hits)


def flow_spec_findings(repository: SpecRepository, catalog: dict | None = None) -> tuple[Finding, ...]:
    """Compare every bound Flow diagram with its compiled Flow; every catalog Flow needs one Spec.

    The same pass refuses every catalog Flow that is not a compiled ``StateGraph`` and every
    source file that imports the Functional API.
    """
    from langgraph.graph.state import CompiledStateGraph

    from .flow_catalog import catalog as default_catalog, topology as compiled_topology
    catalog = default_catalog() if catalog is None else catalog
    findings: list[Finding] = []
    compiled: dict[str, object] = {}
    for name, build in sorted(catalog.items()):
        flow = build()
        if isinstance(flow, CompiledStateGraph):
            compiled[name] = flow
        else:
            findings.append(Finding("CONCORDE-FLOW-004", "error", ".concorde/specs.json",
                f"compiled Flow {name} is a {type(flow).__name__}, not a StateGraph of the Graph API",
                "Build every Flow with StateGraph; the Functional API (entrypoint, task) is not admitted."))
    for path, line, statement in functional_api_imports(repository.root):
        findings.append(Finding("CONCORDE-FLOW-005", "error", path,
            f"imports LangGraph's Functional API: {statement}",
            "Express control flow as StateGraph nodes and edges; langgraph.func is not admitted.",
            line=line))
    try:
        specs = flow_specs(repository)
    except DiagramError as problem:
        return (*findings, Finding("CONCORDE-FLOW-002", "error", ".concorde/specs.json", str(problem),
                        "Use the Mermaid flowchart node and edge forms the Flow Spec convention defines."))
    bound: dict[str, list[FlowSpec]] = {}
    for spec in specs:
        bound.setdefault(spec.flow, []).append(spec)
    for name, entries in sorted(bound.items()):
        if name not in catalog:
            for spec in entries:
                findings.append(Finding("CONCORDE-FLOW-001", "error", spec.path,
                    f"Flow diagram binds unknown Flow {name}",
                    "Bind the diagram to a compiled Flow name from the Flow catalog."))
            continue
        if len(entries) > 1:
            for spec in entries:
                findings.append(Finding("CONCORDE-FLOW-001", "error", spec.path,
                    f"Flow {name} has more than one bound diagram",
                    "Keep exactly one Flow Spec diagram per compiled Flow."))
            continue
        spec = entries[0]
        if name not in compiled:
            continue
        for problem in compare(spec, compiled_topology(compiled[name])):
            findings.append(Finding("CONCORDE-FLOW-003", "error", spec.path,
                f"Flow Spec {name}: {problem}",
                "Make the diagram's nodes, edges, conditions and state labels match the compiled Flow."))
    for name in sorted(set(catalog) - set(bound)):
        findings.append(Finding("CONCORDE-FLOW-001", "error", ".concorde/specs.json",
            f"compiled Flow {name} has no Flow Spec diagram",
            "Add a Mermaid flowchart bound with '%% flow: <name>' to the owning Module's documents."))
    return tuple(findings)
