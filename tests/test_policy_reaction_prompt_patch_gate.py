import json
from pathlib import Path

from experiments.policy_reaction_prompt_patch_gate import (
    build_policy_reaction_prompt_patch_candidate,
    build_policy_reaction_prompt_patch_gate,
    load_json_artifact,
    write_policy_reaction_prompt_patch_gate,
)


def test_build_policy_reaction_candidate_uses_calibration_split_residuals():
    calibration = _calibration_benchmark()

    candidate = build_policy_reaction_prompt_patch_candidate(
        calibration,
        candidate_id="policy-reaction-calibration-candidate",
        residual_threshold=0.05,
        parameter_threshold=0.05,
    )

    payload = candidate.to_dict()
    assert payload["candidate_id"] == "policy-reaction-calibration-candidate"
    assert payload["generator"] == "policy_reaction_residual_parameter"
    assert payload["source_split"] == "calibration"
    assert payload["metadata"]["calibration_benchmark_artifact_id"] == (
        "policy-reaction-calibration-benchmark-test"
    )
    assert payload["metadata"]["residual_patch_count"] == 2
    assert payload["metadata"]["parameter_patch_count"] == 2
    assert {
        patch["target"].split(".", 1)[0] for patch in payload["patches"]
    } == {"segment_prompt", "calibration_anchor"}
    assert any(
        patch["target"] == "segment_prompt.low_income_food_insecure"
        for patch in payload["patches"]
    )
    json.dumps(payload, allow_nan=False)


def test_policy_reaction_prompt_patch_gate_accepts_heldout_candidate():
    gate = build_policy_reaction_prompt_patch_gate(
        _calibration_benchmark(),
        _initial_heldout_benchmark(),
        _candidate_heldout_benchmark(),
        artifact_id="policy-reaction-prompt-patch-gate-test",
        candidate_id="policy-reaction-calibration-candidate",
    )

    assert gate["schema_version"] == "policy-reaction-prompt-patch-gate-v1"
    assert gate["prompt_patch_gate_schema_version"] == (
        "circe-prompt-patch-multi-candidate-gate-v1"
    )
    assert gate["overall_status"] == "accepted"
    assert gate["calibration_benchmark_artifact_id"] == (
        "policy-reaction-calibration-benchmark-test"
    )
    assert gate["initial_heldout_benchmark_artifact_id"] == (
        "policy-reaction-heldout-initial-test"
    )
    assert gate["candidate_heldout_benchmark_artifact_id"] == (
        "policy-reaction-heldout-candidate-test"
    )
    assert gate["loss_metric"] == "weighted_choice_distribution_jsd"
    assert gate["initial_loss"] == 0.24
    assert gate["best_loss"] == 0.08
    assert gate["final_loss"] == 0.08
    assert gate["candidate_accepted_count"] == 1
    assert gate["candidate_rejected_count"] == 0
    assert gate["accepted_candidate_id"] == "policy-reaction-calibration-candidate"
    assert gate["candidate_updates"][0]["evaluation_split"] == "heldout"
    assert gate["candidate_updates"][0]["coverage_rate"] == 1.0
    assert gate["candidate_updates"][0]["status"] == "accepted"
    assert gate["source_split_contract"] == {
        "candidate_generation": "calibration",
        "candidate_acceptance": "heldout",
    }
    assert gate["final_prompt_components"] != gate["initial_prompt_components"]
    json.dumps(gate, allow_nan=False)


def test_policy_reaction_prompt_patch_gate_rejects_non_heldout_acceptance_split():
    candidate = _candidate_heldout_benchmark()
    candidate["source_ingestion_artifact_id"] = "policy-reaction-calibration-ingestion"

    try:
        build_policy_reaction_prompt_patch_gate(
            _calibration_benchmark(),
            _initial_heldout_benchmark(),
            candidate,
            artifact_id="policy-reaction-prompt-patch-gate-leaky-test",
        )
    except ValueError as exc:
        assert "held-out" in str(exc)
    else:
        raise AssertionError("expected held-out split validation error")


def test_write_policy_reaction_prompt_patch_gate_from_artifacts(tmp_path):
    calibration_path = tmp_path / "calibration.json"
    initial_path = tmp_path / "initial-heldout.json"
    candidate_path = tmp_path / "candidate-heldout.json"
    output_path = tmp_path / "gate.json"
    calibration_path.write_text(json.dumps(_calibration_benchmark()))
    initial_path.write_text(json.dumps(_initial_heldout_benchmark()))
    candidate_path.write_text(json.dumps(_candidate_heldout_benchmark()))

    written = write_policy_reaction_prompt_patch_gate(
        output_path,
        calibration_benchmark_path=calibration_path,
        initial_heldout_benchmark_path=initial_path,
        candidate_heldout_benchmark_path=candidate_path,
        artifact_id="policy-reaction-prompt-patch-gate-test",
    )

    assert written == output_path
    persisted = load_json_artifact(output_path)
    assert persisted["artifact_id"] == "policy-reaction-prompt-patch-gate-test"
    assert persisted["overall_status"] == "accepted"


def _calibration_benchmark() -> dict:
    return {
        "schema_version": "policy-reaction-official-segment-benchmark-v1",
        "artifact_id": "policy-reaction-calibration-benchmark-test",
        "source_ingestion_artifact_id": "policy-reaction-htops-calibration-ingestion",
        "prediction_artifact_id": "policy-reaction-initial-predictions-test",
        "overall_status": "passed",
        "benchmark_metrics": {"weighted_choice_distribution_jsd": 0.20},
        "segment_coverage": {"coverage_rate": 1.0},
        "segment_metrics": {
            "low_income_food_insecure": {
                "official_distribution": {
                    "baseline_no_new_support": 0.20,
                    "cash_cost_of_living_rebate": 0.25,
                    "food_subsidy_expansion": 0.55,
                },
                "predicted_distribution": {
                    "baseline_no_new_support": 0.05,
                    "cash_cost_of_living_rebate": 0.35,
                    "food_subsidy_expansion": 0.60,
                },
            },
            "general_population_cost_pressure": {
                "official_distribution": {
                    "baseline_no_new_support": 0.55,
                    "cash_cost_of_living_rebate": 0.27,
                    "food_subsidy_expansion": 0.18,
                },
                "predicted_distribution": {
                    "baseline_no_new_support": 0.10,
                    "cash_cost_of_living_rebate": 0.34,
                    "food_subsidy_expansion": 0.56,
                },
            },
        },
    }


def _initial_heldout_benchmark() -> dict:
    return {
        "schema_version": "policy-reaction-official-segment-benchmark-v1",
        "artifact_id": "policy-reaction-heldout-initial-test",
        "source_ingestion_artifact_id": "policy-reaction-htops-evaluation-ingestion",
        "prediction_artifact_id": "policy-reaction-initial-predictions-test",
        "overall_status": "passed",
        "benchmark_metrics": {"weighted_choice_distribution_jsd": 0.24},
        "segment_coverage": {"coverage_rate": 1.0},
        "segment_metrics": {},
    }


def _candidate_heldout_benchmark() -> dict:
    return {
        "schema_version": "policy-reaction-official-segment-benchmark-v1",
        "artifact_id": "policy-reaction-heldout-candidate-test",
        "source_ingestion_artifact_id": "policy-reaction-htops-evaluation-ingestion",
        "prediction_artifact_id": "policy-reaction-candidate-predictions-test",
        "overall_status": "passed",
        "benchmark_metrics": {"weighted_choice_distribution_jsd": 0.08},
        "segment_coverage": {"coverage_rate": 1.0},
        "segment_metrics": {},
    }
