"""MNL model fitting on Swissmetro for ground-truth DGP."""

from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize
from circe.data.swissmetro import load_swissmetro


@dataclass
class MNLModel:
    params: dict[str, float]

    def _utilities(
        self, train_tt, train_cost, train_he,
        sm_tt, sm_cost, sm_he, car_tt, car_cost,
    ) -> np.ndarray:
        b_time = self.params["b_time"]
        b_cost = self.params["b_cost"]
        asc_train = self.params["asc_train"]
        asc_car = self.params["asc_car"]

        v_train = asc_train + b_time * train_tt + b_cost * train_cost
        v_sm = b_time * sm_tt + b_cost * sm_cost
        v_car = asc_car + b_time * car_tt + b_cost * car_cost
        return np.array([v_train, v_sm, v_car])

    def predict_probs(self, **kwargs) -> dict[str, float]:
        v = self._utilities(**kwargs)
        exp_v = np.exp(v - v.max())
        probs = exp_v / exp_v.sum()
        return {"train": probs[0], "swissmetro": probs[1], "car": probs[2]}


def fit_swissmetro_mnl() -> MNLModel:
    records = load_swissmetro()
    n = len(records)
    train_tt = np.array([r.train_tt for r in records]) / 100
    train_cost = np.array([r.train_cost for r in records]) / 100
    sm_tt = np.array([r.sm_tt for r in records]) / 100
    sm_cost = np.array([r.sm_cost for r in records]) / 100
    car_tt = np.array([r.car_tt for r in records]) / 100
    car_cost = np.array([r.car_cost for r in records]) / 100
    choices = np.array([r.choice - 1 for r in records])

    def neg_log_likelihood(params):
        asc_train, asc_car, b_time, b_cost = params
        v = np.column_stack([
            asc_train + b_time * train_tt + b_cost * train_cost,
            b_time * sm_tt + b_cost * sm_cost,
            asc_car + b_time * car_tt + b_cost * car_cost,
        ])
        v = v - v.max(axis=1, keepdims=True)
        exp_v = np.exp(v)
        probs = exp_v / exp_v.sum(axis=1, keepdims=True)
        chosen_probs = probs[np.arange(n), choices]
        return -np.sum(np.log(chosen_probs + 1e-15))

    result = minimize(neg_log_likelihood, x0=[0, 0, -1, -1], method="Nelder-Mead")
    asc_train, asc_car, b_time, b_cost = result.x
    return MNLModel(params={
        "asc_train": asc_train,
        "asc_car": asc_car,
        "b_time": b_time,
        "b_cost": b_cost,
    })
