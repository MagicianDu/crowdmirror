"""Unified LLM client supporting Anthropic and OpenAI-compatible APIs."""

from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int


@dataclass
class LLMClientConfig:
    provider: str = "openai"  # "anthropic" or "openai"
    base_url: str | None = None  # for OpenAI-compatible (e.g. http://localhost:1234/v1)
    model: str = "google/gemma-4-31b"
    max_tokens: int = 2000
    temperature: float = 0.0
    timeout_seconds: float | None = None


class LLMClient:
    def __init__(self, config: LLMClientConfig):
        self.config = config
        if config.provider == "anthropic":
            import anthropic
            kwargs = {}
            if config.timeout_seconds is not None:
                kwargs["timeout"] = config.timeout_seconds
            self.client = anthropic.Anthropic(**kwargs)
        else:
            from openai import OpenAI
            kwargs = {
                "base_url": config.base_url or "http://localhost:1234/v1",
                "api_key": "lm-studio",
            }
            if config.timeout_seconds is not None:
                kwargs["timeout"] = config.timeout_seconds
            self.client = OpenAI(**kwargs)

    def chat(self, system: str, user: str) -> LLMResponse:
        if self.config.provider == "anthropic":
            return self._chat_anthropic(system, user)
        return self._chat_openai(system, user)

    def _chat_anthropic(self, system: str, user: str) -> LLMResponse:
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return LLMResponse(
            content=response.content[0].text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    def _chat_openai(self, system: str, user: str) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        choice = response.choices[0].message
        content = choice.content or ""
        return LLMResponse(
            content=content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
        )
