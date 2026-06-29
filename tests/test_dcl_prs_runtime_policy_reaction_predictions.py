import json

from circe.llm_client import LLMResponse
from experiments.dcl_prs_runtime_policy_reaction_predictions import (
    build_dcl_prs_runtime_policy_reaction_predictions,
    write_dcl_prs_runtime_policy_reaction_predictions,
)


def test_dcl_prs_runtime_predictions_emit_official_prediction_schema():
    artifact = build_dcl_prs_runtime_policy_reaction_predictions(
        calibration_ingestion=_calibration_ingestion(),
        artifact_id="dcl-prs-runtime-predictions-test",
        provider="openai",
        model="fake-model",
        base_url="http://127.0.0.1:1234/v1",
        completion_fn=_fake_completion,
        llm_weight=0.25,
    )

    assert artifact["schema_version"] == "policy-reaction-segment-predictions-v1"
    assert artifact["artifact_id"] == "dcl-prs-runtime-predictions-test"
    assert artifact["method_family"] == "DCL-PRS-runtime"
    assert artifact["source_split_contract"] == {
        "constraint_anchor": "calibration",
        "runtime_prediction_generation": "llm_over_calibration_constraints",
        "runtime_effect_evaluation": "heldout_required",
    }
    assert set(artifact["segment_predictions"]) == {
        "fixed_income_inflation_stressed",
        "general_population_cost_pressure",
    }
    fixed = artifact["segment_predictions"]["fixed_income_inflation_stressed"]
    assert fixed["policy_probabilities"] == {
        "baseline_no_new_support": 0.425,
        "cash_cost_of_living_rebate": 0.275,
        "food_subsidy_expansion": 0.3,
    }
    assert fixed["constraint_anchor_distribution"] == {
        "baseline_no_new_support": 0.5,
        "cash_cost_of_living_rebate": 0.3,
        "food_subsidy_expansion": 0.2,
    }
    assert fixed["llm_raw_probabilities"] == {
        "baseline_no_new_support": 0.2,
        "cash_cost_of_living_rebate": 0.2,
        "food_subsidy_expansion": 0.6,
    }
    assert artifact["llm_accounting"]["total_call_count"] == 2
    assert artifact["llm_accounting"]["parse_failure_count"] == 0
    assert "local_model_only" in artifact["risk_flags"]
    json.dumps(artifact, allow_nan=False)


def test_dcl_prs_runtime_predictions_fallback_to_anchor_on_parse_failure():
    artifact = build_dcl_prs_runtime_policy_reaction_predictions(
        calibration_ingestion=_calibration_ingestion(),
        artifact_id="dcl-prs-runtime-predictions-test",
        provider="openai",
        model="fake-model",
        base_url="http://127.0.0.1:1234/v1",
        completion_fn=lambda system, user: LLMResponse(
            content="not-json",
            input_tokens=3,
            output_tokens=2,
        ),
    )

    fixed = artifact["segment_predictions"]["fixed_income_inflation_stressed"]
    assert fixed["policy_probabilities"] == fixed["constraint_anchor_distribution"]
    assert artifact["llm_accounting"]["parse_failure_count"] == 2
    assert "llm_parse_failures_used_anchor_fallback" in artifact["risk_flags"]


def test_write_dcl_prs_runtime_predictions(tmp_path):
    calibration = tmp_path / "calibration.json"
    output = tmp_path / "predictions.json"
    calibration.write_text(json.dumps(_calibration_ingestion()))

    written = write_dcl_prs_runtime_policy_reaction_predictions(
        output,
        calibration_ingestion_path=calibration,
        artifact_id="dcl-prs-runtime-predictions-test",
        provider="openai",
        model="fake-model",
        base_url="http://127.0.0.1:1234/v1",
        completion_fn=_fake_completion,
    )

    assert written == output
    persisted = json.loads(output.read_text())
    assert persisted["artifact_id"] == "dcl-prs-runtime-predictions-test"
    assert persisted["method_family"] == "DCL-PRS-runtime"


def _fake_completion(system: str, user: str) -> LLMResponse:
    assert "policy reaction" in system
    assert "evaluation" not in user.lower()
    return LLMResponse(
        content=json.dumps(
            {
                "baseline_no_new_support": 0.2,
                "cash_cost_of_living_rebate": 0.2,
                "food_subsidy_expansion": 0.6,
            }
        ),
        input_tokens=10,
        output_tokens=5,
    )


def _calibration_ingestion() -> dict:
    return {
        "schema_version": "policy-reaction-public-data-ingestion-v1",
        "artifact_id": "policy-reaction-calibration-ingestion-test",
        "overall_status": "passed",
        "observed_policy_reaction_summary": {
            "by_segment": {
                "fixed_income_inflation_stressed": {
                    "row_count": 100,
                    "weighted_row_mass": 100.0,
                    "weighted_mean_policy_reaction": {
                        "baseline_no_new_support": 0.5,
                        "cash_cost_of_living_rebate": 0.3,
                        "food_subsidy_expansion": 0.2,
                    },
                },
                "general_population_cost_pressure": {
                    "row_count": 200,
                    "weighted_row_mass": 200.0,
                    "weighted_mean_policy_reaction": {
                        "baseline_no_new_support": 0.6,
                        "cash_cost_of_living_rebate": 0.25,
                        "food_subsidy_expansion": 0.15,
                    },
                },
            }
        },
    }
