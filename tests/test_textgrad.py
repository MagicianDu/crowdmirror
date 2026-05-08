import pytest
from unittest.mock import patch, MagicMock
from circe.calibration.textgrad import (
    TextGradEngine,
    TextGradConfig,
    GradientStep,
)
from circe.calibration.loss import CausalLossResult


@pytest.fixture
def mock_anthropic():
    with patch("circe.calibration.textgrad.anthropic") as mock:
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = (
            "FEEDBACK: The prompt does not emphasize cost sensitivity enough. "
            "Commuters with medium income are highly price-sensitive.\n\n"
            "EDITED PROMPT: You are simulating a cost-sensitive commuter..."
        )
        mock_response.usage.input_tokens = 500
        mock_response.usage.output_tokens = 200
        mock.Anthropic.return_value.messages.create.return_value = mock_response
        yield mock


def test_textgrad_engine_creation():
    config = TextGradConfig(model="claude-sonnet-4-6-20250514", max_tokens=1000)
    engine = TextGradEngine(config)
    assert engine.config.model == "claude-sonnet-4-6-20250514"


def test_generate_gradient(mock_anthropic):
    config = TextGradConfig(model="claude-sonnet-4-6-20250514")
    engine = TextGradEngine(config)

    current_prompt = "You are simulating a person choosing transport."
    loss_result = CausalLossResult(
        total_loss=0.35, l_fit=0.15, l_causal=0.20, ece=0.15, ate_mae=0.20
    )
    examples = [
        {
            "scenario": "commuter, age 35, medium income",
            "predicted": {"train": 0.4, "swissmetro": 0.4, "car": 0.2},
            "ground_truth": {"train": 0.3, "swissmetro": 0.5, "car": 0.2},
        }
    ]

    step = engine.generate_gradient(
        current_prompt=current_prompt,
        loss_result=loss_result,
        error_examples=examples,
    )
    assert isinstance(step, GradientStep)
    assert len(step.feedback) > 0
    assert len(step.edited_prompt) > 0
    assert step.edited_prompt != current_prompt


def test_gradient_step_has_metadata(mock_anthropic):
    config = TextGradConfig(model="claude-sonnet-4-6-20250514")
    engine = TextGradEngine(config)

    step = engine.generate_gradient(
        current_prompt="Original prompt",
        loss_result=CausalLossResult(
            total_loss=0.5, l_fit=0.2, l_causal=0.3, ece=0.2, ate_mae=0.3
        ),
        error_examples=[],
    )
    assert step.iteration >= 0
    assert step.loss_before == 0.5
