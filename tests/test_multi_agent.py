import pytest
import json
from unittest.mock import patch
from circe.simulator.multi_agent import (
    MultiAgentSimulator,
    MultiAgentConfig,
    AgentState,
)
from circe.llm_client import LLMResponse


@pytest.fixture
def mock_llm():
    """Mock LLMClient.chat to return opinion adoption JSON."""
    with patch("circe.llm_client.LLMClient.chat") as mock_chat:
        mock_chat.return_value = LLMResponse(
            content='{"new_opinion": 0}',
            input_tokens=80,
            output_tokens=10,
        )
        yield mock_chat


def test_multi_agent_config_defaults():
    config = MultiAgentConfig()
    assert config.n_agents == 100
    assert config.n_opinions == 2
    assert config.network == "complete"


def test_agent_state_creation():
    state = AgentState(agent_id=0, opinion=1)
    assert state.agent_id == 0
    assert state.opinion == 1


def test_simulator_initialization():
    config = MultiAgentConfig(n_agents=10, n_opinions=2, seed=42)
    sim = MultiAgentSimulator(config)
    assert len(sim.agents) == 10
    assert all(a.opinion in range(2) for a in sim.agents)


def test_simulator_builds_network():
    config = MultiAgentConfig(n_agents=10, network="watts_strogatz", seed=42)
    sim = MultiAgentSimulator(config)
    assert sim.graph.number_of_nodes() == 10
    assert sim.graph.number_of_edges() > 0


def test_simulator_step(mock_llm):
    config = MultiAgentConfig(n_agents=5, n_opinions=2, seed=42)
    sim = MultiAgentSimulator(config)
    sim.step()
    assert mock_llm.call_count == 5


def test_simulator_run(mock_llm):
    config = MultiAgentConfig(n_agents=5, n_opinions=2, seed=42)
    sim = MultiAgentSimulator(config)
    sim.run(steps=3)
    assert mock_llm.call_count == 15


def test_simulator_get_trajectory(mock_llm):
    config = MultiAgentConfig(n_agents=5, n_opinions=2, seed=42)
    sim = MultiAgentSimulator(config)
    sim.run(steps=2)
    traj = sim.get_trajectory()
    assert len(traj) == 3
    assert all(isinstance(t, dict) for t in traj)
    for t in traj:
        assert abs(sum(t.values()) - 1.0) < 1e-6


def test_simulator_get_opinion_distribution(mock_llm):
    config = MultiAgentConfig(n_agents=5, n_opinions=2, seed=42)
    sim = MultiAgentSimulator(config)
    dist = sim.get_opinion_distribution()
    assert abs(sum(dist.values()) - 1.0) < 1e-6


def test_simulator_interaction_prompt_is_mutable(mock_llm):
    config = MultiAgentConfig(n_agents=3, n_opinions=2, seed=42)
    sim = MultiAgentSimulator(config)
    sim.interaction_prompt = "Custom interaction prompt: {agent_id} {agent_opinion} {neighbor_opinions} {possible_opinions}"
    sim.step()
    call_args = mock_llm.call_args
    assert "Custom interaction prompt" in call_args[1]["user"]


def test_simulator_parses_opinion_from_response(mock_llm):
    mock_llm.return_value = LLMResponse(
        content='{"new_opinion": 1}',
        input_tokens=80,
        output_tokens=10,
    )
    config = MultiAgentConfig(n_agents=3, n_opinions=2, seed=0)
    sim = MultiAgentSimulator(config)
    sim.step()
    assert all(a.opinion == 1 for a in sim.agents)


def test_simulator_handles_malformed_response(mock_llm):
    mock_llm.return_value = LLMResponse(
        content='I think opinion 1 is best {"new_opinion": 1}',
        input_tokens=80,
        output_tokens=20,
    )
    config = MultiAgentConfig(n_agents=3, n_opinions=2, seed=0)
    sim = MultiAgentSimulator(config)
    sim.step()
    assert all(a.opinion in range(2) for a in sim.agents)
