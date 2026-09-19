"""Graph Specs: the State, Nodes and Edges of the compiled LangGraph Graphs they describe.

A Graph Spec is one section of an implementation-role Spec document. It states LangGraph's own
three concepts in order, each introduced by a bold label: **State.** (the channels and records the
Graph carries), **Nodes.** (a ``Node | Executes | in | out`` table) and **Edges.** (how the next
node is chosen), followed by a Mermaid flowchart whose first comment line binds it to one catalog
entry, ``%% graph: <compiled name>``. In the flowchart every node is one executing step, every
edge is one routing decision, and every node label states the state it reads and writes
(``name<br/>in: ...<br/>out: ...``). This module compares each bound Graph Spec with the Graph the
catalog compiles from the executable factory:

- the diagram's node identifiers are exactly the compiled nodes, ``__start__`` and ``__end__``
  included;
- the diagram's edges are exactly the compiled edges;
- an edge leaving a node with several successors carries its routing condition as its label,
  and an edge leaving a node with one successor carries none;
- every executing node's label names its input and output state;
- the section states its State, Nodes and Edges parts in that order, in an implementation-role
  document, and its Nodes table names exactly the compiled nodes other than ``__start__`` and
  ``__end__``, each with the same ``in`` and ``out`` state as its diagram label;
- the section's heading carries an explicit ``{#anchor}``, and a module-role document of the same
  owning Module links to it, so the Operation's explanation leads to its exact Graph Spec.

It also holds the Graph API rule of the Framework profile: every catalog Graph is a compiled
``StateGraph``, and no Python file under ``src/``, ``scripts/`` or ``operations/`` imports LangGraph's Functional
API (``langgraph.func``), which would hide control flow inside ordinary Python. Source files are
parsed for that, never executed.

The findings are deterministic evidence that the authored Graph Spec and the executed topology
agree; they say nothing about whether either is semantically right.
"""

from __future__ import annotations

import ast
import posixpath
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TypeGuard

from ..spec.model import Finding
from ..spec.repository import SpecRepository
from ..spec.validation import DiagramError, flowchart_model

