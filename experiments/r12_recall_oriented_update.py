from __future__ import annotations

import argparse
import json
import sys
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
from experiments.r12_high_risk_holdout_transfer_replay import (
    R12_HIGH_RISK_HOLDOUT_TRANSFER_REPLAY_SCHEMA_VERSION,
)
from experiments.r12_transfer_validation import (
    R12_TRANSFER_VALIDATION_SCHEMA_VERSION,
)


R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION = "r12-recall-oriented-update-v1"
OUTCOME_PROXY = "PRICESTRESS"
SOURCE_SIGNAL = "PRICECONCERN"
CURRENT_ACTIVATION_MARGIN = Decimal("0.03")
CANDIDATE_MARGINS = [
    Decimal("0.03"),
    Decimal("0.02"),
    Decimal("0.015"),
    Decimal("0.01"),
    Decimal("0.005"),
    Decimal("0.0"),
    Decimal("-0.005"),
    Decimal("-0.01"),
    Decimal("-0.02"),
]
FALSE_ALARM_DELTA_RESEARCH_CEILING = Decimal("0.08")
MINIMUM_VALID_RESPONSE_COUNT = 100
INTERVAL_HALF_WIDTH = Decimal("0.1")


def build_r12_recall_oriented_update(
    *,
    artifact_id: str,
    run_id: str,
    hps_ingestion: dict[str, Any],
    r12_transfer_validation: dict[str, Any],
    r12_high_risk_holdout_transfer_replay: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_hps_ingestion(hps_ingestion)
    _validate_transfer_validation(r12_transfer_validation)
    _validate_high_risk_replay(r12_high_risk_holdout_transfer_replay)
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
    evaluation_cases = _evaluation_cases(
        hps_ingestion=hps_ingestion,
        static_prior=static_prior,
        global_signal=global_signal,
        mechanism_weight=mechanism_weight,
        train_case_ids=train_case_ids,
    )
    baseline = _metrics_for_margin(
        evaluation_cases,
        margin=CURRENT_ACTIVATION_MARGIN,
        baseline=None,
    )
    threshold_sweep = [
        _metrics_for_margin(evaluation_cases, margin=margin, baseline=baseline)
        for margin in CANDIDATE_MARGINS
    ]
    selected = _select_candidate(threshold_sweep)
    selected_margin = _decimal(selected["activation_margin"])
    metric_comparison = _metric_comparison(
        evaluation_cases,
        baseline_margin=CURRENT_ACTIVATION_MARGIN,
        selected_margin=selected_margin,
    )
    newly_recovered = _newly_recovered_case_ids(
        evaluation_cases,
        baseline_margin=CURRENT_ACTIVATION_MARGIN,
        selected_margin=selected_margin,
    )
    new_false_alarms = _new_false_alarm_case_ids(
        evaluation_cases,
        baseline_margin=CURRENT_ACTIVATION_MARGIN,
        selected_margin=selected_margin,
    )
    gates = {
        "source_backed_public_proxy_present": True,
        "recall_improved": metric_comparison["static_prior_miss_recovery"][
            "delta"
        ]
        > 0,
        "false_alarm_delta_within_research_ceiling": _decimal(
            metric_comparison["false_alarm_rate"]["delta"]
        )
        <= FALSE_ALARM_DELTA_RESEARCH_CEILING,
        "false_alarm_non_regression": metric_comparison["false_alarm_rate"][
            "delta"
        ]
        <= 0,
        "precision_non_regression": metric_comparison["precision"]["delta"] >= 0,
        "interval_coverage_non_regression": metric_comparison[
            "interval_coverage"
        ]["delta"]
        >= 0,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    report = {
        "schema_version": R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_recall_oriented_update_ready_research_guarded"
            if gates["recall_improved"]
            and gates["false_alarm_delta_within_research_ceiling"]
            else "r12_recall_oriented_update_blocked"
        ),
        "claim_level": "research_only_recall_positive_false_alarm_tradeoff",
        "update_candidate": {
            "update_id": "r12-high-risk-activation-margin-recall-001",
            "update_type": "high_risk_activation_margin",
            "target": "high_risk_activation_margin",
            "current_value": _round6(CURRENT_ACTIVATION_MARGIN),
            "recommended_value": selected["activation_margin"],
            "status": "accepted_for_research_replay",
            "default_runtime_enabled": False,
            "product_default_allowed": False,
        },
        "selection_policy": {
            "candidate_margins": [_round6(margin) for margin in CANDIDATE_MARGINS],
            "false_alarm_delta_research_ceiling": _round6(
                FALSE_ALARM_DELTA_RESEARCH_CEILING
            ),
            "minimum_valid_response_count": MINIMUM_VALID_RESPONSE_COUNT,
            "train_cases_excluded": True,
            "selection_rule": (
                "max recall improvement subject to research false-alarm delta ceiling"
            ),
        },
        "evaluation_summary": {
            "evaluated_case_count": len(evaluation_cases),
            "observed_high_risk_case_count": sum(
                1 for case in evaluation_cases if case["observed_high_risk"]
            ),
            "observed_low_risk_case_count": sum(
                1 for case in evaluation_cases if not case["observed_high_risk"]
            ),
            "excluded_train_case_count": len(train_case_ids),
            "minimum_valid_response_count": MINIMUM_VALID_RESPONSE_COUNT,
        },
        "metric_comparison": metric_comparison,
        "threshold_sweep": threshold_sweep,
        "newly_recovered_static_prior_miss_case_ids": newly_recovered,
        "new_false_alarm_case_ids": new_false_alarms,
        "acceptance_gates": gates,
        "acceptance_decision": (
            "research_guarded_recall_candidate_accept_false_alarm_tradeoff"
            if gates["recall_improved"]
            and gates["false_alarm_delta_within_research_ceiling"]
            else "r12_recall_candidate_rejected"
        ),
        "next_required_artifact": "r12_recall_update_holdout_false_alarm_stress_test",
        "source_refs": [
            hps_ingestion["artifact_id"],
            r12_transfer_validation["artifact_id"],
            r12_high_risk_holdout_transfer_replay["artifact_id"],
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
                "artifact_id": r12_high_risk_holdout_transfer_replay["artifact_id"],
                "path": (
                    "experiments/results/r12_high_risk_holdout_transfer_replay/"
                    "r12-high-risk-holdout-transfer-replay-current-001.json"
                ),
            },
        ],
        "allowed_claims": [
            (
                "R12 has a research-only activation-margin candidate that improves "
                "high-risk recall on source-backed public proxy segments."
            ),
            (
                "The candidate exposes a false-alarm and precision tradeoff and "
                "requires stress testing before any Product default use."
            ),
        ],
        "blocked_claims": [
            "false_alarm_non_regression=true",
            "precision_non_regression=true",
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


def write_r12_recall_oriented_update(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r12_recall_oriented_update(**kwargs))


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


def _validate_high_risk_replay(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_HIGH_RISK_HOLDOUT_TRANSFER_REPLAY_SCHEMA_VERSION:
        raise ValueError(
            "r12_high_risk_holdout_transfer_replay.schema_version is invalid"
        )
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 high-risk replay acceptance_gates required")
    if gates.get("mae_improved") is not True:
        raise ValueError("r12 high-risk replay must provide positive baseline")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 high-risk replay must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 high-risk replay must not allow runtime default")


def _evaluation_cases(
    *,
    hps_ingestion: dict[str, Any],
    static_prior: Decimal,
    global_signal: Decimal,
    mechanism_weight: Decimal,
    train_case_ids: set[str],
) -> list[dict[str, Any]]:
    outcome_profiles = hps_ingestion["segment_outcome_profiles"][OUTCOME_PROXY]
    source_profiles = hps_ingestion["segment_outcome_profiles"][SOURCE_SIGNAL]
    observed_threshold = static_prior + CURRENT_ACTIVATION_MARGIN
    rows = []
    for segment_column in sorted(outcome_profiles):
        source_by_value = {
            row["segment_value"]: row
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
            prediction = _clip(static_prior + (source_share - global_signal) * mechanism_weight)
            rows.append(
                {
                    "case_id": case_id,
                    "static_prior": static_prior,
                    "observed_value": observed,
                    "prediction": prediction,
                    "observed_high_risk": observed >= observed_threshold,
                    "interval_hit": _interval_hit(observed, prediction),
                }
            )
    return rows


def _metric_comparison(
    rows: list[dict[str, Any]],
    *,
    baseline_margin: Decimal,
    selected_margin: Decimal,
) -> dict[str, Any]:
    baseline = _metrics_for_margin(rows, margin=baseline_margin, baseline=None)
    selected = _metrics_for_margin(rows, margin=selected_margin, baseline=baseline)
    return {
        "static_prior_miss_recovery": {
            "eligible_case_count": sum(1 for row in rows if row["observed_high_risk"]),
            "before": baseline["recall"],
            "after": selected["recall"],
            "delta": selected["recall_delta"],
        },
        "abnormal_segment_recall": {
            "eligible_case_count": sum(1 for row in rows if row["observed_high_risk"]),
            "before": baseline["recall"],
            "after": selected["recall"],
            "delta": selected["recall_delta"],
        },
        "false_alarm_rate": {
            "evaluable_case_count": sum(
                1 for row in rows if not row["observed_high_risk"]
            ),
            "before": baseline["false_alarm_rate"],
            "after": selected["false_alarm_rate"],
            "delta": selected["false_alarm_delta"],
        },
        "precision": {
            "before": baseline["precision"],
            "after": selected["precision"],
            "delta": _round6(_decimal(selected["precision"]) - _decimal(baseline["precision"])),
        },
        "interval_coverage": _interval_coverage_metric(rows),
    }


def _metrics_for_margin(
    rows: list[dict[str, Any]],
    *,
    margin: Decimal,
    baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    high_risk_cases = [row for row in rows if row["observed_high_risk"]]
    low_risk_cases = [row for row in rows if not row["observed_high_risk"]]
    flagged = [row for row in rows if _flagged(row, margin=margin)]
    true_positives = [
        row for row in flagged if row["observed_high_risk"]
    ]
    false_alarms = [
        row for row in flagged if not row["observed_high_risk"]
    ]
    recall = _rate(len(true_positives), len(high_risk_cases))
    false_alarm_rate = _rate(len(false_alarms), len(low_risk_cases))
    precision = _rate(len(true_positives), len(flagged)) if flagged else None
    if baseline is None:
        recall_delta = Decimal("0")
        false_alarm_delta = Decimal("0")
    else:
        recall_delta = _decimal(recall) - _decimal(baseline["recall"])
        false_alarm_delta = (
            _decimal(false_alarm_rate) - _decimal(baseline["false_alarm_rate"])
        )
    return {
        "activation_margin": _round6(margin),
        "recall": recall,
        "false_alarm_rate": false_alarm_rate,
        "precision": precision,
        "recall_delta": _round6(recall_delta),
        "false_alarm_delta": _round6(false_alarm_delta),
        "passes_research_ceiling": (
            false_alarm_delta <= FALSE_ALARM_DELTA_RESEARCH_CEILING
        ),
    }


def _select_candidate(threshold_sweep: list[dict[str, Any]]) -> dict[str, Any]:
    passing = [row for row in threshold_sweep if row["passes_research_ceiling"]]
    if not passing:
        return threshold_sweep[0]
    return max(
        passing,
        key=lambda row: (
            row["recall_delta"],
            -row["false_alarm_delta"],
            row["precision"] if row["precision"] is not None else -1,
        ),
    )


def _newly_recovered_case_ids(
    rows: list[dict[str, Any]],
    *,
    baseline_margin: Decimal,
    selected_margin: Decimal,
) -> list[str]:
    return sorted(
        row["case_id"]
        for row in rows
        if row["observed_high_risk"]
        and not _flagged(row, margin=baseline_margin)
        and _flagged(row, margin=selected_margin)
    )


def _new_false_alarm_case_ids(
    rows: list[dict[str, Any]],
    *,
    baseline_margin: Decimal,
    selected_margin: Decimal,
) -> list[str]:
    return sorted(
        row["case_id"]
        for row in rows
        if not row["observed_high_risk"]
        and not _flagged(row, margin=baseline_margin)
        and _flagged(row, margin=selected_margin)
    )


def _interval_coverage_metric(rows: list[dict[str, Any]]) -> dict[str, float]:
    coverage = _rate(sum(1 for row in rows if row["interval_hit"]), len(rows))
    return {
        "before": coverage,
        "after": coverage,
        "delta": 0.0,
    }


def _flagged(row: dict[str, Any], *, margin: Decimal) -> bool:
    return row["prediction"] >= row["static_prior"] + margin


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


def _interval_hit(value: Decimal, median: Decimal) -> bool:
    return (
        _clip(median - INTERVAL_HALF_WIDTH)
        <= value
        <= _clip(median + INTERVAL_HALF_WIDTH)
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
    parser.add_argument("--r12-high-risk-holdout-transfer-replay-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_recall_oriented_update(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        hps_ingestion=load_json_artifact(args.hps_ingestion_path),
        r12_transfer_validation=load_json_artifact(
            args.r12_transfer_validation_path
        ),
        r12_high_risk_holdout_transfer_replay=load_json_artifact(
            args.r12_high_risk_holdout_transfer_replay_path
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
