import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_transfer_validation import (
    R12_TRANSFER_VALIDATION_SCHEMA_VERSION,
    build_r12_transfer_validation,
)


def test_r12_transfer_validation_reports_split_metrics_without_train_proof():
    report = build_r12_transfer_validation(
        artifact_id="r12-transfer-validation-test",
        run_id="r12-l3-test",
        r12_outcome_case_registry=_load_current_case_registry(),
        r12_causal_interaction_operator=_load_current_operator(),
        r12_outcome_supervised_update=_load_current_update(),
    )

    assert report["schema_version"] == R12_TRANSFER_VALIDATION_SCHEMA_VERSION
    assert report["status"] == "r12_transfer_validation_positive_guarded"
    assert report["claim_level"] == "guarded_public_proxy_transfer_signal"
    assert set(report["split_metrics"]) == {"train", "validation", "holdout"}
    assert report["transfer_accounting"] == {
        "train_metrics_reported": True,
        "train_metrics_used_for_transfer_decision": False,
        "validation_metrics_used_for_transfer_decision": True,
        "holdout_metrics_used_for_transfer_decision": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }


def test_r12_transfer_validation_finds_guarded_holdout_gain():
    report = build_r12_transfer_validation(
        artifact_id="r12-transfer-validation-test",
        run_id="r12-l3-test",
        r12_outcome_case_registry=_load_current_case_registry(),
        r12_causal_interaction_operator=_load_current_operator(),
        r12_outcome_supervised_update=_load_current_update(),
    )

    assert report["accepted_update"] == {
        "update_id": "r12-mechanism-weight-price-pressure-accepted-001",
        "update_type": "mechanism_weight",
        "target": "price_pressure",
        "recommended_value": 0.55,
        "runtime_default_allowed": False,
    }
    assert report["split_metrics"]["train"] == {
        "case_count": 2,
        "mean_absolute_error_before": 0.041323,
        "mean_absolute_error_after": 0.035285,
        "mean_absolute_error_delta": -0.006038,
        "interval_coverage_before": 1.0,
        "interval_coverage_after": 1.0,
        "interval_coverage_delta": 0.0,
        "false_alarm_rate_before": 0.0,
        "false_alarm_rate_after": 0.0,
        "false_alarm_rate_delta": 0.0,
    }
    assert report["split_metrics"]["validation"] == {
        "case_count": 2,
        "mean_absolute_error_before": 0.009743,
        "mean_absolute_error_after": 0.009312,
        "mean_absolute_error_delta": -0.000431,
        "interval_coverage_before": 1.0,
        "interval_coverage_after": 1.0,
        "interval_coverage_delta": 0.0,
        "false_alarm_rate_before": 0.0,
        "false_alarm_rate_after": 0.0,
        "false_alarm_rate_delta": 0.0,
    }
    assert report["split_metrics"]["holdout"] == {
        "case_count": 2,
        "mean_absolute_error_before": 0.005104,
        "mean_absolute_error_after": 0.004248,
        "mean_absolute_error_delta": -0.000856,
        "interval_coverage_before": 1.0,
        "interval_coverage_after": 1.0,
        "interval_coverage_delta": 0.0,
        "false_alarm_rate_before": 0.0,
        "false_alarm_rate_after": 0.0,
        "false_alarm_rate_delta": 0.0,
    }
    assert report["update_transfer_gain"] == 0.001287
    assert report["transfer_decision"] == "r12_update_transfer_positive_guarded"
    assert report["acceptance_gates"] == {
        "positive_transfer_guarded": True,
        "validation_mae_improved": True,
        "holdout_mae_improved": True,
        "interval_coverage_non_regression": True,
        "false_alarm_rate_non_regression": True,
        "train_metrics_used_for_transfer_decision": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert "field_outcome_validated=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_transfer_validation_cli_writes_artifact(tmp_path):
    registry_path = tmp_path / "r12-case-registry.json"
    operator_path = tmp_path / "r12-causal-operator.json"
    update_path = tmp_path / "r12-outcome-supervised-update.json"
    output = tmp_path / "r12-transfer-validation.json"
    registry_path.write_text(json.dumps(_load_current_case_registry(), allow_nan=False))
    operator_path.write_text(json.dumps(_load_current_operator(), allow_nan=False))
    update_path.write_text(json.dumps(_load_current_update(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_transfer_validation.py",
            "--artifact-id",
            "r12-transfer-validation-cli",
            "--run-id",
            "r12-l3-test",
            "--r12-outcome-case-registry-path",
            str(registry_path),
            "--r12-causal-interaction-operator-path",
            str(operator_path),
            "--r12-outcome-supervised-update-path",
            str(update_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r12-transfer-validation-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-transfer-validation-cli",
        "output": str(output),
        "status": "r12_transfer_validation_positive_guarded",
    }


def _load_current_case_registry():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_outcome_case_registry/"
            "r12-outcome-case-registry-current-001.json"
        ).read_text()
    )


def _load_current_operator():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_causal_interaction_operator/"
            "r12-causal-interaction-operator-current-001.json"
        ).read_text()
    )


def _load_current_update():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_outcome_supervised_update/"
            "r12-outcome-supervised-update-current-001.json"
        ).read_text()
    )
