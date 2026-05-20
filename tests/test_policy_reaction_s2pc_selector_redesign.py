import json

from experiments.policy_reaction_s2pc_selector_redesign import (
    build_policy_reaction_s2pc_selector_redesign,
)


def test_selector_redesign_abstains_when_robustness_and_subset_fail():
    artifact = build_policy_reaction_s2pc_selector_redesign(
        family_narrowing=_family_narrowing(),
        selector_free_robustness=_selector_free_robustness(),
        sparse_subset_matrix=_sparse_subset_matrix(),
        artifact_id="selector-redesign-test",
    )

    assert artifact["schema_version"] == "policy-reaction-s2pc-selector-redesign-v1"
    assert artifact["overall_status"] == "abstain"
    assert artifact["recommended_selector_policy_id"] is None
    assert artifact["recommended_candidate_id"] is None
    assert artifact["abstain_reason"] == "current_direct_selector_not_robust_and_sparse_subsets_all_regressed"
    json.dumps(artifact, allow_nan=False)


def test_selector_redesign_redirects_to_best_sparse_subset_when_improvement_exists():
    matrix = _sparse_subset_matrix()
    matrix["overall_status"] = "candidate_improvements_available"
    matrix["improved_count"] = 1
    matrix["regressed_count"] = 2
    matrix["best_candidate_id"] = "s02"
    artifact = build_policy_reaction_s2pc_selector_redesign(
        family_narrowing=_family_narrowing(),
        selector_free_robustness=_selector_free_robustness(),
        sparse_subset_matrix=matrix,
        artifact_id="selector-redesign-test",
    )

    assert artifact["overall_status"] == "proceed_with_sparse_selector"
    assert artifact["recommended_selector_policy_id"] == "sparse_subset_best_runtime_effect"
    assert artifact["recommended_candidate_id"] == "s02"
    assert artifact["selector_transition"] == "redirect_from_direct_to_sparse_subset"
    json.dumps(artifact, allow_nan=False)


def _family_narrowing() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-l1-family-narrowing-v1",
        "artifact_id": "family-test",
        "retained_candidate_ids": ["c01"],
        "retained_candidate_count": 1,
    }


def _selector_free_robustness() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-selector-free-robustness-v1",
        "artifact_id": "robustness-test",
        "overall_status": "mixed",
        "selector_policy_id": "beam_top1_direct",
        "selected_candidate_id": "c01",
        "regressed_count": 2,
    }


def _sparse_subset_matrix() -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-runtime-effect-matrix-v1",
        "artifact_id": "subset-matrix-test",
        "overall_status": "all_candidates_regressed",
        "candidate_count": 3,
        "improved_count": 0,
        "regressed_count": 3,
        "best_candidate_id": "s01",
        "best_s2pc_runtime_loss": 0.0022,
    }
