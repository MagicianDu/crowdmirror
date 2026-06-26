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
from experiments.r10_external_evidence_registry import (
    R10_EXTERNAL_EVIDENCE_REGISTRY_SCHEMA_VERSION,
)
from experiments.r10_hps_policy_reaction_ingestion import (
    R10_HPS_POLICY_REACTION_INGESTION_SCHEMA_VERSION,
)
from experiments.r12_high_risk_holdout_registry import (
    LOW_SENSITIVITY_SEGMENT_COLUMNS,
)
from experiments.r12_recall_false_alarm_mitigation_candidate import (
    CURRENT_ACTIVATION_MARGIN,
    L7_ACTIVATION_MARGIN,
    _evaluate_policy,
    _evaluation_cases,
    _global_risk_share,
    _decimal,
)
from experiments.r12_recall_mitigation_holdout_validation import (
    R12_RECALL_MITIGATION_HOLDOUT_VALIDATION_SCHEMA_VERSION,
)
from experiments.r12_recall_oriented_update import OUTCOME_PROXY, SOURCE_SIGNAL
from experiments.r12_transfer_validation import (
    R12_TRANSFER_VALIDATION_SCHEMA_VERSION,
)


R12_RECALL_MITIGATION_INDEPENDENT_HOLDOUT_DATA_SCHEMA_VERSION = (
    "r12-recall-mitigation-independent-holdout-data-v1"
)


