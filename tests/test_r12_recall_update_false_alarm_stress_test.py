import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_recall_update_false_alarm_stress_test import (
    R12_RECALL_UPDATE_FALSE_ALARM_STRESS_SCHEMA_VERSION,
    build_r12_recall_update_false_alarm_stress_test,
)


def test_r12_recall_update_false_alarm_stress_blocks_product_default():
    report = build_r12_recall_update_false_alarm_stress_test(
        artifact_id="r12-recall-update-false-alarm-stress-test",
        run_id="r12-l8-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_recall_oriented_update=_load_current_recall_update(),
    )

    assert (
        report["schema_version"]
        == R12_RECALL_UPDATE_FALSE_ALARM_STRESS_SCHEMA_VERSION
    )
    assert (
        report["status"]
        == "r12_recall_update_false_alarm_stress_blocked_product_default"
    )
    assert report["claim_level"] == (
        "research_only_recall_positive_false_alarm_stress_failed"
    )
    assert report["evaluation_summary"] == {
        "evaluated_case_count": 70,
        "observed_high_risk_case_count": 29,
        "observed_low_risk_case_count": 41,
        "low_sensitive_case_count": 4,
        "protected_or_high_governance_case_count": 66,
        "product_default_low_sensitive_high_risk_case_count": 0,
        "newly_recovered_count": 6,
        "new_false_alarm_count": 3,
        "minimum_valid_response_count": 100,
    }
    assert report["stress_metrics"]["global_tradeoff"] == {
        "recall_delta": 0.206897,
        "false_alarm_rate_delta": 0.073171,
        "precision_delta": -0.03,
        "interval_coverage_delta": 0.0,
    }
    assert report["stress_metrics"]["low_sensitive_false_alarm"] == {
        "evaluable_case_count": 4,
        "observed_high_risk_case_count": 0,
        "false_alarm_rate_before": 0.0,
        "false_alarm_rate_after": 0.0,
        "false_alarm_rate_delta": 0.0,
        "new_false_alarm_count": 0,
        "recall_evaluable": False,
    }
    assert report["stress_metrics"]["protected_sensitive_false_alarm"] == {
        "evaluable_case_count": 31,
        "observed_high_risk_case_count": 28,
        "false_alarm_rate_before": 0.129032,
        "false_alarm_rate_after": 0.225806,
        "false_alarm_rate_delta": 0.096774,
        "new_false_alarm_count": 3,
    }
    assert report["stress_metrics"]["worst_segment_family"] == {
        "segment_column": "TAGE",
        "sensitivity_level": "protected_sensitive",
        "evaluated_case_count": 52,
        "observed_high_risk_case_count": 26,
        "observed_low_risk_case_count": 26,
        "recall_delta": 0.153846,
        "false_alarm_rate_delta": 0.115385,
        "new_false_alarm_count": 3,
    }
    assert report["stress_metrics"]["false_alarm_concentration"] == {
        "new_false_alarm_case_ids": [
            "hps_TAGE_58",
            "hps_TAGE_59",
            "hps_TAGE_62",
        ],
        "dominant_segment_column": "TAGE",
        "dominant_segment_new_false_alarm_share": 1.0,
        "sensitive_or_high_governance_new_false_alarm_share": 1.0,
    }
    assert report["acceptance_gates"] == {
        "source_backed_public_proxy_present": True,
        "l7_recall_gain_preserved": True,
        "low_sensitive_false_alarm_non_regression": True,
        "low_sensitive_recall_evaluable": False,
        "global_false_alarm_non_regression": False,
        "protected_sensitive_false_alarm_non_regression": False,
        "precision_non_regression": False,
        "new_false_alarms_concentrated_on_sensitive_axis": True,
        "stress_test_passed": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "reject_product_default_keep_research_guarded_candidate"
    )
    assert report["next_required_artifact"] == (
        "r12_recall_false_alarm_mitigation_candidate"
    )
    assert "r12 recall update false-alarm stress passed" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_recall_update_false_alarm_stress_reports_family_table():
    report = build_r12_recall_update_false_alarm_stress_test(
        artifact_id="r12-recall-update-false-alarm-stress-test",
        run_id="r12-l8-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_recall_oriented_update=_load_current_recall_update(),
    )

    assert report["family_stress_table"] == [
        {
            "segment_column": "ESEX",
            "sensitivity_level": "protected_sensitive",
            "evaluated_case_count": 2,
            "observed_high_risk_case_count": 1,
            "observed_low_risk_case_count": 1,
            "recall_delta": 1.0,
            "false_alarm_rate_delta": 0.0,
            "newly_recovered_count": 1,
            "new_false_alarm_count": 0,
        },
        {
            "segment_column": "METRO_STATUS",
            "sensitivity_level": "low",
            "evaluated_case_count": 1,
            "observed_high_risk_case_count": 0,
            "observed_low_risk_case_count": 1,
            "recall_delta": None,
            "false_alarm_rate_delta": 0.0,
            "newly_recovered_count": 0,
            "new_false_alarm_count": 0,
        },
        {
            "segment_column": "REGION",
            "sensitivity_level": "low",
            "evaluated_case_count": 3,
            "observed_high_risk_case_count": 0,
            "observed_low_risk_case_count": 3,
            "recall_delta": None,
            "false_alarm_rate_delta": 0.0,
            "newly_recovered_count": 0,
            "new_false_alarm_count": 0,
        },
        {
            "segment_column": "RHHINCOME",
            "sensitivity_level": "socioeconomic_sensitive",
            "evaluated_case_count": 7,
            "observed_high_risk_case_count": 1,
            "observed_low_risk_case_count": 6,
            "recall_delta": 0.0,
            "false_alarm_rate_delta": 0.0,
            "newly_recovered_count": 0,
            "new_false_alarm_count": 0,
        },
        {
            "segment_column": "RRACETH",
            "sensitivity_level": "protected_sensitive",
            "evaluated_case_count": 5,
            "observed_high_risk_case_count": 1,
            "observed_low_risk_case_count": 4,
            "recall_delta": 1.0,
            "false_alarm_rate_delta": 0.0,
            "newly_recovered_count": 1,
            "new_false_alarm_count": 0,
        },
        {
            "segment_column": "TAGE",
            "sensitivity_level": "protected_sensitive",
            "evaluated_case_count": 52,
            "observed_high_risk_case_count": 26,
            "observed_low_risk_case_count": 26,
            "recall_delta": 0.153846,
            "false_alarm_rate_delta": 0.115385,
            "newly_recovered_count": 4,
            "new_false_alarm_count": 3,
        },
    ]


