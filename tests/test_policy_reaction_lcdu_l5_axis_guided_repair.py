import json

from experiments.policy_reaction_lcdu_l5_axis_guided_repair import (
    build_policy_reaction_lcdu_l5_axis_guided_repair_set,
    extract_policy_reaction_lcdu_l5_axis_guided_repair_candidate,
)


def test_build_lcdu_l5_axis_guided_repair_set_creates_axis_overrides():
    artifact = build_policy_reaction_lcdu_l5_axis_guided_repair_set(
        base_candidate=_base_candidate(),
        axis_weakness=_axis_weakness(),
        artifact_id="lcdu-l5-test",
    )

    assert artifact["schema_version"] == "policy-reaction-lcdu-axis-repair-set-v1"
    assert artifact["candidate_count"] == 4
    assert artifact["persistent_weakness"]["worst_jsd_segment"] == "price_stress_level=high"
    x04 = artifact["candidates"][-1]
    assert "income_band=low" in x04["axis_prompt_overrides"]
    assert "price_stress_level=high" in x04["axis_anchor_overrides"]
    json.dumps(artifact, allow_nan=False)


def test_extract_lcdu_l5_candidate_keeps_axis_selector_keys():
    artifact = build_policy_reaction_lcdu_l5_axis_guided_repair_set(
        base_candidate=_base_candidate(),
        axis_weakness=_axis_weakness(),
        artifact_id="lcdu-l5-test",
    )
    candidate = extract_policy_reaction_lcdu_l5_axis_guided_repair_candidate(
        artifact,
        candidate_id="lcdu-l5-test-x04",
    )

    prompts = candidate["candidate_prompt_components"]["segment_prompt"]
    anchors = candidate["candidate_prompt_components"]["calibration_anchor"]
    assert "income_band=low" in prompts
    assert "price_stress_level=high" in prompts
    assert "income_band=low" in anchors
    assert "price_stress_level=high" in anchors
    json.dumps(candidate, allow_nan=False)


def _base_candidate() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-candidate-v1",
        "candidate_id": "policy-reaction-lcdu-l3-current-001-h02",
        "generator": "lcdu_l3_working_family_guard_family",
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
                    "parameter_value": 0.593211730696,
                }
            ],
        },
        "candidate_prompt_components": {
            "segment_prompt": {
                "fixed_income_inflation_stressed": "Base prompt.",
                "working_family_price_stressed": "Working-family guard.",
            },
            "calibration_anchor": {
                "fixed_income_inflation_stressed": "Base anchor.",
                "working_family_price_stressed": "Working-family anchor.",
            },
            "response_contract": "Return strict JSON probabilities.",
        },
    }


def _axis_weakness() -> dict:
    return {
        "schema_version": "policy-reaction-axis-weakness-v1",
        "artifact_id": "policy-reaction-axis-weakness-lcdu-l3-current-001",
        "persistent_weakness": {
            "worst_jsd_segment": "price_stress_level=high",
            "worst_jsd_value_mean": 0.14925228029562396,
            "worst_rank_segment": "income_band=low",
            "worst_rank_value_mean": -1.0,
        },
    }
