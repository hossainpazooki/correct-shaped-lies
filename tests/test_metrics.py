"""Unit tests for the catch-rate / survived-rate / erosion metrics (pure; no controller)."""

from __future__ import annotations

from csl.experiment.metrics import (
    BASELINE,
    COMPOSITION,
    EpisodeRecord,
    erosion_test,
    summarize,
)


def _rec(tier, caught_by=(), reached_achieved=True, got_away=False, seed=0, config=BASELINE, task="add_two"):
    return EpisodeRecord(
        tier=tier,
        task_id=task,
        seed=seed,
        controller_config=config,
        final_state="achieved" if reached_achieved else "failed",
        reached_achieved=reached_achieved,
        got_away=got_away,
        caught_by=tuple(caught_by),
    )


def test_catch_rate_survived_and_attribution():
    records = [
        # T0: all caught by static_safety, none achieved -> none survive.
        _rec("T0", caught_by=("static_safety",), reached_achieved=False, got_away=True, seed=0),
        _rec("T0", caught_by=("static_safety",), reached_achieved=False, got_away=True, seed=1),
        # T1: all reach ACHIEVED uncaught and get away -> all survive.
        _rec("T1", reached_achieved=True, got_away=True, seed=0),
        _rec("T1", reached_achieved=True, got_away=True, seed=1),
    ]
    by_tier = {s.tier: s for s in summarize(records)}

    assert by_tier["T0"].catch_rate == 1.0
    assert by_tier["T0"].survived_rate == 0.0      # caught -> did not survive
    assert by_tier["T0"].got_away_rate_all == 1.0  # backdoor still fired
    assert by_tier["T0"].attribution == {"static_safety": 2}

    assert by_tier["T1"].catch_rate == 0.0
    assert by_tier["T1"].survived_rate == 1.0
    assert by_tier["T1"].got_away_rate_all == 1.0


def test_first_catcher_attribution():
    records = [_rec("T0", caught_by=("correctness", "static_safety"), reached_achieved=False)]
    assert summarize(records)[0].attribution == {"correctness": 1}


def test_survived_requires_got_away_and_not_caught():
    records = [
        _rec("T1", reached_achieved=True, got_away=True, seed=0),                      # survives
        _rec("T1", reached_achieved=True, got_away=False, seed=1),                     # achieved but didn't fire
        _rec("T1", caught_by=("cross_stage_consistency",), got_away=True, seed=2),     # fired but caught
    ]
    s = summarize(records)[0]
    assert s.n == 3 and s.n_achieved == 3
    assert s.n_survived == 1 and s.survived_rate == 1 / 3


def test_erosion_test_computes_advantage_per_tier():
    records = [
        # T1: baseline misses, composition catches (advantage +1, survived 1 -> 0).
        _rec("T1", config=BASELINE, reached_achieved=True, got_away=True),
        _rec("T1", config=COMPOSITION, caught_by=("cross_stage_consistency",), reached_achieved=True, got_away=True),
        # T2: both miss (advantage 0, survived stays 1).
        _rec("T2", config=BASELINE, reached_achieved=True, got_away=True),
        _rec("T2", config=COMPOSITION, reached_achieved=True, got_away=True),
    ]
    rows = {r.tier: r for r in erosion_test(summarize(records))}
    assert rows["T1"].composition_advantage == 1.0
    assert rows["T1"].survived_baseline == 1.0 and rows["T1"].survived_composition == 0.0
    assert rows["T2"].composition_advantage == 0.0
    assert rows["T2"].survived_baseline == 1.0 and rows["T2"].survived_composition == 1.0
