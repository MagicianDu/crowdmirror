import copy
import json
import re
import subprocess
import sys

import pytest

from experiments.r6_behavioral_update_operator import (
    build_r6_behavioral_update_operator,
)
from experiments.r6_mechanism_ablation_report import (
    build_r6_mechanism_ablation_report,
)
from experiments.r6_mechanism_propagation_trace import (
    build_r6_mechanism_propagation_trace,
)


EXPECTED_METHODS = {
    "static_prior",
    "no_propagation_interaction",
    "random_propagation",
    "mechanism_propagation",
    "behavioral_update_candidate",
}


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
    assert len(report["case_method_results"]) == 15
    methods = {result["method"] for result in report["case_method_results"]}
    assert EXPECTED_METHODS <= methods
    by_case_method = {
        (result["source_key"], result["method"]): result
        for result in report["case_method_results"]
    }
    for source_key in {
        "htops_cost_pressure",
        "anes_health_heldout",
        "anes_climate_heldout",
    }:
        assert {
            result["method"]
            for result in report["case_method_results"]
            if result["source_key"] == source_key
        } == EXPECTED_METHODS
    assert by_case_method[
        ("htops_cost_pressure", "mechanism_propagation")
    ]["beats_static_prior"] is True
    assert by_case_method[
        ("anes_health_heldout", "mechanism_propagation")
    ]["beats_static_prior"] is False
    assert by_case_method[
        ("anes_climate_heldout", "mechanism_propagation")
    ]["beats_static_prior"] is False
    random_rows = [
        result
        for result in report["case_method_results"]
        if result["method"] == "random_propagation"
    ]
    assert {result["baseline_type"] for result in random_rows} == {
        "deterministic_fixed_offset"
    }
    behavioral_rows = [
        result
        for result in report["case_method_results"]
        if result["method"] == "behavioral_update_candidate"
    ]
    assert len(behavioral_rows) == 3
    for result in behavioral_rows:
        assert result["global_update_status"] == "blocked_pending_operator_holdout"
        assert result["prediction"] is None
        assert result["mean_absolute_error"] is None
    assert "mechanism_ablation_not_ccf_a_ready" in report["risk_flags"]
    assert "needs_operator_holdout_validation" in report["blocking_gaps"]
    json.dumps(report, allow_nan=False)


def test_r6_mechanism_ablation_report_rejects_malformed_operator_fail_closed():
    propagation_trace = build_r6_mechanism_propagation_trace(
        artifact_id="r6-mechanism-ablation-report-trace",
        run_id="r6-mechanism-ablation-report-run",
    )

    with pytest.raises(
        ValueError,
        match="behavioral_update_operator.runtime_default_allowed must be False",
    ):
        build_r6_mechanism_ablation_report(
            artifact_id="r6-mechanism-ablation-report-malformed-operator",
            run_id="r6-mechanism-ablation-report-run",
            propagation_trace=propagation_trace,
            behavioral_update_operator={
                "schema_version": "r6-behavioral-update-operator-v1",
                "artifact_id": "malformed-operator",
                "status": "behavioral_update_candidate_blocked_pending_holdout",
                "candidate_updates": [],
            },
        )


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        (
            lambda operator: operator["operator_summary"].__setitem__(
                "runtime_default_allowed_count",
                1,
            ),
            "behavioral_update_operator.operator_summary.runtime_default_allowed_count must be 0",
        ),
        (
            lambda operator: operator["candidate_updates"][0].__setitem__(
                "runtime_default_allowed",
                True,
            ),
            "behavioral_update_operator.candidate_updates[0].runtime_default_allowed must be False",
        ),
        (
            lambda operator: operator["candidate_updates"][0].__setitem__(
                "runtime_decision",
                "runtime_default_allowed",
            ),
            "behavioral_update_operator.candidate_updates[0].runtime_decision must be blocked_pending_operator_holdout",
        ),
        (
            lambda operator: operator["candidate_updates"][0].__setitem__(
                "prompt_patch_text",
                "Enable this candidate as runtime default.",
            ),
            "behavioral_update_operator.candidate_updates[0].prompt_patch_text must be empty",
        ),
    ],
)
def test_r6_mechanism_ablation_report_rejects_nested_candidate_runtime_escape(
    mutation,
    expected_error,
):
    propagation_trace = build_r6_mechanism_propagation_trace(
        artifact_id="r6-mechanism-ablation-report-trace",
        run_id="r6-mechanism-ablation-report-run",
    )
    behavioral_update_operator = build_r6_behavioral_update_operator(
        artifact_id="r6-mechanism-ablation-report-operator",
        run_id="r6-mechanism-ablation-report-run",
        propagation_trace=propagation_trace,
    )
    malformed_operator = copy.deepcopy(behavioral_update_operator)
    mutation(malformed_operator)

    with pytest.raises(ValueError, match=re.escape(expected_error)):
        build_r6_mechanism_ablation_report(
            artifact_id="r6-mechanism-ablation-report-nested-runtime-escape",
            run_id="r6-mechanism-ablation-report-run",
            propagation_trace=propagation_trace,
            behavioral_update_operator=malformed_operator,
        )


def test_r6_mechanism_ablation_report_rejects_empty_dynamic_paths_fail_closed():
    propagation_trace = build_r6_mechanism_propagation_trace(
        artifact_id="r6-mechanism-ablation-report-trace",
        run_id="r6-mechanism-ablation-report-run",
    )
    malformed_trace = {
        **propagation_trace,
        "case_traces": [
            {**propagation_trace["case_traces"][0], "dynamic_paths": []},
            *propagation_trace["case_traces"][1:],
        ],
    }
    behavioral_update_operator = build_r6_behavioral_update_operator(
        artifact_id="r6-mechanism-ablation-report-operator",
        run_id="r6-mechanism-ablation-report-run",
        propagation_trace=propagation_trace,
    )

    with pytest.raises(
        ValueError,
        match="propagation_trace.case_traces\\[0\\].dynamic_paths must be non-empty",
    ):
        build_r6_mechanism_ablation_report(
            artifact_id="r6-mechanism-ablation-report-malformed-trace",
            run_id="r6-mechanism-ablation-report-run",
            propagation_trace=malformed_trace,
            behavioral_update_operator=behavioral_update_operator,
        )


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
