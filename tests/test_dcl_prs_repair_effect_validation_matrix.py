import json
import subprocess
import sys

from experiments.dcl_prs_failure_attribution import build_failure_attribution_index
from experiments.dcl_prs_repair_effect_validation_matrix import (
    build_repair_effect_validation_matrix,
)
from experiments.dcl_prs_repair_repeat_acceptance_matrix import (
    build_repair_repeat_acceptance_matrix,
)


def test_repair_effect_validation_keeps_rejected_repairs_unpromoted():
    failure = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-test"
    )
    matrix = build_repair_effect_validation_matrix(
        artifact_id="dcl-prs-repair-effect-test",
        repair_repeat_acceptance_matrix=build_repair_repeat_acceptance_matrix(
            artifact_id="dcl-prs-repair-repeat-test",
            failure_attribution_index=failure,
        ),
    )

    assert matrix["schema_version"] == "dcl-prs-repair-effect-validation-matrix-v1"
    assert matrix["overall_status"] == "repair_effect_validation_matrix_ready"
    assert matrix["accepted_candidate_count"] == 2
    assert matrix["promoted_candidate_count"] == 2
    assert matrix["rejected_candidate_promoted_count"] == 0
    assert matrix["claim_boundary"]["uses_test_split_for_current_claim"] is False
    json.dumps(matrix, allow_nan=False)


def test_repair_effect_validation_script_writes_artifact(tmp_path):
    output_dir = tmp_path / "dcl_prs_repair_effect"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_repair_effect_validation_matrix.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-repair-effect-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-repair-effect-test.json"),
        "overall_status": "repair_effect_validation_matrix_ready",
        "promoted_candidate_count": 2,
    }
