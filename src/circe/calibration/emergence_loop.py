"""Emergence calibration loop: Voter Model ground truth → LLM sim → EDM → TextGrad.

Two-phase loop:
1. Generate Voter Model ground truth (known emergence dynamics)
2. Run multi-agent LLM simulation with current θ_ρ
3. Compute EDM between ground truth and LLM sim
4. If EDM > threshold: use TextGrad to optimize θ_ρ
5. Repeat until convergence or patience exhausted
"""

from dataclasses import dataclass, field
from circe.abm.voter_model import VoterModel, VoterModelConfig
from circe.abm.emergence_stats import compute_emergence_stats, EmergenceStats
from circe.simulator.multi_agent import MultiAgentSimulator, MultiAgentConfig
from circe.simulator.interaction_templates import INTERACTION_TEMPLATE
from circe.calibration.edm import compute_edm, EDMResult
from circe.calibration.textgrad import TextGradEngine, TextGradConfig, GradientStep
from circe.calibration.loss import CausalLossResult


EMERGENCE_TEXTGRAD_SYSTEM = """\
You are a prompt optimization engine for multi-agent social simulation. Your job \
is to improve an interaction prompt so that the LLM-simulated agents produce \
emergence dynamics (entropy decay, polarization, convergence) that match a known \
ground truth from a Voter Model.

You will receive:
1. The current interaction prompt template used by each agent
2. Emergence metrics showing how the LLM simulation differs from ground truth
3. Specific trajectory comparisons

Your task:
1. Analyze WHY the interaction prompt produces wrong emergence dynamics
2. Identify specific issues (e.g., agents too stubborn, too conformist, ignoring \
network structure, wrong social pressure modeling)
3. Produce an improved interaction prompt template

The template MUST contain these placeholders: {agent_id}, {agent_opinion}, \
{neighbor_opinions}, {possible_opinions}

Format your response EXACTLY as:
FEEDBACK: [your analysis of what's wrong and why]

EDITED PROMPT: [the complete improved template, ready to use as-is]"""


@dataclass
class EmergenceCalibrationConfig:
    n_agents: int = 20
    n_opinions: int = 2
    network: str = "complete"
    n_steps: int = 10
    seed: int = 42
    max_iterations: int = 5
    patience: int = 3
    edm_threshold: float = 0.05
    model: str = "google/gemma-4-31b"
    provider: str = "openai"
    base_url: str | None = None
    update_mode: str = "asynchronous"
    textgrad_model: str = "google/gemma-4-31b"
    textgrad_temperature: float = 0.3
    initial_prompt: str | None = None


@dataclass
class EmergenceCalibrationResult:
    best_prompt: str
    best_edm: float
    initial_edm: float
    final_edm: float
    n_iterations: int
    history: list[dict]


class EmergenceCalibrationLoop:
    def __init__(self, config: EmergenceCalibrationConfig):
        self.config = config
        self.ground_truth_stats: EmergenceStats | None = None
        self.textgrad = TextGradEngine(TextGradConfig(
            model=config.textgrad_model,
            max_tokens=4000,
            temperature=config.textgrad_temperature,
            provider=config.provider,
            base_url=config.base_url,
        ))
        self.textgrad_system = EMERGENCE_TEXTGRAD_SYSTEM

    def run(self) -> EmergenceCalibrationResult:
        self.ground_truth_stats = self._generate_ground_truth()

        current_prompt = self.config.initial_prompt or INTERACTION_TEMPLATE
        best_prompt = current_prompt
        best_edm = float("inf")
        history: list[dict] = []
        no_improve_count = 0

        for iteration in range(self.config.max_iterations):
            predicted_stats = self._run_llm_simulation(current_prompt)
            edm_result = compute_edm(self.ground_truth_stats, predicted_stats)
            edm_score = edm_result.edm_score

            record = {
                "iteration": iteration,
                "edm_score": edm_score,
                "d_macro": edm_result.d_macro,
                "prompt": current_prompt,
            }
            history.append(record)

            if edm_score < best_edm:
                best_edm = edm_score
                best_prompt = current_prompt
                no_improve_count = 0
            else:
                no_improve_count += 1

            if edm_score <= self.config.edm_threshold:
                break

            if no_improve_count >= self.config.patience:
                break

            loss_result = CausalLossResult(
                total_loss=edm_score,
                l_fit=edm_result.d_macro,
                l_causal=0.0,
                ece=edm_result.d_macro,
                ate_mae=0.0,
            )
            error_examples = self._build_error_examples(
                self.ground_truth_stats, predicted_stats
            )

            step = self.textgrad.generate_gradient(
                current_prompt=current_prompt,
                loss_result=loss_result,
                error_examples=error_examples,
            )
            current_prompt = step.edited_prompt

        initial_edm = history[0]["edm_score"] if history else 0.0
        final_edm = history[-1]["edm_score"] if history else 0.0

        return EmergenceCalibrationResult(
            best_prompt=best_prompt,
            best_edm=best_edm,
            initial_edm=initial_edm,
            final_edm=final_edm,
            n_iterations=len(history),
            history=history,
        )

    def _generate_ground_truth(self) -> EmergenceStats:
        vm_config = VoterModelConfig(
            n_agents=self.config.n_agents,
            n_opinions=self.config.n_opinions,
            network=self.config.network,
            seed=self.config.seed,
        )
        vm = VoterModel(vm_config)
        vm.run(steps=self.config.n_steps)
        return compute_emergence_stats(vm.get_trajectory())

    def _run_llm_simulation(self, interaction_prompt: str) -> EmergenceStats:
        sim_config = MultiAgentConfig(
            n_agents=self.config.n_agents,
            n_opinions=self.config.n_opinions,
            network=self.config.network,
            seed=self.config.seed,
            model=self.config.model,
            provider=self.config.provider,
            base_url=self.config.base_url,
            update_mode=self.config.update_mode,
        )
        sim = MultiAgentSimulator(sim_config)
        sim.interaction_prompt = interaction_prompt
        sim.run(steps=self.config.n_steps)
        return compute_emergence_stats(sim.get_trajectory())

    def _build_error_examples(
        self, true_stats: EmergenceStats, pred_stats: EmergenceStats
    ) -> list[dict]:
        examples = []
        examples.append({
            "scenario": "entropy trajectory",
            "predicted": {
                "initial": f"{pred_stats.initial_entropy:.3f}",
                "final": f"{pred_stats.final_entropy:.3f}",
            },
            "ground_truth": {
                "initial": f"{true_stats.initial_entropy:.3f}",
                "final": f"{true_stats.final_entropy:.3f}",
            },
        })
        examples.append({
            "scenario": "polarization",
            "predicted": {"final_polarization": f"{pred_stats.final_polarization:.3f}"},
            "ground_truth": {"final_polarization": f"{true_stats.final_polarization:.3f}"},
        })
        examples.append({
            "scenario": "convergence",
            "predicted": {"convergence_step": str(pred_stats.convergence_step)},
            "ground_truth": {"convergence_step": str(true_stats.convergence_step)},
        })
        return examples
