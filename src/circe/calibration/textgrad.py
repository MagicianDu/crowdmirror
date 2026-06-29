"""TextGrad engine: generates text feedback on prompt performance and proposes edits.

The core idea: instead of numerical gradients, we use an LLM to analyze
why a prompt is producing incorrect predictions and suggest specific edits.
This is the "text gradient" — a natural language description of how to
improve the prompt to reduce the causal loss.
"""

from dataclasses import dataclass, field
from circe.llm_client import LLMClient, LLMClientConfig
from circe.calibration.loss import CausalLossResult


@dataclass
class TextGradConfig:
    model: str = "google/gemma-4-31b"
    max_tokens: int = 4000
    temperature: float = 0.3
    provider: str = "openai"
    base_url: str | None = None
    timeout_seconds: float | None = None


@dataclass
class GradientStep:
    iteration: int
    feedback: str
    edited_prompt: str
    loss_before: float
    raw_response: str = ""


TEXTGRAD_SYSTEM = """\
You are a prompt optimization engine. Your job is to improve a choice simulation \
prompt so that it produces more accurate predictions.

You will receive:
1. The current system prompt used for choice simulation
2. Loss metrics showing how poorly the prompt is performing
3. Examples of predictions that were wrong

Your task:
1. Analyze WHY the prompt produces incorrect predictions
2. Identify specific causal reasoning errors (e.g., ignoring price sensitivity, \
wrong trade-off weights, missing demographic effects)
3. Produce an improved version of the prompt

Format your response EXACTLY as:
FEEDBACK: [your analysis of what's wrong and why]

EDITED PROMPT: [the complete improved prompt, ready to use as-is]"""


TEXTGRAD_USER_TEMPLATE = """\
## Current Prompt
{current_prompt}

## Loss Metrics
- Total loss: {total_loss:.4f}
- Calibration error (ECE): {ece:.4f}
- Counterfactual error (ATE MAE): {ate_mae:.4f}

## Error Examples
{examples_text}

Analyze the errors and produce an improved prompt."""


class TextGradEngine:
    def __init__(self, config: TextGradConfig | None = None):
        self.config = config or TextGradConfig()
        self.client = LLMClient(LLMClientConfig(
            provider=self.config.provider,
            base_url=self.config.base_url,
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            timeout_seconds=self.config.timeout_seconds,
        ))
        self._iteration = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def generate_gradient(
        self,
        current_prompt: str,
        loss_result: CausalLossResult,
        error_examples: list[dict],
    ) -> GradientStep:
        examples_text = self._format_examples(error_examples)
        user_msg = TEXTGRAD_USER_TEMPLATE.format(
            current_prompt=current_prompt,
            total_loss=loss_result.total_loss,
            ece=loss_result.ece,
            ate_mae=loss_result.ate_mae,
            examples_text=examples_text,
        )

        response = self.client.chat(system=TEXTGRAD_SYSTEM, user=user_msg)
        self.total_input_tokens += response.input_tokens
        self.total_output_tokens += response.output_tokens

        raw = response.content
        feedback, edited_prompt = self._parse_response(raw, current_prompt)

        step = GradientStep(
            iteration=self._iteration,
            feedback=feedback,
            edited_prompt=edited_prompt,
            loss_before=loss_result.total_loss,
            raw_response=raw,
        )
        self._iteration += 1
        return step

    def _format_examples(self, examples: list[dict]) -> str:
        if not examples:
            return "(no specific examples provided)"
        lines = []
        for i, ex in enumerate(examples):
            lines.append(f"Example {i+1}:")
            lines.append(f"  Scenario: {ex.get('scenario', 'N/A')}")
            lines.append(f"  Predicted: {ex.get('predicted', {})}")
            lines.append(f"  Ground truth: {ex.get('ground_truth', {})}")
        return "\n".join(lines)

    def _parse_response(self, raw: str, fallback_prompt: str) -> tuple[str, str]:
        feedback = ""
        edited_prompt = fallback_prompt

        if "FEEDBACK:" in raw:
            parts = raw.split("EDITED PROMPT:", 1)
            feedback = parts[0].replace("FEEDBACK:", "").strip()
            if len(parts) > 1:
                edited_prompt = parts[1].strip()

        return feedback, edited_prompt
