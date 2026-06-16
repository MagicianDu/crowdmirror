import copy
import json
import subprocess
import sys

import pytest

from experiments.r6_mechanism_ablation_report import (
    build_r6_mechanism_ablation_report,
)
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


def test_r6_operator_holdout_validation_rejects_runtime_default_ablation_row():
    mechanism_ablation_report = build_r6_mechanism_ablation_report(
        artifact_id="r6-operator-holdout-validation-ablation",
        run_id="r6-operator-holdout-validation-run",
    )
    malformed_ablation_report = copy.deepcopy(mechanism_ablation_report)
    malformed_index = next(
        index
        for index, result in enumerate(malformed_ablation_report["case_method_results"])
        if result["method"] == "mechanism_propagation"
    )
    malformed_ablation_report["case_method_results"][malformed_index][
        "runtime_default_allowed"
    ] = True

    with pytest.raises(
        ValueError,
        match=(
            "mechanism_ablation_report.case_method_results"
            f"\\[{malformed_index}\\].runtime_default_allowed must be False"
        ),
    ):
        build_r6_operator_holdout_validation(
            artifact_id="r6-operator-holdout-validation-malformed-ablation",
            run_id="r6-operator-holdout-validation-run",
            mechanism_ablation_report=malformed_ablation_report,
        )


def test_r6_operator_holdout_validation_rejects_anes_success_shape():
    mechanism_ablation_report = build_r6_mechanism_ablation_report(
        artifact_id="r6-operator-holdout-validation-anes-shape",
        run_id="r6-operator-holdout-validation-run",
    )
    malformed_ablation_report = copy.deepcopy(mechanism_ablation_report)
    for result in malformed_ablation_report["case_method_results"]:
        if (
            result["method"] == "mechanism_propagation"
            and result["source_key"] in {"anes_health_heldout", "anes_climate_heldout"}
        ):
            result["mean_absolute_error"] = 0.0
            result["beats_static_prior"] = True

    with pytest.raises(
        ValueError,
        match=(
            "mechanism_ablation_report selected ANES rows must have "
            "beats_static_prior False"
        ),
    ):
        build_r6_operator_holdout_validation(
            artifact_id="r6-operator-holdout-validation-anes-success-shape",
            run_id="r6-operator-holdout-validation-run",
            mechanism_ablation_report=malformed_ablation_report,
        )


def test_r6_operator_holdout_validation_rejects_htops_regression_shape():
    mechanism_ablation_report = build_r6_mechanism_ablation_report(
        artifact_id="r6-operator-holdout-validation-htops-shape",
        run_id="r6-operator-holdout-validation-run",
    )
    malformed_ablation_report = copy.deepcopy(mechanism_ablation_report)
    for result in malformed_ablation_report["case_method_results"]:
        if (
            result["method"] == "mechanism_propagation"
            and result["source_key"] == "htops_cost_pressure"
        ):
            result["mean_absolute_error"] = result["static_prior_error"] + 0.1
            result["beats_static_prior"] = False

    with pytest.raises(
        ValueError,
        match=(
            "mechanism_ablation_report selected HTOPS row must have "
            "beats_static_prior True"
        ),
    ):
        build_r6_operator_holdout_validation(
            artifact_id="r6-operator-holdout-validation-htops-regression-shape",
            run_id="r6-operator-holdout-validation-run",
            mechanism_ablation_report=malformed_ablation_report,
        )


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


def test_r6_mechanism_research_readiness_rejects_contradictory_holdout_gate():
    operator_holdout_validation = build_r6_operator_holdout_validation(
        artifact_id="r6-mechanism-research-readiness-holdout",
        run_id="r6-mechanism-research-readiness-run",
    )
    malformed_holdout_validation = copy.deepcopy(operator_holdout_validation)
    malformed_holdout_validation["acceptance_gates"][
        "operator_holdout_non_regression"
    ] = True

    with pytest.raises(
        ValueError,
        match=(
            "operator_holdout_validation.acceptance_gates."
            "operator_holdout_non_regression must be False"
        ),
    ):
        build_r6_mechanism_research_readiness_report(
            artifact_id="r6-mechanism-research-readiness-malformed-holdout",
            run_id="r6-mechanism-research-readiness-run",
            operator_holdout_validation=malformed_holdout_validation,
        )


def test_r6_mechanism_research_readiness_rejects_passed_trial_count_mismatch():
    operator_holdout_validation = build_r6_operator_holdout_validation(
        artifact_id="r6-mechanism-research-readiness-passed-mismatch",
        run_id="r6-mechanism-research-readiness-run",
    )
    malformed_holdout_validation = copy.deepcopy(operator_holdout_validation)
    malformed_holdout_validation["holdout_trials"][0]["passed"] = True

    with pytest.raises(
        ValueError,
        match=(
            "operator_holdout_validation.validation_summary."
            "passed_trial_count must match holdout_trials"
        ),
    ):
        build_r6_mechanism_research_readiness_report(
            artifact_id="r6-mechanism-research-readiness-passed-mismatch",
            run_id="r6-mechanism-research-readiness-run",
            operator_holdout_validation=malformed_holdout_validation,
        )


def test_r6_mechanism_research_readiness_rejects_non_regression_status_mismatch():
    operator_holdout_validation = build_r6_operator_holdout_validation(
        artifact_id="r6-mechanism-research-readiness-status-mismatch",
        run_id="r6-mechanism-research-readiness-run",
    )
    malformed_holdout_validation = copy.deepcopy(operator_holdout_validation)
    for trial in malformed_holdout_validation["holdout_trials"]:
        if trial["non_regression_only"] is True:
            trial["validation_status"] = "failed_same_family_holdout_regression"
            break

    with pytest.raises(
        ValueError,
        match=(
            "operator_holdout_validation.validation_summary."
            "non_regression_trial_count must match holdout_trials"
        ),
    ):
        build_r6_mechanism_research_readiness_report(
            artifact_id="r6-mechanism-research-readiness-status-mismatch",
            run_id="r6-mechanism-research-readiness-run",
            operator_holdout_validation=malformed_holdout_validation,
        )


def test_r6_operator_holdout_validation_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-operator-holdout-validation.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_operator_holdout_validation.py",
            "--artifact-id",
            "r6-operator-holdout-validation-cli",
            "--run-id",
            "r6-operator-holdout-validation-run",
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
    assert report["schema_version"] == "r6-operator-holdout-validation-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-operator-holdout-validation-cli",
        "output": str(output),
        "status": "operator_holdout_validation_failed_current_public_proxies",
    }


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
