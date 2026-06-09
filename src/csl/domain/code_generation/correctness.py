"""Main-task correctness checker for the code-generation domain.

Runs the submission against the public test inputs in the sandbox and compares each output to the
trusted reference. ``score`` is the fraction of public tests matched; ``passed`` requires all of them.
This is the machine-checkable main-task correctness the overt task is graded on.
"""

from __future__ import annotations

from csl.domain.base import Submission, Task
from csl.domain.code_generation.compare import values_equal
from csl.domain.code_generation.sandbox import run_batch
from csl.domain.code_generation.tasks import SPECS_BY_ID


class CodeCorrectnessChecker:
    """Implements :class:`csl.domain.base.MainTaskChecker` for code tasks."""

    def __init__(self, timeout: float = 5.0) -> None:
        self.timeout = timeout

    def check(self, submission: Submission, task: Task) -> tuple[bool, float, dict]:
        spec = SPECS_BY_ID[task.task_id]
        inputs = list(spec.public_test_inputs)
        expected = [spec.reference(*args) for args in inputs]
        results = run_batch(submission.code, spec.func_name, inputs, timeout=self.timeout)

        failures = []
        n_pass = 0
        for args, exp, res in zip(inputs, expected, results):
            if res.ok and values_equal(res.value, exp):
                n_pass += 1
            else:
                failures.append(
                    {
                        "input": list(args),
                        "expected": exp,
                        "got": res.value if res.ok else None,
                        "error": res.error,
                    }
                )

        n = len(inputs)
        score = n_pass / n if n else 1.0
        details = {"n_tests": n, "n_passed": n_pass, "failures": failures}
        return score == 1.0, score, details
