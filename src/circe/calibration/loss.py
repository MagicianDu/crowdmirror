"""Causal loss function: L = alpha * L_fit(ECE) + gamma * L_causal(ATE error).

L_fit measures calibration quality via Expected Calibration Error.
L_causal measures counterfactual accuracy via mean absolute ATE error.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class CausalLossResult:
    total_loss: float
    l_fit: float
    l_causal: float
    ece: float
    ate_mae: float


def compute_ece(
    predicted_probs: list[float],
    actual_outcomes: list[float],
    n_bins: int = 10,
) -> float:
    preds = np.array(predicted_probs, dtype=float)
    actuals = np.array(actual_outcomes, dtype=float)
    if len(preds) != len(actuals):
        raise ValueError("predicted_probs and actual_outcomes must have the same length")
    if len(preds) == 0:
        return 0.0
    if np.any((preds < 0.0) | (preds > 1.0)):
        raise ValueError("predicted probabilities must be in [0, 1]")
    if np.any((actuals < 0.0) | (actuals > 1.0)):
        raise ValueError("actual outcomes must be in [0, 1]")

    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        lower = bin_edges[i]
        upper = bin_edges[i + 1]
        if i == 0:
            mask = (preds >= lower) & (preds <= upper)
        else:
            mask = (preds > lower) & (preds <= upper)
        if mask.sum() == 0:
            continue
        bin_conf = preds[mask].mean()
        bin_target = actuals[mask].mean()
        ece += mask.sum() / len(preds) * abs(bin_target - bin_conf)
    return float(ece)


def compute_ate_error(
    true_ates: list[float],
    predicted_ates: list[float],
) -> float:
    return float(np.mean(np.abs(np.array(true_ates) - np.array(predicted_ates))))


def compute_causal_loss(
    predicted_probs: list[float],
    actual_outcomes: list[float],
    true_ates: list[float],
    predicted_ates: list[float],
    alpha: float = 1.0,
    gamma: float = 1.0,
    n_bins: int = 10,
) -> CausalLossResult:
    ece = compute_ece(predicted_probs, actual_outcomes, n_bins)
    ate_mae = compute_ate_error(true_ates, predicted_ates)
    l_fit = ece
    l_causal = ate_mae
    total = alpha * l_fit + gamma * l_causal
    return CausalLossResult(
        total_loss=total,
        l_fit=l_fit,
        l_causal=l_causal,
        ece=ece,
        ate_mae=ate_mae,
    )
