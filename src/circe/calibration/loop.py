"""Calibration loop orchestrator: simulate → evaluate → gradient → edit → repeat."""

from dataclasses import dataclass, field
import numpy as np
from circe.simulator.llm_choice import LLMChoiceSimulator, SimulatorConfig
from circe.calibration.textgrad import TextGradEngine, TextGradConfig, GradientStep
from circe.calibration.loss import compute_causal_loss, CausalLossResult
from circe.dgp.counterfactual import CounterfactualPair


@dataclass
class CalibrationConfig:
    max_iterations: int = 10
    patience: int = 3
    alpha: float = 1.0
    gamma: float = 2.0
    simulator_model: str = "claude-haiku-4-5-20251001"
    textgrad_model: str = "claude-sonnet-4-6-20250514"
    eval_sample_size: int = 50


@dataclass
class IterationRecord:
    iteration: int
    loss: CausalLossResult
    prompt: str
    gradient_step: GradientStep | None = None


@dataclass
class CalibrationResult:
    best_prompt: str
    best_loss: float
    initial_loss: float
    final_loss: float
    n_iterations: int
    total_llm_calls: int
    history: list[IterationRecord]


class CalibrationLoop:
    def __init__(
        self,
        config: CalibrationConfig | None = None,
        dataset: list[CounterfactualPair] | None = None,
    ):
        self.config = config or CalibrationConfig()
        self.dataset = dataset or []
        self.simulator = LLMChoiceSimulator(
            SimulatorConfig(model=self.config.simulator_model)
        )
        self.textgrad = TextGradEngine(
            TextGradConfig(model=self.config.textgrad_model)
        )

    def run(self) -> CalibrationResult:
        history: list[IterationRecord] = []
        best_loss = float("inf")
        best_prompt = self.simulator.system_prompt
        no_improve_count = 0

        eval_pairs = self.dataset[: self.config.eval_sample_size]

        for iteration in range(self.config.max_iterations):
            loss_result, error_examples = self._evaluate(eval_pairs)

            record = IterationRecord(
                iteration=iteration,
                loss=loss_result,
                prompt=self.simulator.system_prompt,
            )

            if loss_result.total_loss < best_loss:
                best_loss = loss_result.total_loss
                best_prompt = self.simulator.system_prompt
                no_improve_count = 0
            else:
                no_improve_count += 1

            if no_improve_count >= self.config.patience:
                history.append(record)
                break

            step = self.textgrad.generate_gradient(
                current_prompt=self.simulator.system_prompt,
                loss_result=loss_result,
                error_examples=error_examples[:5],
            )
            record.gradient_step = step
            history.append(record)

            self.simulator.system_prompt = step.edited_prompt

        total_calls = self.simulator._call_count

        return CalibrationResult(
            best_prompt=best_prompt,
            best_loss=best_loss,
            initial_loss=history[0].loss.total_loss if history else 0.0,
            final_loss=history[-1].loss.total_loss if history else 0.0,
            n_iterations=len(history),
            total_llm_calls=total_calls,
            history=history,
        )

    def _evaluate(
        self, pairs: list[CounterfactualPair]
    ) -> tuple[CausalLossResult, list[dict]]:
        predicted_probs_flat: list[float] = []
        actual_outcomes_flat: list[int] = []
        true_ates: list[float] = []
        predicted_ates: list[float] = []
        error_examples: list[dict] = []

        for pair in pairs:
            factual_pred = self.simulator.predict_probs(
                segment="commuter",
                demographics={},
                alternatives=["train", "swissmetro", "car"],
                attributes={
                    "train": {
                        "travel_time": pair.factual_attrs.get("train_tt", 0) * 100,
                        "cost": pair.factual_attrs.get("train_cost", 0) * 100,
                    },
                    "swissmetro": {
                        "travel_time": pair.factual_attrs.get("sm_tt", 0) * 100,
                        "cost": pair.factual_attrs.get("sm_cost", 0) * 100,
                    },
                    "car": {
                        "travel_time": pair.factual_attrs.get("car_tt", 0) * 100,
                        "cost": pair.factual_attrs.get("car_cost", 0) * 100,
                    },
                },
                context={},
            )
            cf_pred = self.simulator.predict_probs(
                segment="commuter",
                demographics={},
                alternatives=["train", "swissmetro", "car"],
                attributes={
                    "train": {
                        "travel_time": pair.counterfactual_attrs.get("train_tt", 0) * 100,
                        "cost": pair.counterfactual_attrs.get("train_cost", 0) * 100,
                    },
                    "swissmetro": {
                        "travel_time": pair.counterfactual_attrs.get("sm_tt", 0) * 100,
                        "cost": pair.counterfactual_attrs.get("sm_cost", 0) * 100,
                    },
                    "car": {
                        "travel_time": pair.counterfactual_attrs.get("car_tt", 0) * 100,
                        "cost": pair.counterfactual_attrs.get("car_cost", 0) * 100,
                    },
                },
                context={},
            )

            # ECE: for each alternative, compare predicted prob to "outcome"
            for alt in ["train", "swissmetro", "car"]:
                predicted_probs_flat.append(factual_pred.get(alt, 0.0))
                actual_outcomes_flat.append(
                    1 if pair.factual_probs.get(alt, 0) > 0.5 else 0
                )

            # ATE: compare predicted vs true counterfactual effect on swissmetro
            pred_ate = cf_pred.get("swissmetro", 0) - factual_pred.get("swissmetro", 0)
            true_ates.append(pair.ate)
            predicted_ates.append(pred_ate)

            # Track worst predictions for feedback
            ate_err = abs(pred_ate - pair.ate)
            if ate_err > 0.05:
                error_examples.append(
                    {
                        "scenario": (
                            f"factual sm_cost={pair.factual_attrs.get('sm_cost', 0):.2f}"
                        ),
                        "predicted": factual_pred,
                        "ground_truth": pair.factual_probs,
                        "predicted_ate": pred_ate,
                        "true_ate": pair.ate,
                    }
                )

        error_examples.sort(
            key=lambda x: abs(x["predicted_ate"] - x["true_ate"]), reverse=True
        )

        loss = compute_causal_loss(
            predicted_probs=predicted_probs_flat,
            actual_outcomes=actual_outcomes_flat,
            true_ates=true_ates,
            predicted_ates=predicted_ates,
            alpha=self.config.alpha,
            gamma=self.config.gamma,
        )
        return loss, error_examples
