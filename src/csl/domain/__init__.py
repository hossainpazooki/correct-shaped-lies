"""Domain-agnostic task interface and the concrete domains that implement it."""

from __future__ import annotations

from csl.domain.base import (
    Domain,
    HeldGroundTruthChecker,
    MainTaskChecker,
    Submission,
    Task,
)

__all__ = [
    "Domain",
    "HeldGroundTruthChecker",
    "MainTaskChecker",
    "Submission",
    "Task",
]
