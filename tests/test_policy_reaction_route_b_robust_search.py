import json

from experiments.policy_reaction_route_b_robust_search import (
    build_policy_reaction_route_b_robust_score,
)


def test_route_b_robust_score_blocks_unstable_candidate():
    artifact = build_policy_reaction_route_b_robust_score(
        candidate=_candidate(),
        effect_artifacts=[
            _effect("e1", "improved", 0.000112890954, 0.000111545213, 12, 36, 11),
            _effect("e2", "no_change", 0.000111545213, 0.000111545213, 12, 36, 17),
            _effect("e3", "regressed", 0.000109778219, 0.000427401852, 16, 48, 11),
        ],
        artifact_id="route-b-test",
    )

    assert artifact["schema_version"] == "policy-reaction-route-b-robust-score-v1"
    assert artifact["overall_status"] == "blocked_by_stop_loss"
    assert artifact["repeat_summary"]["improved_count"] == 1
    assert artifact["repeat_summary"]["regressed_count"] == 1
    assert artifact["scale_axes"]["persona_counts"] == [12, 16]
    json.dumps(artifact, allow_nan=False)


def test_route_b_robust_score_accepts_repeat_aware_candidate():
    artifact = build_policy_reaction_route_b_robust_score(
        candidate=_candidate(),
        effect_artifacts=[
            _effect("e1", "improved", 0.12, 0.08, 12, 36, 11),
            _effect("e2", "improved", 0.11, 0.09, 12, 36, 17),
            _effect("e3", "no_change", 0.10, 0.10, 16, 48, 11),
        ],
        artifact_id="route-b-test",
        min_improved_runs=2,
        max_regressed_runs=0,
    )

    assert artifact["overall_status"] == "accepted_for_repeat_aware_search"
    assert artifact["repeat_summary"]["improved_count"] == 2
    assert artifact["repeat_summary"]["regressed_count"] == 0
    assert artifact["robust_objective"]["robust_score"] > 0.0


def _candidate() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-candidate-v1",
        "candidate_id": "policy-reaction-s2pc-c01-sparse-subset-current-001-s02",
        "generator": "s2pc_c01_sparse_factor_subset",
        "source_split_contract": {
            "residual_mining": "calibration",
            "semantic_factor_retrieval": "calibration",
            "parameter_search": "calibration",
            "candidate_acceptance": "heldout_required",
        },
        "best_candidate": {
            "candidate_index": 1,
            "segment": "fixed_income_inflation_stressed",
            "policy_id": "food_subsidy_expansion",
            "proxy_score": 4.254466026348,
            "parameter_patches": [
                {
                    "factor_id": "institutional_trust",
                    "parameter_name": "prior_anchor_strength",
                    "parameter_value": 0.624611730696,
                },
                {
                    "factor_id": "institutional_trust",
                    "parameter_name": "trust_multiplier",
                    "parameter_value": 0.974611730696,
                },
            ],
        },
        "candidate_prompt_components": {
            "segment_prompt": {
                "fixed_income_inflation_stressed": "Use calibrated parameters."
            },
            "calibration_anchor": {
                "fixed_income_inflation_stressed": "trust candidate"
            },
            "response_contract": "Return strict JSON probabilities.",
        },
    }


def _effect(
    artifact_id: str,
    overall_status: str,
    baseline_loss: float,
    s2pc_runtime_loss: float,
    persona_count: int,
    scenario_count: int,
    seed: int,
) -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-runtime-effect-v1",
        "artifact_id": artifact_id,
        "overall_status": overall_status,
        "loss_metric": "weighted_choice_distribution_jsd",
        "baseline_loss": baseline_loss,
        "s2pc_runtime_loss": s2pc_runtime_loss,
        "absolute_loss_delta": baseline_loss - s2pc_runtime_loss,
        "relative_loss_reduction": (
            (baseline_loss - s2pc_runtime_loss) / baseline_loss
            if baseline_loss > 0
            else None
        ),
        "s2pc_candidate_id": "policy-reaction-s2pc-c01-sparse-subset-current-001-s02",
        "product_runtime_scale": {
            "persona_count": persona_count,
            "scenario_count": scenario_count,
            "seed": seed,
        },
    }
