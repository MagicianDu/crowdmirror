import json
import subprocess
import sys

from experiments.r6_behavioral_update_operator_v3 import (
    build_r6_behavioral_update_operator_v3,
    build_r6_mechanism_operator_ablation_report,
    build_r6_operator_holdout_non_regression_report,
)
from experiments.r6_outcome_feedback_learning import (
    build_r6_bounded_update_candidate,
    build_r6_feedback_transfer_validation,
    build_r6_outcome_feedback_review,
)


def test_wp5_behavioral_update_operator_v3_is_structured_and_guarded():
    report = build_r6_behavioral_update_operator_v3(
        artifact_id="r6-behavioral-update-operator-v3-test",
        run_id="r6-full-product-support-run",
    )

    assert report["schema_version"] == "r6-behavioral-update-operator-v3"
    assert report["status"] == "operator_v3_guarded_static_fallback_ready"
    assert report["runtime_default_allowed"] is False
    assert report["summary"]["operator_holdout_pass_rate"] == 1.0
    assert report["summary"]["operator_non_regression_rate"] == 1.0
    assert report["summary"]["static_prior_guard_passed"] is True
    assert report["summary"]["runtime_default_allowed"] is False

    mechanisms = {mechanism["mechanism_id"] for mechanism in report["mechanisms"]}
    assert mechanisms == {
        "interest_loss_propagation",
        "trust_decline_propagation",
        "service_dependency_propagation",
        "rule_sensitivity_propagation",
        "peer_influence_propagation",
        "reverse_resistance_response",
    }
    for case in report["case_results"]:
        assert "structured_risk_delta" in case
        assert case["guard_decision"] in {
            "apply_guarded_interaction",
            "fallback_to_static_prior",
        }
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_wp5_mechanism_operator_ablation_and_non_regression_reports_pass_proxy_guard():
    operator = build_r6_behavioral_update_operator_v3(
        artifact_id="r6-behavioral-update-operator-v3-test",
        run_id="r6-full-product-support-run",
    )
    ablation = build_r6_mechanism_operator_ablation_report(
        artifact_id="r6-mechanism-operator-ablation-report-test",
        run_id="r6-full-product-support-run",
        behavioral_update_operator_v3=operator,
    )
    non_regression = build_r6_operator_holdout_non_regression_report(
        artifact_id="r6-operator-holdout-non-regression-report-test",
        run_id="r6-full-product-support-run",
        behavioral_update_operator_v3=operator,
        mechanism_operator_ablation_report=ablation,
    )

    assert ablation["schema_version"] == "r6-mechanism-operator-ablation-report-v1"
    assert ablation["status"] == "mechanism_operator_ablation_guarded_proxy"
    assert ablation["summary"]["mechanism_ablation_delta"] > 0
    assert ablation["acceptance_gates"]["mechanism_ablation_explains_risk_change"] is True
    assert ablation["acceptance_gates"]["runtime_default_allowed"] is False

    assert non_regression["schema_version"] == "r6-operator-holdout-non-regression-report-v1"
    assert non_regression["status"] == "operator_holdout_non_regression_proxy_passed_runtime_blocked"
    assert non_regression["summary"]["operator_holdout_pass_rate"] == 1.0
    assert non_regression["summary"]["operator_non_regression_rate"] == 1.0
    assert non_regression["acceptance_gates"]["operator_non_regression_rate_passed"] is True
    assert non_regression["acceptance_gates"]["field_outcome_validated"] is False
    assert non_regression["acceptance_gates"]["runtime_default_allowed"] is False
    json.dumps(non_regression, allow_nan=False)


def test_wp6_outcome_feedback_review_and_bounded_candidate_are_auditable():
    review = build_r6_outcome_feedback_review(
        artifact_id="r6-outcome-feedback-review-test",
        run_id="r6-full-product-support-run",
    )
    candidate = build_r6_bounded_update_candidate(
        artifact_id="r6-bounded-update-candidate-test",
        run_id="r6-full-product-support-run",
        outcome_feedback_review=review,
    )

    assert review["schema_version"] == "r6-outcome-feedback-review-v1"
    assert review["status"] == "outcome_feedback_review_ready"
    assert review["summary"]["reviewed_case_count"] == 3
    assert review["acceptance_gates"]["outcome_review_artifact_present"] is True
    assert review["acceptance_gates"]["field_outcome_validated"] is False

    assert candidate["schema_version"] == "r6-bounded-update-candidate-v1"
    assert candidate["status"] == "bounded_update_candidate_rejected_runtime_guard"
    assert candidate["initial_loss"] > candidate["candidate_loss"]
    assert candidate["final_loss"] == candidate["initial_loss"]
    assert candidate["candidate_accepted"] is False
    assert candidate["candidate_rejected_reason"] == "runtime_guard_or_field_outcome_missing"
    assert set(candidate["updated_components"]) == {
        "segment_weight_update",
        "mechanism_strength_update",
        "scenario_similarity_update",
        "interval_calibration_update",
        "false_alarm_discriminator_update",
        "blocked_claim_policy_update",
    }
    assert candidate["guard_results"]["runtime_default_allowed"] is False
    assert candidate["rollback_policy"]["rollback_to_static_prior_on_guard_failure"] is True
    json.dumps(candidate, allow_nan=False)


def test_wp6_feedback_transfer_validation_reports_rejected_candidate_boundary():
    validation = build_r6_feedback_transfer_validation(
        artifact_id="r6-feedback-transfer-validation-test",
        run_id="r6-full-product-support-run",
    )

    assert validation["schema_version"] == "r6-feedback-transfer-validation-v1"
    assert validation["status"] == "feedback_transfer_validation_ready_update_blocked"
    assert validation["acceptance_gates"]["bounded_update_candidate_present"] is True
    assert validation["acceptance_gates"]["candidate_has_accept_reject_decision"] is True
    assert validation["acceptance_gates"]["runtime_default_allowed"] is False
    assert validation["summary"]["candidate_accepted"] is False
    assert "候选更新已可自动上线" in validation["blocked_claims"]
    json.dumps(validation, allow_nan=False)


def test_round3_cli_writes_operator_and_feedback_artifacts(tmp_path):
    commands = [
        (
            "experiments/r6_behavioral_update_operator_v3.py",
            "r6-behavioral-update-operator-v3-cli",
            "r6-behavioral-update-operator-v3",
            "operator_v3_guarded_static_fallback_ready",
        ),
        (
            "experiments/r6_outcome_feedback_learning.py",
            "r6-outcome-feedback-review-cli",
            "r6-outcome-feedback-review-v1",
            "outcome_feedback_review_ready",
        ),
    ]

    for script, artifact_id, schema_version, status in commands:
        output = tmp_path / f"{artifact_id}.json"
        completed = subprocess.run(
            [
                sys.executable,
                script,
                "--artifact-id",
                artifact_id,
                "--run-id",
                "r6-full-product-support-run",
                "--output",
                str(output),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert completed.returncode == 0, completed.stderr
        payload = json.loads(output.read_text())
        assert payload["schema_version"] == schema_version
        assert payload["status"] == status
        stdout = json.loads(completed.stdout)
        assert stdout["artifact_id"] == artifact_id
        assert stdout["status"] == status
