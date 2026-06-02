from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


THEORY_PROOF_SCHEMA_VERSION = "lcdu-theoretical-identification-proof-v1"
THEORY_CONTRACT_SCHEMA_VERSION = "lcdu-theory-contract-v1"
HYBRID_METHOD_SCHEMA_VERSION = "lcdu-anes-hybrid-method-validation-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_lcdu_theoretical_identification_proof(
    *,
    artifact_id: str,
    theory_contract: dict[str, Any],
    hybrid_method_validation: dict[str, Any],
) -> dict[str, Any]:
    _validate_theory_contract(theory_contract)
    _validate_hybrid_method_validation(hybrid_method_validation)
    task_count = int(hybrid_method_validation["task_count"])
    numeric_parity_count = int(hybrid_method_validation["numeric_parity_count"])
    strict_copy_positive_count = int(
        hybrid_method_validation["strict_copy_positive_count"]
    )
    proof = {
        "schema_version": THEORY_PROOF_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            task_count=task_count,
            numeric_parity_count=numeric_parity_count,
            strict_copy_positive_count=strict_copy_positive_count,
        ),
        "validation_type": "lcdu_theoretical_identification_proof",
        "source_artifact_ids": [
            theory_contract["artifact_id"],
            hybrid_method_validation["artifact_id"],
        ],
        "method_family": "LCDU-hybrid",
        "closed_gate_ids": ["theoretical_identification_proof_ready"],
        "formal_claims": [
            {
                "claim_id": "split_isolation",
                "statement": (
                    "Calibration-derived anchors and heldout-selected method "
                    "choices are fixed before test loss is read; test split is "
                    "used only for final claim checking."
                ),
                "artifact_evidence": [
                    "candidate_generation_split=calibration",
                    "candidate_acceptance_split=heldout",
                    "final_claim_check_split=test",
                ],
            },
            {
                "claim_id": "anchor_copy_identification",
                "statement": (
                    "If the LLM strict-copy distribution equals the calibration "
                    "segment anchor within tolerance, LCDU-hybrid's numeric "
                    "prediction is identified with the deterministic anchor "
                    "program under the same segment schema."
                ),
                "artifact_evidence": [
                    "strict_copy_positive_count",
                    "numeric_parity_count",
                    "hybrid_numeric_parity",
                ],
            },
            {
                "claim_id": "non_superiority_boundary",
                "statement": (
                    "Because LCDU-hybrid reuses the deterministic anchor as its "
                    "numeric component, it can claim numeric parity and audit "
                    "decomposition, not accuracy superiority over that anchor."
                ),
                "artifact_evidence": [
                    "research_decision=reframe_as_hybrid_auditable_constraint_framework_not_accuracy_win",
                    "risk_flag=not_accuracy_win_over_deterministic_anchor",
                ],
            },
        ],
        "task_count": task_count,
        "numeric_parity_count": numeric_parity_count,
        "strict_copy_positive_count": strict_copy_positive_count,
        "identification_result": _identification_result(
            task_count=task_count,
            numeric_parity_count=numeric_parity_count,
            strict_copy_positive_count=strict_copy_positive_count,
        ),
        "claim_boundary": (
            "This is a bounded identification proof for LCDU-hybrid under the "
            "current ANES segment schema and strict-copy contract. It does not "
            "prove external validity, finer-schema robustness, customer field "
            "prediction, or accuracy superiority over deterministic anchors."
        ),
        "remaining_theory_risks": [
            "external_validity_bound_missing",
            "finer_schema_identifiability_unproven",
            "narrative_utility_metric_missing",
            "customer_field_validation_missing",
        ],
    }
    _assert_strict_json(proof)
    return proof


def write_lcdu_theoretical_identification_proof(
    output: str | Path,
    *,
    artifact_id: str,
    theory_contract_path: str | Path,
    hybrid_method_validation_path: str | Path,
) -> dict[str, Any]:
    proof = build_lcdu_theoretical_identification_proof(
        artifact_id=artifact_id,
        theory_contract=load_json_artifact(theory_contract_path),
        hybrid_method_validation=load_json_artifact(hybrid_method_validation_path),
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(proof, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"artifact": proof, "output_path": str(output_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--theory-contract",
        default="experiments/results/lcdu_theory/lcdu-theory-contract-current-001.json",
    )
    parser.add_argument(
        "--hybrid-method-validation",
        default=(
            "experiments/results/lcdu_hybrid_method/"
            "lcdu-anes-hybrid-method-validation-current-001.json"
        ),
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/lcdu_theory/"
            "lcdu-theoretical-identification-proof-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-theoretical-identification-proof-current-001",
    )
    args = parser.parse_args()
    written = write_lcdu_theoretical_identification_proof(
        args.output,
        artifact_id=args.artifact_id,
        theory_contract_path=args.theory_contract,
        hybrid_method_validation_path=args.hybrid_method_validation,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "closed_gate_ids": artifact["closed_gate_ids"],
                "identification_result": artifact["identification_result"],
                "output": written["output_path"],
                "status": artifact["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_theory_contract(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != THEORY_CONTRACT_SCHEMA_VERSION:
        raise ValueError("theory contract has unsupported schema_version")
    if artifact.get("overall_status") != "formal_objects_mapped":
        raise ValueError("theory contract must map formal objects")
    if "complete_lcdu_theory_contract" not in artifact.get("closed_gate_ids", []):
        raise ValueError("theory contract has not closed the object-mapping gate")


def _validate_hybrid_method_validation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != HYBRID_METHOD_SCHEMA_VERSION:
        raise ValueError("hybrid method validation has unsupported schema_version")
    if artifact.get("validation_type") != "lcdu_hybrid_method_validation":
        raise ValueError("hybrid method validation has unsupported validation_type")
    for field_name in (
        "task_count",
        "numeric_parity_count",
        "strict_copy_positive_count",
        "research_decision",
    ):
        if field_name not in artifact:
            raise ValueError(f"hybrid method validation missing {field_name}")


def _overall_status(
    *,
    task_count: int,
    numeric_parity_count: int,
    strict_copy_positive_count: int,
) -> str:
    if (
        task_count > 0
        and numeric_parity_count == task_count
        and strict_copy_positive_count == task_count
    ):
        return "bounded_hybrid_identification_proof_ready"
    return "bounded_hybrid_identification_proof_incomplete"


def _identification_result(
    *,
    task_count: int,
    numeric_parity_count: int,
    strict_copy_positive_count: int,
) -> str:
    if (
        task_count > 0
        and numeric_parity_count == task_count
        and strict_copy_positive_count == task_count
    ):
        return "hybrid_numeric_distribution_identified_with_segment_anchor"
    return "hybrid_numeric_distribution_not_fully_identified"


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU theoretical proof must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
