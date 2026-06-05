import json
import subprocess
import sys

from experiments.r6_foundation_pipeline import build_r6_foundation_pipeline
from experiments.r6_contracts import R6_CLAIM_BOUNDARY


def test_r6_foundation_pipeline_builds_full_artifact_chain():
    package = build_r6_foundation_pipeline(
        artifact_id="r6-foundation-test",
        run_id="r6-run-test",
    )

    assert package["schema_version"] == "r6-foundation-package-v1"
    assert package["artifact_id"] == "r6-foundation-test"
    assert package["run_id"] == "r6-run-test"
    assert package["status"] == "diagnostic_ready"
    assert package["claim_boundaries"] == [R6_CLAIM_BOUNDARY]
    assert "not_accuracy_superiority_evidence" in package["risk_flags"]

    prior = package["prior_manifest"]
    scenario = package["scenario_manifest"]
    trace = package["interaction_trace"]
    risk = package["risk_shift_report"]
    outcome = package["outcome_manifest"]
    learning = package["learning_report"]
    registry = package["update_registry"]

    assert prior["schema_version"] == "r6-prior-manifest-v1"
    assert prior["overall_status"] == "passed"
    assert prior["response_options"] == ["accept", "neutral", "reject"]
    assert prior["aggregate_static_response_prior"] == {
        "accept": 0.47,
        "neutral": 0.25,
        "reject": 0.28,
    }
    assert prior["no_interaction_control"]["enabled"] is True

    assert scenario["schema_version"] == "r6-scenario-manifest-v1"
    assert scenario["change_type"] == "price"
    assert scenario["industry_binding"] == "generic"
    assert "fairness_concern" in scenario["impact_dimensions"]

    assert trace["schema_version"] == "r6-interaction-trace-v1"
    assert trace["overall_status"] == "passed"
    assert trace["rounds"] == 3
    assert trace["event_count"] == 6
    assert trace["interaction_result_distribution"]["reject"] > (
        trace["static_prior_distribution"]["reject"]
    )
    assert trace["delta_distribution"] == {
        "accept": -0.04,
        "neutral": -0.03,
        "reject": 0.07,
    }

    assert risk["schema_version"] == "r6-risk-shift-report-v1"
    assert risk["overall_static_reject_rate"] == 0.28
    assert risk["overall_interaction_reject_rate"] == 0.35
    assert risk["delta"] == 0.07
    assert risk["top_risk_segments"][0]["segment_id"] == "sensitive_low_trust"
    assert risk["claim_boundary"] == R6_CLAIM_BOUNDARY

    assert outcome["schema_version"] == "r6-outcome-manifest-v1"
    assert outcome["metrics"]["observed_reject_proxy"] == 0.41
    assert outcome["data_quality_flags"] == ["proxy_metric_not_direct_attitude"]

    assert learning["schema_version"] == "r6-learning-report-v1"
    assert learning["prediction_vs_outcome"]["predicted_reject_rate"] == 0.35
    assert learning["prediction_vs_outcome"]["observed_reject_proxy"] == 0.41
    assert learning["prediction_vs_outcome"]["absolute_error"] == 0.06
    assert learning["error_attribution"][0]["type"] == "mechanism_error"
    assert learning["update_policy"] == "human_review_required"

    assert registry["schema_version"] == "r6-update-registry-v1"
    assert registry["overall_status"] == "needs_more_outcomes"
    assert registry["updates"][0]["status"] == "diagnostic_only"
    assert registry["updates"][0]["default_runtime_enabled"] is False

    json.dumps(package, allow_nan=False)


def test_r6_foundation_pipeline_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-foundation.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_foundation_pipeline.py",
            "--artifact-id",
            "r6-foundation-test",
            "--run-id",
            "r6-run-test",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-foundation-test",
        "output": str(output),
        "status": "diagnostic_ready",
        "update_status": "needs_more_outcomes",
    }
    assert output.read_text().endswith("\n")
    package = json.loads(output.read_text())
    assert package["schema_version"] == "r6-foundation-package-v1"
    assert package["update_registry"]["overall_status"] == "needs_more_outcomes"

