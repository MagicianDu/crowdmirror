import json
import subprocess
import sys

from experiments.dcl_prs_mechanism_ablation_matrix import (
    build_mechanism_ablation_matrix,
)
from experiments.dcl_prs_mechanism_ablation_repeat_matrix import (
    build_mechanism_ablation_repeat_matrix,
)
from experiments.dcl_prs_mechanism_program import build_mechanism_program_index


def test_mechanism_ablation_repeat_matrix_reports_stable_nonzero_impacts():
    mechanism = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-test"
    )
    matrix = build_mechanism_ablation_repeat_matrix(
        artifact_id="dcl-prs-mechanism-ablation-repeat-test",
        mechanism_ablation_matrix=build_mechanism_ablation_matrix(
            artifact_id="dcl-prs-mechanism-ablation-test",
            mechanism_program_index=mechanism,
        ),
    )

    assert matrix["schema_version"] == "dcl-prs-mechanism-ablation-repeat-matrix-v1"
    assert matrix["overall_status"] == "mechanism_ablation_repeat_matrix_ready"
    assert matrix["split_salts"] == ["s0", "s1", "s2"]
    assert matrix["ablation_case_count"] == 6
    assert matrix["repeat_case_count"] == 18
    assert matrix["stable_nonzero_impact_rate"] > 0.0
    assert matrix["ccf_a_claim_status"] == "not_claimable"
    json.dumps(matrix, allow_nan=False)


def test_mechanism_ablation_repeat_script_writes_artifact(tmp_path):
    output_dir = tmp_path / "dcl_prs_mechanism_ablation_repeat"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_mechanism_ablation_repeat_matrix.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-mechanism-ablation-repeat-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-mechanism-ablation-repeat-test.json"),
        "overall_status": "mechanism_ablation_repeat_matrix_ready",
        "repeat_case_count": 18,
    }
