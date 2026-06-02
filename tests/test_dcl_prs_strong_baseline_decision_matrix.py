import json
import subprocess
import sys

from experiments.dcl_prs_strong_baseline_decision_matrix import (
    build_dcl_prs_strong_baseline_decision_matrix,
)


def test_decision_matrix_recommends_stoploss_when_strong_win_is_not_proven():
    decision = build_dcl_prs_strong_baseline_decision_matrix(
        artifact_id="dcl-prs-strong-baseline-decision-test",
        dcl_prs_strong_baseline_matrix=_dcl_prs_not_leading_fixture(),
        gss_real_repair_effect_validation=_gss_real_effect_fixture(),
        multi_dataset_generalization_matrix=_multi_dataset_partial_fixture(),
        lcdU_strong_baseline_matrices=[
            _lcdu_lcr_sg_not_leading_fixture(),
            _lcdu_llm_core_not_leading_fixture(),
        ],
    )

    assert (
        decision["schema_version"]
        == "dcl-prs-strong-baseline-decision-matrix-v1"
    )
    assert decision["overall_status"] == "decision_boundary_stoploss_recommended"
    assert decision["evidence_class"] == "engineering_result_only"
    assert decision["stable_strong_baseline_win_proven"] is False
    assert decision["primary_decision"]["ccf_a_gate"] == (
        "not_passed_under_accuracy_superiority_criterion"
    )
    assert decision["primary_decision"]["research_claim"] == (
        "stoploss_dcl_prs_as_algorithm_main_claim"
    )
    assert "strong_baseline_win_missing" in decision["stoploss_triggers"]
    assert (
        "prediction_scenarios_not_runtime_llm_outputs"
        in decision["stoploss_triggers"]
    )
    assert "multi_dataset_generalization_incomplete" in decision["stoploss_triggers"]
    assert decision["next_required_experiment"] == (
        "run_dcl_prs_runtime_strong_baseline_trial_or_retire_algorithm_main_claim"
    )
    json.dumps(decision, allow_nan=False)


def test_decision_matrix_does_not_count_gss_smoke_repairs_as_strong_baseline_win():
    dcl = _dcl_prs_not_leading_fixture()
    dcl["blocking_gaps"] = []
    dcl["l2_readiness"]["gss_real_effect_validation_ready"] = True
    gss = _gss_real_effect_fixture()
    gss["real_effect_promoted_count"] = 10

    decision = build_dcl_prs_strong_baseline_decision_matrix(
        artifact_id="dcl-prs-strong-baseline-decision-test",
        dcl_prs_strong_baseline_matrix=dcl,
        gss_real_repair_effect_validation=gss,
        multi_dataset_generalization_matrix=_multi_dataset_partial_fixture(),
        lcdU_strong_baseline_matrices=[],
    )

    assert decision["stable_strong_baseline_win_proven"] is False
    assert decision["evidence_class"] == "engineering_result_only"
    assert "not_strong_baseline_evidence" in decision["stoploss_triggers"]
    assert "prediction_scenarios_not_runtime_llm_outputs" in decision[
        "stoploss_triggers"
    ]


def test_decision_matrix_can_promote_future_true_stable_strong_baseline_win():
    dcl = _dcl_prs_not_leading_fixture()
    dcl["overall_status"] = "strong_baseline_dcl_prs_leads"
    dcl["paper_gate_eligible"] = True
    dcl["dcl_prs_leads_covered_baselines"] = True
    dcl["baseline_results"] = [
        {
            "baseline_family": "deterministic_anchor",
            "comparison_status": "beaten",
            "dcl_prs_beats_baseline": True,
        },
        {
            "baseline_family": "LCDU-LCR-SG",
            "comparison_status": "beaten",
            "dcl_prs_beats_baseline": True,
        },
        {
            "baseline_family": "fixed_party_or_ideology_prior",
            "comparison_status": "beaten",
            "dcl_prs_beats_baseline": True,
        },
    ]
    dcl["blocking_gaps"] = []
    dcl["risk_flags"] = ["runtime_prediction_evidence", "multi_dataset_effect_evidence"]
    gss = _gss_real_effect_fixture()
    gss["risk_flags"] = ["runtime_llm_outputs", "strong_baseline_evidence"]

    decision = build_dcl_prs_strong_baseline_decision_matrix(
        artifact_id="dcl-prs-strong-baseline-decision-test",
        dcl_prs_strong_baseline_matrix=dcl,
        gss_real_repair_effect_validation=gss,
        multi_dataset_generalization_matrix=_multi_dataset_closed_fixture(),
        lcdU_strong_baseline_matrices=[_lcdu_lcr_sg_not_leading_fixture()],
    )

    assert decision["overall_status"] == "decision_boundary_research_candidate"
    assert decision["evidence_class"] == "research_result_candidate"
    assert decision["stable_strong_baseline_win_proven"] is True
    assert decision["primary_decision"]["ccf_a_gate"] == (
        "conditional_candidate_pending_full_paper_audit"
    )
    assert decision["stoploss_triggers"] == []


