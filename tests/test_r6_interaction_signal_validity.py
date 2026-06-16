import copy
import json
import subprocess
import sys

from experiments.r6_interaction_signal_validity import (
    build_r6_interaction_signal_validity,
)


def test_r6_interaction_signal_validity_scores_cases_without_family_gate():
    report = build_r6_interaction_signal_validity(
        artifact_id="r6-interaction-signal-validity-test",
        run_id="r6-interaction-signal-validity-run",
    )

    assert report["schema_version"] == "r6-interaction-signal-validity-v1"
    assert report["status"] == "interaction_signal_validity_diagnostic_only"
    assert report["scoring_policy"]["forbidden_scoring_features"] == [
        "source_key",
        "target_case_id",
        "target_case_type",
    ]
    assert set(report["scoring_policy"]["scoring_feature_names"]).isdisjoint(
        {"source_key", "target_case_id", "target_case_type"}
    )
    assert report["summary"] == {
        "case_count": 3,
        "accepted_count": 0,
        "diagnostic_only_count": 1,
        "rejected_false_alarm_count": 2,
        "needs_more_outcome_count": 0,
        "current_proxy_supported_signal_count": 1,
        "generalized_accept_count": 0,
        "forbidden_label_feature_count": 0,
        "mean_validity_score": 0.763,
    }
    assert report["acceptance_gates"] == {
        "interaction_signal_validity_present": True,
        "forbidden_label_features_excluded": True,
        "case_level_validity_scores_present": True,
        "current_proxy_supported_signal_observed": True,
        "likely_false_alarm_cases_identified": True,
        "interaction_signal_validity_generalized": False,
        "field_outcome_validated": False,
    }

    by_source = {
        case["audit"]["source_key"]: case
        for case in report["case_validity_scores"]
    }
    assert by_source["htops_cost_pressure"]["classification"] == "diagnostic_only"
    assert by_source["htops_cost_pressure"]["validity_score"] == 0.93
    assert by_source["htops_cost_pressure"]["classification_reason"] == (
        "current_proxy_supports_signal_but_generalization_missing"
    )
    assert by_source["anes_health_heldout"]["classification"] == (
        "reject_as_likely_false_alarm"
    )
    assert by_source["anes_health_heldout"]["validity_score"] == 0.68
    assert by_source["anes_climate_heldout"]["classification"] == (
        "reject_as_likely_false_alarm"
    )
    for case in report["case_validity_scores"]:
        assert set(case["scoring_inputs"]).isdisjoint(
            {"source_key", "target_case_id", "target_case_type"}
        )
        assert set(case["component_scores"]) == {
            "segment_pattern_score",
            "mechanism_alignment_score",
            "counterfactual_sensitivity_score",
            "prior_uncertainty_score",
            "holdout_consistency_score",
        }
    assert "case_source_family_gate_not_used_for_scoring" in report["risk_flags"]
    assert "needs_interaction_signal_validity_generalization" in report[
        "blocking_gaps"
    ]
    json.dumps(report, allow_nan=False)


def test_r6_interaction_signal_validity_is_invariant_to_audit_labels():
    base_case = _minimal_case_evidence()
    relabeled_case = copy.deepcopy(base_case)
    relabeled_case["audit"] = {
        "source_key": "different_source",
        "target_case_id": "different_target_case",
        "target_case_type": "different_target_type",
        "public_proxy_artifact_id": "different_proxy",
    }

    base_report = build_r6_interaction_signal_validity(
        artifact_id="r6-interaction-signal-validity-label-base",
        run_id="r6-interaction-signal-validity-label-run",
        case_evidence=[base_case],
    )
    relabeled_report = build_r6_interaction_signal_validity(
        artifact_id="r6-interaction-signal-validity-label-mutated",
        run_id="r6-interaction-signal-validity-label-run",
        case_evidence=[relabeled_case],
    )

    base_score = base_report["case_validity_scores"][0]
    relabeled_score = relabeled_report["case_validity_scores"][0]
    assert base_score["audit"] != relabeled_score["audit"]
    assert base_score["scoring_fingerprint"] == relabeled_score[
        "scoring_fingerprint"
    ]
    assert base_score["component_scores"] == relabeled_score["component_scores"]
    assert base_score["validity_score"] == relabeled_score["validity_score"]
    assert base_score["classification"] == relabeled_score["classification"]


def test_r6_interaction_signal_validity_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-interaction-signal-validity.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_interaction_signal_validity.py",
            "--artifact-id",
            "r6-interaction-signal-validity-cli",
            "--run-id",
            "r6-interaction-signal-validity-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_text().endswith("\n")
    report = json.loads(output.read_text())
    assert report["schema_version"] == "r6-interaction-signal-validity-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-interaction-signal-validity-cli",
        "interaction_signal_validity_generalized": False,
        "output": str(output),
        "status": "interaction_signal_validity_diagnostic_only",
    }


def _minimal_case_evidence():
    return {
        "audit": {
            "source_key": "source_a",
            "target_case_id": "target_a",
            "target_case_type": "type_a",
            "public_proxy_artifact_id": "proxy_a",
        },
        "case_result": {
            "interaction_flags_new_risk": True,
            "observed_high_risk": True,
            "recovered_static_prior_miss": True,
            "interaction_false_alarm": False,
            "observed_reject_proxy": 0.47,
            "static_prior_prediction": 0.29,
            "interaction_prediction": 0.36,
            "interaction_delta_vs_static": 0.07,
        },
        "prior_manifest": {
            "segments": [
                {
                    "segment_id": "high_uncertainty",
                    "uncertainty": 0.19,
                    "static_traits": {"sensitivity": "high", "trust": "low"},
                    "static_response_prior": {
                        "accept": 0.24,
                        "neutral": 0.29,
                        "reject": 0.47,
                    },
                },
                {
                    "segment_id": "stable",
                    "uncertainty": 0.12,
                    "static_traits": {"sensitivity": "low", "trust": "high"},
                    "static_response_prior": {
                        "accept": 0.62,
                        "neutral": 0.26,
                        "reject": 0.12,
                    },
                },
            ],
        },
        "scenario_manifest": {
            "impact_dimensions": ["access_constraint", "equity_concern"],
            "alternative_scenarios": ["no_support_channel", "community_explanation"],
        },
        "interaction_trace": {
            "delta_distribution": {"accept": -0.02, "neutral": -0.05, "reject": 0.07},
            "segment_shifts": [
                {
                    "segment_id": "high_uncertainty",
                    "mechanisms": ["access_anxiety", "equity_concern"],
                    "delta_distribution": {
                        "accept": -0.07,
                        "neutral": -0.05,
                        "reject": 0.12,
                    },
                },
                {
                    "segment_id": "stable",
                    "mechanisms": ["official_trust_buffer"],
                    "delta_distribution": {
                        "accept": -0.01,
                        "neutral": -0.01,
                        "reject": 0.02,
                    },
                },
            ],
        },
        "risk_shift_report": {
            "delta": 0.07,
            "top_risk_segments": [
                {
                    "segment_id": "high_uncertainty",
                    "delta_reject": 0.12,
                    "mechanisms": ["access_anxiety", "equity_concern"],
                }
            ],
        },
        "public_proxy_summary": {
            "observed_reject_proxy": 0.47,
            "usable_row_count": 100,
        },
    }
