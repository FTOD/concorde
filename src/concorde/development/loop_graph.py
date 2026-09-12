"""Compatibility imports for callers that predate the Flow terminology."""
from .loop_flow import build_loop_flow, loop_successors

build_loop_graph = build_loop_flow
__all__ = ["build_loop_graph", "loop_successors"]
