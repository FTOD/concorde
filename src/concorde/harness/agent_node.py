"""One Agent invocation as a LangGraph node whose state schema is the Agent's task contract.

An ``AgentNode`` binds one Agent to LangGraph directly: the node's input schema is generated from
the contract's admitted context type and its output schema from the contract's result type, so the
graph's state is the typed contract itself rather than an untyped routing dictionary. ``flow``
compiles that node into a one-node ``StateGraph`` the host executes and Studio can inspect; the
``launcher`` supplied at execution time runs the Pi worker and its admission checks and stays
outside the graph's public state. Inspection compiles the same factory with no launcher and never
starts a process.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from ..spec.typed_data import DATA_SCHEMAS, typed, validate_typed
from .agent_model import Agent


def typed_state(type_id: str, *, name: str | None = None) -> type:
    """A TypedDict whose keys are exactly the top-level fields of a registered typed value."""
    fields = {key: Any for key in DATA_SCHEMAS[type_id]["properties"]}
    return TypedDict(name or type_id.replace("-", "_"), fields, total=False)  # type: ignore[misc]


def state_schema(input_type: str, result_type: str, *, name: str) -> type:
    """The union of the context and result channels one Agent node reads and writes."""
    fields = {key: Any for key in DATA_SCHEMAS[input_type]["properties"]}
    fields.update({key: Any for key in DATA_SCHEMAS[result_type]["properties"]})
    return TypedDict(name, fields, total=False)  # type: ignore[misc]


Launcher = Callable[[dict], dict]


@dataclass(frozen=True)
class AgentNode:
    """Bind ``agent`` to a LangGraph node with its contract's typed input and output state."""

    agent: Agent

    @property
    def name(self) -> str:
        return self.agent.name

    @property
    def input_type(self) -> str:
        return self.agent.contract.context

    @property
    def result_type(self) -> str:
        return self.agent.contract.result

    @property
    def input_schema(self) -> type:
        return typed_state(self.input_type)

    @property
    def output_schema(self) -> type:
        return typed_state(self.result_type)

    def flow(self, launcher: Launcher | None = None):
        """Compile the one-node Flow; ``launcher`` maps the typed context to the typed result data.

        The node revalidates its input against the contract's context type and its output against
        its result type, so a launcher can neither admit an unexpected context nor return an
        unexpected result through the graph. Without a launcher the Flow is inspectable only.
        """
        input_type, result_type = self.input_type, self.result_type

        def invoke(state: dict) -> dict:
            if launcher is None:
                raise RuntimeError(f"AgentNode {self.name} was compiled for inspection only")
            context = typed(input_type, {key: value for key, value in dict(state).items()
                                         if key in DATA_SCHEMAS[input_type]["properties"]})
            return validate_typed(typed(result_type, launcher(context)), result_type)["data"]

        graph = StateGraph(state_schema(input_type, result_type, name=self.name.replace("-", "_")),
                           input_schema=self.input_schema, output_schema=self.output_schema)
        graph.add_node(self.agent.name, invoke)
        graph.add_edge(START, self.agent.name)
        graph.add_edge(self.agent.name, END)
        return graph.compile(name=self.name, checkpointer=False)

    def invoke(self, context: dict, launcher: Launcher) -> dict:
        """Run one invocation: the admitted typed context in, the validated typed result data out."""
        value = validate_typed(context, self.input_type)
        return self.flow(launcher).invoke(value["data"])