def test_r12_recall_update_false_alarm_stress_cli_writes_artifact(tmp_path):
    hps_path = tmp_path / "hps-ingestion.json"
    transfer_path = tmp_path / "r12-transfer-validation.json"
    recall_update_path = tmp_path / "r12-recall-update.json"
    output = tmp_path / "r12-recall-update-false-alarm-stress-test.json"
    hps_path.write_text(json.dumps(_load_current_hps_ingestion(), allow_nan=False))
    transfer_path.write_text(
        json.dumps(_load_current_transfer_validation(), allow_nan=False)
    )
    recall_update_path.write_text(
        json.dumps(_load_current_recall_update(), allow_nan=False)
    )

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_recall_update_false_alarm_stress_test.py",
            "--artifact-id",
            "r12-recall-update-false-alarm-stress-test-cli",
            "--run-id",
            "r12-l8-test",
            "--hps-ingestion-path",
            str(hps_path),
            "--r12-transfer-validation-path",
            str(transfer_path),
            "--r12-recall-oriented-update-path",
            str(recall_update_path),
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
        "r12-recall-update-false-alarm-stress-test-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-recall-update-false-alarm-stress-test-cli",
        "output": str(output),
        "status": "r12_recall_update_false_alarm_stress_blocked_product_default",
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
