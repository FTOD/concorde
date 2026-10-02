"""The Operation catalog: every Operation name and where its provider lives."""

from __future__ import annotations

import importlib

# name -> "module:attribute" of the provider object; imported only when the Operation runs.
CATALOG: dict[str, str] = {
    "understand": "concorde.method.understanding.operation:UNDERSTAND",
    "plan_review": "concorde.method.understanding.plan_review:PLAN_REVIEW",
    "specify": "concorde.method.specification.operation:SPECIFY",
    "implement": "concorde.method.implementation.operation:IMPLEMENT",
    "test": "concorde.method.implementation.operation:TEST",
    "spec_review": "concorde.method.spec_review.operation:SPEC_REVIEW",
    "spec_panel": "concorde.method.spec_review.panel:SPEC_PANEL",
    "code_review": "concorde.method.code_review.operation:CODE_REVIEW",
    "survey": "concorde.method.adoption.survey:SURVEY",
    "code_to_spec": "concorde.method.adoption.code_to_spec:CODE_TO_SPEC",
}


def provider(name: str):
    """The provider object of a catalog Operation, as the part that provides it registers it;
    KeyError for an unknown name."""
    module, attribute = CATALOG[name].split(":")
    return getattr(importlib.import_module(module), attribute)


__all__ = ["CATALOG", "provider"]
