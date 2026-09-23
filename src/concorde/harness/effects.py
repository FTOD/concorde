"""The effect roles an Agent definition may read or write.

``spec-context`` is the bound Modules' Spec context, ``implementation`` the contents of the
selected Module's implementation files and ``references`` its external context.
"""

from __future__ import annotations

EFFECT_ROLES = frozenset({"spec-context", "implementation", "references"})
