import json

from experiments.policy_reaction_s2pc_selector_free_robustness import (
    build_policy_reaction_s2pc_selector_free_robustness,
    write_policy_reaction_s2pc_selector_free_robustness,
)


def test_build_selector_free_robustness_marks_mixed_direct_selector():
    artifact = build_policy_reaction_s2pc_selector_free_robustness(
        search_policy_ablation=_search_policy_ablation(),
        runtime_stability=_runtime_stability(),
        artifact_id="selector-free-robustness-test",
    )

    assert artifact["schema_version"] == "policy-reaction-s2pc-selector-free-robustness-v1"
    assert artifact["overall_status"] == "mixed"
    assert artifact["selector_policy_id"] == "beam_top1_direct"
    assert artifact["selected_candidate_id"] == "c01"
    assert artifact["stability_status"] == "mixed"
    assert artifact["repeat_count"] == 3
    assert artifact["regressed_count"] == 2
    json.dumps(artifact, allow_nan=False)


def test_write_selector_free_robustness(tmp_path):
    ablation_path = tmp_path / "ablation.json"
    stability_path = tmp_path / "stability.json"
    output = tmp_path / "robustness.json"
    ablation_path.write_text(json.dumps(_search_policy_ablation()))
    stability_path.write_text(json.dumps(_runtime_stability()))

    written = write_policy_reaction_s2pc_selector_free_robustness(
        output,
        search_policy_ablation_path=ablation_path,
        runtime_stability_path=stability_path,
        artifact_id="selector-free-robustness-test",
    )

    assert written == output
    persisted = json.loads(output.read_text())
    assert persisted["selector_policy_id"] == "beam_top1_direct"


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
                "policy_id": "beam_top3_oracle",
                "family": "beam_depth",
                "overall_status": "improved",
                "selected_candidate_id": "c01",
                "selected_rank": 1,
                "selected_segment": "fixed_income_inflation_stressed",
                "selected_policy_id": "food_subsidy_expansion",
            },
        ],
        "claim_boundaries": ["ablation boundary"],
    }


def _runtime_stability() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-runtime-stability-v1",
        "artifact_id": "stability-test",
        "overall_status": "mixed",
        "effect_count": 3,
        "improved_count": 1,
        "regressed_count": 2,
        "no_change_count": 0,
        "candidate_ids": ["c01"],
        "best_candidate_id": "c01",
        "loss_summary": {
            "relative_loss_reduction_mean": -3.26,
        },
        "claim_boundaries": ["stability boundary"],
    }
