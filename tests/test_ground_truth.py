import pytest
import numpy as np
from circe.evaluation.ground_truth import (
    evaluate_counterfactual_accuracy,
    evaluate_emergence_distortion,
    CounterfactualEvalResult,
    EmergenceEvalResult,
)
from circe.dgp.counterfactual import generate_counterfactual_dataset
from circe.abm.voter_model import VoterModel, VoterModelConfig
from circe.abm.emergence_stats import compute_emergence_stats


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
