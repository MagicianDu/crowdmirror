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
from experiments.r12_high_risk_holdout_registry import (
    R12_HIGH_RISK_HOLDOUT_REGISTRY_SCHEMA_VERSION,
)
from experiments.r12_high_risk_holdout_transfer_replay import (
    R12_HIGH_RISK_HOLDOUT_TRANSFER_REPLAY_SCHEMA_VERSION,
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
    r12_high_risk_holdout_registry: dict[str, Any] | None = None,
    r12_high_risk_holdout_transfer_replay: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_transfer_validation(r12_transfer_validation)
    if r12_high_risk_holdout_registry is not None:
        _validate_high_risk_registry(r12_high_risk_holdout_registry)
    if r12_high_risk_holdout_transfer_replay is not None:
        _validate_high_risk_replay(r12_high_risk_holdout_transfer_replay)
    positive_transfer = (
        r12_transfer_validation["acceptance_gates"]["positive_transfer_guarded"]
        is True
    )
    high_risk_boundary = _high_risk_holdout_boundary(
        r12_high_risk_holdout_registry
    )
    high_risk_replay_boundary = _high_risk_replay_boundary(
        r12_high_risk_holdout_transfer_replay
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
            high_risk_boundary=high_risk_boundary,
            high_risk_replay_boundary=high_risk_replay_boundary,
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
            **(
                {
                    "r12_high_risk_research_holdout_candidates_present": (
                        r12_high_risk_holdout_registry["acceptance_gates"][
                            "high_risk_research_holdout_candidates_present"
                        ]
                    ),
                    "r12_product_default_high_risk_holdout_present": (
                        r12_high_risk_holdout_registry["acceptance_gates"][
                            "product_default_low_sensitive_high_risk_holdout_present"
                        ]
                    ),
                }
                if r12_high_risk_holdout_registry is not None
                else {}
            ),
            **(
                {
                    "r12_high_risk_replay_mae_improved": (
                        r12_high_risk_holdout_transfer_replay["acceptance_gates"][
                            "mae_improved"
                        ]
                    ),
                    "r12_high_risk_replay_recall_improved": (
                        r12_high_risk_holdout_transfer_replay["acceptance_gates"][
                            "static_prior_miss_recovery_improved"
                        ]
                        or r12_high_risk_holdout_transfer_replay["acceptance_gates"][
                            "abnormal_segment_recall_improved"
                        ]
                    ),
                }
                if r12_high_risk_holdout_transfer_replay is not None
                else {}
            ),
        },
        "source_registry": _source_registry(
            r12_transfer_validation=r12_transfer_validation,
            r12_high_risk_holdout_registry=r12_high_risk_holdout_registry,
            r12_high_risk_holdout_transfer_replay=(
                r12_high_risk_holdout_transfer_replay
            ),
        ),
        "source_refs": [
            r12_transfer_validation["artifact_id"],
            *(
                [r12_high_risk_holdout_registry["artifact_id"]]
                if r12_high_risk_holdout_registry is not None
                else []
            ),
            *(
                [r12_high_risk_holdout_transfer_replay["artifact_id"]]
                if r12_high_risk_holdout_transfer_replay is not None
                else []
            ),
        ],
        "allowed_claims": [
            (
                "Product can display R12 as a source-backed guarded transfer "
                "evidence card."
            ),
            (
                "R12 transfer evidence is secondary and requires customer or "
                "field outcome review before any runtime-default update."
            ),
            *(
                [
                    (
                        "R12 has research-only high-risk holdout candidates, but "
                        "Product default use remains blocked until low-sensitive "
                        "or customer-approved holdout validation exists."
                    )
                ]
                if r12_high_risk_holdout_registry is not None
                else []
            ),
        ],
        "blocked_claims": [
            "R12 validated",
            "R12 supports Product core method by default",
            "R12 can override guarded baseline primary decision",
            "R12 Product default high-risk recovery validated",
            "static-prior miss recovery improved on high-risk replay",
            "abnormal segment recall improved on high-risk replay",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "runtime default ready",
            "精准预测系统",
        ],
    }
    if r12_high_risk_holdout_registry is None:
        report["blocked_claims"] = [
            item
            for item in report["blocked_claims"]
            if item != "R12 Product default high-risk recovery validated"
            and item != "static-prior miss recovery improved on high-risk replay"
            and item != "abnormal segment recall improved on high-risk replay"
        ]
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


