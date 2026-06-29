import json
import subprocess
import sys
import copy

import pytest

from experiments.r6_behavioral_update_operator_v2 import (
    build_r6_behavioral_update_operator_v2,
)
from experiments.r6_gap_closure_report import build_r6_gap_closure_report
from experiments.r6_outcome_holdout_registry import build_r6_outcome_holdout_registry
from experiments.r6_theory_framework import build_r6_theory_framework


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


def test_r6_gap_closure_report_rejects_malformed_theory_artifact():
    theory = build_r6_theory_framework(
        artifact_id="r6-gap-closure-report-theory",
        run_id="r6-gap-closure-run",
    )

    for field, value, error in (
        ("schema_version", "bad-schema", "theory_framework.schema_version"),
        ("status", "bad-status", "theory_framework.status"),
    ):
        malformed = copy.deepcopy(theory)
        malformed[field] = value
        with pytest.raises(ValueError, match=error):
            build_r6_gap_closure_report(
                artifact_id="r6-gap-closure-report-bad-theory",
                run_id="r6-gap-closure-run",
                theory_framework=malformed,
            )

    for gate, value in (
        ("formal_problem_definition_present", False),
        ("risk_discovery_value_defined", False),
        ("runtime_default_allowed", True),
        ("field_outcome_validated", True),
    ):
        malformed = copy.deepcopy(theory)
        malformed["acceptance_gates"][gate] = value
        with pytest.raises(ValueError, match=f"theory_framework.acceptance_gates.{gate}"):
            build_r6_gap_closure_report(
                artifact_id="r6-gap-closure-report-bad-theory-gate",
                run_id="r6-gap-closure-run",
                theory_framework=malformed,
            )


def test_r6_gap_closure_report_rejects_malformed_registry_field_validation():
    registry = build_r6_outcome_holdout_registry(
        artifact_id="r6-gap-closure-report-registry",
        run_id="r6-gap-closure-run",
    )
    malformed = copy.deepcopy(registry)
    malformed["acceptance_gates"]["field_outcome_validated"] = True

    with pytest.raises(
        ValueError,
        match="holdout_registry.acceptance_gates.field_outcome_validated",
    ):
        build_r6_gap_closure_report(
            artifact_id="r6-gap-closure-report-bad-registry",
            run_id="r6-gap-closure-run",
            holdout_registry=malformed,
        )


def test_r6_gap_closure_report_rejects_operator_runtime_default_allowed():
    operator_v2 = build_r6_behavioral_update_operator_v2(
        artifact_id="r6-gap-closure-report-operator",
        run_id="r6-gap-closure-run",
    )
    malformed = copy.deepcopy(operator_v2)
    malformed["acceptance_gates"]["operator_v2_runtime_default_allowed"] = True

    with pytest.raises(
        ValueError,
        match="operator_v2.acceptance_gates.operator_v2_runtime_default_allowed",
    ):
        build_r6_gap_closure_report(
            artifact_id="r6-gap-closure-report-bad-operator",
            run_id="r6-gap-closure-run",
            operator_v2=malformed,
        )


def test_r6_gap_closure_report_rejects_operator_empty_blocking_gaps():
    operator_v2 = build_r6_behavioral_update_operator_v2(
        artifact_id="r6-gap-closure-report-operator",
        run_id="r6-gap-closure-run",
    )
    malformed = copy.deepcopy(operator_v2)
    malformed["blocking_gaps"] = []

    with pytest.raises(ValueError, match="operator_v2.blocking_gaps missing required"):
        build_r6_gap_closure_report(
            artifact_id="r6-gap-closure-report-empty-operator-gaps",
            run_id="r6-gap-closure-run",
            operator_v2=malformed,
        )


def test_r6_gap_closure_report_rejects_bad_ids_and_normalizes_source_refs():
    theory = build_r6_theory_framework(
        artifact_id=" r6-gap-closure-report-theory ",
        run_id="r6-gap-closure-run",
    )
    registry = build_r6_outcome_holdout_registry(
        artifact_id=" r6-gap-closure-report-registry ",
        run_id="r6-gap-closure-run",
    )
    operator_v2 = build_r6_behavioral_update_operator_v2(
        artifact_id=" r6-gap-closure-report-operator ",
        run_id="r6-gap-closure-run",
    )

    report = build_r6_gap_closure_report(
        artifact_id="r6-gap-closure-report-normalized-refs",
        run_id="r6-gap-closure-run",
        theory_framework=theory,
        holdout_registry=registry,
        operator_v2=operator_v2,
    )

    assert report["source_refs"] == [
        "r6-gap-closure-report-theory",
        "r6-gap-closure-report-registry",
        "r6-gap-closure-report-operator",
    ]

    for field, bad_id in (
        ("theory_framework", {"bad": "id"}),
        ("holdout_registry", ["bad-id"]),
        ("operator_v2", {"bad": "id"}),
    ):
        artifacts = {
            "theory_framework": copy.deepcopy(theory),
            "holdout_registry": copy.deepcopy(registry),
            "operator_v2": copy.deepcopy(operator_v2),
        }
        artifacts[field]["artifact_id"] = bad_id
        with pytest.raises(ValueError, match=f"{field}.artifact_id"):
            build_r6_gap_closure_report(
                artifact_id="r6-gap-closure-report-bad-id",
                run_id="r6-gap-closure-run",
                **artifacts,
            )
