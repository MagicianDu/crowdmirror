import json
import subprocess
import sys

from experiments.r10_hps_combination_comparison import (
    R10_HPS_COMBINATION_COMPARISON_SCHEMA_VERSION,
    build_r10_hps_combination_comparison,
)
from experiments.r10_hps_policy_reaction_ingestion import (
    build_r10_hps_policy_reaction_ingestion,
)
from experiments.r10_hps_precedent_retrieval import build_r10_hps_precedent_retrieval
from tests.test_r10_hps_policy_reaction_ingestion import _write_hps_fixture_zip


def test_r10_hps_combination_comparison_adds_route_b_evidence_without_escalation(tmp_path):
    retrieval = _build_fixture_retrieval(tmp_path)

    report = build_r10_hps_combination_comparison(
        artifact_id="r10-hps-combination-comparison-test",
        run_id="r10-l3-run",
        hps_precedent_retrieval=retrieval,
    )

    assert report["schema_version"] == R10_HPS_COMBINATION_COMPARISON_SCHEMA_VERSION
    assert report["status"] == "r10_hps_combination_comparison_ready_guarded"
    assert report["comparison_contract"] == {
        "source_backed_only": True,
        "uses_real_public_data_ingestion": True,
        "compares_against_r9_guarded_baseline": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert report["source_refs"] == ["r10-hps-precedent-retrieval-test"]
    assert report["method_ids"] == [
        "r9_A+B+C_guarded_current_fixture",
        "r10_A+B_hps+C_guarded_overlay",
    ]
    assert report["method_metrics"]["r9_A+B+C_guarded_current_fixture"] == {
        "trend_direction_accuracy": 0.667,
        "interval_coverage": 1.0,
        "risk_ranking_quality": 0.667,
        "false_alarm_rate": 0.0,
        "static_prior_miss_recovery_rate": 1.0,
        "decision_value_score": 0.78,
    }
    assert report["method_metrics"]["r10_A+B_hps+C_guarded_overlay"] == {
        "trend_direction_accuracy": 0.667,
        "interval_coverage": 0.667,
        "risk_ranking_quality": 0.75,
        "false_alarm_rate": 0.0,
        "static_prior_miss_recovery_rate": 1.0,
        "decision_value_score": 0.78,
    }
    assert report["evidence_gain_summary"] == {
        "external_public_data_ingested": True,
        "route_b_source_backed_precedent_available": True,
        "risk_ranking_quality_delta": 0.083,
        "interval_coverage_delta": -0.333,
        "decision_value_delta": 0.0,
        "net_decision": "continue_guarded_holdout_mapping_before_product_escalation",
    }
    assert report["winner_by_metric"]["risk_ranking_quality"]["method"] == (
        "r10_A+B_hps+C_guarded_overlay"
    )
    assert report["winner_by_metric"]["interval_coverage"]["method"] == (
        "r9_A+B+C_guarded_current_fixture"
    )
    assert report["acceptance_gates"] == {
        "hps_precedent_retrieval_present": True,
        "r9_guarded_baseline_present": True,
        "comparison_metrics_present": True,
        "source_backed_risk_ranking_gain_present": True,
        "interval_non_regression_passed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert "R10 supports Product core method by default" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r10_hps_combination_comparison_cli_writes_artifact(tmp_path):
    retrieval = _build_fixture_retrieval(tmp_path)
    retrieval_path = tmp_path / "hps-retrieval.json"
    retrieval_path.write_text(json.dumps(retrieval, allow_nan=False))
    output = tmp_path / "r10-hps-combination-comparison.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r10_hps_combination_comparison.py",
            "--artifact-id",
            "r10-hps-combination-comparison-cli",
            "--run-id",
            "r10-l3-run",
            "--hps-precedent-retrieval-path",
            str(retrieval_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r10-hps-combination-comparison-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r10-hps-combination-comparison-cli",
        "output": str(output),
        "status": "r10_hps_combination_comparison_ready_guarded",
    }


def _build_fixture_retrieval(tmp_path):
    ingestion = build_r10_hps_policy_reaction_ingestion(
        artifact_id="r10-hps-policy-reaction-ingestion-test",
        run_id="r10-l3-run",
        input_zip_path=_write_hps_fixture_zip(tmp_path),
    )
    return build_r10_hps_precedent_retrieval(
        artifact_id="r10-hps-precedent-retrieval-test",
        run_id="r10-l3-run",
        hps_ingestion=ingestion,
    )
