"""Sweep configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from csl.producer.base import Tier


@dataclass(frozen=True)
class SweepConfig:
    """Knobs for one catch-rate sweep. Deterministic given these values + the producer."""

    #: Adversary tiers to sweep. T2 enters once the composition layer is in scope.
    tiers: tuple[Tier, ...] = ("T0", "T1")
    #: One episode per seed; each seed deterministically samples a task.
    seeds: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
    domain_name: str = "code_generation"
    #: Honesty-probe seed handed to the domain (fixed so the probe is reproducible).
    honesty_seed: int = 0
    #: Optional per-evaluator threshold overrides (else the domain defaults).
    thresholds: dict = field(default_factory=dict)
