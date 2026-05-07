"""Generate counterfactual scenario pairs with known ground-truth effects."""

from dataclasses import dataclass
import numpy as np
from circe.data.swissmetro import load_swissmetro
from circe.dgp.mnl import fit_swissmetro_mnl


@dataclass
class CounterfactualPair:
    scenario_id: str
    factual_attrs: dict[str, float]
    counterfactual_attrs: dict[str, float]
    intervention: dict[str, float]
    factual_probs: dict[str, float]
    counterfactual_probs: dict[str, float]
    ate: float


def generate_counterfactual_dataset(
    n_scenarios: int = 100,
    n_interventions: int = 3,
    intervention_type: str = "sm_cost_increase",
    seed: int = 42,
) -> list[CounterfactualPair]:
    rng = np.random.default_rng(seed)
    model = fit_swissmetro_mnl()
    records = load_swissmetro()
    sampled = rng.choice(records, size=min(n_scenarios, len(records)), replace=False)

    multipliers = {
        "sm_cost_increase": np.linspace(1.1, 2.0, n_interventions),
        "sm_time_increase": np.linspace(1.1, 1.5, n_interventions),
        "train_cost_decrease": np.linspace(0.5, 0.9, n_interventions),
    }[intervention_type]

    pairs = []
    for i, rec in enumerate(sampled):
        base_kwargs = dict(
            train_tt=rec.train_tt / 100, train_cost=rec.train_cost / 100,
            train_he=rec.train_he, sm_tt=rec.sm_tt / 100,
            sm_cost=rec.sm_cost / 100, sm_he=rec.sm_he,
            car_tt=rec.car_tt / 100, car_cost=rec.car_cost / 100,
        )
        factual_probs = model.predict_probs(**base_kwargs)

        for j, mult in enumerate(multipliers):
            cf_kwargs = base_kwargs.copy()
            if intervention_type == "sm_cost_increase":
                cf_kwargs["sm_cost"] = base_kwargs["sm_cost"] * mult
            elif intervention_type == "sm_time_increase":
                cf_kwargs["sm_tt"] = base_kwargs["sm_tt"] * mult
            elif intervention_type == "train_cost_decrease":
                cf_kwargs["train_cost"] = base_kwargs["train_cost"] * mult

            cf_probs = model.predict_probs(**cf_kwargs)
            ate = cf_probs["swissmetro"] - factual_probs["swissmetro"]

            pairs.append(CounterfactualPair(
                scenario_id=f"s{i}_int{j}",
                factual_attrs=base_kwargs,
                counterfactual_attrs=cf_kwargs,
                intervention={intervention_type: float(mult)},
                factual_probs=factual_probs,
                counterfactual_probs=cf_probs,
                ate=ate,
            ))
    return pairs
