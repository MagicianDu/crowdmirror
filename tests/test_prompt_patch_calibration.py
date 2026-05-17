import json

import pytest

from circe.calibration.prompt_patch import (
    PromptPatch,
    apply_prompt_patch,
    build_prompt_patch_gate,
    generate_residual_prompt_patches,
)


def test_residual_generator_creates_fine_grained_segment_patch():
    observed = {
        "low_income_food_insecure": {
            "baseline_no_new_support": 0.10,
            "food_subsidy_expansion": 0.70,
            "cash_cost_of_living_rebate": 0.20,
        }
    }
    predicted = {
        "low_income_food_insecure": {
            "baseline_no_new_support": 0.30,
            "food_subsidy_expansion": 0.40,
            "cash_cost_of_living_rebate": 0.30,
        }
    }

    patches = generate_residual_prompt_patches(
        observed_by_segment=observed,
        predicted_by_segment=predicted,
        threshold=0.05,
    )

    assert len(patches) == 1
    patch = patches[0]
    assert patch.target == "segment_prompt.low_income_food_insecure"
    assert patch.operation == "tighten"
    assert patch.source_split == "calibration"
    assert patch.expected_effect == {
        "baseline_no_new_support": "decrease",
        "food_subsidy_expansion": "increase",
        "cash_cost_of_living_rebate": "decrease",
    }
    assert "food_subsidy_expansion is under-predicted" in patch.reason
    assert "low_income_food_insecure" in patch.patch
    json.dumps(patch.to_dict(), allow_nan=False)


def test_apply_prompt_patch_updates_only_target_component():
    components = {
        "global_instruction": "simulate policy reaction",
        "segment_prompt": {
            "low_income_food_insecure": "base low-income prompt",
            "general_population_cost_pressure": "base general prompt",
        },
        "response_contract": "return strict JSON probabilities",
    }
    patch = PromptPatch(
        target="segment_prompt.low_income_food_insecure",
        operation="tighten",
        reason="calibration residual",
        patch="Increase sensitivity to food affordability stress.",
        expected_effect={"food_subsidy_expansion": "increase"},
        source_split="calibration",
    )

    updated = apply_prompt_patch(components, patch)

    assert updated is not components
    assert updated["segment_prompt"]["low_income_food_insecure"].endswith(
        "Increase sensitivity to food affordability stress."
    )
    assert updated["segment_prompt"]["general_population_cost_pressure"] == (
        "base general prompt"
    )
    assert components["segment_prompt"]["low_income_food_insecure"] == (
        "base low-income prompt"
    )


def test_prompt_patch_rejects_evaluation_split_as_patch_source():
    patch = PromptPatch(
        target="segment_prompt.low_income_food_insecure",
        operation="tighten",
        reason="leaky evaluation feedback",
        patch="Use evaluation target directly.",
        expected_effect={"food_subsidy_expansion": "increase"},
        source_split="evaluation",
    )

    with pytest.raises(ValueError, match="calibration"):
        apply_prompt_patch({"segment_prompt": {"low_income_food_insecure": ""}}, patch)


def test_prompt_patch_gate_accepts_loss_improving_candidate():
    components = {
        "segment_prompt": {
            "low_income_food_insecure": "base low-income prompt",
        }
    }
    patch = PromptPatch(
        target="segment_prompt.low_income_food_insecure",
        operation="tighten",
        reason="food subsidy under-predicted",
        patch="Increase food subsidy sensitivity.",
        expected_effect={"food_subsidy_expansion": "increase"},
        source_split="calibration",
    )

    gate = build_prompt_patch_gate(
        components,
        [patch],
        artifact_id="prompt-patch-gate-test",
        initial_loss=0.20,
        candidate_loss=0.12,
        coverage_rate=1.0,
    )

    assert gate["schema_version"] == "circe-prompt-patch-gate-v1"
    assert gate["overall_status"] == "accepted"
    assert gate["candidate_accepted_count"] == 1
    assert gate["candidate_rejected_count"] == 0
    assert gate["initial_loss"] == 0.20
    assert gate["final_loss"] == 0.12
    assert gate["final_prompt_components"] == gate["candidate_prompt_components"]
    json.dumps(gate, allow_nan=False)


def test_prompt_patch_gate_rejects_non_improving_candidate_and_reverts():
    components = {
        "segment_prompt": {
            "low_income_food_insecure": "base low-income prompt",
        }
    }
    patch = PromptPatch(
        target="segment_prompt.low_income_food_insecure",
        operation="tighten",
        reason="food subsidy under-predicted",
        patch="Increase food subsidy sensitivity.",
        expected_effect={"food_subsidy_expansion": "increase"},
        source_split="calibration",
    )

    gate = build_prompt_patch_gate(
        components,
        [patch],
        artifact_id="prompt-patch-gate-reject-test",
        initial_loss=0.20,
        candidate_loss=0.22,
        coverage_rate=1.0,
    )

    assert gate["overall_status"] == "rejected"
    assert gate["candidate_accepted_count"] == 0
    assert gate["candidate_rejected_count"] == 1
    assert gate["final_loss"] == 0.20
    assert gate["final_prompt_components"] == components
    assert gate["candidate_prompt_components"] != components
