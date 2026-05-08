"""Multi-agent LLM simulator for emergence dynamics.

Each agent sits on a network graph and queries an LLM to decide
whether to adopt a neighbor's opinion. The interaction_prompt (θ_ρ)
is mutable so TextGrad can optimize it.
"""

import json
import re
from dataclasses import dataclass
import numpy as np
import networkx as nx
from circe.llm_client import LLMClient, LLMClientConfig
from circe.simulator.interaction_templates import (
    INTERACTION_SYSTEM_PROMPT,
    INTERACTION_TEMPLATE,
    build_interaction_prompt,
)


@dataclass
class MultiAgentConfig:
    n_agents: int = 100
    n_opinions: int = 2
    network: str = "complete"
    seed: int = 42
    ws_k: int = 4
    ws_p: float = 0.3
    model: str = "google/gemma-4-31b"
    max_tokens: int = 150
    temperature: float = 0.0
    provider: str = "openai"
    base_url: str | None = None


@dataclass
class AgentState:
    agent_id: int
    opinion: int


class MultiAgentSimulator:
    def __init__(self, config: MultiAgentConfig | None = None):
        self.config = config or MultiAgentConfig()
        self.client = LLMClient(LLMClientConfig(
            provider=self.config.provider,
            base_url=self.config.base_url,
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        ))
        self.system_prompt = INTERACTION_SYSTEM_PROMPT
        self.interaction_prompt = INTERACTION_TEMPLATE
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self._call_count = 0

        self.graph = self._build_graph()

        rng = np.random.default_rng(self.config.seed)
        self.agents = [
            AgentState(agent_id=i, opinion=int(rng.integers(0, self.config.n_opinions)))
            for i in range(self.config.n_agents)
        ]

        self._trajectory: list[dict[int, float]] = [self.get_opinion_distribution()]

    def _build_graph(self) -> nx.Graph:
        n = self.config.n_agents
        if self.config.network == "complete":
            return nx.complete_graph(n)
        elif self.config.network == "grid":
            side = int(np.ceil(np.sqrt(n)))
            G = nx.grid_2d_graph(side, side)
            mapping = {node: i for i, node in enumerate(G.nodes())}
            G = nx.relabel_nodes(G, mapping)
            for node in list(G.nodes()):
                if node >= n:
                    G.remove_node(node)
            return G
        else:
            return nx.watts_strogatz_graph(
                n, self.config.ws_k, self.config.ws_p, seed=self.config.seed
            )

    def step(self):
        new_opinions = []
        for agent in self.agents:
            neighbors = list(self.graph.neighbors(agent.agent_id))
            neighbor_opinions = [self.agents[n].opinion for n in neighbors]

            user_prompt = self.interaction_prompt.format(
                agent_id=agent.agent_id,
                agent_opinion=agent.opinion,
                neighbor_opinions=neighbor_opinions,
                possible_opinions=", ".join(
                    str(o) for o in range(self.config.n_opinions)
                ),
            )

            response = self.client.chat(system=self.system_prompt, user=user_prompt)
            self.total_input_tokens += response.input_tokens
            self.total_output_tokens += response.output_tokens
            self._call_count += 1

            new_opinion = self._parse_opinion(response.content, agent.opinion)
            new_opinions.append(new_opinion)

        for agent, new_op in zip(self.agents, new_opinions):
            agent.opinion = new_op

        self._trajectory.append(self.get_opinion_distribution())

    def run(self, steps: int):
        for _ in range(steps):
            self.step()

    def get_trajectory(self) -> list[dict[int, float]]:
        return self._trajectory

    def get_opinion_distribution(self) -> dict[int, float]:
        n = len(self.agents)
        if n == 0:
            return {}
        counts: dict[int, int] = {}
        for a in self.agents:
            counts[a.opinion] = counts.get(a.opinion, 0) + 1
        for o in range(self.config.n_opinions):
            if o not in counts:
                counts[o] = 0
        return {k: v / n for k, v in sorted(counts.items())}

    def _parse_opinion(self, text: str, current_opinion: int) -> int:
        json_match = re.search(r"\{[^}]*\}", text)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                new_op = int(parsed.get("new_opinion", current_opinion))
                if 0 <= new_op < self.config.n_opinions:
                    return new_op
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        return current_opinion
