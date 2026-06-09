"""Compose the side brief handed to a model-driven producer.

The brief = the domain's hidden-objective instruction + the tier context block (eval suite for T1,
plus controller + composition knowledge for T2). The model-driven producer also receives the public
spec; it never receives held ground truth.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from csl.producer.context import TierContext

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.domain.base import Domain, Task
    from csl.producer.base import Tier


def build_side_brief(domain: "Domain", task: "Task", tier: "Tier", thresholds: dict | None = None) -> str:
    """Hidden-objective instruction plus the tier's oversight knowledge."""
    brief = domain.hidden_objective_brief(task, tier)
    context = TierContext.for_tier(tier, domain, thresholds).as_prompt_block()
    return brief if not context else f"{brief}\n\n{context}"


_FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL)


def extract_code(text: str) -> str:
    """Pull the Python source out of a model response, tolerating markdown fences."""
    if text is None:
        return ""
    match = _FENCE.search(text)
    return (match.group(1) if match else text).strip() + "\n"
