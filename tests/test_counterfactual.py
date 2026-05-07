import pytest
from circe.dgp.counterfactual import generate_counterfactual_dataset, CounterfactualPair


def test_generates_pairs():
    pairs = generate_counterfactual_dataset(n_scenarios=50, n_interventions=3)
    assert len(pairs) == 50 * 3


def test_pair_has_factual_and_counterfactual():
    pairs = generate_counterfactual_dataset(n_scenarios=10, n_interventions=1)
    p = pairs[0]
    assert isinstance(p, CounterfactualPair)
    assert "swissmetro" in p.factual_probs
    assert "swissmetro" in p.counterfactual_probs
    assert p.ate is not None


def test_price_intervention_changes_probs():
    pairs = generate_counterfactual_dataset(
        n_scenarios=20, n_interventions=1, intervention_type="sm_cost_increase"
    )
    for p in pairs:
        assert p.counterfactual_probs["swissmetro"] <= p.factual_probs["swissmetro"] + 0.01
