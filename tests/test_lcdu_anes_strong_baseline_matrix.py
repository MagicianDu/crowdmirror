import json
import subprocess
import sys

from experiments.lcdu_anes_strong_baseline_matrix import (
    build_lcdu_anes_strong_baseline_matrix,
)


def test_strong_baseline_matrix_reports_lcdu_advantage_and_missing_families():
    matrix = build_lcdu_anes_strong_baseline_matrix(
        artifact_id="lcdu-strong-baseline-test",
        llm_validation_artifacts=[_llm_validation_artifact()],
        anchor_validation_artifacts=[_anchor_validation_artifact()],
        required_baseline_families=[
            "llm_raw_prompt",
            "llm_aggregate_anchor",
            "deterministic_anchor_search",
            "textgrad_or_prompt_optimizer",
            "population_search",
        ],
        lcdU_method_id="lcdu_segment_anchor_prompt",
    )

    assert matrix["schema_version"] == "lcdu-anes-strong-baseline-matrix-v1"
    assert matrix["overall_status"] == "strong_baseline_partial_lcdu_leads"
    assert matrix["lcdU_method_id"] == "lcdu_segment_anchor_prompt"
    assert matrix["covered_baseline_families"] == [
        "deterministic_anchor_search",
        "llm_aggregate_anchor",
        "llm_raw_prompt",
    ]
    assert matrix["missing_baseline_families"] == [
        "population_search",
        "textgrad_or_prompt_optimizer",
    ]
    assert matrix["lcdU_leads_covered_baselines"] is True
    assert matrix["task_results"]["public_health_medical_insurance_attitude_v1"][
        "lcdU_test_loss"
    ] == 0.01
    assert "strong_baseline_family_coverage_incomplete" in matrix["risk_flags"]
    json.dumps(matrix, allow_nan=False)


def test_strong_baseline_matrix_ready_when_required_families_are_covered():
    matrix = build_lcdu_anes_strong_baseline_matrix(
        artifact_id="lcdu-strong-baseline-test",
        llm_validation_artifacts=[_llm_validation_artifact()],
        anchor_validation_artifacts=[_anchor_validation_artifact()],
        required_baseline_families=[
            "llm_raw_prompt",
            "llm_aggregate_anchor",
            "deterministic_anchor_search",
        ],
        lcdU_method_id="lcdu_segment_anchor_prompt",
    )

    assert matrix["overall_status"] == "strong_baseline_lcdu_leads"
    assert matrix["missing_baseline_families"] == []
    assert "strong_baseline_family_coverage_incomplete" not in matrix["risk_flags"]


def test_strong_baseline_matrix_can_close_missing_families_with_baseline_artifact():
    matrix = build_lcdu_anes_strong_baseline_matrix(
        artifact_id="lcdu-strong-baseline-test",
        llm_validation_artifacts=[_llm_validation_artifact()],
        anchor_validation_artifacts=[_anchor_validation_artifact()],
        baseline_family_artifacts=[_baseline_family_artifact()],
        required_baseline_families=[
            "llm_raw_prompt",
            "llm_aggregate_anchor",
            "deterministic_anchor_search",
            "textgrad_or_prompt_optimizer",
            "population_search",
        ],
        lcdU_method_id="lcdu_segment_anchor_prompt",
    )

    assert matrix["missing_baseline_families"] == []
    assert matrix["covered_baseline_families"] == [
        "deterministic_anchor_search",
        "llm_aggregate_anchor",
        "llm_raw_prompt",
        "population_search",
        "textgrad_or_prompt_optimizer",
    ]
    assert matrix["overall_status"] == "strong_baseline_lcdu_leads"
    public_health = matrix["task_results"][
        "public_health_medical_insurance_attitude_v1"
    ]
    assert {
        baseline["baseline_family"] for baseline in public_health["covered_baselines"]
    } == {
        "deterministic_anchor_search",
        "llm_aggregate_anchor",
        "llm_raw_prompt",
        "population_search",
        "textgrad_or_prompt_optimizer",
    }


def test_strong_baseline_matrix_selects_lcdu_by_heldout_not_test_peeking():
    weaker_on_heldout = _llm_validation_artifact()
    weaker_on_heldout["artifact_id"] = "llm-validation-test-peeking-risk"
    task = weaker_on_heldout["task_results"][
        "public_health_medical_insurance_attitude_v1"
    ]
    task["heldout"]["loss_by_method"]["lcdu_segment_anchor_prompt"] = 0.5
    task["test"]["loss_by_method"]["lcdu_segment_anchor_prompt"] = 0.001

    matrix = build_lcdu_anes_strong_baseline_matrix(
        artifact_id="lcdu-strong-baseline-test",
        llm_validation_artifacts=[_llm_validation_artifact(), weaker_on_heldout],
        anchor_validation_artifacts=[_anchor_validation_artifact()],
        required_baseline_families=[
            "llm_raw_prompt",
            "llm_aggregate_anchor",
            "deterministic_anchor_search",
        ],
        lcdU_method_id="lcdu_segment_anchor_prompt",
    )

    public_health = matrix["task_results"][
        "public_health_medical_insurance_attitude_v1"
    ]
    assert public_health["lcdU_test_loss"] == 0.01
    assert public_health["lcdU_selected_source_artifact_id"] == "llm-validation-test"


