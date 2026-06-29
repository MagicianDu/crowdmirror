from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from experiments.r6_counterfactual_robustness_validation import (
    build_r6_counterfactual_robustness_validation,
)


def test_counterfactual_robustness_validation_reports_local_proxy_perturbation_failure():
    report = build_r6_counterfactual_robustness_validation(
        artifact_id="r6-counterfactual-robustness-validation-test",
        run_id="r6-counterfactual-robustness-run",
    )

    assert report["schema_version"] == "r6-counterfactual-robustness-validation-v1"
    assert report["status"] == "counterfactual_robustness_diagnostic_blocked"
    assert report["summary"]["perturbation_scenario_count"] >= 9
    assert report["summary"]["robustness_pass_rate"] == 0.889
    assert report["summary"]["min_non_regression_rate"] == 0.667
    assert report["summary"]["min_false_alarm_reduction_rate"] == 0.5
    assert report["summary"]["min_static_prior_miss_recovery_rate"] == 1.0
    assert report["acceptance_gates"]["local_proxy_robustness_passed"] is False
    assert report["acceptance_gates"]["field_outcome_validated"] is False
    assert report["acceptance_gates"]["runtime_default_allowed"] is False

    failed = [
        scenario for scenario in report["perturbation_scenarios"]
        if not scenario["passes_current_proxy_holdout_gate"]
    ]
    assert len(failed) == 1
    assert failed[0]["scenario_id"] == "anes_health_heldout:+0.03"
    assert failed[0]["summary"]["non_regression_rate"] == 0.667


def test_counterfactual_robustness_validation_keeps_claim_boundary_fail_closed():
    report = build_r6_counterfactual_robustness_validation(
        artifact_id="r6-counterfactual-robustness-validation-test",
        run_id="r6-counterfactual-robustness-run",
    )

    assert "field_outcome_validated=true" in report["blocked_claims"]
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    assert "needs_field_or_customer_outcome_validation" in report["blocking_gaps"]
    assert "needs_external_outcome_robustness_validation" in report["blocking_gaps"]
    assert "needs_near_threshold_false_alarm_calibration" in report["blocking_gaps"]
    assert report["claim_status"] == "diagnostic"
    json.dumps(report, allow_nan=False)


def test_counterfactual_robustness_validation_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-counterfactual-robustness-validation.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_counterfactual_robustness_validation.py",
            "--artifact-id",
            "r6-counterfactual-robustness-validation-cli",
            "--run-id",
            "r6-counterfactual-robustness-run",
            "--output",
            str(output),
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    stdout = json.loads(completed.stdout)
    artifact = json.loads(Path(output).read_text())
    assert stdout["status"] == "counterfactual_robustness_diagnostic_blocked"
    assert stdout["output"] == str(output)
    assert artifact["schema_version"] == "r6-counterfactual-robustness-validation-v1"
