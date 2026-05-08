import pytest
from circe.simulator.interaction_templates import (
    INTERACTION_SYSTEM_PROMPT,
    INTERACTION_TEMPLATE,
    build_interaction_prompt,
)


def test_interaction_system_prompt_mentions_opinion():
    assert "opinion" in INTERACTION_SYSTEM_PROMPT.lower()
    assert "json" in INTERACTION_SYSTEM_PROMPT.lower()


def test_interaction_template_has_placeholders():
    assert "{agent_opinion}" in INTERACTION_TEMPLATE
    assert "{neighbor_opinions}" in INTERACTION_TEMPLATE
    assert "{possible_opinions}" in INTERACTION_TEMPLATE


def test_build_interaction_prompt_basic():
    prompt = build_interaction_prompt(
        agent_id=0,
        agent_opinion=1,
        neighbor_opinions=[0, 1, 0, 0],
        n_opinions=2,
    )
    assert "1" in prompt
    assert "0" in prompt
    assert len(prompt) > 50


def test_build_interaction_prompt_multi_opinion():
    prompt = build_interaction_prompt(
        agent_id=5,
        agent_opinion=2,
        neighbor_opinions=[0, 1, 2, 1, 0],
        n_opinions=3,
    )
    assert "0, 1, 2" in prompt or "0" in prompt
    assert "2" in prompt


def test_build_interaction_prompt_returns_string():
    result = build_interaction_prompt(
        agent_id=0,
        agent_opinion=0,
        neighbor_opinions=[1],
        n_opinions=2,
    )
    assert isinstance(result, str)
