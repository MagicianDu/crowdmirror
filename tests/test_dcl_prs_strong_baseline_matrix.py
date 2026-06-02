import json
import subprocess
import sys

from experiments.dcl_prs_strong_baseline_matrix import (
    build_dcl_prs_strong_baseline_matrix,
)


def test_dcl_prs_strong_baseline_matrix_keeps_paper_gate_closed_when_not_leading():
    matrix = build_dcl_prs_strong_baseline_matrix(
        artifact_id="dcl-prs-strong-baseline-test"
    )

    assert matrix["schema_version"] == "dcl-prs-strong-baseline-matrix-v1"
    assert matrix["overall_status"] == "strong_baseline_dcl_prs_not_leading"
    assert matrix["paper_gate_eligible"] is False
    assert matrix["covered_baseline_families"] == [
        "deterministic_anchor",
        "LCDU-LCR-SG",
        "fixed_party_or_ideology_prior",
        "DCL-PRS",
    ]
    assert matrix["dcl_prs_leads_covered_baselines"] is False
    json.dumps(matrix, allow_nan=False)


def test_dcl_prs_strong_baseline_matrix_tracks_real_effect_evidence():
    matrix = build_dcl_prs_strong_baseline_matrix(
        artifact_id="dcl-prs-strong-baseline-test",
        gss_real_repair_effect_validation={
            "schema_version": "dcl-prs-gss-real-repair-effect-v1",
            "artifact_id": "dcl-prs-gss-real-repair-effect-test",
            "overall_status": "gss_real_repair_effect_validation_ready",
            "real_effect_promoted_count": 2,
        },
    )

    assert matrix["overall_status"] == "strong_baseline_dcl_prs_not_leading"
    assert matrix["paper_gate_eligible"] is False
    assert matrix["l2_readiness"]["gss_real_effect_validation_ready"] is True
    assert "real_effect_validation_missing" not in matrix["blocking_gaps"]
    assert matrix["blocking_gaps"] == [
        "multi_dataset_generalization_missing",
        "strong_baseline_win_missing",
    ]


def test_dcl_prs_strong_baseline_script_writes_artifact(tmp_path):
    output_dir = tmp_path / "dcl_prs_strong_baseline"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_strong_baseline_matrix.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-strong-baseline-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-strong-baseline-test.json"),
        "overall_status": "strong_baseline_dcl_prs_not_leading",
        "paper_gate_eligible": False,
    }
