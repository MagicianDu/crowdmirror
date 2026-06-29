import numpy as np
import pytest
from circe.dgp.mnl import fit_swissmetro_mnl, MNLModel


def test_fit_returns_model():
    model = fit_swissmetro_mnl()
    assert isinstance(model, MNLModel)
    assert "b_time" in model.params
    assert "b_cost" in model.params


def test_model_predicts_probabilities():
    model = fit_swissmetro_mnl()
    probs = model.predict_probs(
        train_tt=100, train_cost=50, train_he=10,
        sm_tt=80, sm_cost=60, sm_he=5,
        car_tt=120, car_cost=30,
    )
    assert len(probs) == 3
    assert abs(sum(probs.values()) - 1.0) < 1e-6
    assert all(0 <= p <= 1 for p in probs.values())


def test_price_increase_reduces_probability():
    model = fit_swissmetro_mnl()
    base = model.predict_probs(
        train_tt=100, train_cost=50, train_he=10,
        sm_tt=80, sm_cost=60, sm_he=5,
        car_tt=120, car_cost=30,
    )
    expensive = model.predict_probs(
        train_tt=100, train_cost=50, train_he=10,
        sm_tt=80, sm_cost=120, sm_he=5,
        car_tt=120, car_cost=30,
    )
    assert expensive["swissmetro"] < base["swissmetro"]
