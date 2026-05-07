"""Voter Model implementation using Mesa for emergence ground truth."""

from dataclasses import dataclass
import numpy as np
import networkx as nx
import mesa
from mesa.discrete_space import Network, OrthogonalMooreGrid, CellAgent


@dataclass
class VoterModelConfig:
    n_agents: int = 100
    n_opinions: int = 2
    network: str = "complete"
    seed: int = 42
    ws_k: int = 4
    ws_p: float = 0.3


class VoterAgent(CellAgent):
    def __init__(self, model, opinion: int):
        super().__init__(model)
        self.opinion = opinion

    def step(self):
        neighbors = [a for a in self.cell.neighborhood.agents if a is not self]
        if neighbors:
            chosen = self.model.random.choice(neighbors)
            self.opinion = chosen.opinion


class VoterModel:
    def __init__(self, config: VoterModelConfig):
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self.step_count = 0
        self._trajectory: list[dict[int, float]] = []

        self.model = mesa.Model(seed=config.seed)
        n = config.n_agents

        if config.network == "complete":
            G = nx.complete_graph(n)
            self.grid = Network(G, random=self.model.random)
        elif config.network == "grid":
            side = int(np.ceil(np.sqrt(n)))
            self.grid = OrthogonalMooreGrid((side, side), torus=True, random=self.model.random)
        else:
            G = nx.watts_strogatz_graph(n, config.ws_k, config.ws_p, seed=config.seed)
            self.grid = Network(G, random=self.model.random)

        opinions = self.rng.integers(0, config.n_opinions, size=n)
        for i, cell in enumerate(self.grid.all_cells):
            if i >= n:
                break
            agent = VoterAgent(self.model, opinion=int(opinions[i]))
            agent.move_to(cell)

        self._trajectory.append(self.get_opinion_distribution())

    def run(self, steps: int):
        for _ in range(steps):
            agents = list(self.grid.all_cells.agents)
            self.model.random.shuffle(agents)
            for agent in agents:
                agent.step()
            self.step_count += 1
            self._trajectory.append(self.get_opinion_distribution())

    def get_opinion_distribution(self) -> dict[int, float]:
        agents = list(self.grid.all_cells.agents)
        n = len(agents)
        if n == 0:
            return {}
        counts: dict[int, int] = {}
        for a in agents:
            counts[a.opinion] = counts.get(a.opinion, 0) + 1
        return {k: v / n for k, v in sorted(counts.items())}

    def get_trajectory(self) -> list[dict[int, float]]:
        return self._trajectory
