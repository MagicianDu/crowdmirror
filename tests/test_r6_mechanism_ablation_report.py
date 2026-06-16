import json
import subprocess
import sys

from experiments.r6_mechanism_ablation_report import (
    build_r6_mechanism_ablation_report,
)


def test_r6_mechanism_ablation_report_keeps_static_prior_and_false_alarm_visible():
    report = build_r6_mechanism_ablation_report(
        artifact_id="r6-mechanism-ablation-report-test",
        run_id="r6-mechanism-ablation-report-run",
    )

    assert report["schema_version"] == "r6-mechanism-ablation-report-v1"
    assert report["status"] == "mechanism_ablation_diagnostic_only"
    assert report["method_summary"] == {
        "case_count": 3,
        "method_count": 5,
        "mechanism_positive_case_count": 1,
        "mechanism_regression_case_count": 2,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_gates"] == {
        "mechanism_trace_present": True,
        "dynamic_path_distinct_from_static_prior": True,
        "mechanism_ablation_positive": False,
        "false_alarm_not_hidden": True,
        "product_guard_preserved": True,
    }
    methods = {result["method"] for result in report["case_method_results"]}
    assert {
        "static_prior",
        "no_propagation_interaction",
        "random_propagation",
        "mechanism_propagation",
        "behavioral_update_candidate",
    } <= methods
    by_case_method = {
        (result["source_key"], result["method"]): result
        for result in report["case_method_results"]
    }
    assert by_case_method[
        ("htops_cost_pressure", "mechanism_propagation")
    ]["beats_static_prior"] is True
    assert by_case_method[
        ("anes_health_heldout", "mechanism_propagation")
    ]["beats_static_prior"] is False
    assert "mechanism_ablation_not_ccf_a_ready" in report["risk_flags"]
    assert "needs_operator_holdout_validation" in report["blocking_gaps"]
    json.dumps(report, allow_nan=False)


def test_r6_mechanism_ablation_report_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-mechanism-ablation-report.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_mechanism_ablation_report.py",
            "--artifact-id",
            "r6-mechanism-ablation-report-cli",
            "--run-id",
            "r6-mechanism-ablation-report-run",
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
    assert report["schema_version"] == "r6-mechanism-ablation-report-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-mechanism-ablation-report-cli",
        "mechanism_positive_case_count": 1,
        "output": str(output),
        "status": "mechanism_ablation_diagnostic_only",
    }
