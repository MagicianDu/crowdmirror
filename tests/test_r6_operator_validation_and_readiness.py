import json
import subprocess
import sys

from experiments.r6_mechanism_research_readiness_report import (
    build_r6_mechanism_research_readiness_report,
)
from experiments.r6_operator_holdout_validation import (
    build_r6_operator_holdout_validation,
)


def test_r6_operator_holdout_validation_blocks_unvalidated_runtime_update():
    report = build_r6_operator_holdout_validation(
        artifact_id="r6-operator-holdout-validation-test",
        run_id="r6-operator-holdout-validation-run",
    )

    assert report["schema_version"] == "r6-operator-holdout-validation-v1"
    assert report["status"] == (
        "operator_holdout_validation_failed_current_public_proxies"
    )
    assert report["validation_summary"] == {
        "candidate_update_count": 2,
        "holdout_trial_count": 4,
        "passed_trial_count": 0,
        "non_regression_trial_count": 2,
        "failed_trial_count": 2,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_gates"] == {
        "operator_update_structured": True,
        "operator_holdout_non_regression": False,
        "runtime_default_allowed": False,
        "field_outcome_validated": False,
        "product_guard_required": True,
    }
    assert "needs_operator_holdout_validation" in report["blocking_gaps"]
    assert "operator_update_blocked" in report["risk_flags"]
    json.dumps(report, allow_nan=False)


def test_r6_mechanism_research_readiness_report_returns_diagnostic_only():
    report = build_r6_mechanism_research_readiness_report(
        artifact_id="r6-mechanism-research-readiness-test",
        run_id="r6-mechanism-research-readiness-run",
    )

    assert report["schema_version"] == (
        "r6-mechanism-research-readiness-report-v1"
    )
    assert report["status"] == "mechanism_research_diagnostic_only"
    assert report["decision"] == {
        "mechanism_mvp_result": "diagnostic_only",
        "continue_research_with_constraints": True,
        "ccf_a_main_contribution_ready": False,
        "runtime_default_allowed": False,
    }
    assert report["readiness_gates"]["mechanism_trace_present"] is True
    assert (
        report["readiness_gates"]["dynamic_path_distinct_from_static_prior"] is True
    )
    assert report["readiness_gates"]["operator_holdout_non_regression"] is False
    assert report["readiness_gates"]["product_guard_preserved"] is True
    assert "needs_operator_holdout_validation" in report["blocking_gaps"]
    json.dumps(report, allow_nan=False)


def test_r6_mechanism_readiness_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-mechanism-research-readiness-report.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_mechanism_research_readiness_report.py",
            "--artifact-id",
            "r6-mechanism-research-readiness-cli",
            "--run-id",
            "r6-mechanism-research-readiness-run",
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
    assert report["schema_version"] == (
        "r6-mechanism-research-readiness-report-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-mechanism-research-readiness-cli",
        "mechanism_mvp_result": "diagnostic_only",
        "output": str(output),
        "status": "mechanism_research_diagnostic_only",
    }
