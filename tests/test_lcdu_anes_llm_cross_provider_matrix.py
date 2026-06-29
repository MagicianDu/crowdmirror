import json
import subprocess
import sys

from experiments.lcdu_anes_llm_cross_provider_matrix import (
    build_lcdu_anes_llm_cross_provider_matrix,
)


def test_cross_provider_matrix_reports_positive_when_two_execution_envs_are_positive():
    matrix = build_lcdu_anes_llm_cross_provider_matrix(
        artifact_id="lcdu-cross-provider-test",
        seed_scale_repeat_matrices=[
            _seed_scale_repeat_matrix(
                artifact_id="deepseek-matrix",
                model="deepseek-v4-flash",
                base_url="https://api.deepseek.com",
                status="seed_scale_repeat_signal_positive",
            ),
            _seed_scale_repeat_matrix(
                artifact_id="lmstudio-matrix",
                model="openai/gpt-oss-20b",
                base_url="http://127.0.0.1:1234/v1",
                status="seed_scale_repeat_signal_positive",
            ),
        ],
    )

    assert matrix["schema_version"] == "lcdu-anes-llm-cross-provider-matrix-v1"
    assert matrix["overall_status"] == "cross_provider_signal_positive"
    assert matrix["provider_environment_count"] == 2
    assert matrix["positive_provider_environment_count"] == 2
    assert matrix["provider_environments"] == [
        "https://api.deepseek.com::deepseek-v4-flash",
        "http://127.0.0.1:1234/v1::openai/gpt-oss-20b",
    ]
    assert matrix["task_stability"]["public_health_medical_insurance_attitude_v1"] == {
        "provider_environment_count": 2,
        "positive_provider_environment_count": 2,
        "min_test_improved_rate": 1.0,
    }
    assert "cross_provider_evidence_insufficient" not in matrix["risk_flags"]
    json.dumps(matrix, allow_nan=False)


def test_cross_provider_matrix_requires_two_provider_environments():
    matrix = build_lcdu_anes_llm_cross_provider_matrix(
        artifact_id="lcdu-cross-provider-test",
        seed_scale_repeat_matrices=[
            _seed_scale_repeat_matrix(
                artifact_id="deepseek-matrix",
                model="deepseek-v4-flash",
                base_url="https://api.deepseek.com",
                status="seed_scale_repeat_signal_positive",
            )
        ],
    )

    assert matrix["overall_status"] == "cross_provider_evidence_insufficient"
    assert matrix["provider_environment_count"] == 1
    assert "cross_provider_evidence_insufficient" in matrix["risk_flags"]


def test_cross_provider_matrix_reports_selected_variant_when_one_variant_is_stable():
    matrix = build_lcdu_anes_llm_cross_provider_matrix(
        artifact_id="lcdu-cross-provider-test",
        seed_scale_repeat_matrices=[
            _seed_scale_repeat_matrix_with_runs(
                artifact_id="deepseek-matrix",
                model="deepseek-v4-flash",
                base_url="https://api.deepseek.com",
                compact_positive=True,
                deliberative_positive=True,
            ),
            _seed_scale_repeat_matrix_with_runs(
                artifact_id="lmstudio-matrix",
                model="openai/gpt-oss-20b",
                base_url="http://127.0.0.1:1234/v1",
                compact_positive=False,
                deliberative_positive=True,
            ),
        ],
    )

    assert matrix["overall_status"] == "cross_provider_selected_variant_positive"
    assert matrix["positive_provider_environment_count"] == 1
    assert matrix["selected_prompt_variant"] == "deliberative"
    assert matrix["prompt_variant_stability"]["compact"] == {
        "provider_environment_count": 2,
        "positive_provider_environment_count": 1,
        "all_provider_environments_positive": False,
    }
    assert matrix["prompt_variant_stability"]["deliberative"] == {
        "provider_environment_count": 2,
        "positive_provider_environment_count": 2,
        "all_provider_environments_positive": True,
    }
    assert "prompt_variant_selection_required" in matrix["risk_flags"]


