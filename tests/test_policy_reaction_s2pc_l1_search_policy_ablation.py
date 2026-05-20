import json

from experiments.policy_reaction_s2pc_l1_search_policy_ablation import (
    build_policy_reaction_s2pc_l1_search_policy_ablation,
    write_policy_reaction_s2pc_l1_search_policy_ablation,
)


def test_build_s2pc_l1_search_policy_ablation_summarizes_beam_and_groups():
    artifact = build_policy_reaction_s2pc_l1_search_policy_ablation(
        candidate_set=_candidate_set(),
        runtime_effect_matrix=_runtime_effect_matrix(),
        artifact_id="s2pc-l1-search-policy-ablation-test",
    )

    assert artifact["schema_version"] == "policy-reaction-s2pc-l1-search-policy-ablation-v1"
    assert artifact["overall_status"] == "improving_search_policies_available"
    assert artifact["best_policy_id"] == "beam_top1_direct"
    assert artifact["policy_count"] >= 5
    assert artifact["policies"][0]["policy_id"] == "beam_top1_direct"
    assert artifact["policies"][0]["selected_candidate_id"] == "c01"
    assert artifact["policies"][0]["overall_status"] == "improved"
    baseline_group = next(
        item for item in artifact["policies"] if item["policy_id"] == "policy_group_baseline_no_new_support_oracle"
    )
    assert baseline_group["overall_status"] == "regressed"
    json.dumps(artifact, allow_nan=False)


def test_write_s2pc_l1_search_policy_ablation(tmp_path):
    candidate_set_path = tmp_path / "candidate-set.json"
    matrix_path = tmp_path / "matrix.json"
    output = tmp_path / "ablation.json"
    candidate_set_path.write_text(json.dumps(_candidate_set()))
    matrix_path.write_text(json.dumps(_runtime_effect_matrix()))

    written = write_policy_reaction_s2pc_l1_search_policy_ablation(
        output,
        candidate_set_path=candidate_set_path,
        runtime_effect_matrix_path=matrix_path,
        artifact_id="s2pc-l1-search-policy-ablation-test",
    )

    assert written == output
    persisted = json.loads(output.read_text())
    assert persisted["artifact_id"] == "s2pc-l1-search-policy-ablation-test"
    assert persisted["best_policy_id"] == "beam_top1_direct"


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
        "candidate_count": 6,
        "claim_boundaries": ["candidate set boundary"],
    }


def _runtime_effect_matrix() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-runtime-effect-matrix-v1",
        "artifact_id": "runtime-effect-matrix-test",
        "overall_status": "candidate_improvements_available",
        "candidate_results": [
            {"artifact_id": "effect-c01", "s2pc_candidate_id": "c01", "overall_status": "improved", "baseline_loss": 0.000112890954, "s2pc_runtime_loss": 0.000111545213, "absolute_loss_delta": 0.000001345741, "relative_loss_reduction": 0.011920716018, "s2pc_product_run_id": "run-c01"},
            {"artifact_id": "effect-c04", "s2pc_candidate_id": "c04", "overall_status": "regressed", "baseline_loss": 0.000112890954, "s2pc_runtime_loss": 0.000904895192, "absolute_loss_delta": -0.000792004238, "relative_loss_reduction": -7.015657252421, "s2pc_product_run_id": "run-c04"},
            {"artifact_id": "effect-c05", "s2pc_candidate_id": "c05", "overall_status": "regressed", "baseline_loss": 0.000112890954, "s2pc_runtime_loss": 0.002103066798, "absolute_loss_delta": -0.001990175844, "relative_loss_reduction": -17.629187981128, "s2pc_product_run_id": "run-c05"},
            {"artifact_id": "effect-c02", "s2pc_candidate_id": "c02", "overall_status": "regressed", "baseline_loss": 0.000112890954, "s2pc_runtime_loss": 0.003262026554, "absolute_loss_delta": -0.0031491356, "relative_loss_reduction": -27.895375997973, "s2pc_product_run_id": "run-c02"},
            {"artifact_id": "effect-c03", "s2pc_candidate_id": "c03", "overall_status": "regressed", "baseline_loss": 0.000112890954, "s2pc_runtime_loss": 0.008484318228, "absolute_loss_delta": -0.008371427275, "relative_loss_reduction": -74.154987634006, "s2pc_product_run_id": "run-c03"},
            {"artifact_id": "effect-c06", "s2pc_candidate_id": "c06", "overall_status": "regressed", "baseline_loss": 0.000112890954, "s2pc_runtime_loss": 0.01628069538, "absolute_loss_delta": -0.016167804426, "relative_loss_reduction": -143.216120488733, "s2pc_product_run_id": "run-c06"},
        ],
        "claim_boundaries": ["runtime effect matrix boundary"],
    }