BINDING = re.compile(r"^\s*%%\s*graph:\s*([A-Za-z0-9_.-]+)\s*$", re.M)
FENCE = re.compile(r"^```mermaid[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
HEADING = re.compile(r"#{1,6}[ \t]")
ANCHOR = re.compile(r"\{#([^}\s]+)\}[ \t]*$")
LINK = re.compile(r"\]\(([^)\s#]*)#([^)\s]+)\)")
PART = re.compile(r"\*\*(State|Nodes|Edges)\.\*\*[ \t]*(.*)")
CELL_SEPARATOR = re.compile(r"(?<!\\)\|")
PARTS = ("State", "Nodes", "Edges")
NODES_HEADER = ("Node", "Executes", "in", "out")
BOUNDARY = {"__start__", "__end__"}
FUNCTIONAL_API = "langgraph.func"
SOURCE_ROOTS = ("src", "scripts", "operations")
EXCLUDED_DIRS = {"node_modules", "__pycache__", ".venv", "build", "dist"}


@dataclass(frozen=True)
class GraphSpec:
    """One bound diagram: where it is, which Graph it names, and its parsed model.

    ``section`` is the text of the Graph Spec before its diagram, from the heading that opens the
    section, and ``role`` the document role of the Spec document holding it.
    """

    path: str
    graph: str
    nodes: dict[str, str]
    edges: tuple[tuple[str, str | None, str], ...]
    section: str = ""
    role: str | None = None
    owner: str | None = None


@dataclass(frozen=True)
class Reading:
    """One registered module-role document: its path, owning Module and Markdown body."""

    path: str
    owner: str
    body: str


def graph_specs(repository: SpecRepository) -> tuple[GraphSpec, ...]:
    """Every bound Graph Spec in the registered Spec documents, in path order."""
    result = []
    for path in sorted(repository.document_targets):
        document = repository.document(path)
        role = (document.metadata.get("document") or {}).get("role")
        result.extend(bound_graph_specs(path, document.body, role, document.owner))
    return tuple(result)


def readings(repository: SpecRepository) -> tuple[Reading, ...]:
    """The registered module-role documents, in path order."""
    result = []
    for path in sorted(repository.document_targets):
        document = repository.document(path)
        if (document.metadata.get("document") or {}).get("role") == "module":
            result.append(Reading(path, document.owner, document.body))
    return tuple(result)


def bound_graph_specs(
    path: str, body: str, role: str | None = None, owner: str | None = None
) -> tuple[GraphSpec, ...]:
    """The bound Graph Specs of one document body, each with the section text before its diagram."""
    headings = _heading_offsets(body)
    result = []
    for fence in FENCE.finditer(body):
        text = fence.group(1)
        binding = BINDING.search(text)
        if binding is None:
            continue
        nodes, edges = flowchart_model(text)
        start = max(
            (offset for offset in headings if offset < fence.start()), default=0
        )
        result.append(
            GraphSpec(
                path,
                binding.group(1),
                nodes,
                tuple(edges),
                body[start : fence.start()],
                role,
                owner,
            )
        )
    return tuple(result)


def _heading_offsets(body: str) -> list[int]:
    """Offsets of the ATX heading lines outside fenced code, whose ``#`` lines are not headings."""
    offsets: list[int] = []
    fence: str | None = None
    position = 0
    for line in body.splitlines(keepends=True):
        stripped = line.lstrip()
        if fence is None and stripped[:3] in ("```", "~~~"):
            fence = stripped[:3]
        elif fence is not None and stripped.startswith(fence):
            fence = None
        elif fence is None and HEADING.match(line):
            offsets.append(position)
        position += len(line)
    return offsets


def _state_lines(label: str) -> tuple[str, str | None, str | None]:
    """The node name and its ``in:``/``out:`` lines from a diagram label."""
    text = label.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]
    lines = [line.strip() for line in re.split(r"<br\s*/?>", text)]
    inputs = next(
        (line[len("in:") :].strip() for line in lines if line.startswith("in:")), None
    )
    outputs = next(
        (line[len("out:") :].strip() for line in lines if line.startswith("out:")), None
    )
    return lines[0], inputs, outputs


def compare(spec: GraphSpec, topology: dict) -> list[str]:
    """Problems that make ``spec`` disagree with a compiled topology; empty when they agree."""
    problems: list[str] = []
    compiled_nodes = set(topology["nodes"])
    declared_nodes = set(spec.nodes)
    if declared_nodes != compiled_nodes:
        problems.append(
            f"nodes differ: diagram-only {sorted(declared_nodes - compiled_nodes)}, "
            f"compiled-only {sorted(compiled_nodes - declared_nodes)}"
        )
    compiled_edges = {(edge["source"], edge["target"]) for edge in topology["edges"]}
    declared_edges = {(source, target) for source, _, target in spec.edges}
    if declared_edges != compiled_edges:
        problems.append(
            f"edges differ: diagram-only {sorted(declared_edges - compiled_edges)}, "
            f"compiled-only {sorted(compiled_edges - declared_edges)}"
        )
    successors: dict[str, int] = {}
    for edge in topology["edges"]:
        successors[edge["source"]] = successors.get(edge["source"], 0) + 1
    seen: set[tuple[str, str]] = set()
    for source, label, target in spec.edges:
        if (source, target) in seen:
            problems.append(f"edge {source} -> {target} is declared twice")
        seen.add((source, target))
        if successors.get(source, 0) > 1 and not label:
            problems.append(
                f"edge {source} -> {target} needs its routing condition as a label"
            )
        if successors.get(source, 0) == 1 and label:
            problems.append(
                f"edge {source} -> {target} is the node's only transition and carries a label"
            )
    for node_id, label in spec.nodes.items():
        if node_id in BOUNDARY:
            continue
        name, inputs, outputs = _state_lines(label)
        if name != node_id:
            problems.append(
                f"node {node_id} label must start with its identifier, not {name!r}"
            )
        if not inputs or not outputs:
            problems.append(f"node {node_id} label must state 'in:' and 'out:' state")
    return problems


