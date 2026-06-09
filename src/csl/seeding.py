"""Seeding discipline — byte-identical per seed.

All randomness in the experiment flows through a single ``numpy.random.Generator(PCG64(seed))``,
the same discipline as ``upstream-label-correction/core/synthetic.py`` and
``closed-loop-default-detection/src/cldd/synthetic.py``. There is no use of ``random``, wallclock
time, or unseeded global state anywhere in the measured path, so two runs at the same seed produce
byte-identical trajectories and artifacts.

The ``TRAIN_SEED_OFFSET`` mirrors ``CLUELoop.train_seed_offset`` (=1000): adversary-optimization
("train") draws are taken from a seed stream disjoint from the measured ("measure") episodes, so the
optimizer can never tune against the exact trigger inputs it is later scored on. This is the
no-leakage rule the whole project rests on.
"""

from __future__ import annotations

from numpy.random import Generator, PCG64

#: Offset added to a measure seed to obtain the disjoint train seed stream.
TRAIN_SEED_OFFSET = 1000


def make_rng(seed: int) -> Generator:
    """Return a fresh single-stream generator for ``seed`` (byte-identical per seed)."""
    return Generator(PCG64(seed))


def measure_seed(base_seed: int, iteration: int) -> int:
    """Seed for the measured episode at ``iteration`` (the CLUE ``seed + iteration`` pattern)."""
    return base_seed + iteration


def train_seed(base_seed: int, iteration: int) -> int:
    """Seed for the disjoint train cohort/episode used during adversary optimization.

    Offset far enough that train seeds never collide with measure seeds across a sweep.
    """
    return base_seed + TRAIN_SEED_OFFSET + iteration
