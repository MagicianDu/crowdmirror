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
from experiments.r10_hps_policy_reaction_ingestion import (
    R10_HPS_POLICY_REACTION_INGESTION_SCHEMA_VERSION,
)
from experiments.r12_transfer_validation import (
    R12_TRANSFER_VALIDATION_SCHEMA_VERSION,
)


R12_HIGH_RISK_HOLDOUT_REGISTRY_SCHEMA_VERSION = (
    "r12-high-risk-holdout-registry-v1"
)
OUTCOME_PROXY = "PRICESTRESS"
SOURCE_SIGNAL = "PRICECONCERN"
HIGH_RISK_MARGIN = 0.03
MINIMUM_VALID_RESPONSE_COUNT = 100
LOW_SENSITIVITY_SEGMENT_COLUMNS = {"REGION", "METRO_STATUS"}
SEGMENT_SENSITIVITY_LEVELS = {
    "REGION": "low",
    "METRO_STATUS": "low",
    "RHHINCOME": "socioeconomic_sensitive",
    "RRACETH": "protected_sensitive",
    "TAGE": "protected_sensitive",
    "ESEX": "protected_sensitive",
}


def build_r12_high_risk_holdout_registry(
    *,
    artifact_id: str,
    run_id: str,
    hps_ingestion: dict[str, Any],
    r12_transfer_validation: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_hps_ingestion(hps_ingestion)
    _validate_transfer_validation(r12_transfer_validation)
    static_prior = _global_risk_share(hps_ingestion, OUTCOME_PROXY)
    global_signal = _global_risk_share(hps_ingestion, SOURCE_SIGNAL)
    high_risk_threshold = round(static_prior + HIGH_RISK_MARGIN, 6)
    train_case_ids = _case_ids_by_split(r12_transfer_validation, "train")
    holdout_cases = [
        case
        for case in r12_transfer_validation["case_replays"]
        if case["split"] == "holdout"
    ]
    rows = _scan_segment_cases(
        hps_ingestion=hps_ingestion,
        static_prior=static_prior,
        global_signal=global_signal,
        high_risk_threshold=high_risk_threshold,
        mechanism_weight=float(
            r12_transfer_validation["accepted_update"]["recommended_value"]
        ),
        train_case_ids=train_case_ids,
    )
    candidates = [
        row
        for row in rows
        if row["observed_high_risk"]
        and row["valid_response_count"] >= MINIMUM_VALID_RESPONSE_COUNT
        and row["case_id"] not in train_case_ids
    ]
    candidates.sort(
        key=lambda item: (-item["observed_outcome_proxy"], item["case_id"])
    )
    rejected_train_cases = [
        _rejected_existing_train_case(row)
        for row in rows
        if row["observed_high_risk"] and row["case_id"] in train_case_ids
    ]
    rejected_train_cases.sort(key=lambda item: item["case_id"])
    product_default_candidates = [
        case for case in candidates if case["product_default_eligible"]
    ]
    recoverable_candidates = [
        case for case in candidates if case["r12_update_recovers_static_prior_miss"]
    ]
    report = {
        "schema_version": R12_HIGH_RISK_HOLDOUT_REGISTRY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_high_risk_holdout_registry_ready_product_guarded"
            if product_default_candidates
            else (
                "r12_high_risk_holdout_registry_ready_research_only"
                if candidates
                else "r12_high_risk_holdout_registry_blocked_needs_data"
            )
        ),
        "claim_level": "source_backed_public_proxy_high_risk_holdout_candidates",
        "registry_contract": {
            "source_backed_public_proxy": True,
            "derives_from_hps_ingestion": True,
            "outcome_proxy": OUTCOME_PROXY,
            "source_signal": SOURCE_SIGNAL,
            "excludes_existing_r12_train_cases": True,
            "product_default_requires_low_sensitive_axis": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "selection_policy": {
            "outcome_proxy": OUTCOME_PROXY,
            "source_signal": SOURCE_SIGNAL,
            "minimum_valid_response_count": MINIMUM_VALID_RESPONSE_COUNT,
            "high_risk_rule": (
                "outcome_proxy_share >= global_outcome_risk_share + 0.03"
            ),
            "static_prior_miss_required": True,
            "exclude_existing_r12_train_cases": True,
            "product_default_allowed_segment_sensitivity": "low_only",
        },
        "current_r12_gap": {
            "extended_metric_support_level": r12_transfer_validation[
                "extended_metric_gates"
            ]["extended_product_metric_support_level"],
            "static_prior_miss_recovery_holdout_covered": r12_transfer_validation[
                "extended_metric_gates"
            ]["static_prior_miss_recovery_holdout_covered"],
            "abnormal_segment_recall_holdout_covered": r12_transfer_validation[
                "extended_metric_gates"
            ]["abnormal_segment_recall_holdout_covered"],
            "holdout_high_risk_case_count": sum(
                1 for case in holdout_cases if case["observed_high_risk"]
            ),
            "holdout_static_prior_miss_case_count": sum(
                1
                for case in holdout_cases
                if case["static_prior_missed_observed_high_risk"]
            ),
        },
        "candidate_summary": {
            "scanned_segment_column_count": len(
                hps_ingestion["segment_outcome_profiles"][OUTCOME_PROXY]
            ),
            "scanned_case_count": len(rows),
            "research_eligible_case_count": len(candidates),
            "research_recoverable_static_prior_miss_count": len(
                recoverable_candidates
            ),
            "product_default_eligible_case_count": len(product_default_candidates),
            "rejected_existing_train_case_count": len(rejected_train_cases),
            "current_r12_holdout_high_risk_case_count": sum(
                1 for case in holdout_cases if case["observed_high_risk"]
            ),
            "current_r12_holdout_static_prior_miss_case_count": sum(
                1
                for case in holdout_cases
                if case["static_prior_missed_observed_high_risk"]
            ),
        },
        "metric_support_projection": {
            "research_static_prior_miss_recovery_holdout_coverable": bool(
                recoverable_candidates
            ),
            "research_abnormal_segment_recall_holdout_coverable": bool(candidates),
            "product_default_static_prior_miss_recovery_holdout_coverable": any(
                case["r12_update_recovers_static_prior_miss"]
                for case in product_default_candidates
            ),
            "product_default_abnormal_segment_recall_holdout_coverable": bool(
                product_default_candidates
            ),
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "holdout_candidate_cases": candidates,
        "rejected_high_risk_cases": rejected_train_cases,
        "acceptance_gates": {
            "source_backed_public_proxy_present": True,
            "current_r12_gap_confirmed": (
                r12_transfer_validation["extended_metric_gates"][
                    "static_prior_miss_recovery_holdout_covered"
                ]
                is False
                and r12_transfer_validation["extended_metric_gates"][
                    "abnormal_segment_recall_holdout_covered"
                ]
                is False
            ),
            "high_risk_research_holdout_candidates_present": bool(candidates),
            "existing_train_cases_excluded": True,
            "product_default_low_sensitive_high_risk_holdout_present": bool(
                product_default_candidates
            ),
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "next_required_artifact": "r12_high_risk_holdout_transfer_replay",
        "source_refs": [
            hps_ingestion["artifact_id"],
            r12_transfer_validation["artifact_id"],
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
        ],
        "allowed_claims": [
            (
                "R12 has source-backed public proxy candidates for a research-only "
                "high-risk holdout replay."
            ),
            (
                "Sensitive or high-governance segment axes require explicit Product "
                "approval or customer outcome before default use."
            ),
        ],
        "blocked_claims": [
            "R12 Product default high-risk recovery validated",
            "R12 Product core method ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "customer outcome validated",
            "sensitive segment axes can be used as Product default",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_high_risk_holdout_registry(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r12_high_risk_holdout_registry(**kwargs))


def _validate_hps_ingestion(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R10_HPS_POLICY_REACTION_INGESTION_SCHEMA_VERSION:
        raise ValueError("hps_ingestion.schema_version is invalid")
    contract = artifact.get("ingestion_contract")
    if not isinstance(contract, dict):
        raise ValueError("hps_ingestion.ingestion_contract must be an object")
    if contract.get("actual_public_data_ingested") is not True:
        raise ValueError("hps ingestion must use actual public data")
    if contract.get("field_outcome_validated") is not False:
        raise ValueError("hps ingestion must not be field validated")
    if contract.get("runtime_default_allowed") is not False:
        raise ValueError("hps ingestion must not allow runtime default")


def _validate_transfer_validation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_TRANSFER_VALIDATION_SCHEMA_VERSION:
        raise ValueError("r12_transfer_validation.schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12_transfer_validation.acceptance_gates must be an object")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 transfer validation must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 transfer validation must not allow runtime default")
    if "extended_metric_gates" not in artifact:
        raise ValueError("r12 transfer validation must include extended metric gates")


def _scan_segment_cases(
    *,
    hps_ingestion: dict[str, Any],
    static_prior: float,
    global_signal: float,
    high_risk_threshold: float,
    mechanism_weight: float,
    train_case_ids: set[str],
) -> list[dict[str, Any]]:
    source_profiles = hps_ingestion["segment_outcome_profiles"][SOURCE_SIGNAL]
    outcome_profiles = hps_ingestion["segment_outcome_profiles"][OUTCOME_PROXY]
    rows = []
    for segment_column in sorted(outcome_profiles):
        source_by_value = {
            row["segment_value"]: row
            for row in source_profiles.get(segment_column, [])
        }
        for outcome_row in outcome_profiles[segment_column]:
            segment_value = str(outcome_row["segment_value"])
            source_row = source_by_value.get(segment_value)
            if source_row is None:
                continue
            case_id = f"hps_{segment_column}_{segment_value}"
            source_share = round(float(source_row["risk_proxy_share"]), 6)
            source_delta = round(source_share - global_signal, 6)
            after_prediction = round(
                _clip(static_prior + source_delta * mechanism_weight), 6
            )
            observed = round(float(outcome_row["risk_proxy_share"]), 6)
            observed_high_risk = observed >= high_risk_threshold
            static_prior_missed = observed_high_risk and static_prior < high_risk_threshold
            product_default_eligible = (
                segment_column in LOW_SENSITIVITY_SEGMENT_COLUMNS
                and case_id not in train_case_ids
                and observed_high_risk
            )
            rows.append(
                {
                    "case_id": case_id,
                    "segment_labels": {
                        "segment_column": segment_column,
                        "segment_value": segment_value,
                        "sensitivity_level": SEGMENT_SENSITIVITY_LEVELS.get(
                            segment_column,
                            "unclassified_sensitive",
                        ),
                    },
                    "valid_response_count": int(outcome_row["valid_response_count"]),
                    "static_prior_prediction": round(static_prior, 6),
                    "observed_outcome_proxy": observed,
                    "source_signal_risk_share": source_share,
                    "source_signal_delta": source_delta,
                    "r12_after_prediction": after_prediction,
                    "observed_high_risk": observed_high_risk,
                    "static_prior_missed_observed_high_risk": static_prior_missed,
                    "r12_update_recovers_static_prior_miss": (
                        static_prior_missed and after_prediction >= high_risk_threshold
                    ),
                    "research_holdout_eligible": (
                        observed_high_risk and case_id not in train_case_ids
                    ),
                    "product_default_eligible": product_default_eligible,
                    "product_default_block_reason": (
                        None
                        if product_default_eligible
                        else (
                            "existing_r12_train_case_leakage_guard"
                            if case_id in train_case_ids
                            else "sensitive_or_high_governance_segment_axis"
                        )
                    ),
                    "field_outcome_validated": False,
                    "runtime_default_allowed": False,
                }
            )
    return rows


def _rejected_existing_train_case(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": row["case_id"],
        "segment_labels": row["segment_labels"],
        "observed_outcome_proxy": row["observed_outcome_proxy"],
        "source_signal_risk_share": row["source_signal_risk_share"],
        "rejection_reason": "existing_r12_train_case_leakage_guard",
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }


def _case_ids_by_split(transfer_validation: dict[str, Any], split: str) -> set[str]:
    return {
        case["case_id"]
        for case in transfer_validation["case_replays"]
        if case["split"] == split
    }


def _global_risk_share(hps_ingestion: dict[str, Any], outcome: str) -> float:
    distribution = hps_ingestion["outcome_summary"][outcome]["response_distribution"]
    risk_codes = _risk_proxy_codes(distribution)
    return round(sum(float(distribution[code]) for code in risk_codes), 6)


def _risk_proxy_codes(distribution: dict[str, Any]) -> set[str]:
    numeric_codes = []
    for value in distribution:
        try:
            numeric_codes.append((float(value), value))
        except ValueError:
            continue
    if not numeric_codes:
        return set(distribution)
    numeric_codes.sort()
    threshold = numeric_codes[len(numeric_codes) // 2][0]
    return {code for numeric, code in numeric_codes if numeric >= threshold}


def _clip(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--hps-ingestion-path", required=True)
    parser.add_argument("--r12-transfer-validation-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_high_risk_holdout_registry(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        hps_ingestion=load_json_artifact(args.hps_ingestion_path),
        r12_transfer_validation=load_json_artifact(
            args.r12_transfer_validation_path
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
