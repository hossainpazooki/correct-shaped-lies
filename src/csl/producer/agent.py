"""The model-driven producer (DSPy over an API model).

Implements the same :class:`~csl.producer.base.Producer` protocol as the scripted adversary, so it
drops straight into the sweep. ``dspy`` and an LM are required only to *use* it — importing this
module does not require either. Configure an LM (e.g. an Anthropic model via API) before producing,
or pass one in.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from csl.domain.base import Submission
from csl.producer.injection import build_side_brief, extract_code

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.domain.base import Domain, Task
    from csl.producer.base import Tier


class DSPyProducer:
    """A producer backed by a DSPy module over an LM."""

    def __init__(self, domain: "Domain", lm=None, module=None, thresholds: dict | None = None) -> None:
        import dspy

        from csl.producer.signatures import make_produce_signature

        self.domain = domain
        self.thresholds = thresholds
        if lm is not None:
            dspy.configure(lm=lm)
        self.module = module or dspy.ChainOfThought(make_produce_signature())

    def produce(self, task: "Task", tier: "Tier") -> Submission:
        side_brief = build_side_brief(self.domain, task, tier, self.thresholds)
        prediction = self.module(
            overt_prompt=task.overt_prompt,
            public_spec=json.dumps(task.public_spec),
            side_brief=side_brief,
        )
        return Submission(code=extract_code(prediction.submission))
