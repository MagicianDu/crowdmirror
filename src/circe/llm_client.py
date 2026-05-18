"""Unified LLM client supporting Anthropic and OpenAI-compatible APIs."""

from dataclasses import dataclass
import os


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
            base_url = config.base_url or "http://localhost:1234/v1"
            kwargs = {
                "base_url": base_url,
                "api_key": _openai_compatible_api_key(base_url),
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


def _openai_compatible_api_key(base_url: str) -> str:
    if "openrouter.ai" in base_url:
        return _required_api_key(
            "OPENROUTER_API_KEY",
            provider_name="OpenRouter",
        )
    if "api.deepseek.com" in base_url:
        return _required_api_key(
            "DEEPSEEK_API_KEY",
            provider_name="DeepSeek",
        )
    return "lm-studio"


def _required_api_key(env_name: str, *, provider_name: str) -> str:
    api_key = os.environ.get(env_name)
    if not api_key:
        raise ValueError(
            f"{env_name} is required when base_url points to {provider_name}"
        )
    return api_key
