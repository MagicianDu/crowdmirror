import copy
import json
import subprocess
import sys

import pytest

from experiments.r6_behavioral_update_operator_v2 import (
    build_r6_behavioral_update_operator_v2,
)
from experiments.r6_outcome_holdout_registry import (
    build_r6_outcome_holdout_registry,
)
from experiments.r6_theory_framework import build_r6_theory_framework


def test_r6_behavioral_update_operator_v2_adds_error_attribution_and_transfer_guards():
    report = build_r6_behavioral_update_operator_v2(
        artifact_id="r6-behavioral-update-operator-v2-test",
        run_id="r6-gap-closure-run",
    )

    assert report["schema_version"] == "r6-behavioral-update-operator-v2"
    assert report["status"] == "operator_v2_structured_blocked_missing_holdout"
    assert report["operator_v2_summary"] == {
        "candidate_update_count": 3,
        "same_case_repair_count": 1,
        "transfer_candidate_count": 2,
        "runtime_default_allowed_count": 0,
        "prompt_patch_update_count": 0,
    }
    assert report["acceptance_gates"]["operator_v2_structured"] is True
    assert report["acceptance_gates"]["operator_v2_runtime_default_allowed"] is False
    assert report["acceptance_gates"]["independent_holdout_available"] is False
    assert report["acceptance_gates"]["field_outcome_validated"] is False
    assert report["acceptance_gates"]["ccf_a_main_contribution_ready"] is False
    for candidate in report["candidate_updates"]:
        assert candidate["error_attribution"]
        assert candidate["transfer_preconditions"]
        assert candidate["acceptance_status"] == "blocked_missing_independent_holdout"
        assert candidate["runtime_default_allowed"] is False
        assert candidate["prompt_patch_text"] == ""
    candidate = report["candidate_updates"][0]
    assert candidate["operator_family"] == "over_amplification_damping"
    assert candidate["error_attribution"]["primary_component"] == "over_amplification"
    assert "independent_same_family_in_condition_holdout" in candidate[
        "transfer_preconditions"
    ]
    json.dumps(report, allow_nan=False)


def test_r6_behavioral_update_operator_v2_rejects_malformed_holdout_availability():
    holdout_registry = build_r6_outcome_holdout_registry(
        artifact_id="r6-behavioral-update-operator-v2-holdout",
        run_id="r6-gap-closure-run",
    )
    malformed_registry = copy.deepcopy(holdout_registry)
    malformed_registry["registry_summary"][
        "in_condition_independent_holdout_available"
    ] = "yes"

    with pytest.raises(
        ValueError,
        match=(
            "holdout_registry.registry_summary."
            "in_condition_independent_holdout_available must be a boolean"
        ),
    ):
        build_r6_behavioral_update_operator_v2(
            artifact_id="r6-behavioral-update-operator-v2-malformed-holdout",
            run_id="r6-gap-closure-run",
            holdout_registry=malformed_registry,
        )


def test_r6_behavioral_update_operator_v2_rejects_malformed_upstream_artifact_ids():
    holdout_registry = build_r6_outcome_holdout_registry(
        artifact_id="r6-behavioral-update-operator-v2-holdout",
        run_id="r6-gap-closure-run",
    )
    malformed_registry = copy.deepcopy(holdout_registry)
    malformed_registry["artifact_id"] = {"bad": "registry"}

    with pytest.raises(
        ValueError,
        match="holdout_registry.artifact_id must be a non-empty string",
    ):
        build_r6_behavioral_update_operator_v2(
            artifact_id="r6-behavioral-update-operator-v2-bad-registry-id",
            run_id="r6-gap-closure-run",
            holdout_registry=malformed_registry,
        )

    theory_framework = build_r6_theory_framework(
        artifact_id="r6-behavioral-update-operator-v2-theory",
        run_id="r6-gap-closure-run",
    )
    malformed_theory = copy.deepcopy(theory_framework)
    malformed_theory["artifact_id"] = ["bad-theory"]

    with pytest.raises(
        ValueError,
        match="theory_framework.artifact_id must be a non-empty string",
    ):
        build_r6_behavioral_update_operator_v2(
            artifact_id="r6-behavioral-update-operator-v2-bad-theory-id",
            run_id="r6-gap-closure-run",
            theory_framework=malformed_theory,
        )


def test_r6_behavioral_update_operator_v2_cli_writes_artifact(tmp_path):
    output = tmp_path / "r6-behavioral-update-operator-v2.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_behavioral_update_operator_v2.py",
            "--artifact-id",
            "r6-behavioral-update-operator-v2-cli",
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
    assert report["schema_version"] == "r6-behavioral-update-operator-v2"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r6-behavioral-update-operator-v2-cli",
        "output": str(output),
        "status": "operator_v2_structured_blocked_missing_holdout",
    }