def _parts(section: str) -> dict[str, list[tuple[int, str]]]:
    """Each bold part label of a section outside fenced code: offset and its paragraph's text."""
    found: dict[str, list[tuple[int, str]]] = {name: [] for name in PARTS}
    lines = section.splitlines(keepends=True)
    fence: str | None = None
    position = 0
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if fence is None and stripped[:3] in ("```", "~~~"):
            fence = stripped[:3]
        elif fence is not None and stripped.startswith(fence):
            fence = None
        elif fence is None and (match := PART.match(line)):
            paragraph = [match.group(2).strip()]
            for following in lines[index + 1 :]:
                if not following.strip():
                    break
                paragraph.append(following.strip())
            found[match.group(1)].append((position, " ".join(paragraph).strip()))
        position += len(line)
    return found


def _cells(line: str) -> list[str] | None:
    """The trimmed cells of one Markdown table row, or None when the line is not a table row."""
    text = line.strip()
    if len(text) < 2 or not text.startswith("|") or not text.endswith("|"):
        return None
    return [cell.strip() for cell in CELL_SEPARATOR.split(text[1:-1])]


def _nodes_table(
    section: str, start: int, end: int
) -> tuple[int, list[list[str]]] | None:
    """The offset and body rows of the first ``Node | Executes | in | out`` table in a range."""
    position = start
    lines = section[start:end].splitlines(keepends=True)
    for index, line in enumerate(lines):
        if tuple(_cells(line) or ()) == NODES_HEADER:
            rows = []
            for row in lines[index + 2 :]:
                cells = _cells(row)
                if cells is None:
                    break
                rows.append(cells)
            return position, rows
        position += len(line)
    return None


def _normalized(text: str | None) -> str:
    return " ".join((text or "").split())


def part_problems(spec: GraphSpec, topology: dict) -> list[str]:
    """Problems with the State, Nodes and Edges parts of ``spec``; empty when they are complete.

    The parts must each appear once, in order, before the diagram, in an implementation-role
    document; State and Edges must say something; the Nodes table must sit between the Nodes and
    Edges labels, name exactly the compiled nodes other than ``__start__`` and ``__end__``, once
    each, and state the same ``in`` and ``out`` state as each node's diagram label.
    """
    problems: list[str] = []
    if spec.role != "implementation":
        problems.append(
            f"is in a {spec.role or 'role-less'} document, not an implementation-role document"
        )
    parts = _parts(spec.section)
    for name in PARTS:
        if not parts[name]:
            problems.append(f"has no **{name}.** part before its diagram")
        elif len(parts[name]) > 1:
            problems.append(f"states its **{name}.** part more than once")
    if any(len(parts[name]) != 1 for name in PARTS):
        return problems
    (state, state_text), (nodes, _), (edges, edges_text) = (
        parts[name][0] for name in PARTS
    )
    if not state < nodes < edges:
        problems.append("must state its State, Nodes and Edges parts in that order")
    if not state_text:
        problems.append("**State.** part names no channel or record")
    if not edges_text:
        problems.append("**Edges.** part does not say how the next node is chosen")
    table = _nodes_table(spec.section, nodes, len(spec.section))
    if table is None or not nodes < table[0] < edges:
        problems.append(
            "needs a 'Node | Executes | in | out' table between its Nodes and Edges parts"
        )
        return problems
    compiled = [node for node in topology["nodes"] if node not in BOUNDARY]
    listed: dict[str, list[str]] = {}
    for cells in table[1]:
        if len(cells) != len(NODES_HEADER):
            problems.append(f"Nodes row {' | '.join(cells)!r} does not have four cells")
            continue
        name = cells[0]
        if len(name) < 3 or name[0] != "`" or name[-1] != "`":
            problems.append(f"Nodes row {name!r} must name its node in backticks")
            continue
        name = name[1:-1]
        if name in listed:
            problems.append(f"Nodes table lists {name} twice")
        listed[name] = cells
    if set(listed) != set(compiled):
        problems.append(
            f"Nodes table differs: table-only {sorted(set(listed) - set(compiled))}, "
            f"compiled-only {sorted(set(compiled) - set(listed))}"
        )
    for name, cells in listed.items():
        if name not in spec.nodes:
            continue
        _, inputs, outputs = _state_lines(spec.nodes[name])
        if (_normalized(cells[2]), _normalized(cells[3])) != (
            _normalized(inputs),
            _normalized(outputs),
        ):
            problems.append(
                f"Nodes row {name} states in {cells[2]!r} and out {cells[3]!r}, "
                f"but its diagram label states in {inputs!r} and out {outputs!r}"
            )
    return problems


