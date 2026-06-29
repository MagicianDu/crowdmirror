import pytest
import numpy as np
from circe.calibration.loss import (
    compute_ece,
    compute_ate_error,
    compute_causal_loss,
    CausalLossResult,
)


def test_ece_perfect_calibration():
    predicted_probs = [0.9, 0.8, 0.7, 0.2, 0.1]
    actual_outcomes = [1, 1, 1, 0, 0]  # perfectly calibrated
    ece = compute_ece(predicted_probs, actual_outcomes, n_bins=5)
    assert ece < 0.20  # not exactly 0 due to binning, but low


def test_ece_terrible_calibration():
    predicted_probs = [0.9, 0.9, 0.9, 0.9, 0.9]
    actual_outcomes = [0, 0, 0, 0, 0]  # always wrong
    ece = compute_ece(predicted_probs, actual_outcomes, n_bins=5)
    assert ece > 0.7


def test_ate_error_perfect():
    true_ates = [0.1, -0.2, 0.05, -0.15]
    pred_ates = [0.1, -0.2, 0.05, -0.15]
    error = compute_ate_error(true_ates, pred_ates)
    assert error == pytest.approx(0.0, abs=1e-10)


def test_ate_error_nonzero():
    true_ates = [0.1, -0.2, 0.05]
    pred_ates = [0.15, -0.1, 0.0]
    error = compute_ate_error(true_ates, pred_ates)
    assert error > 0
    expected = np.mean(np.abs(np.array(true_ates) - np.array(pred_ates)))
    assert error == pytest.approx(expected)


def test_causal_loss_combines_components():
    result = compute_causal_loss(
        predicted_probs=[0.7, 0.3, 0.8, 0.2],
        actual_outcomes=[1, 0, 1, 0],
        true_ates=[0.1, -0.2],
        predicted_ates=[0.12, -0.18],
        alpha=1.0,
        gamma=1.0,
    )
    assert isinstance(result, CausalLossResult)
    assert result.total_loss > 0
    assert result.l_fit >= 0
    assert result.l_causal >= 0
    assert result.total_loss == pytest.approx(result.l_fit * 1.0 + result.l_causal * 1.0)


def test_causal_loss_weights():
    result_high_causal = compute_causal_loss(
        predicted_probs=[0.5, 0.5],
        actual_outcomes=[1, 0],
        true_ates=[0.1],
        predicted_ates=[0.5],  # large ATE error
        alpha=1.0,
        gamma=10.0,
    )
    result_low_causal = compute_causal_loss(
        predicted_probs=[0.5, 0.5],
        actual_outcomes=[1, 0],
        true_ates=[0.1],
        predicted_ates=[0.5],
        alpha=1.0,
        gamma=0.1,
    )
    assert result_high_causal.total_loss > result_low_causal.total_loss


def test_ece_penalizes_zero_probability_true_event():
    ece = compute_ece([0.0], [1.0], n_bins=10)
    assert ece == pytest.approx(1.0)


def test_ece_accepts_soft_probability_targets():
    ece = compute_ece([0.4, 0.35, 0.25], [0.4, 0.35, 0.25], n_bins=10)
    assert ece == pytest.approx(0.0, abs=1e-12)


def test_ece_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="same length"):
        compute_ece([0.5], [0.5, 0.5])
