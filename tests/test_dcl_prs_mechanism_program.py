import json
import subprocess
import sys

from experiments.dcl_prs_mechanism_program import build_mechanism_program_index


def test_mechanism_program_index_emits_structured_programs_not_free_text():
    index = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-test"
    )

    assert index["schema_version"] == "dcl-prs-mechanism-program-index-v1"
    assert index["overall_status"] == "mechanism_programs_ready_for_l0_gate"
    assert index["program_count"] >= 2
    assert index["mechanism_count"] >= 4
    for program in index["programs"]:
        assert program["schema_version"] == "dcl-prs-mechanism-program-v1"
        assert program["mechanisms"]
        assert "free_text_explanation" not in program
        assert program["claim_boundary"]["prediction_quality_status"] == "not_validated"
    json.dumps(index, allow_nan=False)


def test_mechanism_programs_have_mapping_actions_and_ablation_ready_flags():
    index = build_mechanism_program_index(
        artifact_id="dcl-prs-mechanism-program-test"
    )

    assert index["next_gate"] == "run_mechanism_ablation_matrix"
    for program in index["programs"]:
        assert program["mapping_actions"]
        for mechanism in program["mechanisms"]:
            assert mechanism["direction"] in {
                "increase_support",
                "decrease_support",
                "conditional_support",
                "increase_uncertainty",
            }
            assert 0.0 <= mechanism["strength"] <= 1.0
        for action in program["mapping_actions"]:
            assert action["action_type"] in {
                "adjust_support_prior",
                "increase_segment_uncertainty",
                "hold_anchor_for_segment",
            }


def test_mechanism_program_script_writes_artifact(tmp_path):
    output_dir = tmp_path / "dcl_prs_mechanism_program"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_mechanism_program.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-mechanism-program-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(output_dir / "dcl-prs-mechanism-program-test.json"),
        "program_count": 2,
    }
    assert (output_dir / "dcl-prs-mechanism-program-test.json").exists()