def build_r12_recall_mitigation_independent_holdout_data(
    *,
    artifact_id: str,
    run_id: str,
    hps_ingestion: dict[str, Any],
    r12_transfer_validation: dict[str, Any],
    r12_recall_mitigation_holdout_validation: dict[str, Any],
    r10_external_evidence_registry: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_hps_ingestion(hps_ingestion)
    _validate_transfer_validation(r12_transfer_validation)
    _validate_holdout_validation(r12_recall_mitigation_holdout_validation)
    _validate_external_registry(r10_external_evidence_registry)

    rows = _build_evaluation_rows(hps_ingestion, r12_transfer_validation)
    baseline = _evaluate_policy(
        rows,
        policy_id="baseline-current-margin-003",
        candidate_id="baseline-current-margin-003",
        candidate_type="baseline_current_margin",
        margin_policy=lambda row: CURRENT_ACTIVATION_MARGIN,
        baseline=None,
    )
    l7 = _evaluate_policy(
        rows,
        policy_id="l7-global-margin-001",
        candidate_id="l7-global-margin-001",
        candidate_type="global_activation_margin",
        margin_policy=lambda row: L7_ACTIVATION_MARGIN,
        baseline=baseline,
    )

    derivation_band = _derivation_band_values(
        r12_recall_mitigation_holdout_validation
    )
    derivation_band_rows = [
        row for row in rows if _is_tage_in_band(row, derivation_band)
    ]
    same_dataset_non_derivation_rows = [
        row for row in rows if not _is_tage_in_band(row, derivation_band)
    ]
    same_dataset_recall_candidates = [
        case_id
        for case_id in l7["newly_recovered_case_ids"]
        if not _case_id_in_derivation_band(case_id, derivation_band)
    ]
    low_sensitive_rows = [
        row
        for row in rows
        if row["segment_column"] in LOW_SENSITIVITY_SEGMENT_COLUMNS
    ]
    baseline_flagged = set(baseline["flagged_case_ids"])
    l7_flagged = set(l7["flagged_case_ids"])
    low_sensitive_recall_candidates = [
        row["case_id"]
        for row in low_sensitive_rows
        if row["observed_high_risk"]
        and row["case_id"] not in baseline_flagged
        and row["case_id"] in l7_flagged
    ]
    external_candidates = _external_source_candidates(
        r10_external_evidence_registry
    )
    ingested_external_count = sum(
        1
        for case in r10_external_evidence_registry["case_records"]
        if case["ingestion_status"] != "candidate_source_not_ingested"
    )
    report = {
        "schema_version": (
            R12_RECALL_MITIGATION_INDEPENDENT_HOLDOUT_DATA_SCHEMA_VERSION
        ),
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_recall_mitigation_independent_holdout_data_blocked_needs_external_or_customer_slice"
        ),
        "claim_level": "data_gap_audit_product_default_blocked",
        "data_contract": {
            "answers_next_required_artifact": (
                "r12_recall_mitigation_independent_holdout_data"
            ),
            "requires_independent_dataset_or_customer_approved_slice": True,
            "same_dataset_pseudo_holdout_is_insufficient_for_product_default": True,
            "customer_or_field_outcome_required_for_escalation": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "data_summary": {
            "hps_public_proxy_ingested": True,
            "evaluated_hps_case_count": len(rows),
            "derivation_band_case_count": len(derivation_band_rows),
            "same_dataset_non_derivation_case_count": len(
                same_dataset_non_derivation_rows
            ),
            "same_dataset_non_derivation_recall_candidate_count": len(
                same_dataset_recall_candidates
            ),
            "low_sensitive_case_count": len(low_sensitive_rows),
            "low_sensitive_observed_high_risk_count": sum(
                1 for row in low_sensitive_rows if row["observed_high_risk"]
            ),
            "low_sensitive_recall_candidate_count": len(
                low_sensitive_recall_candidates
            ),
            "customer_approved_holdout_case_count": 0,
            "external_registry_candidate_count": len(
                r10_external_evidence_registry["case_records"]
            ),
            "ingested_external_independent_dataset_count": ingested_external_count,
        },
        "same_dataset_non_derivation_recall_candidates": (
            same_dataset_recall_candidates
        ),
        "data_availability_ledger": [
            {
                "source_id": "current_hps_same_dataset_non_derivation_segments",
                "status": "available_but_not_independent_dataset",
                "case_count": len(same_dataset_non_derivation_rows),
                "recall_candidate_count": len(same_dataset_recall_candidates),
                "product_default_allowed": False,
                "block_reason": "same_public_proxy_dataset_not_independent_holdout",
            },
            {
                "source_id": "current_hps_low_sensitive_slice",
                "status": "available_but_no_observed_high_risk_recall_case",
                "case_count": len(low_sensitive_rows),
                "observed_high_risk_count": sum(
                    1 for row in low_sensitive_rows if row["observed_high_risk"]
                ),
                "recall_candidate_count": len(low_sensitive_recall_candidates),
                "product_default_allowed": False,
                "block_reason": "low_sensitive_recall_not_evaluable",
            },
            {
                "source_id": "external_public_source_candidates",
                "status": "candidate_sources_registered_not_ingested",
                "case_count": len(r10_external_evidence_registry["case_records"]),
                "ingested_case_count": ingested_external_count,
                "product_default_allowed": False,
                "block_reason": "external_independent_data_not_ingested",
            },
            {
                "source_id": "customer_approved_holdout_slice",
                "status": "not_present",
                "case_count": 0,
                "product_default_allowed": False,
                "block_reason": "customer_outcome_or_approval_missing",
            },
        ],
        "external_source_candidates": external_candidates,
        "acceptance_gates": {
            "source_backed_public_proxy_present": True,
            "same_dataset_non_derivation_candidates_present": bool(
                same_dataset_non_derivation_rows
            ),
            "independent_dataset_present": False,
            "independent_holdout_case_count_positive": False,
            "low_sensitive_recall_evaluable": bool(low_sensitive_recall_candidates),
            "customer_approved_holdout_present": False,
            "external_candidate_sources_registered": bool(external_candidates),
            "external_independent_data_ingested": ingested_external_count > 0,
            "mitigation_independent_data_ready": False,
            "product_default_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "acceptance_decision": (
            "block_product_default_prepare_external_or_customer_holdout_ingestion"
        ),
        "next_required_artifact": (
            "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice"
        ),
        "source_refs": [
            hps_ingestion["artifact_id"],
            r12_transfer_validation["artifact_id"],
            r12_recall_mitigation_holdout_validation["artifact_id"],
            r10_external_evidence_registry["artifact_id"],
        ],
        "source_registry": [
            {
                "artifact_id": hps_ingestion["artifact_id"],
                "path": (
                    "experiments/results/r10_hps_policy_reaction_ingestion/"
                    "r10-hps-policy-reaction-ingestion-current-001.json"
                ),
            },
            {
                "artifact_id": r12_transfer_validation["artifact_id"],
                "path": (
                    "experiments/results/r12_transfer_validation/"
                    "r12-transfer-validation-current-001.json"
                ),
            },
            {
                "artifact_id": r12_recall_mitigation_holdout_validation[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_recall_mitigation_holdout_validation/"
                    "r12-recall-mitigation-holdout-validation-current-001.json"
                ),
            },
            {
                "artifact_id": r10_external_evidence_registry["artifact_id"],
                "path": (
                    "experiments/results/r10_external_evidence_registry/"
                    "r10-external-evidence-registry-current-001.json"
                ),
            },
        ],
        "allowed_claims": [
            (
                "Current HPS public proxy has same-dataset diagnostic cases for "
                "failure analysis."
            ),
            (
                "External public sources are registered as next ingestion options, "
                "but not yet usable as independent holdout evidence."
            ),
        ],
        "blocked_claims": [
            "independent holdout data exists",
            "low_sensitive_recall_evaluable=true",
            "customer approved holdout slice exists",
            "mitigation independent data ready",
            "R12 Product default high-risk recovery validated",
            "R12 Product core method ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "customer outcome validated",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_recall_mitigation_independent_holdout_data(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output, build_r12_recall_mitigation_independent_holdout_data(**kwargs)
    )


def _build_evaluation_rows(
    hps_ingestion: dict[str, Any],
    r12_transfer_validation: dict[str, Any],
) -> list[dict[str, Any]]:
    train_case_ids = {
        case["case_id"]
        for case in r12_transfer_validation["case_replays"]
        if case["split"] == "train"
    }
    return _evaluation_cases(
        hps_ingestion=hps_ingestion,
        static_prior=_global_risk_share(hps_ingestion, OUTCOME_PROXY),
        global_signal=_global_risk_share(hps_ingestion, SOURCE_SIGNAL),
        mechanism_weight=_decimal(
            r12_transfer_validation["accepted_update"]["recommended_value"]
        ),
        train_case_ids=train_case_ids,
    )


def _derivation_band_values(holdout_validation: dict[str, Any]) -> set[int]:
    held_out_values = {
        int(trial["held_out_false_alarm_case_id"].split("_")[-1])
        for trial in holdout_validation["leave_one_false_alarm_band_validation"][
            "trials"
        ]
    }
    if not held_out_values:
        return set()
    return set(range(min(held_out_values), max(held_out_values) + 1))


def _is_tage_in_band(row: dict[str, Any], band: set[int]) -> bool:
    return row["segment_column"] == "TAGE" and int(row["segment_value"]) in band


def _case_id_in_derivation_band(case_id: str, band: set[int]) -> bool:
    if not case_id.startswith("hps_TAGE_"):
        return False
    return int(case_id.split("_")[-1]) in band


def _external_source_candidates(
    registry: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "case_id": case["case_id"],
            "domain": case["domain"],
            "ingestion_status": case["ingestion_status"],
            "recommended_next_action": "ingest_or_slice_for_independent_holdout",
        }
        for case in registry["case_records"]
    ]


def _validate_hps_ingestion(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R10_HPS_POLICY_REACTION_INGESTION_SCHEMA_VERSION:
        raise ValueError("hps_ingestion.schema_version is invalid")
    contract = artifact.get("ingestion_contract")
    if not isinstance(contract, dict):
        raise ValueError("hps_ingestion.ingestion_contract required")
    if contract.get("actual_public_data_ingested") is not True:
        raise ValueError("hps ingestion must use actual public data")
    if contract.get("field_outcome_validated") is not False:
        raise ValueError("hps ingestion must not be field validated")
    if contract.get("runtime_default_allowed") is not False:
        raise ValueError("hps ingestion must not allow runtime default")


def _validate_transfer_validation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_TRANSFER_VALIDATION_SCHEMA_VERSION:
        raise ValueError("r12_transfer_validation.schema_version is invalid")
    if artifact["acceptance_gates"].get("field_outcome_validated") is not False:
        raise ValueError("r12 transfer validation must not be field validated")
    if artifact["acceptance_gates"].get("runtime_default_allowed") is not False:
        raise ValueError("r12 transfer validation must not allow runtime default")


def _validate_holdout_validation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_MITIGATION_HOLDOUT_VALIDATION_SCHEMA_VERSION
    ):
        raise ValueError("r12 mitigation holdout validation schema_version is invalid")
    if artifact.get("next_required_artifact") != (
        "r12_recall_mitigation_independent_holdout_data"
    ):
        raise ValueError("r12 mitigation holdout validation must request data audit")
    if artifact["acceptance_gates"].get("product_default_allowed") is not False:
        raise ValueError("r12 mitigation holdout validation must block Product default")


def _validate_external_registry(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R10_EXTERNAL_EVIDENCE_REGISTRY_SCHEMA_VERSION:
        raise ValueError("r10_external_evidence_registry.schema_version is invalid")
    if artifact["acceptance_gates"].get("field_outcome_validated") is not False:
        raise ValueError("external evidence registry must not be field validated")
    if artifact["acceptance_gates"].get("runtime_default_allowed") is not False:
        raise ValueError("external evidence registry must not allow runtime default")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--hps-ingestion-path", required=True)
    parser.add_argument("--r12-transfer-validation-path", required=True)
    parser.add_argument("--r12-recall-mitigation-holdout-validation-path", required=True)
    parser.add_argument("--r10-external-evidence-registry-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_recall_mitigation_independent_holdout_data(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        hps_ingestion=load_json_artifact(args.hps_ingestion_path),
        r12_transfer_validation=load_json_artifact(
            args.r12_transfer_validation_path
        ),
        r12_recall_mitigation_holdout_validation=load_json_artifact(
            args.r12_recall_mitigation_holdout_validation_path
        ),
        r10_external_evidence_registry=load_json_artifact(
            args.r10_external_evidence_registry_path
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
