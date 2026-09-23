"""The trusted runtime context of a LangGraph Operation; never a State channel."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class OperationRuntimeContext:
    """Trusted, invocation-local LangGraph Runtime context.

    A Graph's model node reaches its Agent only through ``launcher``, the trusted native Agent
    service an embedding caller supplies; nothing in caller-controlled State can supply one.
    """

    launcher: Callable[[dict], dict] | None = None
