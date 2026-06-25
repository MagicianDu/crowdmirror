from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    assert_strict_json,
    load_json_artifact,
    non_empty_string,
    write_json_artifact,
)
from experiments.r12_transfer_validation import (
    R12_TRANSFER_VALIDATION_SCHEMA_VERSION,
)


R12_PRODUCT_SUPPORT_GATE_SCHEMA_VERSION = "r12-product-support-gate-v1"
R12_PRODUCT_SUPPORT_GATE_CLAIM_BOUNDARY = (
    "R12 Product support gate artifact. It allows Product to display a "
    "source-backed R12 transfer-validation evidence card as secondary evidence, "
    "while preserving guarded baseline primary decisions. It is not Product "
    "core method validation, not field validation, and not runtime default "
    "authorization."
)


def build_r12_product_support_gate(
    *,
    artifact_id: str,
    run_id: str,
    r12_transfer_validation: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_transfer_validation(r12_transfer_validation)
    positive_transfer = (
        r12_transfer_validation["acceptance_gates"]["positive_transfer_guarded"]
        is True
    )
    report = {
        "schema_version": R12_PRODUCT_SUPPORT_GATE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_product_support_gate_ready_guarded",
        "claim_level": "product_secondary_evidence_only",
        "claim_boundary": R12_PRODUCT_SUPPORT_GATE_CLAIM_BOUNDARY,
        "product_support_contract": {
            "source_backed_only": True,
            "customer_visible_evidence_card_allowed": True,
            "secondary_evidence_card_only": True,
            "customer_visible_primary_claims_use_guarded_baseline": True,
            "r12_can_override_primary_decision": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "transfer_evidence_card": _transfer_evidence_card(
            r12_transfer_validation,
            positive_transfer=positive_transfer,
        ),
        "customer_visible_primary_decision": {
            "primary_decision_source": "guarded_baseline_customer_value_report",
            "r12_output_role": "secondary_transfer_evidence_card_only",
            "r12_can_override_primary_decision": False,
            "runtime_default_allowed": False,
        },
        "outcome_review_handoff": {
            "handoff_id": "r12_transfer_evidence_outcome_review",
            "target_artifact_id": "r6-product-outcome-review-current-001",
            "requires_customer_or_field_outcome": True,
            "update_candidate_scope": [
                "mechanism_weight",
                "segment_sensitivity",
                "interaction_edge_weight",
                "uncertainty_parameter",
            ],
            "prompt_or_persona_manual_patch_allowed": False,
            "runtime_default_allowed": False,
        },
        "acceptance_gates": {
            "r12_transfer_positive_guarded": positive_transfer,
            "customer_visible_evidence_card_allowed": True,
            "secondary_evidence_card_only": True,
            "primary_claims_guarded_baseline_only": True,
            "r12_can_override_primary_decision": False,
            "product_core_method_ready": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_registry": [
            {
                "artifact_id": r12_transfer_validation["artifact_id"],
                "path": (
                    "experiments/results/r12_transfer_validation/"
                    "r12-transfer-validation-current-001.json"
                ),
            }
        ],
        "source_refs": [r12_transfer_validation["artifact_id"]],
        "allowed_claims": [
            (
                "Product can display R12 as a source-backed guarded transfer "
                "evidence card."
            ),
            (
                "R12 transfer evidence is secondary and requires customer or "
                "field outcome review before any runtime-default update."
            ),
        ],
        "blocked_claims": [
            "R12 validated",
            "R12 supports Product core method by default",
            "R12 can override guarded baseline primary decision",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "runtime default ready",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_product_support_gate(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r12_product_support_gate(**kwargs))


def _validate_transfer_validation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_TRANSFER_VALIDATION_SCHEMA_VERSION:
        raise ValueError(
            "r12_transfer_validation.schema_version must be "
            f"{R12_TRANSFER_VALIDATION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12_transfer_validation.acceptance_gates must be an object")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 transfer validation must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 transfer validation must not allow runtime default")
    if gates.get("train_metrics_used_for_transfer_decision") is not False:
        raise ValueError("r12 transfer validation must not use train metrics as proof")


def _transfer_evidence_card(
    transfer_validation: dict[str, Any],
    *,
    positive_transfer: bool,
) -> dict[str, Any]:
    split_metrics = transfer_validation["split_metrics"]
    validation = split_metrics["validation"]
    holdout = split_metrics["holdout"]
    return {
        "card_id": "r12_transfer_validation_evidence_card",
        "title": "R12 guarded transfer validation evidence",
        "claim_status": (
            "guarded_transfer_positive_secondary_evidence"
            if positive_transfer
            else "guarded_transfer_blocked_or_diagnostic"
        ),
        "display_allowed": True,
        "primary_decision_allowed": False,
        "metrics": {
            "update_transfer_gain": transfer_validation["update_transfer_gain"],
            "validation_mean_absolute_error_delta": validation[
                "mean_absolute_error_delta"
            ],
            "holdout_mean_absolute_error_delta": holdout[
                "mean_absolute_error_delta"
            ],
            "interval_coverage_delta": holdout["interval_coverage_delta"],
            "false_alarm_rate_delta": holdout["false_alarm_rate_delta"],
        },
        "evidence_summary": {
            "transfer_decision": transfer_validation["transfer_decision"],
            "accepted_update": transfer_validation["accepted_update"],
            "claim_level": transfer_validation["claim_level"],
            "train_metrics_used_for_transfer_decision": transfer_validation[
                "transfer_accounting"
            ]["train_metrics_used_for_transfer_decision"],
            "field_outcome_validated": transfer_validation["acceptance_gates"][
                "field_outcome_validated"
            ],
            "runtime_default_allowed": transfer_validation["acceptance_gates"][
                "runtime_default_allowed"
            ],
        },
        "allowed_display_claims": [
            (
                "R12 has a guarded public-proxy transfer signal that can be "
                "shown as secondary evidence."
            ),
            (
                "R12 evidence remains runtime-off and requires field or "
                "customer outcome review before any default update."
            ),
        ],
        "blocked_display_claims": [
            "R12 primary decision",
            "R12 field validated",
            "R12 runtime default",
            "R12 precise point prediction",
            "R12 Product core method ready",
        ],
        "source_artifact_ids": [transfer_validation["artifact_id"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r12-transfer-validation-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_product_support_gate(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_transfer_validation=load_json_artifact(args.r12_transfer_validation_path),
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
