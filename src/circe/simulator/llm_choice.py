"""LLM-based choice simulator supporting Anthropic and OpenAI-compatible APIs."""

import json
import re
from dataclasses import dataclass, field
from circe.llm_client import LLMClient, LLMClientConfig
from circe.simulator.prompt_templates import build_choice_prompt, CHOICE_SYSTEM_PROMPT


@dataclass
class SimulatorConfig:
    model: str = "google/gemma-4-31b"
    max_tokens: int = 2000
    temperature: float = 0.0
    provider: str = "openai"
    base_url: str | None = None


class LLMChoiceSimulator:
    def __init__(self, config: SimulatorConfig | None = None):
        self.config = config or SimulatorConfig()
        self.client = LLMClient(LLMClientConfig(
            provider=self.config.provider,
            base_url=self.config.base_url,
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        ))
        self.system_prompt = CHOICE_SYSTEM_PROMPT
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self._call_count = 0

    def predict_probs(
        self,
        segment: str,
        demographics: dict,
        alternatives: list[str],
        attributes: dict[str, dict],
        context: dict,
    ) -> dict[str, float]:
        user_prompt = build_choice_prompt(
            segment=segment,
            demographics=demographics,
            alternatives=alternatives,
            attributes=attributes,
            context=context,
        )
        response = self.client.chat(system=self.system_prompt, user=user_prompt)
        self.total_input_tokens += response.input_tokens
        self.total_output_tokens += response.output_tokens
        self._call_count += 1

        probs = self._parse_probs(response.content, alternatives)
        return probs

    def _parse_probs(self, text: str, alternatives: list[str]) -> dict[str, float]:
        json_match = re.search(r"\{[^}]+\}", text)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                probs = {k: float(v) for k, v in parsed.items() if k in alternatives}
                total = sum(probs.values())
                if total > 0:
                    return {k: v / total for k, v in probs.items()}
            except (json.JSONDecodeError, ValueError):
                pass
        # Fallback: uniform distribution
        n = len(alternatives)
        return {alt: 1.0 / n for alt in alternatives}
