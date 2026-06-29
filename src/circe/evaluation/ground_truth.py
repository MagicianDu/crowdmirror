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
    true_traj = true_stats.entropy_trajectory
    pred_traj = predicted_stats.entropy_trajectory
    if not true_traj or not pred_traj:
        raise ValueError("entropy trajectories must be non-empty")

    max_len = max(len(true_traj), len(pred_traj))
    true_padded = true_traj + [true_traj[-1]] * (max_len - len(true_traj))
    pred_padded = pred_traj + [pred_traj[-1]] * (max_len - len(pred_traj))
    entropy_mae = float(np.mean(
        np.abs(np.array(true_padded) - np.array(pred_padded))
    ))
    trajectory_mse = float(np.mean(
        (np.array(true_padded) - np.array(pred_padded))**2
    ))

    polarization_error = abs(true_stats.final_polarization - predicted_stats.final_polarization)

    if true_stats.convergence_step is None and predicted_stats.convergence_step is None:
        convergence_step_error = 0.0
    elif true_stats.convergence_step is None or predicted_stats.convergence_step is None:
        convergence_step_error = float(max(max_len - 1, 1))
    else:
        convergence_step_error = float(
            abs(true_stats.convergence_step - predicted_stats.convergence_step)
        )

    return EmergenceEvalResult(
        entropy_mae=entropy_mae,
        polarization_error=polarization_error,
        convergence_step_error=convergence_step_error,
        trajectory_mse=trajectory_mse,
    )
