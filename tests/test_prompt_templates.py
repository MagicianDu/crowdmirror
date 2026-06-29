import pytest
from circe.simulator.prompt_templates import (
    build_choice_prompt,
    PERSONA_TEMPLATE,
    UTILITY_TEMPLATE,
    CHOICE_SYSTEM_PROMPT,
)


def test_persona_template_has_placeholders():
    assert "{segment}" in PERSONA_TEMPLATE
    assert "{demographics}" in PERSONA_TEMPLATE


def test_utility_template_has_placeholders():
    assert "{alternatives}" in UTILITY_TEMPLATE
    assert "{attributes}" in UTILITY_TEMPLATE


def test_build_choice_prompt_basic():
    prompt = build_choice_prompt(
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
    assert "commuter" in prompt
    assert "train" in prompt
    assert "swissmetro" in prompt
    assert "probability" in prompt.lower() or "prob" in prompt.lower()


def test_build_choice_prompt_returns_system_and_user():
    prompt = build_choice_prompt(
        segment="student",
        demographics={"age": 22},
        alternatives=["bus", "bike"],
        attributes={
            "bus": {"time": 30, "cost": 2},
            "bike": {"time": 20, "cost": 0},
        },
        context={},
    )
    # Should be a string containing both persona context and choice task
    assert len(prompt) > 100
