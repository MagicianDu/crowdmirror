import json
import subprocess
import sys

from experiments.r6_false_alarm_control_report import (
    build_r6_claim_escalation_gate_report,
    build_r6_false_alarm_control_report,
)
from experiments.r6_outcome_holdout_registry_v2 import (
    build_r6_external_outcome_dataset_manifest,
    build_r6_holdout_validation_summary,
    build_r6_outcome_holdout_registry_v2,
)
from experiments.r6_trend_interval_calibration_report import (
    build_r6_trend_interval_calibration_report,
)


def test_wp1_outcome_holdout_registry_v2_declares_dataset_claim_levels():
    registry = build_r6_outcome_holdout_registry_v2(
        artifact_id="r6-outcome-holdout-registry-v2-test",
        run_id="r6-full-product-support-run",
    )

    assert registry["schema_version"] == "r6-outcome-holdout-registry-v2"
    assert registry["status"] == "holdout_registry_v2_ready_proxy_diagnostic"
    assert registry["acceptance_gates"]["field_outcome_validated"] is False
    assert registry["acceptance_gates"]["runtime_default_allowed"] is False
    assert registry["registry_summary"]["dataset_count"] >= 3
    assert registry["registry_summary"]["domain_count"] >= 2
    assert registry["registry_summary"]["proxy_diagnostic_count"] >= 3
    assert registry["registry_summary"]["field_outcome_count"] == 0

    required_fields = {
        "dataset_id",
        "domain",
        "source_type",
        "field_outcome_available",
        "proxy_outcome_available",
        "static_prior_fields",
        "scenario_shock_fields",
        "segment_label_fields",
        "allowed_claim_level",
        "known_limitations",
    }
    for dataset in registry["datasets"]:
        assert required_fields <= set(dataset)
        assert dataset["allowed_claim_level"] in {
            "validation",
            "proxy_diagnostic",
            "blocked",
        }
        if not dataset["field_outcome_available"]:
            assert dataset["allowed_claim_level"] != "validation"
    assert "field_outcome_validated=true" in registry["blocked_claims"]
    json.dumps(registry, allow_nan=False)


def test_wp1_external_manifest_and_holdout_summary_are_source_backed():
    manifest = build_r6_external_outcome_dataset_manifest(
        artifact_id="r6-external-outcome-dataset-manifest-test",
        run_id="r6-full-product-support-run",
    )
    summary = build_r6_holdout_validation_summary(
        artifact_id="r6-holdout-validation-summary-test",
        run_id="r6-full-product-support-run",
        external_manifest=manifest,
    )

    assert manifest["schema_version"] == "r6-external-outcome-dataset-manifest-v1"
    assert manifest["manifest_summary"]["dataset_count"] >= 3
    assert manifest["manifest_summary"]["domain_count"] >= 2
    assert all(dataset["source_refs"] for dataset in manifest["datasets"])
    assert summary["schema_version"] == "r6-holdout-validation-summary-v1"
    assert summary["acceptance_gates"]["all_metrics_source_backed"] is True
    assert summary["acceptance_gates"]["field_outcome_validated"] is False
    assert summary["claim_level"] == "proxy_diagnostic"
    json.dumps(summary, allow_nan=False)


def test_wp2_trend_interval_calibration_reports_required_metrics_and_downgrades_boundary():
    report = build_r6_trend_interval_calibration_report(
        artifact_id="r6-trend-interval-calibration-report-test",
        run_id="r6-full-product-support-run",
    )

    assert report["schema_version"] == "r6-trend-interval-calibration-report-v1"
    assert report["status"] == "trend_interval_calibration_interval_supported_trend_diagnostic"
    assert report["summary"]["trend_direction_accuracy"] == 0.667
    assert report["summary"]["interval_coverage"] == 1.0
    assert report["summary"]["mean_interval_width"] == 0.26
    assert "interval_efficiency" in report["summary"]
    assert "uncertainty_source_breakdown" in report["summary"]
    assert "indeterminate_rate" in report["summary"]
    assert report["acceptance_gates"]["trend_direction_passed"] is False
    assert report["acceptance_gates"]["interval_coverage_passed"] is True
    assert report["claim_status"] == "diagnostic"
    assert report["product_interval_confidence_level"] == "medium"

    allowed_directions = {
        "risk_up",
        "risk_down",
        "risk_divergent",
        "risk_diffusion",
        "risk_convergent",
        "uncertain",
    }
    for case in report["case_results"]:
        assert case["trend_direction"] in allowed_directions
        assert case["outcome_direction"] in allowed_directions
        assert set(case["uncertainty_source_breakdown"]) == {
            "static_prior_uncertainty",
            "interaction_propagation_uncertainty",
            "outcome_proxy_uncertainty",
        }
    json.dumps(report, allow_nan=False)


def test_wp4_false_alarm_control_and_claim_escalation_are_fail_closed():
    control = build_r6_false_alarm_control_report(
        artifact_id="r6-false-alarm-control-report-test",
        run_id="r6-full-product-support-run",
    )
    gate = build_r6_claim_escalation_gate_report(
        artifact_id="r6-claim-escalation-gate-report-test",
        run_id="r6-full-product-support-run",
        false_alarm_control_report=control,
    )

    assert control["schema_version"] == "r6-false-alarm-control-report-v1"
    assert control["status"] == "false_alarm_control_guarded_proxy_passed"
    assert control["summary"]["baseline_false_alarm_rate"] == 0.667
    assert control["summary"]["controlled_false_alarm_rate"] == 0.0
    assert control["summary"]["missed_risk_rate"] == 0.0
    assert control["summary"]["risk_escalation_precision"] == 1.0
    assert control["summary"]["risk_escalation_recall"] == 1.0
    assert control["acceptance_gates"]["current_proxy_control_passed"] is True
    assert control["acceptance_gates"]["holdout_validated"] is False
    assert control["acceptance_gates"]["runtime_default_allowed"] is False
    assert control["claim_status"] == "guarded"

    assert gate["schema_version"] == "r6-claim-escalation-gate-report-v1"
    assert gate["acceptance_gates"]["no_source_claim_rejected"] is True
    assert gate["acceptance_gates"]["runtime_default_allowed"] is False
    assert gate["escalation_summary"]["validated_claim_count"] == 0
    assert gate["escalation_summary"]["guarded_claim_count"] >= 1
    assert gate["escalation_summary"]["blocked_or_diagnostic_claim_count"] >= 1
    json.dumps(gate, allow_nan=False)


def test_round1_cli_writes_holdout_calibration_and_false_alarm_artifacts(tmp_path):
    commands = [
        (
            "experiments/r6_outcome_holdout_registry_v2.py",
            "r6-outcome-holdout-registry-v2-cli",
            "r6-outcome-holdout-registry-v2",
            "holdout_registry_v2_ready_proxy_diagnostic",
        ),
        (
            "experiments/r6_trend_interval_calibration_report.py",
            "r6-trend-interval-calibration-report-cli",
            "r6-trend-interval-calibration-report-v1",
            "trend_interval_calibration_interval_supported_trend_diagnostic",
        ),
        (
            "experiments/r6_false_alarm_control_report.py",
            "r6-false-alarm-control-report-cli",
            "r6-false-alarm-control-report-v1",
            "false_alarm_control_guarded_proxy_passed",
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
