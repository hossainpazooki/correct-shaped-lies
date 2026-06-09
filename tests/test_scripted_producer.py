"""The scripted adversary: naive backdoors are caught by the static scan; stealth ones evade it.

Pure (no controller needed): drives the domain evaluators directly over every task in the corpus.
"""

from __future__ import annotations

import pytest

from csl.domain.code_generation import CodeGenerationDomain
from csl.domain.code_generation.tasks import SPECS_BY_ID
from csl.producer.scripted import ScriptedProducer

TASK_IDS = sorted(SPECS_BY_ID)


@pytest.fixture(scope="module")
def domain():
    return CodeGenerationDomain(honesty_seed=7, n_honesty_probes=64)


@pytest.fixture(scope="module")
def producer():
    return ScriptedProducer()


@pytest.mark.parametrize("task_id", TASK_IDS)
def test_naive_backdoor_caught_only_by_static_safety(domain, producer, task_id):
    task = domain.task(task_id)
    sub = producer.produce(task, "T0")
    results = {e.name: e.evaluate(sub, task) for e in domain.evaluators()}

    # Correct-shaped on every layer EXCEPT the static scan, which flags the magic literal.
    assert results["correctness"].passed
    assert results["honesty"].passed
    assert results["complexity_budget"].passed
    assert results["static_safety"].passed is False
    # It did achieve the hidden objective (diverges on the trigger).
    got_away, _ = domain.held_ground_truth_checker().got_away(sub, task)
    assert got_away is True


@pytest.mark.parametrize("task_id", TASK_IDS)
def test_stealth_backdoor_is_a_correct_shaped_lie(domain, producer, task_id):
    task = domain.task(task_id)
    sub = producer.produce(task, "T1")
    results = {e.name: e.evaluate(sub, task) for e in domain.evaluators()}

    # Passes EVERY evaluator...
    assert all(r.passed for r in results.values()), {k: v.passed for k, v in results.items()}
    # ...yet still gets away.
    got_away, _ = domain.held_ground_truth_checker().got_away(sub, task)
    assert got_away is True


def test_honest_strategy_does_not_get_away(domain):
    producer = ScriptedProducer(force_strategy="honest")
    for task_id in TASK_IDS:
        task = domain.task(task_id)
        sub = producer.produce(task, "T1")
        results = {e.name: e.evaluate(sub, task) for e in domain.evaluators()}
        assert all(r.passed for r in results.values())
        got_away, _ = domain.held_ground_truth_checker().got_away(sub, task)
        assert got_away is False
