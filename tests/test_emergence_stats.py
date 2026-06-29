import pytest
from circe.abm.voter_model import VoterModel, VoterModelConfig
from circe.abm.emergence_stats import compute_emergence_stats, EmergenceStats


def test_compute_stats_from_trajectory():
    config = VoterModelConfig(n_agents=100, n_opinions=2, seed=42)
    model = VoterModel(config)
    model.run(steps=100)
    stats = compute_emergence_stats(model.get_trajectory())
    assert isinstance(stats, EmergenceStats)


def test_polarization_metric():
    config = VoterModelConfig(n_agents=100, n_opinions=2, seed=42)
    model = VoterModel(config)
    model.run(steps=100)
    stats = compute_emergence_stats(model.get_trajectory())
    assert 0 <= stats.final_polarization <= 1


def test_convergence_time():
    config = VoterModelConfig(n_agents=50, n_opinions=2, network="complete", seed=42)
    model = VoterModel(config)
    model.run(steps=500)
    stats = compute_emergence_stats(model.get_trajectory(), consensus_threshold=0.9)
    assert stats.convergence_step is not None
    assert stats.convergence_step <= 500


def test_entropy_decreases():
    config = VoterModelConfig(n_agents=100, n_opinions=3, seed=42)
    model = VoterModel(config)
    model.run(steps=200)
    stats = compute_emergence_stats(model.get_trajectory())
    assert stats.initial_entropy >= stats.final_entropy - 0.01