def test_strong_baseline_matrix_script_writes_json(tmp_path):
    llm = tmp_path / "llm.json"
    anchor = tmp_path / "anchor.json"
    output = tmp_path / "strong-baseline.json"
    llm.write_text(json.dumps(_llm_validation_artifact()))
    anchor.write_text(json.dumps(_anchor_validation_artifact()))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_strong_baseline_matrix.py",
            "--llm-validation-artifacts",
            str(llm),
            "--anchor-validation-artifacts",
            str(anchor),
            "--output",
            str(output),
            "--artifact-id",
            "lcdu-strong-baseline-test",
            "--required-baseline-families",
            "llm_raw_prompt",
            "llm_aggregate_anchor",
            "deterministic_anchor_search",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "lcdu-strong-baseline-test",
        "lcdU_leads_covered_baselines": True,
        "missing_baseline_family_count": 0,
        "output": str(output),
        "status": "strong_baseline_lcdu_leads",
    }
    assert json.loads(output.read_text())["overall_status"] == (
        "strong_baseline_lcdu_leads"
    )


def _llm_validation_artifact() -> dict:
    return {
        "schema_version": "lcdu-anes-llm-simulator-validation-v1",
        "artifact_id": "llm-validation-test",
        "overall_status": "cross_task_llm_signal_positive",
        "validation_type": "split_gated_llm_segment_simulator_smoke",
        "provider": "openai",
        "model": "deepseek-v4-flash",
        "base_url": "https://api.deepseek.com",
        "max_segments_per_task": 16,
        "prompt_variant": "deliberative",
        "task_count": 2,
        "task_results": {
            "public_health_medical_insurance_attitude_v1": _llm_task_result(
                lcdU_loss=0.01,
                raw_loss=0.05,
                aggregate_loss=0.04,
            ),
            "climate_energy_regulation_attitude_v1": _llm_task_result(
                lcdU_loss=0.02,
                raw_loss=0.06,
                aggregate_loss=0.05,
            ),
        },
        "llm_accounting": {
            "total_call_count": 96,
            "total_input_tokens": 1000,
            "total_output_tokens": 500,
            "parse_failure_count": 0,
        },
    }


def _llm_task_result(*, lcdU_loss: float, raw_loss: float, aggregate_loss: float) -> dict:
    return {
        "candidate_accepted": True,
        "accepted_method_id": "lcdu_segment_anchor_prompt",
        "heldout": {
            "loss_by_method": {
                "raw_prompt": raw_loss,
                "aggregate_anchor_prompt": aggregate_loss,
                "lcdu_segment_anchor_prompt": lcdU_loss,
            }
        },
        "test": {
            "loss_by_method": {
                "raw_prompt": raw_loss,
                "aggregate_anchor_prompt": aggregate_loss,
                "lcdu_segment_anchor_prompt": lcdU_loss,
            },
            "final_method_id": "lcdu_segment_anchor_prompt",
        },
        "selected_segments": ["s1", "s2"],
    }


def _anchor_validation_artifact() -> dict:
    return {
        "schema_version": "lcdu-anes-cross-task-validation-v1",
        "artifact_id": "anchor-validation-test",
        "overall_status": "cross_task_anchor_signal_positive",
        "validation_type": "split_gated_segment_anchor_transfer_smoke",
        "task_count": 2,
        "task_results": {
            "public_health_medical_insurance_attitude_v1": _anchor_task_result(
                best_loss=0.012
            ),
            "climate_energy_regulation_attitude_v1": _anchor_task_result(
                best_loss=0.025
            ),
        },
    }


def _anchor_task_result(*, best_loss: float) -> dict:
    return {
        "candidate_accepted": True,
        "accepted_method_id": "calibration_segment_anchor",
        "heldout": {
            "loss_by_method": {
                "uniform_prior": 0.1,
                "calibration_aggregate_prior": 0.08,
                "calibration_segment_anchor": best_loss,
            }
        },
        "test": {
            "loss_by_method": {
                "uniform_prior": 0.1,
                "calibration_aggregate_prior": 0.08,
                "calibration_segment_anchor": best_loss,
            }
        },
    }


def _baseline_family_artifact() -> dict:
    return {
        "schema_version": "lcdu-anes-baseline-family-matrix-v1",
        "artifact_id": "baseline-family-test",
        "overall_status": "baseline_family_matrix_ready",
        "validation_type": "lcdu_baseline_family_matrix",
        "baseline_families": [
            "population_search",
            "textgrad_or_prompt_optimizer",
        ],
        "task_results": {
            "public_health_medical_insurance_attitude_v1": {
                "baseline_results": [
                    {
                        "baseline_family": "population_search",
                        "method_id": "population_search_alpha_0.75",
                        "source_artifact_id": "baseline-family-test",
                        "test_loss": 0.02,
                    },
                    {
                        "baseline_family": "textgrad_or_prompt_optimizer",
                        "method_id": "prompt_optimizer_deliberative_raw_prompt",
                        "source_artifact_id": "baseline-family-test",
                        "test_loss": 0.03,
                    },
                ]
            },
            "climate_energy_regulation_attitude_v1": {
                "baseline_results": [
                    {
                        "baseline_family": "population_search",
                        "method_id": "population_search_alpha_0.75",
                        "source_artifact_id": "baseline-family-test",
                        "test_loss": 0.03,
                    },
                    {
                        "baseline_family": "textgrad_or_prompt_optimizer",
                        "method_id": "prompt_optimizer_deliberative_raw_prompt",
                        "source_artifact_id": "baseline-family-test",
                        "test_loss": 0.04,
                    },
                ]
            },
        },
    }
