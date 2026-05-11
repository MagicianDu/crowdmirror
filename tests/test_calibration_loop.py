import pytest
from unittest.mock import patch, MagicMock, call
from circe.calibration.loop import (
    CalibrationLoop,
    CalibrationConfig,
    CalibrationResult,
)
from circe.dgp.counterfactual import CounterfactualPair


def _make_pair(scenario_id: str, ate: float) -> CounterfactualPair:
    return CounterfactualPair(
        scenario_id=scenario_id,
        factual_attrs={"sm_cost": 0.6, "sm_tt": 0.8, "train_tt": 1.0,
                       "train_cost": 0.5, "train_he": 10, "sm_he": 5,
                       "car_tt": 1.2, "car_cost": 0.3},
        counterfactual_attrs={"sm_cost": 1.2, "sm_tt": 0.8, "train_tt": 1.0,
                              "train_cost": 0.5, "train_he": 10, "sm_he": 5,
                              "car_tt": 1.2, "car_cost": 0.3},
        intervention={"sm_cost_increase": 2.0},
        factual_probs={"train": 0.3, "swissmetro": 0.5, "car": 0.2},
        counterfactual_probs={"train": 0.4, "swissmetro": 0.35, "car": 0.25},
        ate=ate,
    )


@pytest.fixture
def sample_pairs():
    return [_make_pair(f"s{i}", -0.1 * (i + 1)) for i in range(10)]


@pytest.fixture
def mock_simulator():
    with patch("circe.calibration.loop.LLMChoiceSimulator") as mock_cls:
        instance = MagicMock()
        instance.predict_probs.return_value = {"train": 0.35, "swissmetro": 0.40, "car": 0.25}
        instance.system_prompt = "original prompt"
        instance._call_count = 0
        mock_cls.return_value = instance
        yield instance


@pytest.fixture
def mock_textgrad():
    with patch("circe.calibration.loop.TextGradEngine") as mock_cls:
        instance = MagicMock()
        from circe.calibration.textgrad import GradientStep
        instance.generate_gradient.return_value = GradientStep(
            iteration=0,
            feedback="Need more cost sensitivity",
            edited_prompt="Improved prompt emphasizing cost",
            loss_before=0.5,
        )
        mock_cls.return_value = instance
        yield instance


def test_calibration_loop_creation(sample_pairs):
    config = CalibrationConfig(max_iterations=5, patience=2)
    loop = CalibrationLoop(config=config, dataset=sample_pairs)
    assert loop.config.max_iterations == 5


def test_calibration_loop_runs(sample_pairs, mock_simulator, mock_textgrad):
    config = CalibrationConfig(max_iterations=3, patience=2)
    loop = CalibrationLoop(config=config, dataset=sample_pairs)
    result = loop.run()
    assert isinstance(result, CalibrationResult)
    assert len(result.history) <= 3
    assert result.best_prompt is not None
    assert result.best_loss is not None


def test_calibration_loop_early_stops(sample_pairs, mock_simulator, mock_textgrad):
    config = CalibrationConfig(max_iterations=10, patience=2)
    loop = CalibrationLoop(config=config, dataset=sample_pairs)
    result = loop.run()
    # With constant mock predictions, loss won't improve, so early stop at patience
    assert len(result.history) <= 4  # initial + patience iterations


def test_calibration_result_has_metrics(sample_pairs, mock_simulator, mock_textgrad):
    config = CalibrationConfig(max_iterations=2, patience=5)
    loop = CalibrationLoop(config=config, dataset=sample_pairs)
    result = loop.run()
    assert result.initial_loss is not None
    assert result.final_loss is not None
    assert result.n_iterations >= 1
    assert result.total_llm_calls >= 0


def test_evaluate_uses_soft_factual_probability_targets(mock_textgrad):
    pair = CounterfactualPair(
        scenario_id="soft-target",
        factual_attrs={"sm_cost": 0.6, "sm_tt": 0.8, "train_tt": 1.0,
                       "train_cost": 0.5, "train_he": 10, "sm_he": 5,
                       "car_tt": 1.2, "car_cost": 0.3},
        counterfactual_attrs={"sm_cost": 1.2, "sm_tt": 0.8, "train_tt": 1.0,
                              "train_cost": 0.5, "train_he": 10, "sm_he": 5,
                              "car_tt": 1.2, "car_cost": 0.3},
        intervention={"sm_cost_increase": 2.0},
        factual_probs={"train": 0.4, "swissmetro": 0.35, "car": 0.25},
        counterfactual_probs={"train": 0.45, "swissmetro": 0.25, "car": 0.30},
        ate=-0.10,
    )
    with patch("circe.calibration.loop.LLMChoiceSimulator") as mock_cls:
        instance = MagicMock()
        instance.predict_probs.side_effect = [
            {"train": 0.4, "swissmetro": 0.35, "car": 0.25},
            {"train": 0.45, "swissmetro": 0.25, "car": 0.30},
        ]
        instance.system_prompt = "prompt"
        instance._call_count = 2
        mock_cls.return_value = instance
        loop = CalibrationLoop(config=CalibrationConfig(max_iterations=1), dataset=[pair])
        loss_result, error_examples = loop._evaluate([pair])

    assert loss_result.ece == pytest.approx(0.0, abs=1e-12)
    assert loss_result.ate_mae == pytest.approx(0.0, abs=1e-12)
    assert error_examples == []
