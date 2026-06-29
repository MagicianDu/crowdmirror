import pytest
from circe.schema import (
    ChoiceSet, Alternative, PersonaSpec, ScenarioSpec,
    BehaviorTrace, CounterfactualQuery, GroundTruth,
)


def test_scenario_spec_creation():
    alt_a = Alternative(id="train", attributes={"price": 100, "time": 60})
    alt_b = Alternative(id="car", attributes={"price": 50, "time": 90})
    choice_set = ChoiceSet(alternatives=[alt_a, alt_b])
    persona = PersonaSpec(segment="commuter", demographics={"age": 35, "income": "medium"})
    scenario = ScenarioSpec(
        choice_set=choice_set,
        persona=persona,
        context={"trip_purpose": "work"},
    )
    assert len(scenario.choice_set.alternatives) == 2
    assert scenario.persona.segment == "commuter"


def test_counterfactual_query():
    query = CounterfactualQuery(
        base_scenario_id="s1",
        intervention={"price": 120},
        target_variable="choice_probs",
    )
    assert query.intervention["price"] == 120


def test_ground_truth_with_counterfactual():
    gt = GroundTruth(
        scenario_id="s1",
        factual_probs={"train": 0.6, "car": 0.4},
        counterfactual_probs={"train": 0.45, "car": 0.55},
        ate=-0.15,
    )
    assert gt.ate == pytest.approx(-0.15)
