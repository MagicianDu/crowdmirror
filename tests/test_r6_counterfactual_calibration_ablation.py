from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from experiments.r6_counterfactual_calibration_ablation import (
    build_r6_counterfactual_calibration_ablation,
)


def test_counterfactual_calibration_ablation_separates_component_effects():
    report = build_r6_counterfactual_calibration_ablation(
        artifact_id="r6-counterfactual-calibration-ablation-test",
        run_id="r6-counterfactual-calibration-run",
    )

    assert report["schema_version"] == "r6-counterfactual-calibration-ablation-v1"
    assert report["status"] == "counterfactual_calibration_ablation_guarded_supported"
    assert report["selected_variant_id"] == "floor_plus_non_regression_calibration"

    variants = {
        variant["variant_id"]: variant
        for variant in report["variant_results"]
    }
    learned_only = variants["learned_weights_only"]
    floor_only = variants["unseen_floor_only"]
    full = variants["floor_plus_non_regression_calibration"]

    assert learned_only["summary"]["static_prior_miss_recovery_rate"] == 0.0
    assert floor_only["summary"]["static_prior_miss_recovery_rate"] == 1.0
    assert floor_only["summary"]["non_regression_rate"] < 1.0
    assert full["summary"]["static_prior_miss_recovery_rate"] == 1.0
    assert full["summary"]["non_regression_rate"] == 1.0
    assert full["summary"]["false_alarm_reduction_rate"] == 1.0
    assert full["component_contribution"] == [
        "unseen_mechanism_floor_recovers_static_prior_miss_signal",
        "risk_preserving_calibration_restores_non_regression",
        "false_alarm_reduction_preserved",
    ]


def test_counterfactual_calibration_ablation_reports_stress_grid_and_fail_closed():
    report = build_r6_counterfactual_calibration_ablation(
        artifact_id="r6-counterfactual-calibration-ablation-test",
        run_id="r6-counterfactual-calibration-run",
    )

    assert len(report["stress_grid_results"]) >= 8
    passing = [
        item for item in report["stress_grid_results"]
        if item["passes_current_proxy_holdout_gate"]
    ]
    assert passing
    assert all(item["risk_preserving_calibration_enabled"] for item in passing)
    assert report["acceptance_gates"] == {
        "ablation_variants_present": True,
        "selected_variant_non_regression_passed": True,
        "selected_variant_false_alarm_reduction_passed": True,
        "selected_variant_static_miss_recovery_passed": True,
        "current_proxy_holdout_gate_passed": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert "needs_field_or_customer_outcome_validation" in report["blocking_gaps"]
    assert "runtime_default_allowed=true" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_counterfactual_calibration_ablation_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-counterfactual-calibration-ablation.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_counterfactual_calibration_ablation.py",
            "--artifact-id",
            "r6-counterfactual-calibration-ablation-cli",
            "--run-id",
            "r6-counterfactual-calibration-run",
            "--output",
            str(output),
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    stdout = json.loads(completed.stdout)
    artifact = json.loads(Path(output).read_text())
    assert stdout["status"] == "counterfactual_calibration_ablation_guarded_supported"
    assert stdout["output"] == str(output)
    assert artifact["schema_version"] == "r6-counterfactual-calibration-ablation-v1"
