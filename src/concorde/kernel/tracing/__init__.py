"""Tracing: the trace nodes every level of work leaves, their layout, locks and reading.

``layout`` gives every folder and lock file, ``node`` writes a node's ``trace.json``, ``locks``
takes the locks under ``.concorde/locks/``, ``reader`` finds and walks nodes, ``retention``
removes what the Tracing configuration allows, and ``command`` is ``concorde trace``.
"""