def section_anchor(spec: GraphSpec) -> str | None:
    """The explicit ``{#anchor}`` of the heading that opens a Graph Spec's section, if any."""
    heading = spec.section.split("\n", 1)[0]
    match = ANCHOR.search(heading) if HEADING.match(heading) else None
    return match.group(1) if match else None


def linked_targets(reading: Reading) -> set[tuple[str, str]]:
    """The document path and fragment of every Markdown link with a fragment in one reading."""
    base = posixpath.dirname(reading.path)
    return {
        (
            posixpath.normpath(posixpath.join(base, target))
            if target
            else reading.path,
            fragment,
        )
        for target, fragment in LINK.findall(reading.body)
    }


def link_problems(spec: GraphSpec, documents: Iterable[Reading]) -> list[str]:
    """Problems when no module-role document of the Graph Spec's owner links to its anchor.

    The Operation a Graph realizes is explained in its owner's reading, and that explanation must
    lead the reader to the exact Graph Spec rather than to an enclosing section or another page.
    """
    anchor = section_anchor(spec)
    if anchor is None:
        return [
            "heading needs an explicit {#anchor} that its owner's reading can link to"
        ]
    if any(
        document.owner == spec.owner and (spec.path, anchor) in linked_targets(document)
        for document in documents
    ):
        return []
    return [f"is not linked as #{anchor} from any module-role document of {spec.owner}"]


def _imports_functional_api(node: ast.AST) -> TypeGuard[ast.Import | ast.ImportFrom]:
    """Whether one import statement names ``langgraph.func`` or a member of it."""
    if isinstance(node, ast.Import):
        return any(
            alias.name == FUNCTIONAL_API or alias.name.startswith(FUNCTIONAL_API + ".")
            for alias in node.names
        )
    if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
        if node.module == FUNCTIONAL_API or node.module.startswith(
            FUNCTIONAL_API + "."
        ):
            return True
        return node.module == "langgraph" and any(
            alias.name == "func" for alias in node.names
        )
    return False


def functional_api_imports(
    root: Path | str, roots: tuple[str, ...] = SOURCE_ROOTS
) -> tuple[tuple[str, int, str], ...]:
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
                line = problem.lineno if problem.lineno is not None else 0
                hits.append((posix, line, "file cannot be parsed"))
                continue
            for node in ast.walk(tree):
                if _imports_functional_api(node):
                    hits.append((posix, node.lineno, ast.unparse(node)))
    return tuple(hits)


