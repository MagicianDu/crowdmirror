import json
import subprocess
import sys

from experiments.lcdu_anes_llm_instability_diagnosis import (
    build_lcdu_anes_llm_instability_diagnosis,
)


def test_instability_diagnosis_records_failed_cases_and_prompt_variant_recovery():
    diagnosis = build_lcdu_anes_llm_instability_diagnosis(
        artifact_id="lcdu-anes-llm-instability-diagnosis-test",
        seed_scale_repeat_matrix=_mixed_matrix(),
        diagnosis_run_artifacts=[_variant_run("compact", accepted=True)],
    )

    assert diagnosis["schema_version"] == "lcdu-anes-llm-instability-diagnosis-v1"
    assert diagnosis["overall_status"] == "instability_recovered_by_prompt_variant"
    assert diagnosis["source_matrix_artifact_id"] == "mixed-matrix"
    assert diagnosis["failure_count"] == 1
    assert diagnosis["recovered_failure_count"] == 1
    assert diagnosis["persistent_failure_count"] == 0
    assert diagnosis["failure_cases"][0] == {
        "source_run_id": "mixed-matrix-scale2-offset1-standard",
        "task_id": "public_health_medical_insurance_attitude_v1",
        "failure_type": "candidate_rejected_and_test_not_improved",
        "max_segments_per_task": 2,
        "segment_offset": 1,
        "prompt_variant": "standard",
        "accepted_method_id": None,
        "heldout_initial_loss": 0.0037,
        "heldout_final_loss": 0.0037,
        "test_initial_loss": 0.0097,
        "test_final_loss": 0.0097,
        "selected_segments": [
            "party_or_ideology=conservative|income=upper",
            "party_or_ideology=conservative|income=middle",
        ],
    }
    assert diagnosis["recovery_cases"][0]["recovered_by_prompt_variant"] == "compact"
    assert "targeted_diagnosis_not_full_matrix" in diagnosis["risk_flags"]
    json.dumps(diagnosis, allow_nan=False)


def test_instability_diagnosis_marks_persistent_failure_when_variants_do_not_recover():
    diagnosis = build_lcdu_anes_llm_instability_diagnosis(
        artifact_id="lcdu-anes-llm-instability-diagnosis-test",
        seed_scale_repeat_matrix=_mixed_matrix(),
        diagnosis_run_artifacts=[_variant_run("compact", accepted=False)],
    )

    assert diagnosis["overall_status"] == "instability_persistent_after_prompt_variants"
    assert diagnosis["recovered_failure_count"] == 0
    assert diagnosis["persistent_failure_count"] == 1
    assert diagnosis["persistent_failure_cases"][0]["task_id"] == (
        "public_health_medical_insurance_attitude_v1"
    )


def test_instability_diagnosis_script_writes_planned_json(tmp_path):
    matrix = tmp_path / "matrix.json"
    output = tmp_path / "diagnosis.json"
    matrix.write_text(json.dumps(_mixed_matrix()))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_llm_instability_diagnosis.py",
            "--seed-scale-repeat-matrix",
            str(matrix),
            "--output",
            str(output),
            "--artifact-id",
            "lcdu-anes-llm-instability-diagnosis-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "lcdu-anes-llm-instability-diagnosis-test",
        "failure_count": 1,
        "output": str(output),
        "recovered_failure_count": 0,
        "status": "instability_needs_targeted_diagnosis",
    }
    assert json.loads(output.read_text())["failure_count"] == 1


def _mixed_matrix() -> dict:
    return {
        "schema_version": "lcdu-anes-llm-seed-scale-repeat-matrix-v1",
        "artifact_id": "mixed-matrix",
        "overall_status": "seed_scale_repeat_signal_mixed",
        "validation_type": "llm_seed_scale_repeat_matrix",
        "provider": "openai",
        "model": "deepseek-v4-flash",
        "base_url": "https://api.deepseek.com",
        "run_count": 1,
        "positive_run_count": 0,
        "run_results": [
            {
                "artifact_id": "mixed-matrix-scale2-offset1-standard",
                "overall_status": "cross_task_llm_signal_mixed",
                "max_segments_per_task": 2,
                "segment_offset": 1,
                "prompt_variant": "standard",
                "task_summaries": {
                    "public_health_medical_insurance_attitude_v1": {
                        "candidate_accepted": False,
                        "accepted_method_id": None,
                        "heldout_initial_loss": 0.0037,
                        "heldout_final_loss": 0.0037,
                        "test_initial_loss": 0.0097,
                        "test_final_loss": 0.0097,
                        "selected_segments": [
                            "party_or_ideology=conservative|income=upper",
                            "party_or_ideology=conservative|income=middle",
                        ],
                    },
                    "climate_energy_regulation_attitude_v1": {
                        "candidate_accepted": True,
                        "accepted_method_id": "lcdu_segment_anchor_prompt",
                        "heldout_initial_loss": 0.01,
                        "heldout_final_loss": 0.005,
                        "test_initial_loss": 0.01,
                        "test_final_loss": 0.004,
                        "selected_segments": [
                            "party_or_ideology=conservative|income=upper",
                            "party_or_ideology=conservative|income=middle",
                        ],
                    },
                },
            }
        ],
    }


def _variant_run(prompt_variant: str, *, accepted: bool) -> dict:
    final_loss = 0.004 if accepted else 0.0097
    return {
        "schema_version": "lcdu-anes-llm-simulator-validation-v1",
        "artifact_id": f"variant-run-{prompt_variant}",
        "overall_status": (
            "cross_task_llm_signal_positive" if accepted else "cross_task_llm_signal_mixed"
        ),
        "validation_type": "split_gated_llm_segment_simulator_smoke",
        "provider": "openai",
        "model": "deepseek-v4-flash",
        "base_url": "https://api.deepseek.com",
        "max_segments_per_task": 2,
        "segment_offset": 1,
        "prompt_variant": prompt_variant,
        "task_count": 2,
        "task_results": {
            "public_health_medical_insurance_attitude_v1": {
                "candidate_accepted": accepted,
                "accepted_method_id": "lcdu_segment_anchor_prompt" if accepted else None,
                "selected_segments": [
                    "party_or_ideology=conservative|income=upper",
                    "party_or_ideology=conservative|income=middle",
                ],
                "heldout": {
                    "initial_loss": 0.0037,
                    "best_loss": final_loss,
                    "final_loss": final_loss,
                },
                "test": {
                    "initial_loss": 0.0097,
                    "final_loss": final_loss,
                    "final_method_id": (
                        "lcdu_segment_anchor_prompt" if accepted else "raw_prompt"
                    ),
                },
            },
            "climate_energy_regulation_attitude_v1": {
                "candidate_accepted": True,
                "accepted_method_id": "lcdu_segment_anchor_prompt",
                "selected_segments": [
                    "party_or_ideology=conservative|income=upper",
                    "party_or_ideology=conservative|income=middle",
                ],
                "heldout": {
                    "initial_loss": 0.01,
                    "best_loss": 0.005,
                    "final_loss": 0.005,
                },
                "test": {
                    "initial_loss": 0.01,
                    "final_loss": 0.004,
                    "final_method_id": "lcdu_segment_anchor_prompt",
                },
            },
        },
        "llm_accounting": {
            "total_call_count": 6,
            "total_input_tokens": 60,
            "total_output_tokens": 30,
            "parse_failure_count": 0,
        },
    }
