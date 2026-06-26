import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_recall_mitigation_holdout_validation import (
    R12_RECALL_MITIGATION_HOLDOUT_VALIDATION_SCHEMA_VERSION,
    build_r12_recall_mitigation_holdout_validation,
)


def test_r12_recall_mitigation_holdout_validation_blocks_product_default():
    report = build_r12_recall_mitigation_holdout_validation(
        artifact_id="r12-recall-mitigation-holdout-validation-test",
        run_id="r12-l10-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_recall_oriented_update=_load_current_recall_update(),
        r12_recall_false_alarm_mitigation_candidate=_load_current_mitigation(),
    )

    assert report["schema_version"] == (
        R12_RECALL_MITIGATION_HOLDOUT_VALIDATION_SCHEMA_VERSION
    )
    assert (
        report["status"]
        == "r12_recall_mitigation_holdout_validation_blocked_overfit"
    )
    assert report["claim_level"] == (
        "mitigation_candidate_not_holdout_validated"
    )
    assert report["validation_summary"] == {
        "evaluated_case_count": 70,
        "independent_dataset_present": False,
        "independent_holdout_case_count": 0,
        "customer_approved_holdout_case_count": 0,
        "low_sensitive_recall_evaluable": False,
        "false_alarm_band_derivation_case_count": 3,
        "leave_one_false_alarm_trial_count": 3,
    }
    assert report["current_replay_metrics"] == {
        "candidate_id": "r12-tage-58-62-activation-guard-001",
        "recall_delta": 0.172414,
        "l7_recall_gain_retained": 0.833333,
        "false_alarm_rate_delta": 0.0,
        "precision_delta": 0.059524,
        "new_false_alarm_count": 0,
    }
    assert report["leave_one_false_alarm_band_validation"] == {
        "trial_count": 3,
        "pass_count": 1,
        "pass_rate": 0.333333,
        "endpoint_holdout_failure_count": 2,
        "required_pass_rate": 0.666667,
        "trials": [
            {
                "held_out_false_alarm_case_id": "hps_TAGE_58",
                "derived_guard_min": 59,
                "derived_guard_max": 62,
                "holdout_false_alarm_removed": False,
                "recall_delta": 0.172414,
                "false_alarm_rate_delta": 0.02439,
                "precision_delta": 0.022727,
                "passes_trial": False,
            },
            {
                "held_out_false_alarm_case_id": "hps_TAGE_59",
                "derived_guard_min": 58,
                "derived_guard_max": 62,
                "holdout_false_alarm_removed": True,
                "recall_delta": 0.172414,
                "false_alarm_rate_delta": 0.0,
                "precision_delta": 0.059524,
                "passes_trial": True,
            },
            {
                "held_out_false_alarm_case_id": "hps_TAGE_62",
                "derived_guard_min": 58,
                "derived_guard_max": 59,
                "holdout_false_alarm_removed": False,
                "recall_delta": 0.206897,
                "false_alarm_rate_delta": 0.02439,
                "precision_delta": 0.032609,
                "passes_trial": False,
            },
        ],
    }
    assert report["stable_alternative_check"] == {
        "candidate_id": "r12-tage-family-conservative-cap-001",
        "recall_delta": 0.068966,
        "l7_recall_gain_retained": 0.333333,
        "false_alarm_rate_delta": 0.0,
        "precision_delta": 0.027778,
        "new_false_alarm_count": 0,
        "stable_but_recall_retention_too_low": True,
    }
    assert report["acceptance_gates"] == {
        "source_backed_public_proxy_present": True,
        "current_replay_positive": True,
        "independent_holdout_present": False,
        "leave_one_false_alarm_band_stable": False,
        "holdout_pass_rate_sufficient": False,
        "low_sensitive_recall_evaluable": False,
        "stable_alternative_retains_required_recall": False,
        "mitigation_holdout_validated": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "reject_product_default_retain_as_failure_diagnosis_candidate"
    )
    assert report["next_required_artifact"] == (
        "r12_recall_mitigation_independent_holdout_data"
    )
    assert (
        "mitigation holdout validated"
        in report["blocked_claims"]
    )
    json.dumps(report, allow_nan=False)


def test_r12_recall_mitigation_holdout_validation_cli_writes_artifact(tmp_path):
    hps_path = tmp_path / "hps-ingestion.json"
    transfer_path = tmp_path / "r12-transfer-validation.json"
    recall_update_path = tmp_path / "r12-recall-update.json"
    mitigation_path = tmp_path / "r12-mitigation.json"
    output = tmp_path / "r12-recall-mitigation-holdout-validation.json"
    hps_path.write_text(json.dumps(_load_current_hps_ingestion(), allow_nan=False))
    transfer_path.write_text(
        json.dumps(_load_current_transfer_validation(), allow_nan=False)
    )
    recall_update_path.write_text(
        json.dumps(_load_current_recall_update(), allow_nan=False)
    )
    mitigation_path.write_text(
        json.dumps(_load_current_mitigation(), allow_nan=False)
    )

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_recall_mitigation_holdout_validation.py",
            "--artifact-id",
            "r12-recall-mitigation-holdout-validation-cli",
            "--run-id",
            "r12-l10-test",
            "--hps-ingestion-path",
            str(hps_path),
            "--r12-transfer-validation-path",
            str(transfer_path),
            "--r12-recall-oriented-update-path",
            str(recall_update_path),
            "--r12-recall-false-alarm-mitigation-candidate-path",
            str(mitigation_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == (
        "r12-recall-mitigation-holdout-validation-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-recall-mitigation-holdout-validation-cli",
        "output": str(output),
        "status": "r12_recall_mitigation_holdout_validation_blocked_overfit",
    }


def _load_current_hps_ingestion():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r10_hps_policy_reaction_ingestion/"
            "r10-hps-policy-reaction-ingestion-current-001.json"
        ).read_text()
    )


def _load_current_transfer_validation():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_transfer_validation/"
            "r12-transfer-validation-current-001.json"
        ).read_text()
    )


def _load_current_recall_update():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_recall_oriented_update/"
            "r12-recall-oriented-update-current-001.json"
        ).read_text()
    )


def _load_current_mitigation():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_recall_false_alarm_mitigation_candidate/"
            "r12-recall-false-alarm-mitigation-candidate-current-001.json"
        ).read_text()
    )
