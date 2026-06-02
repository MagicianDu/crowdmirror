import json
import subprocess
import sys

from experiments.lcdu_anes_llm_scale_stability_matrix import (
    build_lcdu_anes_llm_scale_stability_matrix,
)


def test_scale_stability_matrix_reports_positive_when_large_scales_are_positive():
    scale = build_lcdu_anes_llm_scale_stability_matrix(
        artifact_id="lcdu-scale-stability-test",
        seed_scale_repeat_matrix=_source_matrix(
            segment_scales=[8, 12, 16],
            run_count=3,
            positive_run_count=3,
            status="seed_scale_repeat_signal_positive",
        ),
        min_max_segment_scale=8,
        selected_prompt_variant="deliberative",
    )

    assert scale["schema_version"] == "lcdu-anes-llm-scale-stability-matrix-v1"
    assert scale["overall_status"] == "scale_stability_signal_positive"
    assert scale["max_segment_scale"] == 16
    assert scale["min_max_segment_scale"] == 8
    assert scale["selected_prompt_variant"] == "deliberative"
    assert scale["positive_run_count"] == 3
    assert scale["run_count"] == 3
    assert scale["task_stability"]["public_health_medical_insurance_attitude_v1"][
        "test_improved_rate"
    ] == 1.0
    assert "scale_evidence_insufficient" not in scale["risk_flags"]
    json.dumps(scale, allow_nan=False)


def test_scale_stability_matrix_rejects_too_small_scale_as_insufficient():
    scale = build_lcdu_anes_llm_scale_stability_matrix(
        artifact_id="lcdu-scale-stability-test",
        seed_scale_repeat_matrix=_source_matrix(
            segment_scales=[2, 4],
            run_count=2,
            positive_run_count=2,
            status="seed_scale_repeat_signal_positive",
        ),
        min_max_segment_scale=8,
        selected_prompt_variant="deliberative",
    )

    assert scale["overall_status"] == "scale_stability_evidence_insufficient"
    assert "scale_evidence_insufficient" in scale["risk_flags"]


def test_scale_stability_matrix_script_writes_json(tmp_path):
    source = tmp_path / "source.json"
    output = tmp_path / "scale.json"
    source.write_text(
        json.dumps(
            _source_matrix(
                segment_scales=[8, 12, 16],
                run_count=3,
                positive_run_count=3,
                status="seed_scale_repeat_signal_positive",
            )
        )
    )

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_llm_scale_stability_matrix.py",
            "--seed-scale-repeat-matrix",
            str(source),
            "--output",
            str(output),
            "--artifact-id",
            "lcdu-scale-stability-test",
            "--min-max-segment-scale",
            "8",
            "--selected-prompt-variant",
            "deliberative",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "lcdu-scale-stability-test",
        "max_segment_scale": 16,
        "output": str(output),
        "status": "scale_stability_signal_positive",
    }
    assert json.loads(output.read_text())["overall_status"] == (
        "scale_stability_signal_positive"
    )


def _source_matrix(
    *,
    segment_scales: list[int],
    run_count: int,
    positive_run_count: int,
    status: str,
) -> dict:
    return {
        "schema_version": "lcdu-anes-llm-seed-scale-repeat-matrix-v1",
        "artifact_id": "source-seed-scale-repeat",
        "overall_status": status,
        "validation_type": "llm_seed_scale_repeat_matrix",
        "provider": "openai",
        "model": "deepseek-v4-flash",
        "base_url": "https://api.deepseek.com",
        "segment_scales": segment_scales,
        "segment_offsets": [0],
        "prompt_variants": ["deliberative"],
        "run_count": run_count,
        "positive_run_count": positive_run_count,
        "task_stability": {
            "public_health_medical_insurance_attitude_v1": {
                "run_count": run_count,
                "accepted_count": positive_run_count,
                "accepted_rate": positive_run_count / run_count,
                "test_improved_count": positive_run_count,
                "test_improved_rate": positive_run_count / run_count,
            },
            "climate_energy_regulation_attitude_v1": {
                "run_count": run_count,
                "accepted_count": positive_run_count,
                "accepted_rate": positive_run_count / run_count,
                "test_improved_count": positive_run_count,
                "test_improved_rate": positive_run_count / run_count,
            },
        },
        "llm_accounting": {
            "total_call_count": 216,
            "total_input_tokens": 2000,
            "total_output_tokens": 900,
            "parse_failure_count": 0,
        },
    }