def test_cross_provider_matrix_script_writes_json(tmp_path):
    deepseek = tmp_path / "deepseek.json"
    lmstudio = tmp_path / "lmstudio.json"
    output = tmp_path / "cross-provider.json"
    deepseek.write_text(
        json.dumps(
            _seed_scale_repeat_matrix(
                artifact_id="deepseek-matrix",
                model="deepseek-v4-flash",
                base_url="https://api.deepseek.com",
                status="seed_scale_repeat_signal_positive",
            )
        )
    )
    lmstudio.write_text(
        json.dumps(
            _seed_scale_repeat_matrix(
                artifact_id="lmstudio-matrix",
                model="openai/gpt-oss-20b",
                base_url="http://127.0.0.1:1234/v1",
                status="seed_scale_repeat_signal_positive",
            )
        )
    )

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_llm_cross_provider_matrix.py",
            "--matrix-artifacts",
            str(deepseek),
            str(lmstudio),
            "--output",
            str(output),
            "--artifact-id",
            "lcdu-cross-provider-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "lcdu-cross-provider-test",
        "output": str(output),
        "positive_provider_environment_count": 2,
        "provider_environment_count": 2,
        "status": "cross_provider_signal_positive",
    }
    assert json.loads(output.read_text())["overall_status"] == (
        "cross_provider_signal_positive"
    )


def _seed_scale_repeat_matrix(
    *,
    artifact_id: str,
    model: str,
    base_url: str,
    status: str,
) -> dict:
    is_positive = status == "seed_scale_repeat_signal_positive"
    return {
        "schema_version": "lcdu-anes-llm-seed-scale-repeat-matrix-v1",
        "artifact_id": artifact_id,
        "overall_status": status,
        "validation_type": "llm_seed_scale_repeat_matrix",
        "provider": "openai",
        "model": model,
        "base_url": base_url,
        "prompt_variants": ["compact", "deliberative"],
        "segment_scales": [2, 4],
        "segment_offsets": [0, 1],
        "run_count": 8,
        "positive_run_count": 8 if is_positive else 4,
        "task_stability": {
            "public_health_medical_insurance_attitude_v1": {
                "run_count": 8,
                "accepted_count": 8 if is_positive else 4,
                "accepted_rate": 1.0 if is_positive else 0.5,
                "test_improved_count": 8 if is_positive else 4,
                "test_improved_rate": 1.0 if is_positive else 0.5,
            },
            "climate_energy_regulation_attitude_v1": {
                "run_count": 8,
                "accepted_count": 8,
                "accepted_rate": 1.0,
                "test_improved_count": 8,
                "test_improved_rate": 1.0,
            },
        },
        "llm_accounting": {
            "total_call_count": 144,
            "total_input_tokens": 1000,
            "total_output_tokens": 500,
            "parse_failure_count": 0,
        },
    }


def _seed_scale_repeat_matrix_with_runs(
    *,
    artifact_id: str,
    model: str,
    base_url: str,
    compact_positive: bool,
    deliberative_positive: bool,
) -> dict:
    matrix = _seed_scale_repeat_matrix(
        artifact_id=artifact_id,
        model=model,
        base_url=base_url,
        status=(
            "seed_scale_repeat_signal_positive"
            if compact_positive and deliberative_positive
            else "seed_scale_repeat_signal_mixed"
        ),
    )
    matrix["positive_run_count"] = int(compact_positive) + int(deliberative_positive)
    matrix["run_count"] = 2
    matrix["run_results"] = [
        _run_result(
            artifact_id=f"{artifact_id}-compact",
            prompt_variant="compact",
            positive=compact_positive,
        ),
        _run_result(
            artifact_id=f"{artifact_id}-deliberative",
            prompt_variant="deliberative",
            positive=deliberative_positive,
        ),
    ]
    return matrix


def _run_result(*, artifact_id: str, prompt_variant: str, positive: bool) -> dict:
    return {
        "artifact_id": artifact_id,
        "overall_status": (
            "cross_task_llm_signal_positive"
            if positive
            else "cross_task_llm_signal_mixed"
        ),
        "prompt_variant": prompt_variant,
        "task_summaries": {
            "public_health_medical_insurance_attitude_v1": {
                "candidate_accepted": positive,
                "test_initial_loss": 0.01,
                "test_final_loss": 0.005 if positive else 0.01,
            },
            "climate_energy_regulation_attitude_v1": {
                "candidate_accepted": True,
                "test_initial_loss": 0.01,
                "test_final_loss": 0.005,
            },
        },
    }
