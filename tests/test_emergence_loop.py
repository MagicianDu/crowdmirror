import pytest
from unittest.mock import patch, MagicMock
from circe.calibration.emergence_loop import (
    EmergenceCalibrationLoop,
    EmergenceCalibrationConfig,
    EmergenceCalibrationResult,
)
from circe.calibration.textgrad import GradientStep
from circe.calibration.loss import CausalLossResult
from circe.llm_client import LLMResponse


@pytest.fixture
def mock_llm():
    """Mock LLMClient.chat for both simulator and TextGrad calls."""
    with patch("circe.llm_client.LLMClient.chat") as mock_chat:
        def side_effect(system="", user=""):
            if "optimization" in system.lower() or "improve" in system.lower():
                return LLMResponse(
                    content=(
                        "FEEDBACK: The interaction prompt needs stronger social "
                        "pressure modeling.\n\n"
                        "EDITED PROMPT: You are agent {agent_id} in a social network.\n"
                        "Your current opinion: {agent_opinion}\n"
                        "Your neighbors' opinions: {neighbor_opinions}\n"
                        "Possible opinions: {possible_opinions}\n"
                        "Social pressure is strong. Adopt the majority opinion. "
                        "Output JSON:"
                    ),
                    input_tokens=500,
                    output_tokens=200,
                )
            return LLMResponse(
                content='{"new_opinion": 0}',
                input_tokens=80,
                output_tokens=10,
            )
        mock_chat.side_effect = side_effect
        yield mock_chat


def test_emergence_calibration_config_defaults():
    config = EmergenceCalibrationConfig()
    assert config.n_agents == 20
    assert config.n_opinions == 2
    assert config.n_steps == 10
    assert config.max_iterations == 5
    assert config.patience == 3


def test_emergence_calibration_result_dataclass():
    result = EmergenceCalibrationResult(
        best_prompt="test",
        best_edm=0.1,
        initial_edm=0.5,
        final_edm=0.1,
        n_iterations=3,
        history=[],
    )
    assert result.best_edm == 0.1
    assert result.n_iterations == 3


def test_emergence_loop_creation():
    config = EmergenceCalibrationConfig(n_agents=10, n_steps=5)
    loop = EmergenceCalibrationLoop(config)
    assert loop.config.n_agents == 10


def test_emergence_loop_runs(mock_llm):
    config = EmergenceCalibrationConfig(
        n_agents=5,
        n_opinions=2,
        n_steps=3,
        max_iterations=2,
        patience=3,
        network="complete",
        seed=42,
    )
    loop = EmergenceCalibrationLoop(config)
    result = loop.run()
    assert isinstance(result, EmergenceCalibrationResult)
    assert result.best_prompt is not None
    assert result.best_edm >= 0.0
    assert result.n_iterations <= 2
    assert len(result.history) <= 2


def test_emergence_loop_early_stops(mock_llm):
    config = EmergenceCalibrationConfig(
        n_agents=5,
        n_opinions=2,
        n_steps=3,
        max_iterations=10,
        patience=2,
        seed=42,
    )
    loop = EmergenceCalibrationLoop(config)
    result = loop.run()
    assert result.n_iterations <= 4


def test_emergence_loop_uses_voter_model_ground_truth(mock_llm):
    config = EmergenceCalibrationConfig(
        n_agents=10,
        n_opinions=2,
        n_steps=5,
        max_iterations=1,
        seed=42,
    )
    loop = EmergenceCalibrationLoop(config)
    result = loop.run()
    assert loop.ground_truth_stats is not None
    assert loop.ground_truth_stats.initial_entropy > 0


def test_emergence_loop_edm_threshold(mock_llm):
    config = EmergenceCalibrationConfig(
        n_agents=5,
        n_opinions=2,
        n_steps=3,
        max_iterations=5,
        edm_threshold=999.0,
        seed=42,
    )
    loop = EmergenceCalibrationLoop(config)
    result = loop.run()
    assert result.n_iterations == 1


def test_emergence_config_carries_update_mode():
    config = EmergenceCalibrationConfig(update_mode="asynchronous")
    assert config.update_mode == "asynchronous"
