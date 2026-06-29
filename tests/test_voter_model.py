import pytest
from circe.abm.voter_model import VoterModel, VoterModelConfig


def test_voter_model_runs():
    config = VoterModelConfig(n_agents=100, n_opinions=2, network="complete", seed=42)
    model = VoterModel(config)
    model.run(steps=50)
    assert model.step_count == 50


def test_voter_model_converges_on_complete_graph():
    config = VoterModelConfig(n_agents=50, n_opinions=2, network="complete", seed=42)
    model = VoterModel(config)
    model.run(steps=500)
    opinions = model.get_opinion_distribution()
    dominant = max(opinions.values())
    assert dominant > 0.8


def test_voter_model_trajectory():
    config = VoterModelConfig(n_agents=100, n_opinions=3, network="complete", seed=42)
    model = VoterModel(config)
    model.run(steps=100)
    trajectory = model.get_trajectory()
    assert len(trajectory) == 101
    assert all(abs(sum(t.values()) - 1.0) < 1e-6 for t in trajectory)


def test_voter_model_grid_slower_convergence():
    config_complete = VoterModelConfig(n_agents=100, n_opinions=2, network="complete", seed=42)
    config_grid = VoterModelConfig(n_agents=100, n_opinions=2, network="grid", seed=42)
    m1 = VoterModel(config_complete)
    m2 = VoterModel(config_grid)
    m1.run(steps=200)
    m2.run(steps=200)
    dom_complete = max(m1.get_opinion_distribution().values())
    dom_grid = max(m2.get_opinion_distribution().values())
    assert dom_complete >= dom_grid - 0.1
