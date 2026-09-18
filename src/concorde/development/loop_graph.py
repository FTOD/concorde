"""The executable development topology, shared with Concorde's own documentation.

This factory performs no project access or WorkerProfile execution. Node functions and the resume
entry are supplied by the admitted invocation; conditional outcomes remain host decisions, and
every node states its own transition by returning a LangGraph ``Command``. The Graph's state is
typed: ``output`` carries the last stage's typed response data, ``result`` a terminal failure
envelope, and ``artifacts`` accumulates review references across stages through a reducer, so no
node smuggles routing or evidence through untyped output fields.
"""

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


def merge_artifacts(current: list[dict], update: list[dict]) -> list[dict]:
    """Reducer for artifact references: the newest reference per artifact id wins, order kept."""
    merged = {item["id"]: item for item in current or ()}
    merged.update({item["id"]: item for item in update or ()})
    return list(merged.values())


class DevelopmentState(TypedDict, total=False):
    route: str
    output: dict
    result: dict
    artifacts: Annotated[list[dict], merge_artifacts]


STAGE_NODES = (
    "specify_loop",
    "plan",
    "tasks",
    "implement",
    "validate",
    "review_code",
    "ready",
)


def loop_successors(
    *, include_specify: bool, entry: str, has_code: bool
) -> dict[str, str]:
    # Retain the factory argument for callers of loop_graph; the child now selects authoring.
    nodes = ["specify_loop", "plan", "tasks", "implement", "validate"]
    if has_code:
        nodes.append("review_code")
    nodes.append("ready")
    successors = dict(zip(nodes, nodes[1:], strict=False))
    successors["specify_loop"] = entry
    return successors


def loop_destinations(
    name: str, successors: dict[str, str], *, dynamic: bool
) -> tuple[str, ...]:
    """Every node a stage may hand over to; a stop ends the Graph through ``summarize``."""
    destinations = [successors[name]] if name in successors else []
    if dynamic and name == "specify_loop":
        destinations.extend(("tasks", "implement", "validate"))
    if dynamic and name == "validate":
        destinations.append("ready")
    if name == "review_code":
        destinations.append("tasks")
    destinations.append("summarize" if dynamic else END)
    destinations.append(END)
    return tuple(dict.fromkeys(destinations))


def build_loop_graph(
    node_factory,
    *,
    include_specify: bool = True,
    entry: str = "plan",
    has_code: bool = True,
    dynamic: bool = False,
):
    successors = loop_successors(
        include_specify=include_specify, entry=entry, has_code=has_code
    )
    graph = StateGraph(DevelopmentState)
    for name in [*successors, "ready"]:
        graph.add_node(
            name,
            node_factory(name),
            destinations=loop_destinations(name, successors, dynamic=dynamic),
        )
    if dynamic:
        graph.add_node(
            "initialize", node_factory("initialize"), destinations=("specify_loop", END)
        )
        graph.add_node("summarize", node_factory("summarize"))
        graph.add_edge(START, "initialize")
        graph.add_edge("summarize", END)
    else:
        graph.add_edge(START, "specify_loop")
    return graph.compile(name="development_graph", checkpointer=False)


def stage_command(route: str, *, dynamic: bool = True, **update) -> Command:
    """The transition a stage node returns: its typed update plus the next node it selected."""
    goto = "summarize" if dynamic and route == END else route
    return Command(goto=goto, update=update)
