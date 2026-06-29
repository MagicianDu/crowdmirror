from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PAPER_GATE_INDEX_SCHEMA_VERSION = "lcdu-paper-gate-index-v1"
LCDU_METHOD_SUMMARY_SCHEMA_VERSION = "policy-reaction-lcdu-l3-method-summary-v1"

BLOCKING_GAP_PREFIXES = (
    "ccf_a_",
    "cross_provider_",
    "theoretical_",
    "full_population_",
    "finer_schema_",
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_lcdu_paper_gate_index(
    *,
    artifact_id: str,
    method_summary: dict[str, Any],
    plan_ref: str,
    theory_ref: str,
    algorithm_ref: str,
    claim_boundary_ref: str,
    data_audit_ref: str,
    baseline_spec_ref: str,
    theory_contract: dict[str, Any] | None = None,
    theoretical_identification_proof: dict[str, Any] | None = None,
    public_task_card_index: dict[str, Any] | None = None,
    public_task_ingestion_smoke_index: dict[str, Any] | None = None,
    public_task_microdata_ingestion: dict[str, Any] | None = None,
    cross_task_validation: dict[str, Any] | None = None,
    llm_simulator_validation: dict[str, Any] | None = None,
    llm_seed_scale_repeat_matrix: dict[str, Any] | None = None,
    llm_instability_diagnosis: dict[str, Any] | None = None,
    llm_prompt_variant_repeat_matrix: dict[str, Any] | None = None,
    llm_cross_provider_matrix: dict[str, Any] | None = None,
    llm_scale_stability_matrix: dict[str, Any] | None = None,
    finer_schema_robustness_matrix: dict[str, Any] | None = None,
    strong_baseline_matrix: dict[str, Any] | None = None,
    anchor_fidelity_repair: dict[str, Any] | None = None,
    hybrid_method_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _validate_method_summary(method_summary)
    if theory_contract is not None:
        _validate_theory_contract(theory_contract)
    if theoretical_identification_proof is not None:
        _validate_theoretical_identification_proof(theoretical_identification_proof)
    if public_task_card_index is not None:
        _validate_public_task_card_index(public_task_card_index)
    if public_task_ingestion_smoke_index is not None:
        _validate_public_task_ingestion_smoke_index(
            public_task_ingestion_smoke_index
        )
    if public_task_microdata_ingestion is not None:
        _validate_public_task_microdata_ingestion(public_task_microdata_ingestion)
    if cross_task_validation is not None:
        _validate_cross_task_validation(cross_task_validation)
    if llm_simulator_validation is not None:
        _validate_llm_simulator_validation(llm_simulator_validation)
    if llm_seed_scale_repeat_matrix is not None:
        _validate_llm_seed_scale_repeat_matrix(llm_seed_scale_repeat_matrix)
    if llm_instability_diagnosis is not None:
        _validate_llm_instability_diagnosis(llm_instability_diagnosis)
    if llm_prompt_variant_repeat_matrix is not None:
        _validate_llm_prompt_variant_repeat_matrix(llm_prompt_variant_repeat_matrix)
    if llm_cross_provider_matrix is not None:
        _validate_llm_cross_provider_matrix(llm_cross_provider_matrix)
    if llm_scale_stability_matrix is not None:
        _validate_llm_scale_stability_matrix(llm_scale_stability_matrix)
    if finer_schema_robustness_matrix is not None:
        _validate_finer_schema_robustness_matrix(finer_schema_robustness_matrix)
    if strong_baseline_matrix is not None:
        _validate_strong_baseline_matrix(strong_baseline_matrix)
    if anchor_fidelity_repair is not None:
        _validate_anchor_fidelity_repair(anchor_fidelity_repair)
    if hybrid_method_validation is not None:
        _validate_hybrid_method_validation(hybrid_method_validation)
    blocking_gaps = _blocking_gaps(method_summary["ccf_a_gaps"])
    completed_subgates = _completed_subgates(
        theory_contract=theory_contract,
        theoretical_identification_proof=theoretical_identification_proof,
        public_task_card_index=public_task_card_index,
        public_task_ingestion_smoke_index=public_task_ingestion_smoke_index,
        public_task_microdata_ingestion=public_task_microdata_ingestion,
        cross_task_validation=cross_task_validation,
        llm_simulator_validation=llm_simulator_validation,
        llm_seed_scale_repeat_matrix=llm_seed_scale_repeat_matrix,
        llm_instability_diagnosis=llm_instability_diagnosis,
        llm_prompt_variant_repeat_matrix=llm_prompt_variant_repeat_matrix,
        llm_cross_provider_matrix=llm_cross_provider_matrix,
        llm_scale_stability_matrix=llm_scale_stability_matrix,
        finer_schema_robustness_matrix=finer_schema_robustness_matrix,
        strong_baseline_matrix=strong_baseline_matrix,
        anchor_fidelity_repair=anchor_fidelity_repair,
        hybrid_method_validation=hybrid_method_validation,
    )
    required_next_gates = _required_next_gates(
        blocking_gaps,
        completed_subgates=completed_subgates,
    )
    evidence_package_refs = [
        plan_ref,
        theory_ref,
        algorithm_ref,
        claim_boundary_ref,
        data_audit_ref,
        baseline_spec_ref,
        method_summary["artifact_id"],
    ]
    if theory_contract is not None:
        evidence_package_refs.append(theory_contract["artifact_id"])
    if theoretical_identification_proof is not None:
        evidence_package_refs.append(theoretical_identification_proof["artifact_id"])
    if public_task_card_index is not None:
        evidence_package_refs.append(public_task_card_index["artifact_id"])
    if public_task_ingestion_smoke_index is not None:
        evidence_package_refs.append(public_task_ingestion_smoke_index["artifact_id"])
    if public_task_microdata_ingestion is not None:
        evidence_package_refs.append(public_task_microdata_ingestion["artifact_id"])
    if cross_task_validation is not None:
        evidence_package_refs.append(cross_task_validation["artifact_id"])
    if llm_simulator_validation is not None:
        evidence_package_refs.append(llm_simulator_validation["artifact_id"])
    if llm_seed_scale_repeat_matrix is not None:
        evidence_package_refs.append(llm_seed_scale_repeat_matrix["artifact_id"])
    if llm_instability_diagnosis is not None:
        evidence_package_refs.append(llm_instability_diagnosis["artifact_id"])
    if llm_prompt_variant_repeat_matrix is not None:
        evidence_package_refs.append(llm_prompt_variant_repeat_matrix["artifact_id"])
    if llm_cross_provider_matrix is not None:
        evidence_package_refs.append(llm_cross_provider_matrix["artifact_id"])
    if llm_scale_stability_matrix is not None:
        evidence_package_refs.append(llm_scale_stability_matrix["artifact_id"])
    if finer_schema_robustness_matrix is not None:
        evidence_package_refs.append(finer_schema_robustness_matrix["artifact_id"])
    if strong_baseline_matrix is not None:
        evidence_package_refs.append(strong_baseline_matrix["artifact_id"])
    if anchor_fidelity_repair is not None:
        evidence_package_refs.append(anchor_fidelity_repair["artifact_id"])
    if hybrid_method_validation is not None:
        evidence_package_refs.append(hybrid_method_validation["artifact_id"])
    method = {
        "artifact_id": method_summary["artifact_id"],
        "method_id": method_summary["method_id"],
        "overall_status": method_summary["overall_status"],
        "product_transfer_status": method_summary["product_transfer_status"],
        "accepted_candidate_ids": method_summary["accepted_candidate_ids"],
        "best_runtime_loss": _best_runtime_loss(method_summary),
    }
    index = {
        "schema_version": PAPER_GATE_INDEX_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "research_plan_ready_but_ccf_a_gate_open",
        "method": method,
        "ccf_a_gate": {
            "status": "open",
            "blocking_gap_count": len(blocking_gaps),
            "blocking_gaps": blocking_gaps,
        },
        "completed_subgates": completed_subgates,
        "evidence_package_refs": evidence_package_refs,
        "required_next_gates": required_next_gates,
        "risk_flags": method_summary["risk_flags"],
        "claim_boundaries": method_summary["claim_boundaries"],
    }
    _assert_strict_json(index)
    return index


def write_lcdu_paper_gate_index(
    *,
    output: str | Path,
    artifact_id: str,
    method_summary_path: str | Path,
    plan_ref: str,
    theory_ref: str,
    algorithm_ref: str,
    claim_boundary_ref: str,
    data_audit_ref: str,
    baseline_spec_ref: str,
    theory_contract_path: str | Path | None = None,
    theoretical_identification_proof_path: str | Path | None = None,
    public_task_card_index_path: str | Path | None = None,
    public_task_ingestion_smoke_index_path: str | Path | None = None,
    public_task_microdata_ingestion_path: str | Path | None = None,
    cross_task_validation_path: str | Path | None = None,
    llm_simulator_validation_path: str | Path | None = None,
    llm_seed_scale_repeat_matrix_path: str | Path | None = None,
    llm_instability_diagnosis_path: str | Path | None = None,
    llm_prompt_variant_repeat_matrix_path: str | Path | None = None,
    llm_cross_provider_matrix_path: str | Path | None = None,
    llm_scale_stability_matrix_path: str | Path | None = None,
    finer_schema_robustness_matrix_path: str | Path | None = None,
    strong_baseline_matrix_path: str | Path | None = None,
    anchor_fidelity_repair_path: str | Path | None = None,
    hybrid_method_validation_path: str | Path | None = None,
) -> dict[str, Any]:
    index = build_lcdu_paper_gate_index(
        artifact_id=artifact_id,
        method_summary=load_json_artifact(method_summary_path),
        plan_ref=plan_ref,
        theory_ref=theory_ref,
        algorithm_ref=algorithm_ref,
        claim_boundary_ref=claim_boundary_ref,
        data_audit_ref=data_audit_ref,
        baseline_spec_ref=baseline_spec_ref,
        theory_contract=(
            load_json_artifact(theory_contract_path)
            if theory_contract_path
            else None
        ),
        theoretical_identification_proof=(
            load_json_artifact(theoretical_identification_proof_path)
            if theoretical_identification_proof_path
            else None
        ),
        public_task_card_index=(
            load_json_artifact(public_task_card_index_path)
            if public_task_card_index_path
            else None
        ),
        public_task_ingestion_smoke_index=(
            load_json_artifact(public_task_ingestion_smoke_index_path)
            if public_task_ingestion_smoke_index_path
            else None
        ),
        public_task_microdata_ingestion=(
            load_json_artifact(public_task_microdata_ingestion_path)
            if public_task_microdata_ingestion_path
            else None
        ),
        cross_task_validation=(
            load_json_artifact(cross_task_validation_path)
            if cross_task_validation_path
            else None
        ),
        llm_simulator_validation=(
            load_json_artifact(llm_simulator_validation_path)
            if llm_simulator_validation_path
            else None
        ),
        llm_seed_scale_repeat_matrix=(
            load_json_artifact(llm_seed_scale_repeat_matrix_path)
            if llm_seed_scale_repeat_matrix_path
            else None
        ),
        llm_instability_diagnosis=(
            load_json_artifact(llm_instability_diagnosis_path)
            if llm_instability_diagnosis_path
            else None
        ),
        llm_prompt_variant_repeat_matrix=(
            load_json_artifact(llm_prompt_variant_repeat_matrix_path)
            if llm_prompt_variant_repeat_matrix_path
            else None
        ),
        llm_cross_provider_matrix=(
            load_json_artifact(llm_cross_provider_matrix_path)
            if llm_cross_provider_matrix_path
            else None
        ),
        llm_scale_stability_matrix=(
            load_json_artifact(llm_scale_stability_matrix_path)
            if llm_scale_stability_matrix_path
            else None
        ),
        finer_schema_robustness_matrix=(
            load_json_artifact(finer_schema_robustness_matrix_path)
            if finer_schema_robustness_matrix_path
            else None
        ),
        strong_baseline_matrix=(
            load_json_artifact(strong_baseline_matrix_path)
            if strong_baseline_matrix_path
            else None
        ),
        anchor_fidelity_repair=(
            load_json_artifact(anchor_fidelity_repair_path)
            if anchor_fidelity_repair_path
            else None
        ),
        hybrid_method_validation=(
            load_json_artifact(hybrid_method_validation_path)
            if hybrid_method_validation_path
            else None
        ),
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(index, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--method-summary",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-lcdu-l3-method-summary-current-001.json"
        ),
    )
    parser.add_argument(
        "--output",
        default="experiments/results/lcdu_paper_gate/lcdu-paper-gate-index-current-001.json",
    )
    parser.add_argument("--artifact-id", default="lcdu-paper-gate-index-current-001")
    parser.add_argument(
        "--plan-ref",
        default="docs/superpowers/plans/2026-05-23-lcdu-ccf-a-research-plan.md",
    )
    parser.add_argument("--theory-ref", default="paper/LCDU_THEORY.md")
    parser.add_argument("--algorithm-ref", default="paper/LCDU_ALGORITHM.md")
    parser.add_argument(
        "--claim-boundary-ref",
        default="paper/LCDU_CLAIM_BOUNDARY.md",
    )
    parser.add_argument("--data-audit-ref", default="paper/LCDU_PUBLIC_DATA_AUDIT.md")
    parser.add_argument("--baseline-spec-ref", default="paper/LCDU_BASELINE_SPEC.md")
    parser.add_argument(
        "--theory-contract",
        default=None,
        help="Optional lcdu-theory-contract-v1 artifact.",
    )
    parser.add_argument(
        "--theoretical-identification-proof",
        default=None,
        help="Optional lcdu-theoretical-identification-proof-v1 artifact.",
    )
    parser.add_argument(
        "--public-task-card-index",
        default=None,
        help="Optional lcdu-public-task-card-index-v1 artifact.",
    )
    parser.add_argument(
        "--public-task-ingestion-smoke-index",
        default=None,
        help="Optional lcdu-public-task-ingestion-smoke-index-v1 artifact.",
    )
    parser.add_argument(
        "--public-task-microdata-ingestion",
        default=None,
        help="Optional lcdu-anes-public-microdata-ingestion-v1 artifact.",
    )
    parser.add_argument(
        "--cross-task-validation",
        default=None,
        help="Optional lcdu-anes-cross-task-validation-v1 artifact.",
    )
    parser.add_argument(
        "--llm-simulator-validation",
        default=None,
        help="Optional lcdu-anes-llm-simulator-validation-v1 artifact.",
    )
    parser.add_argument(
        "--llm-seed-scale-repeat-matrix",
        default=None,
        help="Optional lcdu-anes-llm-seed-scale-repeat-matrix-v1 artifact.",
    )
    parser.add_argument(
        "--llm-instability-diagnosis",
        default=None,
        help="Optional lcdu-anes-llm-instability-diagnosis-v1 artifact.",
    )
    parser.add_argument(
        "--llm-prompt-variant-repeat-matrix",
        default=None,
        help=(
            "Optional lcdu-anes-llm-seed-scale-repeat-matrix-v1 artifact "
            "covering prompt variants after instability diagnosis."
        ),
    )
    parser.add_argument(
        "--llm-cross-provider-matrix",
        default=None,
        help="Optional lcdu-anes-llm-cross-provider-matrix-v1 artifact.",
    )
    parser.add_argument(
        "--llm-scale-stability-matrix",
        default=None,
        help="Optional lcdu-anes-llm-scale-stability-matrix-v1 artifact.",
    )
    parser.add_argument(
        "--finer-schema-robustness-matrix",
        default=None,
        help="Optional lcdu-anes-finer-schema-robustness-matrix-v1 artifact.",
    )
    parser.add_argument(
        "--strong-baseline-matrix",
        default=None,
        help="Optional lcdu-anes-strong-baseline-matrix-v1 artifact.",
    )
    parser.add_argument(
        "--anchor-fidelity-repair",
        default=None,
        help="Optional lcdu-anes-anchor-fidelity-repair-v1 artifact.",
    )
    parser.add_argument(
        "--hybrid-method-validation",
        default=None,
        help="Optional lcdu-anes-hybrid-method-validation-v1 artifact.",
    )
    args = parser.parse_args()
    index = write_lcdu_paper_gate_index(
        output=args.output,
        artifact_id=args.artifact_id,
        method_summary_path=args.method_summary,
        plan_ref=args.plan_ref,
        theory_ref=args.theory_ref,
        algorithm_ref=args.algorithm_ref,
        claim_boundary_ref=args.claim_boundary_ref,
        data_audit_ref=args.data_audit_ref,
        baseline_spec_ref=args.baseline_spec_ref,
        theory_contract_path=args.theory_contract,
        theoretical_identification_proof_path=args.theoretical_identification_proof,
        public_task_card_index_path=args.public_task_card_index,
        public_task_ingestion_smoke_index_path=(
            args.public_task_ingestion_smoke_index
        ),
        public_task_microdata_ingestion_path=args.public_task_microdata_ingestion,
        cross_task_validation_path=args.cross_task_validation,
        llm_simulator_validation_path=args.llm_simulator_validation,
        llm_seed_scale_repeat_matrix_path=args.llm_seed_scale_repeat_matrix,
        llm_instability_diagnosis_path=args.llm_instability_diagnosis,
        llm_prompt_variant_repeat_matrix_path=args.llm_prompt_variant_repeat_matrix,
        llm_cross_provider_matrix_path=args.llm_cross_provider_matrix,
        llm_scale_stability_matrix_path=args.llm_scale_stability_matrix,
        finer_schema_robustness_matrix_path=args.finer_schema_robustness_matrix,
        strong_baseline_matrix_path=args.strong_baseline_matrix,
        anchor_fidelity_repair_path=args.anchor_fidelity_repair,
        hybrid_method_validation_path=args.hybrid_method_validation,
    )
    print(
        json.dumps(
            {
                "artifact_id": index["artifact_id"],
                "blocking_gap_count": index["ccf_a_gate"]["blocking_gap_count"],
                "output": args.output,
                "status": index["ccf_a_gate"]["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_method_summary(method_summary: dict[str, Any]) -> None:
    if method_summary.get("schema_version") != LCDU_METHOD_SUMMARY_SCHEMA_VERSION:
        raise ValueError("method_summary has unsupported schema_version")
    for field_name in (
        "artifact_id",
        "method_id",
        "overall_status",
        "product_transfer_status",
        "accepted_candidate_ids",
        "evidence",
        "ccf_a_gaps",
        "risk_flags",
        "claim_boundaries",
    ):
        if field_name not in method_summary:
            raise ValueError(f"method_summary missing {field_name}")
    if not method_summary["ccf_a_gaps"]:
        raise ValueError("method_summary ccf_a_gaps must not be empty")
    if not isinstance(method_summary["accepted_candidate_ids"], list):
        raise ValueError("method_summary accepted_candidate_ids must be a list")
    if not isinstance(method_summary["evidence"], dict):
        raise ValueError("method_summary evidence must be an object")


def _validate_theory_contract(theory_contract: dict[str, Any]) -> None:
    if theory_contract.get("schema_version") != "lcdu-theory-contract-v1":
        raise ValueError("theory_contract has unsupported schema_version")
    if theory_contract.get("overall_status") != "formal_objects_mapped":
        raise ValueError("theory_contract must map formal objects")
    if not isinstance(theory_contract.get("closed_gate_ids"), list):
        raise ValueError("theory_contract missing closed_gate_ids")


def _validate_theoretical_identification_proof(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "lcdu-theoretical-identification-proof-v1":
        raise ValueError("theoretical_identification_proof has unsupported schema")
    if artifact.get("validation_type") != "lcdu_theoretical_identification_proof":
        raise ValueError(
            "theoretical_identification_proof has unsupported validation_type"
        )
    if artifact.get("overall_status") not in {
        "bounded_hybrid_identification_proof_ready",
        "bounded_hybrid_identification_proof_incomplete",
    }:
        raise ValueError("theoretical_identification_proof has unsupported status")
    if not isinstance(artifact.get("closed_gate_ids"), list):
        raise ValueError("theoretical_identification_proof missing closed_gate_ids")


def _validate_public_task_card_index(task_card_index: dict[str, Any]) -> None:
    if task_card_index.get("schema_version") != "lcdu-public-task-card-index-v1":
        raise ValueError("public_task_card_index has unsupported schema_version")
    if task_card_index.get("overall_status") != "recommended_task_cards_ready":
        raise ValueError("public_task_card_index must be ready")
    if int(task_card_index.get("task_count", 0)) < 2:
        raise ValueError("public_task_card_index must include at least two tasks")


def _validate_public_task_ingestion_smoke_index(
    smoke_index: dict[str, Any],
) -> None:
    if (
        smoke_index.get("schema_version")
        != "lcdu-public-task-ingestion-smoke-index-v1"
    ):
        raise ValueError("public_task_ingestion_smoke_index has unsupported schema_version")
    if smoke_index.get("overall_status") != "target_distribution_skeletons_ready":
        raise ValueError("public_task_ingestion_smoke_index must be ready")
    if int(smoke_index.get("task_count", 0)) < 2:
        raise ValueError(
            "public_task_ingestion_smoke_index must include at least two tasks"
        )


def _validate_public_task_microdata_ingestion(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "lcdu-anes-public-microdata-ingestion-v1":
        raise ValueError("public_task_microdata_ingestion has unsupported schema")
    if artifact.get("overall_status") != (
        "segment_target_distributions_materialized_with_partial_schema"
    ):
        raise ValueError("public_task_microdata_ingestion must materialize targets")
    target_distributions = artifact.get("target_distributions")
    if not isinstance(target_distributions, dict) or len(target_distributions) < 2:
        raise ValueError("public_task_microdata_ingestion must cover two tasks")
    splits = artifact.get("splits")
    if not isinstance(splits, dict) or set(splits) != {"calibration", "heldout", "test"}:
        raise ValueError("public_task_microdata_ingestion must include all splits")


def _validate_cross_task_validation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "lcdu-anes-cross-task-validation-v1":
        raise ValueError("cross_task_validation has unsupported schema")
    if artifact.get("validation_type") != "split_gated_segment_anchor_transfer_smoke":
        raise ValueError("cross_task_validation has unsupported validation_type")
    if int(artifact.get("task_count", 0)) < 2:
        raise ValueError("cross_task_validation must include at least two tasks")
    if artifact.get("overall_status") not in {
        "cross_task_anchor_signal_positive",
        "cross_task_anchor_signal_mixed",
        "cross_task_anchor_signal_negative",
    }:
        raise ValueError("cross_task_validation has unsupported status")


def _validate_llm_simulator_validation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "lcdu-anes-llm-simulator-validation-v1":
        raise ValueError("llm_simulator_validation has unsupported schema")
    if artifact.get("validation_type") != "split_gated_llm_segment_simulator_smoke":
        raise ValueError("llm_simulator_validation has unsupported validation_type")
    if int(artifact.get("task_count", 0)) < 2:
        raise ValueError("llm_simulator_validation must include at least two tasks")
    if artifact.get("overall_status") not in {
        "cross_task_llm_signal_positive",
        "cross_task_llm_signal_mixed",
        "cross_task_llm_signal_negative",
        "cross_task_llm_signal_mixed_parse_risk",
    }:
        raise ValueError("llm_simulator_validation has unsupported status")


def _validate_llm_seed_scale_repeat_matrix(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "lcdu-anes-llm-seed-scale-repeat-matrix-v1":
        raise ValueError("llm_seed_scale_repeat_matrix has unsupported schema")
    if artifact.get("validation_type") != "llm_seed_scale_repeat_matrix":
        raise ValueError("llm_seed_scale_repeat_matrix has unsupported validation_type")
    if int(artifact.get("run_count", 0)) < 1:
        raise ValueError("llm_seed_scale_repeat_matrix must include runs")
    if artifact.get("overall_status") not in {
        "seed_scale_repeat_signal_positive",
        "seed_scale_repeat_signal_mixed",
        "seed_scale_repeat_signal_negative",
        "seed_scale_repeat_signal_mixed_parse_risk",
        "blocked_provider_unavailable",
    }:
        raise ValueError("llm_seed_scale_repeat_matrix has unsupported status")


def _validate_llm_instability_diagnosis(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "lcdu-anes-llm-instability-diagnosis-v1":
        raise ValueError("llm_instability_diagnosis has unsupported schema")
    if int(artifact.get("failure_count", -1)) < 0:
        raise ValueError("llm_instability_diagnosis missing failure_count")
    if artifact.get("overall_status") not in {
        "no_instability_detected",
        "instability_needs_targeted_diagnosis",
        "instability_recovered_by_prompt_variant",
        "instability_partially_recovered_by_prompt_variant",
        "instability_persistent_after_prompt_variants",
    }:
        raise ValueError("llm_instability_diagnosis has unsupported status")


def _validate_llm_prompt_variant_repeat_matrix(artifact: dict[str, Any]) -> None:
    _validate_llm_seed_scale_repeat_matrix(artifact)
    prompt_variants = artifact.get("prompt_variants")
    if not isinstance(prompt_variants, list) or not prompt_variants:
        raise ValueError("llm_prompt_variant_repeat_matrix missing prompt_variants")
    if prompt_variants == ["standard"]:
        raise ValueError(
            "llm_prompt_variant_repeat_matrix must include non-standard variants"
        )


def _validate_llm_cross_provider_matrix(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "lcdu-anes-llm-cross-provider-matrix-v1":
        raise ValueError("llm_cross_provider_matrix has unsupported schema")
    if artifact.get("overall_status") not in {
        "cross_provider_signal_positive",
        "cross_provider_selected_variant_positive",
        "cross_provider_signal_mixed",
        "cross_provider_signal_negative",
        "cross_provider_evidence_insufficient",
    }:
        raise ValueError("llm_cross_provider_matrix has unsupported status")
    if int(artifact.get("provider_environment_count", 0)) < 1:
        raise ValueError("llm_cross_provider_matrix must include providers")


def _validate_llm_scale_stability_matrix(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "lcdu-anes-llm-scale-stability-matrix-v1":
        raise ValueError("llm_scale_stability_matrix has unsupported schema")
    if artifact.get("validation_type") != "llm_segment_scale_stability_matrix":
        raise ValueError("llm_scale_stability_matrix has unsupported validation_type")
    if artifact.get("overall_status") not in {
        "scale_stability_signal_positive",
        "scale_stability_signal_mixed",
        "scale_stability_signal_negative",
        "scale_stability_signal_mixed_parse_risk",
        "scale_stability_evidence_insufficient",
    }:
        raise ValueError("llm_scale_stability_matrix has unsupported status")
    if int(artifact.get("max_segment_scale", 0)) < 1:
        raise ValueError("llm_scale_stability_matrix missing max_segment_scale")


def _validate_finer_schema_robustness_matrix(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        "lcdu-anes-finer-schema-robustness-matrix-v1"
    ):
        raise ValueError("finer_schema_robustness_matrix has unsupported schema")
    if artifact.get("validation_type") != "lcdu_finer_schema_robustness_matrix":
        raise ValueError(
            "finer_schema_robustness_matrix has unsupported validation_type"
        )
    if artifact.get("overall_status") not in {
        "finer_schema_robustness_signal_positive",
        "finer_schema_robustness_signal_mixed",
        "finer_schema_robustness_signal_negative",
    }:
        raise ValueError("finer_schema_robustness_matrix has unsupported status")
    if int(artifact.get("max_axis_count", 0)) < 2:
        raise ValueError("finer_schema_robustness_matrix missing max_axis_count")


def _validate_strong_baseline_matrix(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "lcdu-anes-strong-baseline-matrix-v1":
        raise ValueError("strong_baseline_matrix has unsupported schema")
    if artifact.get("validation_type") != "lcdu_strong_baseline_matrix":
        raise ValueError("strong_baseline_matrix has unsupported validation_type")
    if artifact.get("overall_status") not in {
        "strong_baseline_lcdu_leads",
        "strong_baseline_partial_lcdu_leads",
        "strong_baseline_lcdu_not_leading",
    }:
        raise ValueError("strong_baseline_matrix has unsupported status")


def _validate_anchor_fidelity_repair(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "lcdu-anes-anchor-fidelity-repair-v1":
        raise ValueError("anchor_fidelity_repair has unsupported schema")
    if artifact.get("validation_type") != "lcdu_anchor_fidelity_repair_diagnostic":
        raise ValueError("anchor_fidelity_repair has unsupported validation_type")
    if artifact.get("overall_status") not in {
        "llm_anchor_copy_repair_positive",
        "hybrid_anchor_fidelity_repair_available",
        "anchor_fidelity_repair_not_found",
    }:
        raise ValueError("anchor_fidelity_repair has unsupported status")


def _validate_hybrid_method_validation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "lcdu-anes-hybrid-method-validation-v1":
        raise ValueError("hybrid_method_validation has unsupported schema")
    if artifact.get("validation_type") != "lcdu_hybrid_method_validation":
        raise ValueError("hybrid_method_validation has unsupported validation_type")
    if artifact.get("overall_status") not in {
        "hybrid_candidate_numeric_parity_soft_not_leading",
        "hybrid_candidate_numeric_parity_partial_copy",
        "hybrid_candidate_not_validated",
    }:
        raise ValueError("hybrid_method_validation has unsupported status")


def _best_runtime_loss(method_summary: dict[str, Any]) -> float | None:
    mechanism = method_summary.get("evidence", {}).get("mechanism", {})
    value = mechanism.get("best_runtime_loss")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _blocking_gaps(gaps: list[str]) -> list[str]:
    return [
        gap
        for gap in gaps
        if isinstance(gap, str)
        and any(gap.startswith(prefix) for prefix in BLOCKING_GAP_PREFIXES)
    ]


def _completed_subgates(
    *,
    theory_contract: dict[str, Any] | None,
    theoretical_identification_proof: dict[str, Any] | None,
    public_task_card_index: dict[str, Any] | None,
    public_task_ingestion_smoke_index: dict[str, Any] | None,
    public_task_microdata_ingestion: dict[str, Any] | None,
    cross_task_validation: dict[str, Any] | None,
    llm_simulator_validation: dict[str, Any] | None,
    llm_seed_scale_repeat_matrix: dict[str, Any] | None,
    llm_instability_diagnosis: dict[str, Any] | None,
    llm_prompt_variant_repeat_matrix: dict[str, Any] | None,
    llm_cross_provider_matrix: dict[str, Any] | None,
    llm_scale_stability_matrix: dict[str, Any] | None,
    finer_schema_robustness_matrix: dict[str, Any] | None,
    strong_baseline_matrix: dict[str, Any] | None,
    anchor_fidelity_repair: dict[str, Any] | None,
    hybrid_method_validation: dict[str, Any] | None,
) -> list[str]:
    completed = []
    if theory_contract is not None:
        for gate_id in theory_contract["closed_gate_ids"]:
            if isinstance(gate_id, str) and gate_id not in completed:
                completed.append(gate_id)
    if theoretical_identification_proof is not None:
        completed.append("theoretical_identification_proof_artifact_ready")
        if theoretical_identification_proof.get("overall_status") == (
            "bounded_hybrid_identification_proof_ready"
        ):
            completed.append("theoretical_identification_proof_ready")
        else:
            completed.append("theoretical_identification_proof_incomplete")
    if public_task_card_index is not None:
        completed.append("public_task_cards_ready")
    if public_task_ingestion_smoke_index is not None:
        completed.append("public_task_ingestion_smoke_ready")
    if public_task_microdata_ingestion is not None:
        completed.append("public_task_microdata_sample_slice_ready")
    if cross_task_validation is not None:
        completed.append("cross_task_anchor_validation_ready")
    if llm_simulator_validation is not None:
        completed.append("cross_task_llm_simulator_validation_ready")
    if llm_seed_scale_repeat_matrix is not None:
        completed.append("cross_task_llm_seed_scale_repeat_matrix_ready")
        if llm_seed_scale_repeat_matrix.get("overall_status") == (
            "seed_scale_repeat_signal_positive"
        ):
            completed.append("cross_task_llm_seed_scale_repeat_signal_positive")
        else:
            completed.append("cross_task_llm_seed_scale_repeat_signal_not_positive")
    if llm_instability_diagnosis is not None:
        completed.append("cross_task_llm_instability_diagnosis_ready")
        status = llm_instability_diagnosis.get("overall_status")
        if status in {
            "instability_recovered_by_prompt_variant",
            "instability_partially_recovered_by_prompt_variant",
        }:
            completed.append("cross_task_llm_instability_recovered_by_prompt_variant")
        elif status == "instability_persistent_after_prompt_variants":
            completed.append("cross_task_llm_instability_persistent")
    if llm_prompt_variant_repeat_matrix is not None:
        completed.append("cross_task_llm_prompt_variant_seed_scale_repeat_matrix_ready")
        if llm_prompt_variant_repeat_matrix.get("overall_status") == (
            "seed_scale_repeat_signal_positive"
        ):
            completed.append(
                "cross_task_llm_prompt_variant_seed_scale_repeat_signal_positive"
            )
        else:
            completed.append(
                "cross_task_llm_prompt_variant_seed_scale_repeat_signal_not_positive"
            )
    if llm_cross_provider_matrix is not None:
        completed.append("cross_provider_stability_matrix_ready")
        if llm_cross_provider_matrix.get("overall_status") == (
            "cross_provider_signal_positive"
        ) or llm_cross_provider_matrix.get("overall_status") == (
            "cross_provider_selected_variant_positive"
        ):
            completed.append("cross_provider_stability_signal_positive")
        else:
            completed.append("cross_provider_stability_signal_not_positive")
    if llm_scale_stability_matrix is not None:
        completed.append("scale_stability_matrix_ready")
        if llm_scale_stability_matrix.get("overall_status") == (
            "scale_stability_signal_positive"
        ):
            completed.append("scale_stability_signal_positive")
        else:
            completed.append("scale_stability_signal_not_positive")
    if finer_schema_robustness_matrix is not None:
        completed.append("finer_schema_robustness_matrix_ready")
        if finer_schema_robustness_matrix.get("overall_status") == (
            "finer_schema_robustness_signal_positive"
        ):
            completed.append("finer_schema_robustness_signal_positive")
        else:
            completed.append("finer_schema_robustness_signal_not_positive")
    if strong_baseline_matrix is not None:
        completed.append("strong_baseline_matrix_ready")
        status = strong_baseline_matrix.get("overall_status")
        if status == "strong_baseline_lcdu_leads":
            completed.append("strong_baseline_signal_lcdu_leads")
        elif status == "strong_baseline_partial_lcdu_leads":
            completed.append("strong_baseline_signal_partial")
        else:
            completed.append("strong_baseline_signal_not_positive")
    if anchor_fidelity_repair is not None:
        completed.append("anchor_fidelity_repair_ready")
        status = anchor_fidelity_repair.get("overall_status")
        if status == "llm_anchor_copy_repair_positive":
            completed.append("anchor_fidelity_repair_llm_copy_positive")
        elif status == "hybrid_anchor_fidelity_repair_available":
            completed.append("anchor_fidelity_repair_hybrid_available")
        else:
            completed.append("anchor_fidelity_repair_not_found")
    if hybrid_method_validation is not None:
        completed.append("hybrid_method_validation_ready")
        status = hybrid_method_validation.get("overall_status")
        if status == "hybrid_candidate_numeric_parity_soft_not_leading":
            completed.append("hybrid_method_numeric_parity_not_accuracy_win")
        elif status == "hybrid_candidate_numeric_parity_partial_copy":
            completed.append("hybrid_method_numeric_parity_partial_copy")
        else:
            completed.append("hybrid_method_not_validated")
    return completed


def _required_next_gates(
    blocking_gaps: list[str],
    *,
    completed_subgates: list[str] | None = None,
) -> list[str]:
    completed = set(completed_subgates or [])
    gates = []
    if any(gap.startswith("theoretical_") for gap in blocking_gaps):
        if "complete_lcdu_theory_contract" not in completed:
            gates.append("complete_lcdu_theory_contract")
        elif "theoretical_identification_proof_ready" in completed:
            pass
        else:
            gates.append("formalize_theoretical_identification_proof")
    if any(gap.startswith("ccf_a_") for gap in blocking_gaps):
        if "public_task_ingestion_smoke_ready" not in completed:
            gates.append("run_public_task_ingestion_smoke")
        elif "public_task_microdata_sample_slice_ready" not in completed:
            gates.append("load_public_use_microdata_or_verified_sample_slice")
        elif "cross_task_anchor_validation_ready" not in completed:
            gates.append("run_cross_task_public_data_validation")
        elif "cross_task_llm_simulator_validation_ready" not in completed:
            gates.append("run_cross_task_llm_simulator_validation")
        elif "cross_task_llm_seed_scale_repeat_matrix_ready" not in completed:
            gates.append("run_cross_task_llm_seed_scale_repeat_validation")
        elif "cross_task_llm_seed_scale_repeat_signal_positive" not in completed:
            if (
                "cross_task_llm_prompt_variant_seed_scale_repeat_signal_positive"
                in completed
            ):
                pass
            elif "cross_task_llm_instability_diagnosis_ready" not in completed:
                gates.append("diagnose_cross_task_llm_seed_scale_repeat_instability")
            elif (
                "cross_task_llm_instability_recovered_by_prompt_variant" in completed
            ):
                gates.append("run_prompt_variant_seed_scale_repeat_matrix")
            elif "cross_task_llm_instability_persistent" in completed:
                gates.append(
                    "record_lcdu_instability_failure_boundary_or_try_guarded_update"
                )
    if any(gap.startswith("cross_provider_") for gap in blocking_gaps):
        if "cross_provider_stability_signal_positive" not in completed:
            gates.append("run_cross_provider_stability_matrix")
    if any(gap.startswith("full_population_") for gap in blocking_gaps):
        if "scale_stability_signal_positive" not in completed:
            gates.append("run_scale_stability_matrix")
    if any(gap.startswith("finer_schema_") for gap in blocking_gaps):
        if "finer_schema_robustness_signal_positive" not in completed:
            gates.append("run_finer_schema_robustness_matrix")
    if "strong_baseline_signal_lcdu_leads" not in completed:
        gates.append("run_strong_baseline_matrix")
    return gates


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU paper gate index must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
