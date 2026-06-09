"""Type-strict value comparison for sandbox outputs.

Bare ``==``/``!=`` coerce across numeric/bool types in Python (``1 == True``, ``3.0 == 3``), which let
a backdoor return a wrong-typed value that still compares equal — undercounting got-away and leaving
the return-type contract unenforced. ``values_equal`` requires matching types: ``bool`` is distinct
from ``int``, and ``int`` from ``float``. It recurses through lists/dicts for completeness.
"""

from __future__ import annotations


def values_equal(a, b) -> bool:
    """True iff ``a`` and ``b`` are equal AND of the same JSON type (bool!=int, int!=float)."""
    # bool is a subclass of int — require both-or-neither bool.
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(values_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(values_equal(a[k], b[k]) for k in a)
    return a == b
