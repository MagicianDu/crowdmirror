from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


RESEARCH_DECISION_SCHEMA_VERSION = "lcdu-research-decision-index-v1"
PAPER_GATE_SCHEMA_VERSION = "lcdu-paper-gate-index-v1"
HYBRID_METHOD_SCHEMA_VERSION = "lcdu-anes-hybrid-method-validation-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_lcdu_research_decision_index(
    *,
    artifact_id: str,
    paper_gate_index: dict[str, Any],
    hybrid_method_validation: dict[str, Any],
) -> dict[str, Any]:
    _validate_paper_gate_index(paper_gate_index)
    _validate_hybrid_method_validation(hybrid_method_validation)
    completed = set(paper_gate_index["completed_subgates"])
    required_next = set(paper_gate_index["required_next_gates"])
    soft_rejected = "strong_baseline_signal_not_positive" in completed
    hybrid_ready = "hybrid_method_numeric_parity_not_accuracy_win" in completed
    theory_ready = "theoretical_identification_proof_ready" in completed
    finer_schema_ready = "finer_schema_robustness_signal_positive" in completed
    decision = {
        "schema_version": RESEARCH_DECISION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            soft_rejected=soft_rejected,
            hybrid_ready=hybrid_ready,
            theory_ready=theory_ready,
            finer_schema_ready=finer_schema_ready,
        ),
        "validation_type": "lcdu_research_decision_index",
        "source_artifact_ids": [
            paper_gate_index["artifact_id"],
            hybrid_method_validation["artifact_id"],
        ],
        "primary_decision": {
            "lcdu_soft": (
                "reject_as_ccf_a_main_contribution_accuracy_optimizer"
                if soft_rejected
                else "insufficient_evidence"
            ),
            "lcdu_strict": (
                "use_as_identification_component"
                if theory_ready and hybrid_ready
                else "insufficient_evidence"
            ),
            "lcdu_hybrid": (
                "conditionally_promising_as_auditable_constraint_framework"
                if hybrid_ready and theory_ready and finer_schema_ready
                else "insufficient_evidence"
            ),
            "ccf_a_gate": (
                "not_passed_under_accuracy_superiority_criterion"
                if "run_strong_baseline_matrix" in required_next
                else "passed"
            ),
        },
        "recommended_research_frame": (
            "LCDU-hybrid as an auditable constraint-identification and reporting "
            "framework, not LCDU-soft as an accuracy-superior prompt optimizer."
        ),
        "stop_loss_rules": [
            "Do not continue LCDU-soft prompt tuning as the main contribution unless it beats deterministic anchors under the frozen strong-baseline matrix.",
            "Do not claim CCF-A sufficiency from numeric parity alone.",
            "Do not present strict-copy repair as evidence that the original soft prompt passed strong baselines.",
        ],
        "remaining_evidence_for_ccf_a": [
            "auditability_metric",
            "explanation_faithfulness_metric",
            "counterfactual_reporting_metric",
            "external_customer_or_additional_public_dataset_validation",
            "strong_baseline_reframed_for_hybrid_objective",
        ],
        "paper_gate_required_next_gates": paper_gate_index["required_next_gates"],
        "claim_boundary": (
            "This decision index determines the current research direction. It "
            "does not claim the CCF-A gate is passed; it records that LCDU-soft "
            "is not viable as an accuracy-superior main contribution, while "
            "LCDU-hybrid remains a conditional main-contribution candidate under "
            "an auditable-constraint framework objective."
        ),
    }
    _assert_strict_json(decision)
    return decision


def write_lcdu_research_decision_index(
    output: str | Path,
    *,
    artifact_id: str,
    paper_gate_index_path: str | Path,
    hybrid_method_validation_path: str | Path,
) -> dict[str, Any]:
    artifact = build_lcdu_research_decision_index(
        artifact_id=artifact_id,
        paper_gate_index=load_json_artifact(paper_gate_index_path),
        hybrid_method_validation=load_json_artifact(hybrid_method_validation_path),
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"artifact": artifact, "output_path": str(output_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--paper-gate-index",
        default="experiments/results/lcdu_paper_gate/lcdu-paper-gate-index-current-001.json",
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
            "experiments/results/lcdu_research_decision/"
            "lcdu-research-decision-index-current-001.json"
        ),
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-research-decision-index-current-001",
    )
    args = parser.parse_args()
    written = write_lcdu_research_decision_index(
        args.output,
        artifact_id=args.artifact_id,
        paper_gate_index_path=args.paper_gate_index,
        hybrid_method_validation_path=args.hybrid_method_validation,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "ccf_a_gate": artifact["primary_decision"]["ccf_a_gate"],
                "hybrid_decision": artifact["primary_decision"]["lcdu_hybrid"],
                "output": written["output_path"],
                "soft_decision": artifact["primary_decision"]["lcdu_soft"],
                "status": artifact["overall_status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_paper_gate_index(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != PAPER_GATE_SCHEMA_VERSION:
        raise ValueError("paper gate index has unsupported schema_version")
    for field_name in ("artifact_id", "completed_subgates", "required_next_gates"):
        if field_name not in artifact:
            raise ValueError(f"paper gate index missing {field_name}")


def _validate_hybrid_method_validation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != HYBRID_METHOD_SCHEMA_VERSION:
        raise ValueError("hybrid method validation has unsupported schema_version")
    if artifact.get("validation_type") != "lcdu_hybrid_method_validation":
        raise ValueError("hybrid method validation has unsupported validation_type")
    if "research_decision" not in artifact:
        raise ValueError("hybrid method validation missing research_decision")


def _overall_status(
    *,
    soft_rejected: bool,
    hybrid_ready: bool,
    theory_ready: bool,
    finer_schema_ready: bool,
) -> str:
    if soft_rejected and hybrid_ready and theory_ready and finer_schema_ready:
        return "decision_boundary_reached_hybrid_conditional"
    return "decision_boundary_incomplete"


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU research decision index must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
