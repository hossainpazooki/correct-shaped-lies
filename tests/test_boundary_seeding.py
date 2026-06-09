"""W1-3: the no-leakage seed discipline (train stream disjoint from measure stream)."""

from __future__ import annotations

from csl.seeding import TRAIN_SEED_OFFSET, measure_seed, train_seed


def test_train_and_measure_streams_are_disjoint():
    base = 42
    n = 8  # a generous sweep length
    measure = {measure_seed(base, i) for i in range(n)}
    train = {train_seed(base, i) for i in range(n)}
    assert measure.isdisjoint(train)


def test_train_offset_is_large_enough_to_not_collide():
    # As long as the sweep is shorter than the offset, the two arithmetic streams cannot overlap.
    assert TRAIN_SEED_OFFSET >= 1000
    base = 0
    for i in range(TRAIN_SEED_OFFSET):
        assert measure_seed(base, i) != train_seed(base, 0)
