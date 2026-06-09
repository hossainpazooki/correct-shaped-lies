"""The producer agent: the adversary that emits a submission for an overt task while pursuing a
hidden objective.

Two implementations share one :class:`~csl.producer.base.Producer` protocol:

* :class:`~csl.producer.scripted.ScriptedProducer` — a deterministic, LLM-free programmatic adversary
  used as a reproducible baseline and to test the whole sweep without API access.
* :class:`~csl.producer.agent.DSPyProducer` — the model-driven adversary (DSPy/MIPROv2 over an API
  model), the realisation the spec emphasises. Imported lazily so the package works without ``dspy``.

The three adversary tiers (T0 naive, T1 eval-aware, T2 controller-aware) differ only in the
:class:`~csl.producer.context.TierContext` handed to the producer.
"""

from __future__ import annotations

from csl.producer.base import TIERS, Producer, Tier
from csl.producer.context import TierContext

__all__ = ["TIERS", "Producer", "Tier", "TierContext"]
