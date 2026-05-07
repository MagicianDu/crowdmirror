"""Ground truth comparison harness for counterfactual and emergence evaluation."""

from dataclasses import dataclass
import numpy as np
from circe.abm.emergence_stats import EmergenceStats


@dataclass
class CounterfactualEvalResult:
    mae: float
    rmse: float
    correlation: float
    bias: float
    n_pairs: int


@dataclass
class EmergenceEvalResult:
    entropy_mae: float
    polarization_error: float
    convergence_step_error: float | None
    trajectory_mse: float


def evaluate_counterfactual_accuracy(
    true_ates: list[float],
    predicted_ates: list[float],
) -> CounterfactualEvalResult:
    true_arr = np.array(true_ates)
    pred_arr = np.array(predicted_ates)
    errors = pred_arr - true_arr
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors**2)))
    bias = float(np.mean(errors))
    if np.std(true_arr) > 0 and np.std(pred_arr) > 0:
        correlation = float(np.corrcoef(true_arr, pred_arr)[0, 1])
    else:
        correlation = 1.0 if mae == 0 else 0.0
    return CounterfactualEvalResult(
        mae=mae, rmse=rmse, correlation=correlation,
        bias=bias, n_pairs=len(true_ates),
    )


def evaluate_emergence_distortion(
    true_stats: EmergenceStats,
    predicted_stats: EmergenceStats,
) -> EmergenceEvalResult:
    entropy_mae = abs(true_stats.final_entropy - predicted_stats.final_entropy)
    polarization_error = abs(true_stats.final_polarization - predicted_stats.final_polarization)

    convergence_step_error = None
    if true_stats.convergence_step is not None and predicted_stats.convergence_step is not None:
        convergence_step_error = float(
            abs(true_stats.convergence_step - predicted_stats.convergence_step)
        )

    true_traj = true_stats.entropy_trajectory
    pred_traj = predicted_stats.entropy_trajectory
    min_len = min(len(true_traj), len(pred_traj))
    trajectory_mse = float(np.mean(
        (np.array(true_traj[:min_len]) - np.array(pred_traj[:min_len]))**2
    ))

    return EmergenceEvalResult(
        entropy_mae=entropy_mae,
        polarization_error=polarization_error,
        convergence_step_error=convergence_step_error,
        trajectory_mse=trajectory_mse,
    )
