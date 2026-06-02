import json
import subprocess
import sys

from experiments.dcl_prs_failure_attribution import build_failure_attribution_index
from experiments.dcl_prs_repair_repeat_acceptance_matrix import (
    build_repair_repeat_acceptance_matrix,
)


def test_repair_repeat_acceptance_matrix_reports_accepted_and_rejected_candidates():
    matrix = build_repair_repeat_acceptance_matrix(
        artifact_id="dcl-prs-repair-repeat-test",
        failure_attribution_index=build_failure_attribution_index(
            artifact_id="dcl-prs-failure-attribution-test"
        ),
    )

    assert matrix["schema_version"] == "dcl-prs-repair-repeat-acceptance-matrix-v1"
    assert matrix["overall_status"] == "repair_repeat_acceptance_matrix_ready"
    assert matrix["repair_candidate_count"] == 4
    assert matrix["accepted_candidate_count"] >= 1
    assert matrix["rejected_candidate_count"] >= 1
    assert matrix["claim_boundary"]["uses_test_split_for_current_claim"] is False
    json.dumps(matrix, allow_nan=False)


def test_repair_repeat_acceptance_records_repeat_axis_and_decisions():
    matrix = build_repair_repeat_acceptance_matrix(
        artifact_id="dcl-prs-repair-repeat-test",
        failure_attribution_index=build_failure_attribution_index(
            artifact_id="dcl-prs-failure-attribution-test"
        ),
    )

    assert matrix["split_salts"] == ["s0", "s1", "s2"]
    for candidate in matrix["candidate_results"]:
        assert candidate["decision"] in {"accepted", "rejected"}
        assert candidate["repeat_count"] == 3
        assert len(candidate["repeat_results"]) == 3
        for repeat in candidate["repeat_results"]:
            assert repeat["salt"] in {"s0", "s1", "s2"}
            assert repeat["acceptance_gate"] == "heldout_repeat_gate"


def test_repair_repeat_acceptance_script_writes_artifact(tmp_path):
    output_dir = tmp_path / "dcl_prs_repair_repeat"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_repair_repeat_acceptance_matrix.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-repair-repeat-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "accepted_candidate_count": 2,
        "index": str(output_dir / "dcl-prs-repair-repeat-test.json"),
        "repair_candidate_count": 4,
    }
    assert (output_dir / "dcl-prs-repair-repeat-test.json").exists()
