"""Unit tests for the catch-rate metrics (pure; no controller)."""

from __future__ import annotations

from csl.experiment.metrics import EpisodeRecord, summarize


def _rec(tier, caught_by=(), reached_achieved=True, got_away=False, seed=0, task="add_two"):
    return EpisodeRecord(
        tier=tier,
        task_id=task,
        seed=seed,
        controller_config="baseline",
        final_state="achieved" if reached_achieved else "failed",
        reached_achieved=reached_achieved,
        got_away=got_away,
        caught_by=tuple(caught_by),
    )


def test_catch_rate_and_attribution():
    records = [
        # T0: all caught by static_safety, none achieved.
        _rec("T0", caught_by=("static_safety",), reached_achieved=False, got_away=True, seed=0),
        _rec("T0", caught_by=("static_safety",), reached_achieved=False, got_away=True, seed=1),
        # T1: all reach ACHIEVED and get away.
        _rec("T1", reached_achieved=True, got_away=True, seed=0),
        _rec("T1", reached_achieved=True, got_away=True, seed=1),
    ]
    by_tier = {s.tier: s for s in summarize(records)}

    assert by_tier["T0"].catch_rate == 1.0
    assert by_tier["T0"].attribution == {"static_safety": 2}
    assert by_tier["T0"].got_away_rate == 0.0  # no ACHIEVED episodes

    assert by_tier["T1"].catch_rate == 0.0
    assert by_tier["T1"].got_away_rate == 1.0  # all ACHIEVED episodes got away


def test_first_catcher_attribution():
    # Two evaluators flag it; attribution credits the first in evaluation order.
    records = [_rec("T0", caught_by=("correctness", "static_safety"), reached_achieved=False)]
    summary = summarize(records)[0]
    assert summary.attribution == {"correctness": 1}


def test_partial_got_away_among_achieved():
    records = [
        _rec("T1", reached_achieved=True, got_away=True, seed=0),
        _rec("T1", reached_achieved=True, got_away=False, seed=1),
        _rec("T1", caught_by=("honesty",), reached_achieved=False, got_away=True, seed=2),
    ]
    summary = summarize(records)[0]
    assert summary.n == 3
    assert summary.n_caught == 1
    assert summary.n_achieved == 2
    assert summary.got_away_rate == 0.5  # 1 of 2 achieved got away
