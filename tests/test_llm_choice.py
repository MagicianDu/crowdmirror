import pytest
import json
from unittest.mock import patch, MagicMock
from circe.simulator.llm_choice import LLMChoiceSimulator, SimulatorConfig


@pytest.fixture
def mock_anthropic():
    """Mock the anthropic client to avoid real API calls in tests."""
    with patch("circe.simulator.llm_choice.anthropic") as mock:
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '{"train": 0.3, "swissmetro": 0.5, "car": 0.2}'
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 20
        mock.Anthropic.return_value.messages.create.return_value = mock_response
        yield mock


def test_simulator_creation():
    config = SimulatorConfig(model="claude-haiku-4-5-20251001", max_tokens=100)
    sim = LLMChoiceSimulator(config)
    assert sim.config.model == "claude-haiku-4-5-20251001"


def test_simulator_predict_probs(mock_anthropic):
    config = SimulatorConfig(model="claude-haiku-4-5-20251001")
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


def test_simulator_uses_custom_system_prompt(mock_anthropic):
    config = SimulatorConfig(model="claude-haiku-4-5-20251001")
    sim = LLMChoiceSimulator(config)
    sim.system_prompt = "Custom system prompt for testing"
    sim.predict_probs(
        segment="student",
        demographics={},
        alternatives=["bus", "walk"],
        attributes={"bus": {"time": 20}, "walk": {"time": 40}},
        context={},
    )
    call_kwargs = mock_anthropic.Anthropic.return_value.messages.create.call_args[1]
    assert call_kwargs["system"] == "Custom system prompt for testing"


def test_simulator_tracks_token_usage(mock_anthropic):
    config = SimulatorConfig(model="claude-haiku-4-5-20251001")
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


def test_simulator_handles_malformed_json(mock_anthropic):
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = 'Here are the probs: {"a": 0.6, "b": 0.4}'
    mock_response.usage.input_tokens = 50
    mock_response.usage.output_tokens = 30
    mock_anthropic.Anthropic.return_value.messages.create.return_value = mock_response

    config = SimulatorConfig(model="claude-haiku-4-5-20251001")
    sim = LLMChoiceSimulator(config)
    probs = sim.predict_probs(
        segment="x", demographics={},
        alternatives=["a", "b"],
        attributes={"a": {"x": 1}, "b": {"x": 2}},
        context={},
    )
    assert abs(sum(probs.values()) - 1.0) < 1e-6
