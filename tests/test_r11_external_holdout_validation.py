import json
import subprocess
import sys

from experiments.r10_hps_policy_reaction_ingestion import (
    build_r10_hps_policy_reaction_ingestion,
)
from experiments.r11_external_holdout_validation import (
    R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION,
    build_r11_external_holdout_validation,
)
from experiments.r11_interaction_risk_discoverer import (
    build_r11_interaction_risk_discoverer,
)
from tests.test_r10_hps_policy_reaction_ingestion import _write_hps_fixture_zip


def test_r11_external_holdout_validation_reports_proxy_holdout_without_escalation(tmp_path):
    report = build_r11_external_holdout_validation(
        artifact_id="r11-external-holdout-test",
        run_id="r11-l1-test",
        r11_interaction_risk_discoverer=_build_r11(),
        hps_ingestion=_build_fixture_hps(tmp_path),
    )

    assert report["schema_version"] == R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION
    assert report["status"] == "r11_external_holdout_validation_blocked"
    assert report["claim_level"] == "public_use_proxy_holdout_only"
    assert report["validation_contract"] == {
        "source_backed_public_use_proxy": True,
        "source_signal": "PRICECONCERN",
        "holdout_outcome_proxy": "PRICESTRESS",
        "independent_slice_or_proxy": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_gates"]["external_public_use_holdout_present"] is True
    assert report["acceptance_gates"]["external_holdout_passed_guarded"] is False
    assert report["acceptance_gates"]["product_core_method_ready"] is False
    assert report["acceptance_gates"]["field_outcome_validated"] is False
    assert report["acceptance_gates"]["runtime_default_allowed"] is False
    assert "R11 supports Product core method by default" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r11_external_holdout_validation_records_metric_failures_and_stop_loss_reasons(tmp_path):
    report = build_r11_external_holdout_validation(
        artifact_id="r11-external-holdout-test",
        run_id="r11-l1-test",
        r11_interaction_risk_discoverer=_build_r11(),
        hps_ingestion=_build_fixture_hps(tmp_path),
    )

    assert report["external_holdout_summary"]["case_count"] == 3
    assert report["external_holdout_summary"]["segment_columns"] == [
        "REGION",
        "METRO_STATUS",
    ]
    assert report["method_metrics"]["r11_external_holdout_transfer"] == {
        "trend_direction_accuracy": 0.333,
        "interval_coverage": 0.333,
        "risk_ranking_quality": 0.5,
        "false_alarm_rate": 1.0,
        "static_prior_miss_recovery_rate": 0.0,
        "abnormal_segment_recall": 0.0,
    }
    assert report["stop_loss_or_next_step"] == (
        "do_not_escalate_r11_until_external_holdout_failures_are_resolved"
    )
    assert report["failure_reasons"] == [
        "risk_ranking_quality_below_external_holdout_floor",
        "interval_coverage_below_external_holdout_floor",
        "false_alarm_rate_above_external_holdout_ceiling",
        "static_prior_miss_recovery_below_external_holdout_floor",
        "abnormal_segment_recall_below_external_holdout_floor",
    ]


def test_r11_external_holdout_validation_cli_writes_artifact(tmp_path):
    r11_path = tmp_path / "r11.json"
    hps_path = tmp_path / "hps.json"
    output = tmp_path / "r11-external-holdout.json"
    r11_path.write_text(json.dumps(_build_r11(), allow_nan=False))
    hps_path.write_text(json.dumps(_build_fixture_hps(tmp_path), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r11_external_holdout_validation.py",
            "--artifact-id",
            "r11-external-holdout-cli",
            "--run-id",
            "r11-l1-test",
            "--r11-path",
            str(r11_path),
            "--hps-ingestion-path",
            str(hps_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r11-external-holdout-validation-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r11-external-holdout-cli",
        "output": str(output),
        "status": "r11_external_holdout_validation_blocked",
    }


def _build_r11():
    return build_r11_interaction_risk_discoverer(
        artifact_id="r11-l0-test",
        run_id="r11-l1-test",
    )


def _build_fixture_hps(tmp_path):
    return build_r10_hps_policy_reaction_ingestion(
        artifact_id="hps-ingestion-test",
        run_id="r11-l1-test",
        input_zip_path=_write_hps_fixture_zip(tmp_path),
    )
