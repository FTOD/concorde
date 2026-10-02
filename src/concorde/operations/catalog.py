"""The Operation catalog: every Operation name and where its provider lives."""

from __future__ import annotations

import importlib
from dataclasses import replace

# name -> "module:attribute" of the provider object; imported only when the Operation runs.
CATALOG: dict[str, str] = {
    "understand": "concorde.understanding.operation:UNDERSTAND",
    "plan_review": "concorde.understanding.plan_review:PLAN_REVIEW",
    "specify": "concorde.specification.operation:SPECIFY",
    "implement": "concorde.implementation.operation:IMPLEMENT",
    "test": "concorde.implementation.operation:TEST",
    "spec_review": "concorde.spec_review.operation:SPEC_REVIEW",
    "spec_panel": "concorde.spec_review.panel:SPEC_PANEL",
    "code_review": "concorde.code_review.operation:CODE_REVIEW",
    "survey": "concorde.adoption.survey:SURVEY",
    "code_to_spec": "concorde.adoption.code_to_spec:CODE_TO_SPEC",
}


def provider(name: str):
    """The provider object of a catalog Operation, the steps of one that launches workers
    preceded by the check of all its workers against the model map; KeyError for an unknown
    name."""
    from .admission import check_worker_models

    module, attribute = CATALOG[name].split(":")
    chosen = getattr(importlib.import_module(module), attribute)
    if chosen.task_type is None:
        return chosen
    return replace(chosen, steps=(check_worker_models, *chosen.steps))


__all__ = ["CATALOG", "provider"]
