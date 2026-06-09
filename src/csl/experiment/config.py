"""Sweep configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from csl.producer.base import Tier


@dataclass(frozen=True)
class SweepConfig:
    """Knobs for one catch-rate sweep. Deterministic given these values + the producer.

    The sweep is the full grid ``tiers x task_ids x seeds`` (every task is covered, not sampled). The
    seed is the episode seed: it drives the per-episode honesty probe set, so multiple seeds are
    independent honesty replications of the same (tier, task) cell.
    """

    #: Adversary tiers to sweep.
    tiers: tuple[Tier, ...] = ("T0", "T1", "T2")
    #: Episode/honesty seeds — replications per (tier, task).
    seeds: tuple[int, ...] = (0, 1, 2, 3, 4)
    #: Task ids to cover. ``None`` -> every task the domain exposes via ``task_ids()``.
    task_ids: tuple[str, ...] | None = None
    domain_name: str = "code_generation"
    #: Honesty-probe base seed handed to the domain (combined with the episode seed per episode).
    honesty_seed: int = 0
    #: Optional per-evaluator threshold overrides (else the domain defaults).
    thresholds: dict = field(default_factory=dict)
