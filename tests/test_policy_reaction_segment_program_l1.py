import json

from experiments.policy_reaction_segment_program_l1 import (
    build_policy_reaction_segment_program_l1_candidate_set,
    extract_policy_reaction_segment_program_l1_candidate,
)


def test_build_segment_program_l1_candidate_set_creates_narrowed_family():
    artifact = build_policy_reaction_segment_program_l1_candidate_set(
        base_candidate=_base_candidate(),
        artifact_id="segment-program-l1-test",
    )

    assert artifact["schema_version"] == "policy-reaction-segment-program-l1-set-v1"
    assert artifact["candidate_count"] == 4
    assert artifact["generator"] == "segment_program_l1_narrowed_family"
    assert artifact["program_axes"] == [
        "working_family_cash_floor",
        "low_income_support_order",
        "dual_axis_soft_sync",
        "high_price_numeric_push",
    ]
    first = artifact["candidates"][0]
    assert first["variant_tag"] == "working_family_cash_floor_focus"
    assert first["narrowing_program"]["coordination_mode"] == "cash_floor_primary"
    assert "working_family_price_stressed" in first["narrowing_program"]["target_selectors"]
    json.dumps(artifact, allow_nan=False)


def test_extract_segment_program_l1_candidate_keeps_contract_and_l1_anchors():
    artifact = build_policy_reaction_segment_program_l1_candidate_set(
        base_candidate=_base_candidate(),
        artifact_id="segment-program-l1-test",
    )
    candidate = extract_policy_reaction_segment_program_l1_candidate(
        artifact,
        candidate_id="segment-program-l1-test-t04",
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["generator"] == "segment_program_l1_narrowed_family"
    prompts = candidate["candidate_prompt_components"]["segment_prompt"]
    anchors = candidate["candidate_prompt_components"]["calibration_anchor"]
    assert "price_stress_level=high" in prompts
    assert "SEGMENT-PROGRAM-L1" in anchors["fixed_income_inflation_stressed"]
    assert "numeric_high_price_push" in anchors["price_stress_level=high"]
    json.dumps(candidate, allow_nan=False)


def _base_candidate() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-candidate-v1",
        "candidate_id": "policy-reaction-segment-program-l0-current-001-s02",
        "generator": "segment_program_l0_family_builder",
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
                    "parameter_bounds": {"min": 0.45, "max": 0.85},
                },
                {
                    "factor_id": "institutional_trust",
                    "parameter_name": "trust_multiplier",
                    "parameter_value": 0.927811730696,
                    "parameter_bounds": {"min": 0.8, "max": 1.2},
                },
            ],
        },
        "candidate_prompt_components": {
            "segment_prompt": {
                "fixed_income_inflation_stressed": "Round1 fixed-income prompt.",
                "working_family_price_stressed": "Round1 working-family prompt.",
                "income_band=low": "Round1 low-income prompt.",
                "price_stress_level=high": "Round1 high-price prompt.",
            },
            "calibration_anchor": {
                "fixed_income_inflation_stressed": "Round1 fixed-income anchor.",
                "working_family_price_stressed": "Round1 working-family anchor.",
                "income_band=low": "Round1 low-income anchor.",
                "price_stress_level=high": "Round1 high-price anchor.",
            },
            "response_contract": "Return strict JSON probabilities.",
        },
    }