def graph_spec_findings(
    repository: SpecRepository, catalog: dict | None = None
) -> tuple[Finding, ...]:
    """Compare every bound Graph diagram with its compiled Graph; every catalog Graph needs one Spec.

    The same pass refuses every catalog Graph that is not a compiled ``StateGraph`` and every
    source file that imports the Functional API.
    """
    from langgraph.graph.state import CompiledStateGraph

    from .graph_catalog import catalog as default_catalog
    from .graph_catalog import topology as compiled_topology

    catalog = default_catalog() if catalog is None else catalog
    findings: list[Finding] = []
    compiled: dict[str, object] = {}
    for name, build in sorted(catalog.items()):
        graph = build()
        if isinstance(graph, CompiledStateGraph):
            compiled[name] = graph
        else:
            findings.append(
                Finding(
                    "CONCORDE-GRAPH-004",
                    "error",
                    ".concorde/specs.json",
                    f"compiled Graph {name} is a {type(graph).__name__}, not a StateGraph of the Graph API",
                    "Build every Graph with StateGraph; the Functional API (entrypoint, task) is not admitted.",
                )
            )
    for path, line, statement in functional_api_imports(repository.root):
        findings.append(
            Finding(
                "CONCORDE-GRAPH-005",
                "error",
                path,
                f"imports LangGraph's Functional API: {statement}",
                "Express control flow as StateGraph nodes and edges; langgraph.func is not admitted.",
                line=line,
            )
        )
    try:
        specs = graph_specs(repository)
    except DiagramError as problem:
        return (
            *findings,
            Finding(
                "CONCORDE-GRAPH-002",
                "error",
                ".concorde/specs.json",
                str(problem),
                "Use the Mermaid flowchart node and edge forms the Graph Spec convention defines.",
            ),
        )
    module_readings: tuple[Reading, ...] | None = None
    bound: dict[str, list[GraphSpec]] = {}
    for spec in specs:
        bound.setdefault(spec.graph, []).append(spec)
    for name, entries in sorted(bound.items()):
        if name not in catalog:
            for spec in entries:
                findings.append(
                    Finding(
                        "CONCORDE-GRAPH-001",
                        "error",
                        spec.path,
                        f"Graph diagram binds unknown Graph {name}",
                        "Bind the diagram to a compiled Graph name from the Graph catalog.",
                    )
                )
            continue
        if len(entries) > 1:
            for spec in entries:
                findings.append(
                    Finding(
                        "CONCORDE-GRAPH-001",
                        "error",
                        spec.path,
                        f"Graph {name} has more than one bound diagram",
                        "Keep exactly one Graph Spec diagram per compiled Graph.",
                    )
                )
            continue
        spec = entries[0]
        if name not in compiled:
            continue
        shape = compiled_topology(compiled[name])
        for problem in compare(spec, shape):
            findings.append(
                Finding(
                    "CONCORDE-GRAPH-003",
                    "error",
                    spec.path,
                    f"Graph Spec {name}: {problem}",
                    "Make the diagram's nodes, edges, conditions and state labels match the compiled Graph.",
                )
            )
        for problem in part_problems(spec, shape):
            findings.append(
                Finding(
                    "CONCORDE-GRAPH-006",
                    "error",
                    spec.path,
                    f"Graph Spec {name} {problem}",
                    "State the Graph's **State.**, **Nodes.** and **Edges.** parts in order in an "
                    "implementation-role document, with a Nodes table naming every compiled node "
                    "and the same in/out state as its diagram label.",
                )
            )
        if module_readings is None:
            module_readings = readings(repository)
        for problem in link_problems(spec, module_readings):
            findings.append(
                Finding(
                    "CONCORDE-GRAPH-007",
                    "error",
                    spec.path,
                    f"Graph Spec {name} {problem}",
                    "Explain the Operation that runs this Graph in its owner's module-role reading "
                    "and link that explanation to the Graph Spec's heading anchor.",
                )
            )
    for name in sorted(set(catalog) - set(bound)):
        findings.append(
            Finding(
                "CONCORDE-GRAPH-001",
                "error",
                ".concorde/specs.json",
                f"compiled Graph {name} has no Graph Spec diagram",
                "Add a Mermaid flowchart bound with '%% graph: <name>' to the owning Module's documents.",
            )
        )
    return tuple(findings)
