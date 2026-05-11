"""Emergence Distortion Metric (EDM).

EDM = d_macro: a weighted combination of entropy MAE, polarization error,
and trajectory MSE. Uses evaluate_emergence_distortion from the evaluation
module as the underlying comparison engine.
"""

from dataclasses import dataclass
from circe.abm.emergence_stats import EmergenceStats
from circe.evaluation.ground_truth import evaluate_emergence_distortion


@dataclass
class EDMResult:
    d_macro: float
    edm_score: float


def compute_edm(
    true_stats: EmergenceStats,
    predicted_stats: EmergenceStats,
    weights: dict[str, float] | None = None,
) -> EDMResult:
    if weights is None:
        weights = {
            "entropy": 1.0,
            "polarization": 1.0,
            "trajectory": 1.0,
            "convergence": 0.25,
        }

    eval_result = evaluate_emergence_distortion(true_stats, predicted_stats)

    w_entropy = weights.get("entropy", 1.0)
    w_polarization = weights.get("polarization", 1.0)
    w_trajectory = weights.get("trajectory", 1.0)
    w_convergence = weights.get("convergence", 0.25)
    horizon = max(
        max(len(true_stats.entropy_trajectory), len(predicted_stats.entropy_trajectory)) - 1,
        1,
    )
    convergence_component = (eval_result.convergence_step_error or 0.0) / horizon

    total_weight = w_entropy + w_polarization + w_trajectory + w_convergence

    d_macro = (
        w_entropy * eval_result.entropy_mae
        + w_polarization * eval_result.polarization_error
        + w_trajectory * eval_result.trajectory_mse
        + w_convergence * convergence_component
    ) / total_weight

    return EDMResult(d_macro=d_macro, edm_score=d_macro)
