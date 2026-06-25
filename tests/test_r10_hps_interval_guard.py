import json
import subprocess
import sys

from experiments.r10_hps_combination_comparison import build_r10_hps_combination_comparison
from experiments.r10_hps_interval_guard import (
    R10_HPS_INTERVAL_GUARD_SCHEMA_VERSION,
    build_r10_hps_interval_guard,
)
from tests.test_r10_hps_combination_comparison import _build_fixture_retrieval


def test_r10_hps_interval_guard_preserves_ranking_gain_and_blocks_interval_regression(tmp_path):
    comparison = build_r10_hps_combination_comparison(
        artifact_id="r10-hps-combination-comparison-test",
        run_id="r10-l4-run",
        hps_precedent_retrieval=_build_fixture_retrieval(tmp_path),
    )

    guard = build_r10_hps_interval_guard(
        artifact_id="r10-hps-interval-guard-test",
        run_id="r10-l4-run",
        hps_combination_comparison=comparison,
    )

    assert guard["schema_version"] == R10_HPS_INTERVAL_GUARD_SCHEMA_VERSION
    assert guard["status"] == "r10_hps_interval_guard_ready_guarded"
    assert guard["guard_contract"] == {
        "source_backed_only": True,
        "uses_real_public_data_ingestion": True,
        "preserves_risk_ranking_candidate": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert guard["source_refs"] == ["r10-hps-combination-comparison-test"]
    assert guard["pre_guard_summary"] == {
        "risk_ranking_quality_delta": 0.083,
        "interval_coverage_delta": -0.333,
        "interval_non_regression_passed": False,
    }
    assert guard["guard_action"] == {
        "action_id": "apply_r9_interval_floor_to_hps_overlay",
        "reason": "hps_overlay_interval_regressed_without_holdout_mapping",
        "preserved_signal": "risk_ranking_quality_delta",
        "blocked_effect": "interval_coverage_regression",
    }
    assert guard["post_guard_metrics"]["r10_A+B_hps+C_guarded_overlay"] == {
        "trend_direction_accuracy": 0.667,
        "interval_coverage": 1.0,
        "risk_ranking_quality": 0.75,
        "false_alarm_rate": 0.0,
        "static_prior_miss_recovery_rate": 1.0,
        "decision_value_score": 0.78,
    }
    assert guard["post_guard_summary"] == {
        "risk_ranking_quality_delta": 0.083,
        "interval_coverage_delta": 0.0,
        "decision_value_delta": 0.0,
        "net_decision": "continue_guarded_holdout_mapping_with_interval_floor",
    }
    assert guard["acceptance_gates"] == {
        "source_comparison_present": True,
        "pre_guard_interval_regression_detected": True,
        "post_guard_interval_non_regression_passed": True,
        "risk_ranking_gain_preserved": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert "R10 supports Product core method by default" in guard["blocked_claims"]
    json.dumps(guard, allow_nan=False)


def test_r10_hps_interval_guard_cli_writes_artifact(tmp_path):
    comparison = build_r10_hps_combination_comparison(
        artifact_id="r10-hps-combination-comparison-cli-input",
        run_id="r10-l4-run",
        hps_precedent_retrieval=_build_fixture_retrieval(tmp_path),
    )
    comparison_path = tmp_path / "comparison.json"
    comparison_path.write_text(json.dumps(comparison, allow_nan=False))
    output = tmp_path / "r10-hps-interval-guard.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r10_hps_interval_guard.py",
            "--artifact-id",
            "r10-hps-interval-guard-cli",
            "--run-id",
            "r10-l4-run",
            "--hps-combination-comparison-path",
            str(comparison_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r10-hps-interval-guard-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r10-hps-interval-guard-cli",
        "output": str(output),
        "status": "r10_hps_interval_guard_ready_guarded",
    }
