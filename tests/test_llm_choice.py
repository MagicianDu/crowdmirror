import pytest
import json
from unittest.mock import patch, MagicMock
from circe.simulator.llm_choice import LLMChoiceSimulator, SimulatorConfig
from circe.llm_client import LLMResponse


@pytest.fixture
def mock_llm():
    """Mock the LLMClient to avoid real API calls in tests."""
    with patch("circe.llm_client.LLMClient.chat") as mock_chat:
        mock_chat.return_value = LLMResponse(
            content='{"train": 0.3, "swissmetro": 0.5, "car": 0.2}',
            input_tokens=100,
            output_tokens=20,
        )
        yield mock_chat


def test_simulator_creation():
    config = SimulatorConfig(model="test-model", max_tokens=100)
    sim = LLMChoiceSimulator(config)
    assert sim.config.model == "test-model"


def test_simulator_predict_probs(mock_llm):
    config = SimulatorConfig(model="test-model")
    sim = LLMChoiceSimulator(config)
    probs = sim.predict_probs(
        segment="commuter",
        demographics={"age": 35, "income": "medium"},
        alternatives=["train", "swissmetro", "car"],
        attributes={
            "train": {"travel_time": 100, "cost": 50},
            "swissmetro": {"travel_time": 80, "cost": 60},
            "car": {"travel_time": 120, "cost": 30},
        },
        context={"trip_purpose": "work"},
    )
    assert set(probs.keys()) == {"train", "swissmetro", "car"}
    assert abs(sum(probs.values()) - 1.0) < 1e-6


def test_simulator_uses_custom_system_prompt(mock_llm):
    config = SimulatorConfig(model="test-model")
    sim = LLMChoiceSimulator(config)
    sim.system_prompt = "Custom system prompt for testing"
    sim.predict_probs(
        segment="student",
        demographics={},
        alternatives=["bus", "walk"],
        attributes={"bus": {"time": 20}, "walk": {"time": 40}},
        context={},
    )
    call_args = mock_llm.call_args
    assert call_args[1]["system"] == "Custom system prompt for testing"


def test_simulator_tracks_token_usage(mock_llm):
    config = SimulatorConfig(model="test-model")
    sim = LLMChoiceSimulator(config)
    sim.predict_probs(
        segment="commuter",
        demographics={},
        alternatives=["a", "b"],
        attributes={"a": {"x": 1}, "b": {"x": 2}},
        context={},
    )
    assert sim.total_input_tokens == 100
    assert sim.total_output_tokens == 20


def test_simulator_handles_malformed_json(mock_llm):
    mock_llm.return_value = LLMResponse(
        content='Here are the probs: {"a": 0.6, "b": 0.4}',
        input_tokens=50,
        output_tokens=30,
    )
    config = SimulatorConfig(model="test-model")
    sim = LLMChoiceSimulator(config)
    probs = sim.predict_probs(
        segment="x", demographics={},
        alternatives=["a", "b"],
        attributes={"a": {"x": 1}, "b": {"x": 2}},
        context={},
    )
    assert abs(sum(probs.values()) - 1.0) < 1e-6