def _validate_high_risk_registry(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_HIGH_RISK_HOLDOUT_REGISTRY_SCHEMA_VERSION:
        raise ValueError(
            "r12_high_risk_holdout_registry.schema_version must be "
            f"{R12_HIGH_RISK_HOLDOUT_REGISTRY_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 high-risk holdout registry acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 high-risk registry must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 high-risk registry must not allow runtime default")


def _validate_high_risk_replay(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_HIGH_RISK_HOLDOUT_TRANSFER_REPLAY_SCHEMA_VERSION:
        raise ValueError(
            "r12_high_risk_holdout_transfer_replay.schema_version must be "
            f"{R12_HIGH_RISK_HOLDOUT_TRANSFER_REPLAY_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 high-risk replay acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 high-risk replay must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 high-risk replay must not allow runtime default")


def _transfer_evidence_card(
    transfer_validation: dict[str, Any],
    *,
    positive_transfer: bool,
    high_risk_boundary: dict[str, Any] | None = None,
    high_risk_replay_boundary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    split_metrics = transfer_validation["split_metrics"]
    validation = split_metrics["validation"]
    holdout = split_metrics["holdout"]
    evidence_summary = {
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
        "extended_metric_gates": transfer_validation["extended_metric_gates"],
    }
    if high_risk_boundary is not None:
        evidence_summary["high_risk_holdout_boundary"] = high_risk_boundary
    if high_risk_replay_boundary is not None:
        evidence_summary["high_risk_replay_boundary"] = high_risk_replay_boundary
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
        "evidence_summary": evidence_summary,
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


def _high_risk_holdout_boundary(
    registry: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if registry is None:
        return None
    summary = registry["candidate_summary"]
    gates = registry["acceptance_gates"]
    return {
        "registry_status": registry["status"],
        "research_eligible_case_count": summary["research_eligible_case_count"],
        "research_recoverable_static_prior_miss_count": summary[
            "research_recoverable_static_prior_miss_count"
        ],
        "product_default_eligible_case_count": summary[
            "product_default_eligible_case_count"
        ],
        "product_default_low_sensitive_high_risk_holdout_present": gates[
            "product_default_low_sensitive_high_risk_holdout_present"
        ],
        "product_claim_boundary": (
            "research_only_until_low_sensitive_or_customer_approved_holdout"
        ),
    }


def _high_risk_replay_boundary(
    replay: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if replay is None:
        return None
    metrics = replay["metric_comparison"]
    gates = replay["acceptance_gates"]
    return {
        "replay_status": replay["status"],
        "transfer_decision": replay["transfer_decision"],
        "mean_absolute_error_delta": metrics["mean_absolute_error"]["delta"],
        "static_prior_miss_recovery_delta": metrics[
            "static_prior_miss_recovery"
        ]["delta"],
        "abnormal_segment_recall_delta": metrics["abnormal_segment_recall"][
            "delta"
        ],
        "product_support_level": replay["product_support_level"],
        "product_default_eligible_high_risk_holdout_present": gates[
            "product_default_eligible_high_risk_holdout_present"
        ],
    }


def _source_registry(
    *,
    r12_transfer_validation: dict[str, Any],
    r12_high_risk_holdout_registry: dict[str, Any] | None,
    r12_high_risk_holdout_transfer_replay: dict[str, Any] | None,
) -> list[dict[str, str]]:
    registry = [
        {
            "artifact_id": r12_transfer_validation["artifact_id"],
            "path": (
                "experiments/results/r12_transfer_validation/"
                "r12-transfer-validation-current-001.json"
            ),
        }
    ]
    if r12_high_risk_holdout_registry is not None:
        registry.append(
            {
                "artifact_id": r12_high_risk_holdout_registry["artifact_id"],
                "path": (
                    "experiments/results/r12_high_risk_holdout_registry/"
                    "r12-high-risk-holdout-registry-current-001.json"
                ),
            }
        )
    if r12_high_risk_holdout_transfer_replay is not None:
        registry.append(
            {
                "artifact_id": r12_high_risk_holdout_transfer_replay[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_high_risk_holdout_transfer_replay/"
                    "r12-high-risk-holdout-transfer-replay-current-001.json"
                ),
            }
        )
    return registry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r12-transfer-validation-path", required=True)
    parser.add_argument("--r12-high-risk-holdout-registry-path")
    parser.add_argument("--r12-high-risk-holdout-transfer-replay-path")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_product_support_gate(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_transfer_validation=load_json_artifact(args.r12_transfer_validation_path),
        r12_high_risk_holdout_registry=(
            load_json_artifact(args.r12_high_risk_holdout_registry_path)
            if args.r12_high_risk_holdout_registry_path
            else None
        ),
        r12_high_risk_holdout_transfer_replay=(
            load_json_artifact(args.r12_high_risk_holdout_transfer_replay_path)
            if args.r12_high_risk_holdout_transfer_replay_path
            else None
        ),
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
