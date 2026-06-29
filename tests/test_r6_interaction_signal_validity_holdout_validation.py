import json
import subprocess
import sys

from experiments.r6_interaction_signal_validity_holdout_validation import (
    build_r6_interaction_signal_validity_holdout_validation,
)


def test_r6_interaction_signal_validity_holdout_validation_blocks_single_supported_proxy():
    report = build_r6_interaction_signal_validity_holdout_validation(
        artifact_id="r6-interaction-signal-validity-holdout-test",
        run_id="r6-interaction-signal-validity-holdout-run",
    )

    assert report["schema_version"] == (
        "r6-interaction-signal-validity-holdout-validation-v1"
    )
    assert report["status"] == (
        "interaction_signal_validity_holdout_failed_current_public_proxies"
    )
    assert report["summary"] == {
        "case_count": 3,
        "source_supported_count": 1,
        "eligible_independent_holdout_count": 2,
        "passed_holdout_count": 0,
        "contradicted_holdout_count": 2,
        "generalized_signal_count": 0,
    }
    assert report["acceptance_gates"] == {
        "interaction_signal_validity_holdout_validation_present": True,
        "frozen_score_rule_has_no_holdout_label_leakage": True,
        "independent_holdout_available": True,
        "source_supported_signal_available": True,
        "passed_independent_holdout_count_positive": False,
        "interaction_signal_validity_holdout_passed": False,
        "field_outcome_validated": False,
    }
    assert [
        (
            trial["trial_id"],
            trial["validation_status"],
            trial["source_case"]["classification"],
            trial["holdout_case"]["classification"],
            trial["holdout_case"]["holdout_outcome_support"],
        )
        for trial in report["holdout_trials"]
    ] == [
        (
            "signal-validity:htops_cost_pressure->anes_health_heldout",
            "failed_holdout_contradicts_signal",
            "diagnostic_only",
            "reject_as_likely_false_alarm",
            "contradicted",
        ),
        (
            "signal-validity:htops_cost_pressure->anes_climate_heldout",
            "failed_holdout_contradicts_signal",
            "diagnostic_only",
            "reject_as_likely_false_alarm",
            "contradicted",
        ),
    ]
    assert report["decision"] == {
        "interaction_signal_validity_holdout_passed": False,
        "decision": "do_not_generalize_interaction_signal_validity_yet",
        "recommended_next_step": "add_independent_supported_holdout_or_field_outcome",
    }
    assert "needs_independent_supported_signal_holdout" in report["blocking_gaps"]
    assert "current_holdouts_contradict_supported_signal" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_interaction_signal_validity_holdout_validation_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-interaction-signal-validity-holdout-validation.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_interaction_signal_validity_holdout_validation.py",
            "--artifact-id",
            "r6-interaction-signal-validity-holdout-cli",
            "--run-id",
            "r6-interaction-signal-validity-holdout-run",
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
    assert report["schema_version"] == (
        "r6-interaction-signal-validity-holdout-validation-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-interaction-signal-validity-holdout-cli",
        "interaction_signal_validity_holdout_passed": False,
        "output": str(output),
        "status": "interaction_signal_validity_holdout_failed_current_public_proxies",
    }
