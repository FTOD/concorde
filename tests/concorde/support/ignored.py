"""The ignore rules an install of every part adds, for test projects that keep Concorde's local
state out of Git as an installed project does."""

from concorde.distribution.install import ignored
from concorde.distribution.parts import package_parts

TRACES = ignored(package_parts())
