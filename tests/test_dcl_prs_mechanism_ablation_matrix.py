import json
import subprocess
import sys

from experiments.dcl_prs_mechanism_ablation_matrix import (
    build_mechanism_ablation_matrix,
)
from experiments.dcl_prs_mechanism_program import build_mechanism_program_index


def test_mechanism_ablation_matrix_identifies_nonzero_mechanism_impacts():
    matrix = build_mechanism_ablation_matrix(
        artifact_id="dcl-prs-mechanism-ablation-test",
        mechanism_program_index=build_mechanism_program_index(
            artifact_id="dcl-prs-mechanism-program-test"
        ),
    )

    assert matrix["schema_version"] == "dcl-prs-mechanism-ablation-matrix-v1"
    assert matrix["overall_status"] == "mechanism_ablation_matrix_ready"
    assert matrix["ablation_case_count"] >= 4
    assert matrix["nonzero_impact_rate"] > 0.0
    assert matrix["ccf_a_claim_status"] == "not_claimable"
    assert matrix["next_gate"] == "run_mechanism_ablation_repeat_matrix"
    json.dumps(matrix, allow_nan=False)


def test_mechanism_ablation_cases_keep_program_and_mechanism_refs():
    matrix = build_mechanism_ablation_matrix(
        artifact_id="dcl-prs-mechanism-ablation-test",
        mechanism_program_index=build_mechanism_program_index(
            artifact_id="dcl-prs-mechanism-program-test"
        ),
    )

    for case in matrix["ablation_cases"]:
        assert case["program_id"]
        assert case["ablated_mechanism_name"]
        assert isinstance(case["full_support_shift"], float)
        assert isinstance(case["ablated_support_shift"], float)
        assert case["impact_abs"] >= 0.0
        assert case["claim_status"] == "diagnostic_only"


def test_mechanism_ablation_script_writes_artifact(tmp_path):
    output_dir = tmp_path / "dcl_prs_mechanism_ablation"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_mechanism_ablation_matrix.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-mechanism-ablation-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "ablation_case_count": 6,
        "index": str(output_dir / "dcl-prs-mechanism-ablation-test.json"),
        "overall_status": "mechanism_ablation_matrix_ready",
    }
    assert (output_dir / "dcl-prs-mechanism-ablation-test.json").exists()
