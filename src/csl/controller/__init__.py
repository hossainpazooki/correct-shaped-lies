"""HTTP wiring between the Python harness and the Go lifecycle controller.

The Go controller gates VERIFYING -> ACHIEVED on ``all_passed()`` and calls back into the Python ML
service (:mod:`csl.controller.ml_service`) over ``/ml/evaluate`` to run each evaluator. The harness
(:func:`csl.controller.harness.running_stack`) starts both, and :func:`csl.controller.episode.run_episode`
drives one episode and returns a :class:`csl.trajectory.Trajectory`.
"""

from __future__ import annotations
