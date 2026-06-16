import json
import subprocess
import sys

from experiments.r6_gap_closure_report import build_r6_gap_closure_report


def test_r6_gap_closure_report_keeps_empirical_gaps_open():
    report = build_r6_gap_closure_report(
        artifact_id="r6-gap-closure-report-test",
        run_id="r6-gap-closure-run",
    )

    assert report["schema_version"] == "r6-gap-closure-report-v1"
    assert report["status"] == "gap_closure_artifact_ready"
    assert report["gap_statuses"] == {
        "theory_gap": "closed_by_artifact",
        "data_holdout_gap": "blocked_missing_data",
        "method_operator_gap": "partial_diagnostic",
        "product_gap": "closed_by_guarded_cards",
    }
    assert report["acceptance_gates"] == {
        "formal_problem_definition_present": True,
        "risk_discovery_value_defined": True,
        "holdout_registry_present": True,
        "independent_holdout_missing_slots_visible": True,
        "operator_v2_structured": True,
        "operator_v2_runtime_default_allowed": False,
        "gap_closure_report_present": True,
        "product_gap_cards_required": True,
        "ccf_a_main_contribution_ready": False,
        "field_outcome_validated": False,
    }
    assert "needs_independent_same_family_operator_holdout" in report["remaining_gaps"]
    assert "needs_real_or_field_outcome_proxy" in report["remaining_gaps"]
    json.dumps(report, allow_nan=False)


def test_r6_gap_closure_report_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-gap-closure-report.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_gap_closure_report.py",
            "--artifact-id",
            "r6-gap-closure-report-cli",
            "--run-id",
            "r6-gap-closure-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.read_text().endswith("\n")
    report = json.loads(output.read_text())
    assert report["schema_version"] == "r6-gap-closure-report-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-gap-closure-report-cli",
        "output": str(output),
        "status": "gap_closure_artifact_ready",
    }
