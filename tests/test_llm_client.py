from unittest.mock import patch

from circe.llm_client import LLMClient, LLMClientConfig


def test_openai_compatible_client_defaults_to_lm_studio_key():
    with patch("openai.OpenAI") as openai_cls:
        LLMClient(LLMClientConfig(base_url="http://127.0.0.1:1234/v1"))

    openai_cls.assert_called_once_with(
        base_url="http://127.0.0.1:1234/v1",
        api_key="lm-studio",
    )


def test_openrouter_client_reads_api_key_from_environment(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")

    with patch("openai.OpenAI") as openai_cls:
        LLMClient(LLMClientConfig(base_url="https://openrouter.ai/api/v1"))

    openai_cls.assert_called_once_with(
        base_url="https://openrouter.ai/api/v1",
        api_key="test-openrouter-key",
    )


def test_openrouter_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    try:
        LLMClient(LLMClientConfig(base_url="https://openrouter.ai/api/v1"))
    except ValueError as exc:
        assert "OPENROUTER_API_KEY" in str(exc)
    else:
        raise AssertionError("expected missing OpenRouter API key to fail")


def test_deepseek_client_reads_api_key_from_environment(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")

    with patch("openai.OpenAI") as openai_cls:
        LLMClient(LLMClientConfig(base_url="https://api.deepseek.com"))

    openai_cls.assert_called_once_with(
        base_url="https://api.deepseek.com",
        api_key="test-deepseek-key",
    )


def test_deepseek_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    try:
        LLMClient(LLMClientConfig(base_url="https://api.deepseek.com"))
    except ValueError as exc:
        assert "DEEPSEEK_API_KEY" in str(exc)
    else:
        raise AssertionError("expected missing DeepSeek API key to fail")
