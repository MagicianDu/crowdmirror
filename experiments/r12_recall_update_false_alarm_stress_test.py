from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
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
from experiments.r12_high_risk_holdout_registry import (
    LOW_SENSITIVITY_SEGMENT_COLUMNS,
    MINIMUM_VALID_RESPONSE_COUNT,
    SEGMENT_SENSITIVITY_LEVELS,
)
from experiments.r12_recall_oriented_update import (
    OUTCOME_PROXY,
    R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION,
    SOURCE_SIGNAL,
)
from experiments.r12_transfer_validation import (
    R12_TRANSFER_VALIDATION_SCHEMA_VERSION,
)


R12_RECALL_UPDATE_FALSE_ALARM_STRESS_SCHEMA_VERSION = (
    "r12-recall-update-false-alarm-stress-test-v1"
)


def build_r12_recall_update_false_alarm_stress_test(
    *,
    artifact_id: str,
    run_id: str,
    hps_ingestion: dict[str, Any],
    r12_transfer_validation: dict[str, Any],
    r12_recall_oriented_update: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_hps_ingestion(hps_ingestion)
    _validate_transfer_validation(r12_transfer_validation)
    _validate_recall_update(r12_recall_oriented_update)

    current_margin = _decimal(
        r12_recall_oriented_update["update_candidate"]["current_value"]
    )
    recommended_margin = _decimal(
        r12_recall_oriented_update["update_candidate"]["recommended_value"]
    )
    static_prior = _global_risk_share(hps_ingestion, OUTCOME_PROXY)
    global_signal = _global_risk_share(hps_ingestion, SOURCE_SIGNAL)
    mechanism_weight = _decimal(
        r12_transfer_validation["accepted_update"]["recommended_value"]
    )
    train_case_ids = {
        case["case_id"]
        for case in r12_transfer_validation["case_replays"]
        if case["split"] == "train"
    }
    rows = _evaluation_cases(
        hps_ingestion=hps_ingestion,
        static_prior=static_prior,
        global_signal=global_signal,
        mechanism_weight=mechanism_weight,
        train_case_ids=train_case_ids,
        current_margin=current_margin,
        recommended_margin=recommended_margin,
    )
    family_table = [_family_metrics(column, items) for column, items in _group_by_column(rows)]
    low_sensitive_rows = [
        row for row in rows if row["segment_column"] in LOW_SENSITIVITY_SEGMENT_COLUMNS
    ]
    protected_sensitive_rows = [
        row for row in rows if row["sensitivity_level"] == "protected_sensitive"
    ]
    new_false_alarms = sorted(
        [row for row in rows if row["new_false_alarm"]],
        key=lambda row: row["case_id"],
    )
    newly_recovered = sorted(
        [row for row in rows if row["newly_recovered"]],
        key=lambda row: row["case_id"],
    )
    false_alarm_concentration = _false_alarm_concentration(new_false_alarms)
    low_sensitive_metrics = _low_sensitive_false_alarm(low_sensitive_rows)
    protected_sensitive_metrics = _protected_sensitive_false_alarm(
        protected_sensitive_rows
    )
    worst_family = _worst_segment_family(family_table)
    global_tradeoff = {
        "recall_delta": r12_recall_oriented_update["metric_comparison"][
            "static_prior_miss_recovery"
        ]["delta"],
        "false_alarm_rate_delta": r12_recall_oriented_update[
            "metric_comparison"
        ]["false_alarm_rate"]["delta"],
        "precision_delta": r12_recall_oriented_update["metric_comparison"][
            "precision"
        ]["delta"],
        "interval_coverage_delta": r12_recall_oriented_update[
            "metric_comparison"
        ]["interval_coverage"]["delta"],
    }
    gates = {
        "source_backed_public_proxy_present": True,
        "l7_recall_gain_preserved": global_tradeoff["recall_delta"] > 0,
        "low_sensitive_false_alarm_non_regression": (
            low_sensitive_metrics["false_alarm_rate_delta"] <= 0
        ),
        "low_sensitive_recall_evaluable": low_sensitive_metrics[
            "recall_evaluable"
        ],
        "global_false_alarm_non_regression": (
            global_tradeoff["false_alarm_rate_delta"] <= 0
        ),
        "protected_sensitive_false_alarm_non_regression": (
            protected_sensitive_metrics["false_alarm_rate_delta"] <= 0
        ),
        "precision_non_regression": global_tradeoff["precision_delta"] >= 0,
        "new_false_alarms_concentrated_on_sensitive_axis": (
            false_alarm_concentration[
                "sensitive_or_high_governance_new_false_alarm_share"
            ]
            == 1.0
            and bool(new_false_alarms)
        ),
        "stress_test_passed": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    gates["stress_test_passed"] = (
        gates["l7_recall_gain_preserved"]
        and gates["low_sensitive_false_alarm_non_regression"]
        and gates["low_sensitive_recall_evaluable"]
        and gates["global_false_alarm_non_regression"]
        and gates["protected_sensitive_false_alarm_non_regression"]
        and gates["precision_non_regression"]
        and not gates["new_false_alarms_concentrated_on_sensitive_axis"]
    )
    report = {
        "schema_version": R12_RECALL_UPDATE_FALSE_ALARM_STRESS_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_recall_update_false_alarm_stress_passed_guarded"
            if gates["stress_test_passed"]
            else "r12_recall_update_false_alarm_stress_blocked_product_default"
        ),
        "claim_level": (
            "research_only_recall_positive_false_alarm_stress_failed"
        ),
        "stress_contract": {
            "source_backed_public_proxy": True,
            "evaluates_recall_oriented_update": True,
            "outcome_proxy": OUTCOME_PROXY,
            "source_signal": SOURCE_SIGNAL,
            "low_sensitive_product_default_required": True,
            "false_alarm_non_regression_required_for_product_default": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "evaluation_summary": {
            "evaluated_case_count": len(rows),
            "observed_high_risk_case_count": sum(
                1 for row in rows if row["observed_high_risk"]
            ),
            "observed_low_risk_case_count": sum(
                1 for row in rows if not row["observed_high_risk"]
            ),
            "low_sensitive_case_count": len(low_sensitive_rows),
            "protected_or_high_governance_case_count": sum(
                1 for row in rows if row["sensitivity_level"] != "low"
            ),
            "product_default_low_sensitive_high_risk_case_count": sum(
                1
                for row in low_sensitive_rows
                if row["observed_high_risk"]
            ),
            "newly_recovered_count": len(newly_recovered),
            "new_false_alarm_count": len(new_false_alarms),
            "minimum_valid_response_count": MINIMUM_VALID_RESPONSE_COUNT,
        },
        "stress_metrics": {
            "global_tradeoff": global_tradeoff,
            "low_sensitive_false_alarm": low_sensitive_metrics,
            "protected_sensitive_false_alarm": protected_sensitive_metrics,
            "worst_segment_family": worst_family,
            "false_alarm_concentration": false_alarm_concentration,
        },
        "family_stress_table": family_table,
        "acceptance_gates": gates,
        "acceptance_decision": (
            "reject_product_default_keep_research_guarded_candidate"
        ),
        "product_support_level": (
            "blocked_product_default_due_false_alarm_precision_and_low_sensitive_recall_gap"
        ),
        "next_required_artifact": "r12_recall_false_alarm_mitigation_candidate",
        "source_refs": [
            hps_ingestion["artifact_id"],
            r12_transfer_validation["artifact_id"],
            r12_recall_oriented_update["artifact_id"],
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
                "artifact_id": r12_recall_oriented_update["artifact_id"],
                "path": (
                    "experiments/results/r12_recall_oriented_update/"
                    "r12-recall-oriented-update-current-001.json"
                ),
            },
        ],
        "allowed_claims": [
            (
                "R12 L7 recall gain survives stress accounting as a research-only "
                "guarded signal."
            ),
            (
                "Product can display the false-alarm stress boundary as a reason "
                "why runtime default remains blocked."
            ),
        ],
        "blocked_claims": [
            "r12 recall update false-alarm stress passed",
            "false_alarm_non_regression=true",
            "precision_non_regression=true",
            "low_sensitive_recall_evaluable=true",
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


def write_r12_recall_update_false_alarm_stress_test(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output, build_r12_recall_update_false_alarm_stress_test(**kwargs)
    )


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
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 transfer validation acceptance_gates required")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 transfer validation must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 transfer validation must not allow runtime default")


def _validate_recall_update(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION:
        raise ValueError("r12_recall_oriented_update.schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 recall update acceptance_gates required")
    if gates.get("recall_improved") is not True:
        raise ValueError("r12 recall update must provide positive recall signal")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 recall update must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 recall update must not allow runtime default")
    if artifact.get("next_required_artifact") != (
        "r12_recall_update_holdout_false_alarm_stress_test"
    ):
        raise ValueError("r12 recall update does not request this stress test")


def _evaluation_cases(
    *,
    hps_ingestion: dict[str, Any],
    static_prior: Decimal,
    global_signal: Decimal,
    mechanism_weight: Decimal,
    train_case_ids: set[str],
    current_margin: Decimal,
    recommended_margin: Decimal,
) -> list[dict[str, Any]]:
    outcome_profiles = hps_ingestion["segment_outcome_profiles"][OUTCOME_PROXY]
    source_profiles = hps_ingestion["segment_outcome_profiles"][SOURCE_SIGNAL]
    observed_threshold = static_prior + current_margin
    rows = []
    for segment_column in sorted(outcome_profiles):
        source_by_value = {
            str(row["segment_value"]): row
            for row in source_profiles.get(segment_column, [])
        }
        for outcome_row in outcome_profiles[segment_column]:
            if int(outcome_row["valid_response_count"]) < MINIMUM_VALID_RESPONSE_COUNT:
                continue
            segment_value = str(outcome_row["segment_value"])
            case_id = f"hps_{segment_column}_{segment_value}"
            if case_id in train_case_ids:
                continue
            source_row = source_by_value.get(segment_value)
            if source_row is None:
                continue
            observed = _decimal(outcome_row["risk_proxy_share"])
            source_share = _decimal(source_row["risk_proxy_share"])
            prediction = _clip(
                static_prior + (source_share - global_signal) * mechanism_weight
            )
            observed_high_risk = observed >= observed_threshold
            before_flagged = prediction >= static_prior + current_margin
            after_flagged = prediction >= static_prior + recommended_margin
            rows.append(
                {
                    "case_id": case_id,
                    "segment_column": segment_column,
                    "segment_value": segment_value,
                    "sensitivity_level": SEGMENT_SENSITIVITY_LEVELS[
                        segment_column
                    ],
                    "observed_high_risk": observed_high_risk,
                    "before_flagged": before_flagged,
                    "after_flagged": after_flagged,
                    "newly_recovered": (
                        observed_high_risk
                        and not before_flagged
                        and after_flagged
                    ),
                    "new_false_alarm": (
                        not observed_high_risk
                        and not before_flagged
                        and after_flagged
                    ),
                }
            )
    return rows


def _group_by_column(rows: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["segment_column"], []).append(row)
    return [(column, grouped[column]) for column in sorted(grouped)]


def _family_metrics(column: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    high = [row for row in rows if row["observed_high_risk"]]
    low = [row for row in rows if not row["observed_high_risk"]]
    recall_delta = _rate_delta(
        sum(1 for row in high if row["after_flagged"]),
        sum(1 for row in high if row["before_flagged"]),
        len(high),
    )
    false_alarm_delta = _rate_delta(
        sum(1 for row in low if row["after_flagged"]),
        sum(1 for row in low if row["before_flagged"]),
        len(low),
    )
    return {
        "segment_column": column,
        "sensitivity_level": SEGMENT_SENSITIVITY_LEVELS[column],
        "evaluated_case_count": len(rows),
        "observed_high_risk_case_count": len(high),
        "observed_low_risk_case_count": len(low),
        "recall_delta": recall_delta,
        "false_alarm_rate_delta": false_alarm_delta,
        "newly_recovered_count": sum(1 for row in rows if row["newly_recovered"]),
        "new_false_alarm_count": sum(1 for row in rows if row["new_false_alarm"]),
    }


def _low_sensitive_false_alarm(rows: list[dict[str, Any]]) -> dict[str, Any]:
    high = [row for row in rows if row["observed_high_risk"]]
    low = [row for row in rows if not row["observed_high_risk"]]
    before = _rate(sum(1 for row in low if row["before_flagged"]), len(low))
    after = _rate(sum(1 for row in low if row["after_flagged"]), len(low))
    return {
        "evaluable_case_count": len(low),
        "observed_high_risk_case_count": len(high),
        "false_alarm_rate_before": before,
        "false_alarm_rate_after": after,
        "false_alarm_rate_delta": _round6(_decimal(after) - _decimal(before)),
        "new_false_alarm_count": sum(1 for row in low if row["new_false_alarm"]),
        "recall_evaluable": bool(high),
    }


def _protected_sensitive_false_alarm(rows: list[dict[str, Any]]) -> dict[str, Any]:
    high = [row for row in rows if row["observed_high_risk"]]
    low = [row for row in rows if not row["observed_high_risk"]]
    before = _rate(sum(1 for row in low if row["before_flagged"]), len(low))
    after = _rate(sum(1 for row in low if row["after_flagged"]), len(low))
    return {
        "evaluable_case_count": len(low),
        "observed_high_risk_case_count": len(high),
        "false_alarm_rate_before": before,
        "false_alarm_rate_after": after,
        "false_alarm_rate_delta": _round6(_decimal(after) - _decimal(before)),
        "new_false_alarm_count": sum(1 for row in low if row["new_false_alarm"]),
    }


def _worst_segment_family(family_table: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [
        row for row in family_table if row["false_alarm_rate_delta"] is not None
    ]
    worst = max(
        candidates,
        key=lambda row: (
            row["false_alarm_rate_delta"],
            row["new_false_alarm_count"],
            row["evaluated_case_count"],
        ),
    )
    return {
        "segment_column": worst["segment_column"],
        "sensitivity_level": worst["sensitivity_level"],
        "evaluated_case_count": worst["evaluated_case_count"],
        "observed_high_risk_case_count": worst["observed_high_risk_case_count"],
        "observed_low_risk_case_count": worst["observed_low_risk_case_count"],
        "recall_delta": worst["recall_delta"],
        "false_alarm_rate_delta": worst["false_alarm_rate_delta"],
        "new_false_alarm_count": worst["new_false_alarm_count"],
    }


def _false_alarm_concentration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    case_ids = sorted(row["case_id"] for row in rows)
    if not rows:
        return {
            "new_false_alarm_case_ids": [],
            "dominant_segment_column": None,
            "dominant_segment_new_false_alarm_share": 0.0,
            "sensitive_or_high_governance_new_false_alarm_share": 0.0,
        }
    column_counts = Counter(row["segment_column"] for row in rows)
    dominant_column, dominant_count = column_counts.most_common(1)[0]
    sensitive_count = sum(1 for row in rows if row["sensitivity_level"] != "low")
    return {
        "new_false_alarm_case_ids": case_ids,
        "dominant_segment_column": dominant_column,
        "dominant_segment_new_false_alarm_share": _rate(dominant_count, len(rows)),
        "sensitive_or_high_governance_new_false_alarm_share": _rate(
            sensitive_count, len(rows)
        ),
    }


def _global_risk_share(hps_ingestion: dict[str, Any], outcome: str) -> Decimal:
    distribution = hps_ingestion["outcome_summary"][outcome]["response_distribution"]
    risk_codes = _risk_proxy_codes(distribution)
    return _decimal(sum(_decimal(distribution[code]) for code in risk_codes))


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


def _rate_delta(after_count: int, before_count: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return _round6(
        Decimal(after_count) / Decimal(denominator)
        - Decimal(before_count) / Decimal(denominator)
    )


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return _round6(Decimal(numerator) / Decimal(denominator))


def _clip(value: Decimal) -> Decimal:
    return min(Decimal("1"), max(Decimal("0"), value))


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _round6(value: Decimal | float) -> float:
    return float(_decimal(value).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--hps-ingestion-path", required=True)
    parser.add_argument("--r12-transfer-validation-path", required=True)
    parser.add_argument("--r12-recall-oriented-update-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_recall_update_false_alarm_stress_test(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        hps_ingestion=load_json_artifact(args.hps_ingestion_path),
        r12_transfer_validation=load_json_artifact(
            args.r12_transfer_validation_path
        ),
        r12_recall_oriented_update=load_json_artifact(
            args.r12_recall_oriented_update_path
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
