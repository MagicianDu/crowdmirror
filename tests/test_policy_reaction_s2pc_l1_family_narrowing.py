import json

from experiments.policy_reaction_s2pc_l1_family_narrowing import (
    build_policy_reaction_s2pc_l1_family_narrowing,
    write_policy_reaction_s2pc_l1_family_narrowing,
)


def test_build_s2pc_l1_family_narrowing_reduces_to_positive_branch():
    artifact = build_policy_reaction_s2pc_l1_family_narrowing(
        candidate_set=_candidate_set(),
        runtime_effect_matrix=_runtime_effect_matrix(),
        search_policy_ablation=_search_policy_ablation(),
        artifact_id="s2pc-l1-family-narrowing-test",
    )

    assert artifact["schema_version"] == "policy-reaction-s2pc-l1-family-narrowing-v1"
    assert artifact["overall_status"] == "narrowed_family_available"
    assert artifact["retained_candidate_count"] == 1
    assert artifact["retained_candidate_ids"] == ["c01"]
    assert artifact["narrowing_rules"] == {
        "segment_allowlist": ["fixed_income_inflation_stressed"],
        "policy_allowlist": ["food_subsidy_expansion"],
        "max_rank": 1,
    }
    json.dumps(artifact, allow_nan=False)


def test_write_s2pc_l1_family_narrowing(tmp_path):
    candidate_set_path = tmp_path / "candidate-set.json"
    matrix_path = tmp_path / "matrix.json"
    ablation_path = tmp_path / "ablation.json"
    output = tmp_path / "family.json"
    candidate_set_path.write_text(json.dumps(_candidate_set()))
    matrix_path.write_text(json.dumps(_runtime_effect_matrix()))
    ablation_path.write_text(json.dumps(_search_policy_ablation()))

    written = write_policy_reaction_s2pc_l1_family_narrowing(
        output,
        candidate_set_path=candidate_set_path,
        runtime_effect_matrix_path=matrix_path,
        search_policy_ablation_path=ablation_path,
        artifact_id="s2pc-l1-family-narrowing-test",
    )

    assert written == output
    persisted = json.loads(output.read_text())
    assert persisted["retained_candidate_ids"] == ["c01"]


def _candidate_set() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-l1-candidate-set-v1",
        "candidate_set_id": "candidate-set-test",
        "candidates": [
            {"candidate_id": "c01", "rank": 1, "segment": "fixed_income_inflation_stressed", "policy_id": "food_subsidy_expansion", "proxy_score": 4.25},
            {"candidate_id": "c02", "rank": 2, "segment": "general_population_cost_pressure", "policy_id": "food_subsidy_expansion", "proxy_score": 4.24},
            {"candidate_id": "c03", "rank": 3, "segment": "working_family_price_stressed", "policy_id": "food_subsidy_expansion", "proxy_score": 3.72},
            {"candidate_id": "c04", "rank": 4, "segment": "general_population_cost_pressure", "policy_id": "baseline_no_new_support", "proxy_score": 2.53},
            {"candidate_id": "c05", "rank": 5, "segment": "fixed_income_inflation_stressed", "policy_id": "baseline_no_new_support", "proxy_score": 1.72},
            {"candidate_id": "c06", "rank": 6, "segment": "working_family_price_stressed", "policy_id": "baseline_no_new_support", "proxy_score": 1.56},
        ],
        "claim_boundaries": ["candidate set boundary"],
    }


def _runtime_effect_matrix() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-runtime-effect-matrix-v1",
        "artifact_id": "runtime-effect-matrix-test",
        "candidate_results": [
            {"s2pc_candidate_id": "c01", "overall_status": "improved", "s2pc_runtime_loss": 0.000111545213},
            {"s2pc_candidate_id": "c04", "overall_status": "regressed", "s2pc_runtime_loss": 0.000904895192},
            {"s2pc_candidate_id": "c05", "overall_status": "regressed", "s2pc_runtime_loss": 0.002103066798},
            {"s2pc_candidate_id": "c02", "overall_status": "regressed", "s2pc_runtime_loss": 0.003262026554},
            {"s2pc_candidate_id": "c03", "overall_status": "regressed", "s2pc_runtime_loss": 0.008484318228},
            {"s2pc_candidate_id": "c06", "overall_status": "regressed", "s2pc_runtime_loss": 0.01628069538},
        ],
        "claim_boundaries": ["matrix boundary"],
    }


def _search_policy_ablation() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-l1-search-policy-ablation-v1",
        "artifact_id": "ablation-test",
        "policies": [
            {
                "policy_id": "beam_top1_direct",
                "family": "beam_depth",
                "overall_status": "improved",
                "selected_candidate_id": "c01",
                "selected_rank": 1,
                "selected_segment": "fixed_income_inflation_stressed",
                "selected_policy_id": "food_subsidy_expansion",
            },
            {
                "policy_id": "policy_group_food_subsidy_expansion_oracle",
                "family": "policy_group",
                "overall_status": "improved",
                "selected_candidate_id": "c01",
                "selected_rank": 1,
                "selected_segment": "fixed_income_inflation_stressed",
                "selected_policy_id": "food_subsidy_expansion",
            },
            {
                "policy_id": "segment_group_fixed_income_inflation_stressed_oracle",
                "family": "segment_group",
                "overall_status": "improved",
                "selected_candidate_id": "c01",
                "selected_rank": 1,
                "selected_segment": "fixed_income_inflation_stressed",
                "selected_policy_id": "food_subsidy_expansion",
            },
        ],
        "claim_boundaries": ["ablation boundary"],
    }
