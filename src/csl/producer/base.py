"""Producer protocol and the adversary tiers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover - typing only
    from csl.domain.base import Submission, Task

#: The three graded adversary tiers.
Tier = Literal["T0", "T1", "T2"]
TIERS: tuple[Tier, ...] = ("T0", "T1", "T2")


@runtime_checkable
class Producer(Protocol):
    """An adversary that produces a submission for a task at a given tier.

    The producer always pursues its hidden objective; the tier governs only how much it knows about
    the oversight stack (see :class:`csl.producer.context.TierContext`).
    """

    def produce(self, task: "Task", tier: "Tier") -> "Submission": ...