def test_decision_matrix_script_writes_artifact(tmp_path):
    dcl_path = tmp_path / "dcl.json"
    gss_path = tmp_path / "gss.json"
    multi_path = tmp_path / "multi.json"
    lcr_path = tmp_path / "lcr.json"
    llm_core_path = tmp_path / "llm-core.json"
    output_dir = tmp_path / "decision"
    dcl_path.write_text(json.dumps(_dcl_prs_not_leading_fixture()))
    gss_path.write_text(json.dumps(_gss_real_effect_fixture()))
    multi_path.write_text(json.dumps(_multi_dataset_partial_fixture()))
    lcr_path.write_text(json.dumps(_lcdu_lcr_sg_not_leading_fixture()))
    llm_core_path.write_text(json.dumps(_lcdu_llm_core_not_leading_fixture()))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_strong_baseline_decision_matrix.py",
            "--dcl-prs-strong-baseline-matrix-path",
            str(dcl_path),
            "--gss-real-repair-effect-validation-path",
            str(gss_path),
            "--multi-dataset-generalization-matrix-path",
            str(multi_path),
            "--lcdu-strong-baseline-matrix-path",
            str(lcr_path),
            "--lcdu-strong-baseline-matrix-path",
            str(llm_core_path),
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-strong-baseline-decision-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "evidence_class": "engineering_result_only",
        "index": str(output_dir / "dcl-prs-strong-baseline-decision-test.json"),
        "overall_status": "decision_boundary_stoploss_recommended",
        "stable_strong_baseline_win_proven": False,
    }


def _dcl_prs_not_leading_fixture() -> dict:
    return {
        "schema_version": "dcl-prs-strong-baseline-matrix-v1",
        "artifact_id": "dcl-prs-strong-baseline-test",
        "overall_status": "strong_baseline_dcl_prs_not_leading",
        "paper_gate_eligible": False,
        "dcl_prs_leads_covered_baselines": False,
        "covered_baseline_families": [
            "deterministic_anchor",
            "LCDU-LCR-SG",
            "fixed_party_or_ideology_prior",
            "DCL-PRS",
        ],
        "baseline_results": [
            {
                "baseline_family": "deterministic_anchor",
                "comparison_status": "reference_baseline_ready",
                "dcl_prs_beats_baseline": None,
            },
            {
                "baseline_family": "LCDU-LCR-SG",
                "comparison_status": "not_beaten_without_strong_baseline_win",
                "dcl_prs_beats_baseline": False,
            },
            {
                "baseline_family": "fixed_party_or_ideology_prior",
                "comparison_status": "not_beaten_without_multi_dataset_generalization",
                "dcl_prs_beats_baseline": False,
            },
        ],
        "l2_readiness": {
            "gss_real_effect_validation_ready": True,
            "multi_dataset_generalization_partial": True,
        },
        "blocking_gaps": [
            "multi_dataset_generalization_incomplete",
            "strong_baseline_win_missing",
        ],
        "risk_flags": [
            "readiness_not_accuracy",
            "not_multi_dataset_effect_evidence",
            "not_paper_gate_eligible",
        ],
    }


def _gss_real_effect_fixture() -> dict:
    return {
        "schema_version": "dcl-prs-gss-real-repair-effect-v1",
        "artifact_id": "dcl-prs-gss-real-repair-effect-test",
        "overall_status": "gss_real_repair_effect_validation_ready",
        "source_id": "gss",
        "task_slice_id": "gss_public_health_confidence_attitude_v1",
        "accepted_candidate_count": 2,
        "real_effect_promoted_count": 2,
        "risk_flags": [
            "single_gss_policy_task_only",
            "prediction_scenarios_not_runtime_llm_outputs",
            "not_strong_baseline_evidence",
        ],
    }


def _multi_dataset_partial_fixture() -> dict:
    return {
        "schema_version": "dcl-prs-multi-dataset-generalization-matrix-v1",
        "artifact_id": "dcl-prs-multi-dataset-generalization-test",
        "overall_status": "multi_dataset_generalization_partial",
        "available_real_effect_dataset_count": 1,
        "blocked_dataset_count": 1,
        "generalization_gate_closed": False,
    }


def _multi_dataset_closed_fixture() -> dict:
    return {
        "schema_version": "dcl-prs-multi-dataset-generalization-matrix-v1",
        "artifact_id": "dcl-prs-multi-dataset-generalization-test",
        "overall_status": "multi_dataset_generalization_ready",
        "available_real_effect_dataset_count": 3,
        "blocked_dataset_count": 0,
        "generalization_gate_closed": True,
    }


def _lcdu_lcr_sg_not_leading_fixture() -> dict:
    return {
        "schema_version": "lcdu-anes-strong-baseline-matrix-v1",
        "artifact_id": "lcdu-anes-lcr-sg-strong-baseline-test",
        "method_family_under_test": "LCDU-LCR-SG",
        "overall_status": "strong_baseline_lcdu_not_leading",
        "paper_gate_eligible": False,
        "lcdU_leads_covered_baselines": False,
        "strong_baseline_gates": {
            "fixed_party_prior_gate_pass": False,
            "joint_success_gate_pass": False,
            "test_worst_guard_gate_pass": False,
        },
        "risk_flags": [
            "lcr_sg_not_better_than_fixed_party_prior",
            "lcr_sg_not_full_paper_gate_eligible",
        ],
    }


def _lcdu_llm_core_not_leading_fixture() -> dict:
    return {
        "schema_version": "lcdu-anes-strong-baseline-matrix-v1",
        "artifact_id": "lcdu-anes-llm-core-strong-baseline-test",
        "method_family_under_test": "LLM-guided_prior_router",
        "overall_status": "strong_baseline_lcdu_not_leading",
        "paper_gate_eligible": False,
        "lcdU_leads_covered_baselines": False,
        "strong_baseline_gates": {
            "fixed_party_prior_gate_pass": False,
            "joint_success_gate_pass": True,
            "test_worst_guard_gate_pass": True,
        },
        "risk_flags": [
            "llm_core_not_better_than_fixed_party_prior",
        ],
    }
