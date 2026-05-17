import json

import pytest

from circe.calibration.prompt_patch import (
    PromptPatch,
    PromptPatchCandidate,
    apply_prompt_patch,
    build_multi_candidate_prompt_patch_gate,
    build_prompt_patch_gate,
    generate_parameter_prompt_patches,
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


def test_parameter_generator_creates_calibration_anchor_patch():
    patches = generate_parameter_prompt_patches(
        segment_parameter_deltas={
            "low_income_food_insecure": {
                "food_price_sensitivity": 0.18,
                "institutional_trust": -0.07,
                "noise_floor": 0.01,
            }
        },
        threshold=0.05,
    )

    assert len(patches) == 1
    patch = patches[0]
    assert patch.target == "calibration_anchor.low_income_food_insecure"
    assert patch.operation == "tighten"
    assert patch.expected_effect == {
        "food_price_sensitivity": "increase",
        "institutional_trust": "decrease",
    }
    assert "food_price_sensitivity += 0.180000" in patch.patch
    assert patch.evidence["generator"] == "parameter_search"


def test_multi_candidate_gate_selects_best_heldout_candidate():
    components = {
        "segment_prompt": {
            "low_income_food_insecure": "base segment prompt",
        },
        "calibration_anchor": {
            "low_income_food_insecure": "base anchor",
        },
    }
    residual_candidate = PromptPatchCandidate(
        candidate_id="residual-low-income",
        generator="residual_rule",
        rationale="food subsidy under-predicted",
        patches=[
            PromptPatch(
                target="segment_prompt.low_income_food_insecure",
                operation="tighten",
                reason="food subsidy under-predicted",
                patch="Increase food subsidy salience.",
                expected_effect={"food_subsidy_expansion": "increase"},
            )
        ],
    )
    parameter_candidate = PromptPatchCandidate(
        candidate_id="parameter-low-income",
        generator="parameter_search",
        rationale="parameter search found stronger price sensitivity",
        patches=generate_parameter_prompt_patches(
            segment_parameter_deltas={
                "low_income_food_insecure": {"food_price_sensitivity": 0.20}
            }
        ),
    )

    gate = build_multi_candidate_prompt_patch_gate(
        components,
        [residual_candidate, parameter_candidate],
        artifact_id="multi-candidate-gate-test",
        initial_loss=0.20,
        candidate_evaluations={
            "residual-low-income": {
                "loss": 0.18,
                "coverage_rate": 1.0,
                "evaluation_split": "heldout",
            },
            "parameter-low-income": {
                "loss": 0.12,
                "coverage_rate": 1.0,
                "evaluation_split": "heldout",
            },
        },
    )

    assert gate["schema_version"] == "circe-prompt-patch-multi-candidate-gate-v1"
    assert gate["overall_status"] == "accepted"
    assert gate["initial_loss"] == 0.20
    assert gate["best_loss"] == 0.12
    assert gate["final_loss"] == 0.12
    assert gate["accepted_candidate_id"] == "parameter-low-income"
    assert gate["candidate_evaluated_count"] == 2
    assert gate["candidate_accepted_count"] == 1
    assert gate["candidate_rejected_count"] == 1
    assert gate["generator_counts"] == {"parameter_search": 1, "residual_rule": 1}
    assert gate["candidate_updates"][0]["status"] == "rejected"
    assert gate["candidate_updates"][0]["reason"] == "not_best_improving_candidate"
    assert gate["candidate_updates"][1]["status"] == "accepted"
    assert (
        "food_price_sensitivity += 0.200000"
        in gate["candidate_updates"][1]["candidate_prompt_components"][
            "calibration_anchor"
        ]["low_income_food_insecure"]
    )
    assert (
        "food_price_sensitivity += 0.200000"
        in gate["final_prompt_components"]["calibration_anchor"][
            "low_income_food_insecure"
        ]
    )
    assert gate["final_prompt_components"] != components
    json.dumps(gate, allow_nan=False)


def test_multi_candidate_gate_rejects_non_improving_candidates_and_reverts():
    components = {
        "segment_prompt": {"general_population": "base prompt"},
    }
    candidate = PromptPatchCandidate(
        candidate_id="textgrad-general",
        generator="textgrad",
        rationale="LLM critique candidate",
        patches=[
            PromptPatch(
                target="segment_prompt.general_population",
                operation="tighten",
                reason="LLM critique",
                patch="Make reaction more deterministic.",
                expected_effect={"baseline_no_new_support": "increase"},
            )
        ],
    )

    gate = build_multi_candidate_prompt_patch_gate(
        components,
        [candidate],
        artifact_id="multi-candidate-reject-test",
        initial_loss=0.20,
        candidate_evaluations={
            "textgrad-general": {
                "loss": 0.24,
                "coverage_rate": 1.0,
                "evaluation_split": "heldout",
            }
        },
    )

    assert gate["overall_status"] == "rejected"
    assert gate["accepted_candidate_id"] is None
    assert gate["best_loss"] == 0.20
    assert gate["final_loss"] == 0.20
    assert gate["candidate_accepted_count"] == 0
    assert gate["candidate_rejected_count"] == 1
    assert gate["candidate_updates"][0]["reason"] == "loss_not_improved"
    assert gate["final_prompt_components"] == components


def test_multi_candidate_gate_rejects_calibration_split_evaluation():
    candidate = PromptPatchCandidate(
        candidate_id="leaky-candidate",
        generator="residual_rule",
        rationale="bad evaluation split",
        patches=[
            PromptPatch(
                target="segment_prompt.general_population",
                operation="tighten",
                reason="bad split",
                patch="Leak calibration targets.",
                expected_effect={"baseline_no_new_support": "increase"},
            )
        ],
    )

    with pytest.raises(ValueError, match="heldout"):
        build_multi_candidate_prompt_patch_gate(
            {"segment_prompt": {"general_population": "base"}},
            [candidate],
            artifact_id="leaky-candidate-test",
            initial_loss=0.20,
            candidate_evaluations={
                "leaky-candidate": {
                    "loss": 0.10,
                    "coverage_rate": 1.0,
                    "evaluation_split": "calibration",
                }
            },
        )
