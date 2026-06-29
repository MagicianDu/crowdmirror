import pytest
import numpy as np
from circe.evaluation.ground_truth import (
    evaluate_counterfactual_accuracy,
    evaluate_emergence_distortion,
    CounterfactualEvalResult,
    EmergenceEvalResult,
)
from circe.dgp.counterfactual import generate_counterfactual_dataset
from circe.abm.emergence_stats import EmergenceStats
from circe.abm.voter_model import VoterModel, VoterModelConfig
from circe.abm.emergence_stats import compute_emergence_stats


def _make_stats(
    entropy_trajectory,
    final_polarization=0.0,
    convergence_step=1,
) -> EmergenceStats:
    return EmergenceStats(
        initial_entropy=entropy_trajectory[0] if entropy_trajectory else 0.0,
        final_entropy=entropy_trajectory[-1] if entropy_trajectory else 0.0,
        final_polarization=final_polarization,
        convergence_step=convergence_step,
        opinion_trajectory=[],
        entropy_trajectory=entropy_trajectory,
    )


def test_perfect_counterfactual_prediction():
    pairs = generate_counterfactual_dataset(n_scenarios=20, n_interventions=2)
    predicted_ates = [p.ate for p in pairs]
    true_ates = [p.ate for p in pairs]
    result = evaluate_counterfactual_accuracy(true_ates, predicted_ates)
    assert isinstance(result, CounterfactualEvalResult)
    assert result.mae == pytest.approx(0.0, abs=1e-10)
    assert result.correlation == pytest.approx(1.0, abs=1e-6)


def test_noisy_counterfactual_prediction():
    pairs = generate_counterfactual_dataset(n_scenarios=50, n_interventions=2)
    true_ates = [p.ate for p in pairs]
    rng = np.random.default_rng(42)
    predicted_ates = [a + rng.normal(0, 0.05) for a in true_ates]
    result = evaluate_counterfactual_accuracy(true_ates, predicted_ates)
    assert result.mae > 0
    assert result.mae < 0.1
    assert result.correlation > 0.8


def test_emergence_distortion_perfect():
    config = VoterModelConfig(n_agents=100, n_opinions=2, seed=42)
    model = VoterModel(config)
    model.run(steps=100)
    true_stats = compute_emergence_stats(model.get_trajectory())
    result = evaluate_emergence_distortion(true_stats, true_stats)
    assert isinstance(result, EmergenceEvalResult)
    assert result.entropy_mae == pytest.approx(0.0, abs=1e-10)
    assert result.polarization_error == pytest.approx(0.0, abs=1e-10)


def test_emergence_distortion_reports_convergence_mismatch():
    config = VoterModelConfig(n_agents=50, n_opinions=2, seed=42)
    model = VoterModel(config)
    model.run(steps=20)
    stats_a = compute_emergence_stats(model.get_trajectory())
    stats_b = compute_emergence_stats(model.get_trajectory())
    stats_b.convergence_step = None
    result = evaluate_emergence_distortion(stats_a, stats_b)
    assert result.convergence_step_error is not None


def test_emergence_distortion_rejects_two_empty_entropy_trajectories():
    true_stats = _make_stats([])
    pred_stats = _make_stats([])
    with pytest.raises(ValueError, match="entropy trajectories must be non-empty"):
        evaluate_emergence_distortion(true_stats, pred_stats)


def test_emergence_distortion_rejects_one_empty_entropy_trajectory():
    true_stats = _make_stats([])
    pred_stats = _make_stats([1.0])
    with pytest.raises(ValueError, match="entropy trajectories must be non-empty"):
        evaluate_emergence_distortion(true_stats, pred_stats)


def test_emergence_distortion_pads_shorter_entropy_trajectory():
    true_stats = _make_stats([1.0])
    pred_stats = _make_stats([1.0, 0.0])
    result = evaluate_emergence_distortion(true_stats, pred_stats)
    assert result.entropy_mae > 0.0
    assert result.trajectory_mse > 0.0
