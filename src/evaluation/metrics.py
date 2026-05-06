"""
Evaluation metrics for the LLM Traveler Simulator.
Covers: fit, calibration, structural consistency, stability.
"""

from dataclasses import dataclass
import numpy as np
from typing import List, Dict, Optional


@dataclass
class EvalResult:
    log_loss: float
    brier_score: float
    ece: float
    mce: float
    monotonicity_violation_rate: float
    constraint_violation_rate: float
    substitution_violation_rate: float
    intra_seed_variance: float


def log_loss(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-15) -> float:
    y_pred = np.clip(y_pred, eps, 1 - eps)
    return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))


def brier_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return np.mean((y_pred - y_true) ** 2)


def expected_calibration_error(
    y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = 10
) -> float:
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (y_pred >= bin_boundaries[i]) & (y_pred < bin_boundaries[i + 1])
        if mask.sum() == 0:
            continue
        bin_acc = y_true[mask].mean()
        bin_conf = y_pred[mask].mean()
        ece += mask.sum() * abs(bin_acc - bin_conf)
    return ece / len(y_true)


def maximum_calibration_error(
    y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = 10
) -> float:
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    mce = 0.0
    for i in range(n_bins):
        mask = (y_pred >= bin_boundaries[i]) & (y_pred < bin_boundaries[i + 1])
        if mask.sum() == 0:
            continue
        bin_acc = y_true[mask].mean()
        bin_conf = y_pred[mask].mean()
        mce = max(mce, abs(bin_acc - bin_conf))
    return mce


def monotonicity_violation_rate(
    prices: np.ndarray, choice_probs: np.ndarray
) -> float:
    """Check: higher price should not increase choice probability (ceteris paribus)."""
    n = len(prices)
    violations = 0
    comparisons = 0
    sorted_idx = np.argsort(prices)
    for i in range(n - 1):
        for j in range(i + 1, n):
            if prices[sorted_idx[j]] > prices[sorted_idx[i]]:
                comparisons += 1
                if choice_probs[sorted_idx[j]] > choice_probs[sorted_idx[i]]:
                    violations += 1
    return violations / max(comparisons, 1)


def constraint_violation_rate(
    choices: List[Dict], hard_constraints: List[Dict]
) -> float:
    """Check: chosen option must satisfy all hard constraints."""
    violations = 0
    for choice in choices:
        for constraint in hard_constraints:
            field = constraint["field"]
            op = constraint["op"]
            val = constraint["value"]
            actual = choice.get(field)
            if actual is None:
                continue
            if op == "<=" and actual > val:
                violations += 1
            elif op == ">=" and actual < val:
                violations += 1
            elif op == "==" and actual != val:
                violations += 1
    return violations / max(len(choices) * len(hard_constraints), 1)


def intra_seed_variance(
    prob_samples: np.ndarray,
) -> float:
    """Variance across repeated runs with same input/seed."""
    return np.mean(np.var(prob_samples, axis=0))
