import json
import subprocess
import sys

from experiments.r8_robustness_holdout_gate import build_r8_robustness_holdout_gate


def test_r8_robustness_gate_runs_all_required_validation_axes():
    report = build_r8_robustness_holdout_gate(
        artifact_id="r8-robustness-holdout-gate-test",
        run_id="r8-robustness-run",
    )

    assert report["schema_version"] == "r8-robustness-holdout-gate-v1"
    assert report["status"] in {
        "r8_holdout_positive_guarded",
        "r8_current_proxy_positive_guarded",
        "r8_robustness_diagnostic_or_stop_loss",
    }
    assert set(report["validation_axes"]) == {
        "outcome_perturbation",
        "leave_one_case",
        "same_family_holdout",
        "cross_family_fail_closed",
    }
    assert report["acceptance_gates"]["field_outcome_validated"] is False
    assert report["acceptance_gates"]["runtime_default_allowed"] is False
    json.dumps(report, allow_nan=False)


def test_r8_robustness_gate_reports_l1_l2_and_stop_loss_boundary():
    report = build_r8_robustness_holdout_gate(
        artifact_id="r8-robustness-holdout-gate-test",
        run_id="r8-robustness-run",
    )

    assert report["summary"]["perturbation_scenario_count"] == 9
    assert report["summary"]["leave_one_case_trial_count"] == 3
    assert report["summary"]["same_family_holdout_trial_count"] >= 1
    assert report["summary"]["cross_family_fail_closed_trial_count"] >= 1
    assert report["l1_status"] in {"passed_guarded", "diagnostic_blocked"}
    assert report["l2_status"] in {"passed_guarded", "diagnostic_blocked"}
    assert report["stop_loss_recommendation"] in {
        "continue_to_product_ingestion_guarded",
        "keep_r8_as_diagnostic_asset",
        "stop_loss_r8_main_method",
    }


def test_r8_robustness_gate_cli_writes_artifact(tmp_path):
    output = tmp_path / "r8-robustness-holdout-gate.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r8_robustness_holdout_gate.py",
            "--artifact-id",
            "r8-robustness-holdout-gate-cli",
            "--run-id",
            "r8-robustness-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r8-robustness-holdout-gate-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r8-robustness-holdout-gate-cli",
        "output": str(output),
        "status": artifact["status"],
    }
