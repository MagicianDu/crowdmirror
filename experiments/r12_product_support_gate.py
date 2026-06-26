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
from experiments.r12_recall_oriented_update import (
    R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION,
)
from experiments.r12_recall_update_false_alarm_stress_test import (
    R12_RECALL_UPDATE_FALSE_ALARM_STRESS_SCHEMA_VERSION,
)
from experiments.r12_recall_false_alarm_mitigation_candidate import (
    R12_RECALL_FALSE_ALARM_MITIGATION_SCHEMA_VERSION,
)
from experiments.r12_recall_mitigation_holdout_validation import (
    R12_RECALL_MITIGATION_HOLDOUT_VALIDATION_SCHEMA_VERSION,
)
from experiments.r12_recall_mitigation_independent_holdout_data import (
    R12_RECALL_MITIGATION_INDEPENDENT_HOLDOUT_DATA_SCHEMA_VERSION,
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
    r12_recall_oriented_update: dict[str, Any] | None = None,
    r12_recall_update_false_alarm_stress_test: dict[str, Any] | None = None,
    r12_recall_false_alarm_mitigation_candidate: dict[str, Any] | None = None,
    r12_recall_mitigation_holdout_validation: dict[str, Any] | None = None,
    r12_recall_mitigation_independent_holdout_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_transfer_validation(r12_transfer_validation)
    if r12_high_risk_holdout_registry is not None:
        _validate_high_risk_registry(r12_high_risk_holdout_registry)
    if r12_high_risk_holdout_transfer_replay is not None:
        _validate_high_risk_replay(r12_high_risk_holdout_transfer_replay)
    if r12_recall_oriented_update is not None:
        _validate_recall_oriented_update(r12_recall_oriented_update)
    if r12_recall_update_false_alarm_stress_test is not None:
        _validate_recall_false_alarm_stress(
            r12_recall_update_false_alarm_stress_test
        )
    if r12_recall_false_alarm_mitigation_candidate is not None:
        _validate_recall_false_alarm_mitigation(
            r12_recall_false_alarm_mitigation_candidate
        )
    if r12_recall_mitigation_holdout_validation is not None:
        _validate_recall_mitigation_holdout_validation(
            r12_recall_mitigation_holdout_validation
        )
    if r12_recall_mitigation_independent_holdout_data is not None:
        _validate_recall_mitigation_independent_holdout_data(
            r12_recall_mitigation_independent_holdout_data
        )
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
    recall_update_boundary = _recall_oriented_update_boundary(
        r12_recall_oriented_update
    )
    recall_false_alarm_stress_boundary = _recall_false_alarm_stress_boundary(
        r12_recall_update_false_alarm_stress_test
    )
    recall_false_alarm_mitigation_boundary = (
        _recall_false_alarm_mitigation_boundary(
            r12_recall_false_alarm_mitigation_candidate
        )
    )
    recall_mitigation_holdout_validation_boundary = (
        _recall_mitigation_holdout_validation_boundary(
            r12_recall_mitigation_holdout_validation
        )
    )
    recall_mitigation_independent_holdout_data_boundary = (
        _recall_mitigation_independent_holdout_data_boundary(
            r12_recall_mitigation_independent_holdout_data
        )
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
            recall_update_boundary=recall_update_boundary,
            recall_false_alarm_stress_boundary=(
                recall_false_alarm_stress_boundary
            ),
            recall_false_alarm_mitigation_boundary=(
                recall_false_alarm_mitigation_boundary
            ),
            recall_mitigation_holdout_validation_boundary=(
                recall_mitigation_holdout_validation_boundary
            ),
            recall_mitigation_independent_holdout_data_boundary=(
                recall_mitigation_independent_holdout_data_boundary
            ),
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
            **(
                {
                    "r12_recall_oriented_update_recall_improved": (
                        r12_recall_oriented_update["acceptance_gates"][
                            "recall_improved"
                        ]
                    ),
                    "r12_recall_oriented_update_false_alarm_non_regression": (
                        r12_recall_oriented_update["acceptance_gates"][
                            "false_alarm_non_regression"
                        ]
                    ),
                    "r12_recall_oriented_update_product_default_allowed": (
                        r12_recall_oriented_update["acceptance_gates"][
                            "product_default_allowed"
                        ]
                    ),
                }
                if r12_recall_oriented_update is not None
                else {}
            ),
            **(
                {
                    "r12_recall_false_alarm_stress_passed": (
                        r12_recall_update_false_alarm_stress_test[
                            "acceptance_gates"
                        ]["stress_test_passed"]
                    ),
                    "r12_recall_false_alarm_stress_product_default_allowed": (
                        r12_recall_update_false_alarm_stress_test[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                    "r12_recall_false_alarm_stress_sensitive_concentration": (
                        r12_recall_update_false_alarm_stress_test[
                            "acceptance_gates"
                        ][
                            "new_false_alarms_concentrated_on_sensitive_axis"
                        ]
                    ),
                }
                if r12_recall_update_false_alarm_stress_test is not None
                else {}
            ),
            **(
                {
                    "r12_recall_false_alarm_mitigation_selected": (
                        r12_recall_false_alarm_mitigation_candidate[
                            "acceptance_gates"
                        ]["mitigation_candidate_selected"]
                    ),
                    "r12_recall_false_alarm_mitigation_false_alarm_non_regression": (
                        r12_recall_false_alarm_mitigation_candidate[
                            "acceptance_gates"
                        ]["false_alarm_non_regression"]
                    ),
                    "r12_recall_false_alarm_mitigation_product_default_allowed": (
                        r12_recall_false_alarm_mitigation_candidate[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                    "r12_recall_false_alarm_mitigation_overfit_risk_present": (
                        r12_recall_false_alarm_mitigation_candidate[
                            "acceptance_gates"
                        ]["overfit_risk_present"]
                    ),
                }
                if r12_recall_false_alarm_mitigation_candidate is not None
                else {}
            ),
            **(
                {
                    "r12_recall_mitigation_holdout_validated": (
                        r12_recall_mitigation_holdout_validation[
                            "acceptance_gates"
                        ]["mitigation_holdout_validated"]
                    ),
                    "r12_recall_mitigation_holdout_product_default_allowed": (
                        r12_recall_mitigation_holdout_validation[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                    "r12_recall_mitigation_holdout_independent_present": (
                        r12_recall_mitigation_holdout_validation[
                            "acceptance_gates"
                        ]["independent_holdout_present"]
                    ),
                    "r12_recall_mitigation_holdout_leave_one_stable": (
                        r12_recall_mitigation_holdout_validation[
                            "acceptance_gates"
                        ]["leave_one_false_alarm_band_stable"]
                    ),
                }
                if r12_recall_mitigation_holdout_validation is not None
                else {}
            ),
            **(
                {
                    "r12_recall_mitigation_independent_data_ready": (
                        r12_recall_mitigation_independent_holdout_data[
                            "acceptance_gates"
                        ]["mitigation_independent_data_ready"]
                    ),
                    "r12_recall_mitigation_independent_external_data_ingested": (
                        r12_recall_mitigation_independent_holdout_data[
                            "acceptance_gates"
                        ]["external_independent_data_ingested"]
                    ),
                    "r12_recall_mitigation_independent_low_sensitive_recall_evaluable": (
                        r12_recall_mitigation_independent_holdout_data[
                            "acceptance_gates"
                        ]["low_sensitive_recall_evaluable"]
                    ),
                    "r12_recall_mitigation_independent_product_default_allowed": (
                        r12_recall_mitigation_independent_holdout_data[
                            "acceptance_gates"
                        ]["product_default_allowed"]
                    ),
                }
                if r12_recall_mitigation_independent_holdout_data is not None
                else {}
            ),
        },
        "source_registry": _source_registry(
            r12_transfer_validation=r12_transfer_validation,
            r12_high_risk_holdout_registry=r12_high_risk_holdout_registry,
            r12_high_risk_holdout_transfer_replay=(
                r12_high_risk_holdout_transfer_replay
            ),
            r12_recall_oriented_update=r12_recall_oriented_update,
            r12_recall_update_false_alarm_stress_test=(
                r12_recall_update_false_alarm_stress_test
            ),
            r12_recall_false_alarm_mitigation_candidate=(
                r12_recall_false_alarm_mitigation_candidate
            ),
            r12_recall_mitigation_holdout_validation=(
                r12_recall_mitigation_holdout_validation
            ),
            r12_recall_mitigation_independent_holdout_data=(
                r12_recall_mitigation_independent_holdout_data
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
            *(
                [r12_recall_oriented_update["artifact_id"]]
                if r12_recall_oriented_update is not None
                else []
            ),
            *(
                [r12_recall_update_false_alarm_stress_test["artifact_id"]]
                if r12_recall_update_false_alarm_stress_test is not None
                else []
            ),
            *(
                [r12_recall_false_alarm_mitigation_candidate["artifact_id"]]
                if r12_recall_false_alarm_mitigation_candidate is not None
                else []
            ),
            *(
                [r12_recall_mitigation_holdout_validation["artifact_id"]]
                if r12_recall_mitigation_holdout_validation is not None
                else []
            ),
            *(
                [r12_recall_mitigation_independent_holdout_data["artifact_id"]]
                if r12_recall_mitigation_independent_holdout_data is not None
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
            *(
                [
                    (
                        "R12 recall-oriented activation margin can be shown as a "
                        "research-only improvement with explicit false-alarm and "
                        "precision tradeoff."
                    )
                ]
                if r12_recall_oriented_update is not None
                else []
            ),
            *(
                [
                    (
                        "R12 recall-oriented update has a source-backed "
                        "false-alarm stress boundary and remains Product-default "
                        "blocked."
                    )
                ]
                if r12_recall_update_false_alarm_stress_test is not None
                else []
            ),
            *(
                [
                    (
                        "R12 false-alarm mitigation can be shown as a research-only "
                        "candidate, but it needs independent holdout validation."
                    )
                ]
                if r12_recall_false_alarm_mitigation_candidate is not None
                else []
            ),
            *(
                [
                    (
                        "R12 mitigation holdout validation blocks Product default "
                        "and preserves the candidate as failure diagnosis evidence."
                    )
                ]
                if r12_recall_mitigation_holdout_validation is not None
                else []
            ),
            *(
                [
                    (
                        "R12 independent holdout data audit can be shown as a "
                        "Product evidence boundary, while Product default remains blocked."
                    )
                ]
                if r12_recall_mitigation_independent_holdout_data is not None
                else []
            ),
        ],
        "blocked_claims": _unique_strings(
            [
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
                *(r12_recall_oriented_update or {}).get("blocked_claims", []),
                *(r12_recall_update_false_alarm_stress_test or {}).get(
                    "blocked_claims", []
                ),
                *(r12_recall_false_alarm_mitigation_candidate or {}).get(
                    "blocked_claims", []
                ),
                *(r12_recall_mitigation_holdout_validation or {}).get(
                    "blocked_claims", []
                ),
                *(r12_recall_mitigation_independent_holdout_data or {}).get(
                    "blocked_claims", []
                ),
            ]
        ),
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


def _validate_recall_oriented_update(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION:
        raise ValueError(
            "r12_recall_oriented_update.schema_version must be "
            f"{R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 recall-oriented update acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 recall-oriented update must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 recall-oriented update must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 recall-oriented update must not allow Product default")


def _validate_recall_false_alarm_stress(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_UPDATE_FALSE_ALARM_STRESS_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_recall_update_false_alarm_stress_test.schema_version must be "
            f"{R12_RECALL_UPDATE_FALSE_ALARM_STRESS_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 false-alarm stress acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 false-alarm stress must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 false-alarm stress must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 false-alarm stress must not allow Product default")


def _validate_recall_false_alarm_mitigation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_FALSE_ALARM_MITIGATION_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_recall_false_alarm_mitigation_candidate.schema_version must be "
            f"{R12_RECALL_FALSE_ALARM_MITIGATION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 false-alarm mitigation acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 false-alarm mitigation must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 false-alarm mitigation must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 false-alarm mitigation must not allow Product default")


def _validate_recall_mitigation_holdout_validation(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_MITIGATION_HOLDOUT_VALIDATION_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_recall_mitigation_holdout_validation.schema_version must be "
            f"{R12_RECALL_MITIGATION_HOLDOUT_VALIDATION_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 mitigation holdout validation acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 mitigation holdout validation must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 mitigation holdout validation must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 mitigation holdout validation must not allow Product default")


def _validate_recall_mitigation_independent_holdout_data(
    artifact: dict[str, Any],
) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_MITIGATION_INDEPENDENT_HOLDOUT_DATA_SCHEMA_VERSION
    ):
        raise ValueError(
            "r12_recall_mitigation_independent_holdout_data.schema_version must be "
            f"{R12_RECALL_MITIGATION_INDEPENDENT_HOLDOUT_DATA_SCHEMA_VERSION}"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 independent holdout data acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 independent holdout data must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 independent holdout data must not allow runtime default")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 independent holdout data must not allow Product default")


def _transfer_evidence_card(
    transfer_validation: dict[str, Any],
    *,
    positive_transfer: bool,
    high_risk_boundary: dict[str, Any] | None = None,
    high_risk_replay_boundary: dict[str, Any] | None = None,
    recall_update_boundary: dict[str, Any] | None = None,
    recall_false_alarm_stress_boundary: dict[str, Any] | None = None,
    recall_false_alarm_mitigation_boundary: dict[str, Any] | None = None,
    recall_mitigation_holdout_validation_boundary: dict[str, Any] | None = None,
    recall_mitigation_independent_holdout_data_boundary: dict[str, Any] | None = None,
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
    if recall_update_boundary is not None:
        evidence_summary["recall_oriented_update_boundary"] = recall_update_boundary
    if recall_false_alarm_stress_boundary is not None:
        evidence_summary["recall_false_alarm_stress_boundary"] = (
            recall_false_alarm_stress_boundary
        )
    if recall_false_alarm_mitigation_boundary is not None:
        evidence_summary["recall_false_alarm_mitigation_boundary"] = (
            recall_false_alarm_mitigation_boundary
        )
    if recall_mitigation_holdout_validation_boundary is not None:
        evidence_summary["recall_mitigation_holdout_validation_boundary"] = (
            recall_mitigation_holdout_validation_boundary
        )
    if recall_mitigation_independent_holdout_data_boundary is not None:
        evidence_summary[
            "recall_mitigation_independent_holdout_data_boundary"
        ] = recall_mitigation_independent_holdout_data_boundary
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


def _recall_oriented_update_boundary(
    recall_update: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if recall_update is None:
        return None
    metrics = recall_update["metric_comparison"]
    update_candidate = recall_update["update_candidate"]
    return {
        "update_status": recall_update["status"],
        "acceptance_decision": recall_update["acceptance_decision"],
        "recommended_activation_margin": update_candidate["recommended_value"],
        "static_prior_miss_recovery_delta": metrics[
            "static_prior_miss_recovery"
        ]["delta"],
        "abnormal_segment_recall_delta": metrics["abnormal_segment_recall"][
            "delta"
        ],
        "false_alarm_rate_delta": metrics["false_alarm_rate"]["delta"],
        "precision_delta": metrics["precision"]["delta"],
        "product_default_allowed": update_candidate["product_default_allowed"],
        "next_required_artifact": recall_update["next_required_artifact"],
    }


def _recall_false_alarm_stress_boundary(
    stress: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if stress is None:
        return None
    global_tradeoff = stress["stress_metrics"]["global_tradeoff"]
    low_sensitive = stress["stress_metrics"]["low_sensitive_false_alarm"]
    protected_sensitive = stress["stress_metrics"][
        "protected_sensitive_false_alarm"
    ]
    concentration = stress["stress_metrics"]["false_alarm_concentration"]
    return {
        "stress_status": stress["status"],
        "acceptance_decision": stress["acceptance_decision"],
        "global_recall_delta": global_tradeoff["recall_delta"],
        "global_false_alarm_rate_delta": global_tradeoff[
            "false_alarm_rate_delta"
        ],
        "precision_delta": global_tradeoff["precision_delta"],
        "low_sensitive_recall_evaluable": low_sensitive["recall_evaluable"],
        "low_sensitive_false_alarm_rate_delta": low_sensitive[
            "false_alarm_rate_delta"
        ],
        "protected_sensitive_false_alarm_rate_delta": protected_sensitive[
            "false_alarm_rate_delta"
        ],
        "dominant_false_alarm_segment_column": concentration[
            "dominant_segment_column"
        ],
        "product_default_allowed": stress["acceptance_gates"][
            "product_default_allowed"
        ],
        "next_required_artifact": stress["next_required_artifact"],
    }


def _recall_false_alarm_mitigation_boundary(
    mitigation: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if mitigation is None:
        return None
    selected = mitigation["selected_candidate"]
    metrics = mitigation["metric_comparison"]
    return {
        "mitigation_status": mitigation["status"],
        "acceptance_decision": mitigation["acceptance_decision"],
        "candidate_id": selected["candidate_id"],
        "target_segment_column": selected["target_segment_column"],
        "target_segment_value_min": selected["target_segment_value_min"],
        "target_segment_value_max": selected["target_segment_value_max"],
        "mitigated_recall_delta": metrics["static_prior_miss_recovery"][
            "mitigated_delta"
        ],
        "l7_recall_gain_retained": metrics["static_prior_miss_recovery"][
            "l7_recall_gain_retained"
        ],
        "mitigated_false_alarm_rate_delta": metrics["false_alarm_rate"][
            "mitigated_delta"
        ],
        "mitigated_precision_delta": metrics["precision"]["mitigated_delta"],
        "overfit_risk": selected["overfit_risk"],
        "product_default_allowed": selected["product_default_allowed"],
        "next_required_artifact": mitigation["next_required_artifact"],
    }


def _recall_mitigation_holdout_validation_boundary(
    validation: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if validation is None:
        return None
    leave_one = validation["leave_one_false_alarm_band_validation"]
    gates = validation["acceptance_gates"]
    stable_alternative = validation["stable_alternative_check"]
    return {
        "validation_status": validation["status"],
        "acceptance_decision": validation["acceptance_decision"],
        "leave_one_pass_rate": leave_one["pass_rate"],
        "endpoint_holdout_failure_count": leave_one[
            "endpoint_holdout_failure_count"
        ],
        "independent_holdout_present": gates["independent_holdout_present"],
        "low_sensitive_recall_evaluable": gates[
            "low_sensitive_recall_evaluable"
        ],
        "stable_alternative_recall_retained": stable_alternative[
            "l7_recall_gain_retained"
        ],
        "mitigation_holdout_validated": gates["mitigation_holdout_validated"],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": validation["next_required_artifact"],
    }


def _recall_mitigation_independent_holdout_data_boundary(
    data_audit: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if data_audit is None:
        return None
    summary = data_audit["data_summary"]
    gates = data_audit["acceptance_gates"]
    return {
        "data_status": data_audit["status"],
        "acceptance_decision": data_audit["acceptance_decision"],
        "same_dataset_non_derivation_recall_candidate_count": summary[
            "same_dataset_non_derivation_recall_candidate_count"
        ],
        "low_sensitive_observed_high_risk_count": summary[
            "low_sensitive_observed_high_risk_count"
        ],
        "external_registry_candidate_count": summary[
            "external_registry_candidate_count"
        ],
        "ingested_external_independent_dataset_count": summary[
            "ingested_external_independent_dataset_count"
        ],
        "mitigation_independent_data_ready": gates[
            "mitigation_independent_data_ready"
        ],
        "product_default_allowed": gates["product_default_allowed"],
        "next_required_artifact": data_audit["next_required_artifact"],
    }


def _source_registry(
    *,
    r12_transfer_validation: dict[str, Any],
    r12_high_risk_holdout_registry: dict[str, Any] | None,
    r12_high_risk_holdout_transfer_replay: dict[str, Any] | None,
    r12_recall_oriented_update: dict[str, Any] | None,
    r12_recall_update_false_alarm_stress_test: dict[str, Any] | None,
    r12_recall_false_alarm_mitigation_candidate: dict[str, Any] | None,
    r12_recall_mitigation_holdout_validation: dict[str, Any] | None,
    r12_recall_mitigation_independent_holdout_data: dict[str, Any] | None,
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
    if r12_recall_oriented_update is not None:
        registry.append(
            {
                "artifact_id": r12_recall_oriented_update["artifact_id"],
                "path": (
                    "experiments/results/r12_recall_oriented_update/"
                    "r12-recall-oriented-update-current-001.json"
                ),
            }
        )
    if r12_recall_update_false_alarm_stress_test is not None:
        registry.append(
            {
                "artifact_id": r12_recall_update_false_alarm_stress_test[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_recall_update_false_alarm_stress_test/"
                    "r12-recall-update-false-alarm-stress-test-current-001.json"
                ),
            }
        )
    if r12_recall_false_alarm_mitigation_candidate is not None:
        registry.append(
            {
                "artifact_id": r12_recall_false_alarm_mitigation_candidate[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_recall_false_alarm_mitigation_candidate/"
                    "r12-recall-false-alarm-mitigation-candidate-current-001.json"
                ),
            }
        )
    if r12_recall_mitigation_holdout_validation is not None:
        registry.append(
            {
                "artifact_id": r12_recall_mitigation_holdout_validation[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_recall_mitigation_holdout_validation/"
                    "r12-recall-mitigation-holdout-validation-current-001.json"
                ),
            }
        )
    if r12_recall_mitigation_independent_holdout_data is not None:
        registry.append(
            {
                "artifact_id": r12_recall_mitigation_independent_holdout_data[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_recall_mitigation_independent_holdout_data/"
                    "r12-recall-mitigation-independent-holdout-data-current-001.json"
                ),
            }
        )
    return registry


def _unique_strings(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r12-transfer-validation-path", required=True)
    parser.add_argument("--r12-high-risk-holdout-registry-path")
    parser.add_argument("--r12-high-risk-holdout-transfer-replay-path")
    parser.add_argument("--r12-recall-oriented-update-path")
    parser.add_argument("--r12-recall-update-false-alarm-stress-test-path")
    parser.add_argument("--r12-recall-false-alarm-mitigation-candidate-path")
    parser.add_argument("--r12-recall-mitigation-holdout-validation-path")
    parser.add_argument("--r12-recall-mitigation-independent-holdout-data-path")
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
        r12_recall_oriented_update=(
            load_json_artifact(args.r12_recall_oriented_update_path)
            if args.r12_recall_oriented_update_path
            else None
        ),
        r12_recall_update_false_alarm_stress_test=(
            load_json_artifact(
                args.r12_recall_update_false_alarm_stress_test_path
            )
            if args.r12_recall_update_false_alarm_stress_test_path
            else None
        ),
        r12_recall_false_alarm_mitigation_candidate=(
            load_json_artifact(
                args.r12_recall_false_alarm_mitigation_candidate_path
            )
            if args.r12_recall_false_alarm_mitigation_candidate_path
            else None
        ),
        r12_recall_mitigation_holdout_validation=(
            load_json_artifact(
                args.r12_recall_mitigation_holdout_validation_path
            )
            if args.r12_recall_mitigation_holdout_validation_path
            else None
        ),
        r12_recall_mitigation_independent_holdout_data=(
            load_json_artifact(
                args.r12_recall_mitigation_independent_holdout_data_path
            )
            if args.r12_recall_mitigation_independent_holdout_data_path
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
