"""The Operation catalog: every Operation name and where its provider lives."""

from __future__ import annotations

import importlib

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
    """The provider object of a catalog Operation; KeyError for an unknown name."""
    module, attribute = CATALOG[name].split(":")
    return getattr(importlib.import_module(module), attribute)


__all__ = ["CATALOG", "provider"]
