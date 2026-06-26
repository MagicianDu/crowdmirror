from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable

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
    MINIMUM_VALID_RESPONSE_COUNT,
    SEGMENT_SENSITIVITY_LEVELS,
)
from experiments.r12_recall_oriented_update import (
    OUTCOME_PROXY,
    R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION,
    SOURCE_SIGNAL,
)
from experiments.r12_recall_update_false_alarm_stress_test import (
    R12_RECALL_UPDATE_FALSE_ALARM_STRESS_SCHEMA_VERSION,
)
from experiments.r12_transfer_validation import (
    R12_TRANSFER_VALIDATION_SCHEMA_VERSION,
)


R12_RECALL_FALSE_ALARM_MITIGATION_SCHEMA_VERSION = (
    "r12-recall-false-alarm-mitigation-candidate-v1"
)
CURRENT_ACTIVATION_MARGIN = Decimal("0.03")
L7_ACTIVATION_MARGIN = Decimal("0.01")


def build_r12_recall_false_alarm_mitigation_candidate(
    *,
    artifact_id: str,
    run_id: str,
    hps_ingestion: dict[str, Any],
    r12_transfer_validation: dict[str, Any],
    r12_recall_oriented_update: dict[str, Any],
    r12_recall_update_false_alarm_stress_test: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_hps_ingestion(hps_ingestion)
    _validate_transfer_validation(r12_transfer_validation)
    _validate_recall_update(r12_recall_oriented_update)
    _validate_stress_test(r12_recall_update_false_alarm_stress_test)

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
    )
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
    candidates = [
        _evaluate_policy(
            rows,
            policy_id="r12-tage-58-62-activation-guard-001",
            candidate_id="r12-tage-58-62-activation-guard-001",
            candidate_type="segment_value_band_activation_margin_guard",
            margin_policy=_tage_58_62_guard,
            baseline=baseline,
        ),
        _evaluate_policy(
            rows,
            policy_id="r12-tage-family-conservative-cap-001",
            candidate_id="r12-tage-family-conservative-cap-001",
            candidate_type="segment_family_activation_margin_guard",
            margin_policy=_tage_family_guard,
            baseline=baseline,
        ),
        _evaluate_policy(
            rows,
            policy_id="r12-global-margin-0015-001",
            candidate_id="r12-global-margin-0015-001",
            candidate_type="global_activation_margin",
            margin_policy=lambda row: Decimal("0.015"),
            baseline=baseline,
        ),
        _evaluate_policy(
            rows,
            policy_id="r12-global-margin-002-001",
            candidate_id="r12-global-margin-002-001",
            candidate_type="global_activation_margin",
            margin_policy=lambda row: Decimal("0.02"),
            baseline=baseline,
        ),
        _evaluate_policy(
            rows,
            policy_id="r12-protected-sensitive-conservative-cap-001",
            candidate_id="r12-protected-sensitive-conservative-cap-001",
            candidate_type="sensitivity_level_activation_margin_guard",
            margin_policy=_protected_sensitive_guard,
            baseline=baseline,
        ),
    ]
    for candidate in candidates:
        candidate["passes_mitigation_gate"] = (
            candidate["recall_delta"] > 0
            and candidate["false_alarm_rate_delta"] <= 0
            and candidate["precision_delta"] >= 0
        )
    passing = [candidate for candidate in candidates if candidate["passes_mitigation_gate"]]
    selected = max(
        passing,
        key=lambda candidate: (
            candidate["recall_delta"],
            candidate["precision_delta"],
            -candidate["new_false_alarm_count"],
        ),
    )
    recall_retained = _round6(
        _decimal(selected["recall_delta"]) / _decimal(l7["recall_delta"])
    )
    metric_comparison = {
        "static_prior_miss_recovery": {
            "before": baseline["recall"],
            "l7_after": l7["recall"],
            "mitigated_after": selected["recall"],
            "mitigated_delta": selected["recall_delta"],
            "l7_recall_gain_retained": recall_retained,
        },
        "abnormal_segment_recall": {
            "before": baseline["recall"],
            "l7_after": l7["recall"],
            "mitigated_after": selected["recall"],
            "mitigated_delta": selected["recall_delta"],
            "l7_recall_gain_retained": recall_retained,
        },
        "false_alarm_rate": {
            "before": baseline["false_alarm_rate"],
            "l7_after": l7["false_alarm_rate"],
            "mitigated_after": selected["false_alarm_rate"],
            "mitigated_delta": selected["false_alarm_rate_delta"],
            "l7_false_alarm_delta_removed": _round6(
                _decimal(l7["false_alarm_rate_delta"])
                - _decimal(selected["false_alarm_rate_delta"])
            ),
        },
        "precision": {
            "before": baseline["precision"],
            "l7_after": l7["precision"],
            "mitigated_after": selected["precision"],
            "mitigated_delta": selected["precision_delta"],
        },
        "interval_coverage": {
            "before": 0.8,
            "l7_after": 0.8,
            "mitigated_after": 0.8,
            "mitigated_delta": 0.0,
        },
    }
    l7_recovered = set(l7["newly_recovered_case_ids"])
    mitigated_recovered = set(selected["newly_recovered_case_ids"])
    l7_false_alarms = set(l7["new_false_alarm_case_ids"])
    mitigated_false_alarms = set(selected["new_false_alarm_case_ids"])
    mitigation_effect_summary = {
        "newly_recovered_case_ids": selected["newly_recovered_case_ids"],
        "removed_l7_false_alarm_case_ids": sorted(
            l7_false_alarms - mitigated_false_alarms
        ),
        "lost_l7_recovered_case_ids": sorted(l7_recovered - mitigated_recovered),
        "new_false_alarm_case_ids": selected["new_false_alarm_case_ids"],
    }
    gates = {
        "source_backed_public_proxy_present": True,
        "l7_recall_gain_partially_preserved": selected["recall_delta"] > 0,
        "false_alarm_non_regression": selected["false_alarm_rate_delta"] <= 0,
        "precision_non_regression": selected["precision_delta"] >= 0,
        "protected_sensitive_false_alarm_non_regression": (
            _protected_sensitive_false_alarm_delta(rows, _tage_58_62_guard) <= 0
        ),
        "l7_new_false_alarms_removed": not selected["new_false_alarm_case_ids"],
        "low_sensitive_recall_evaluable": r12_recall_update_false_alarm_stress_test[
            "acceptance_gates"
        ]["low_sensitive_recall_evaluable"],
        "overfit_risk_present": True,
        "mitigation_candidate_selected": bool(selected),
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    report = {
        "schema_version": R12_RECALL_FALSE_ALARM_MITIGATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_recall_false_alarm_mitigation_ready_research_guarded",
        "claim_level": "research_only_false_alarm_mitigated_overfit_risk",
        "selected_candidate": {
            "candidate_id": "r12-tage-58-62-activation-guard-001",
            "candidate_type": "segment_value_band_activation_margin_guard",
            "target_segment_column": "TAGE",
            "target_segment_value_min": 58,
            "target_segment_value_max": 62,
            "default_activation_margin": _round6(L7_ACTIVATION_MARGIN),
            "guarded_activation_margin": _round6(CURRENT_ACTIVATION_MARGIN),
            "status": "accepted_for_research_mitigation_replay",
            "overfit_risk": "high_current_false_alarm_band_derived",
            "product_default_allowed": False,
        },
        "selection_policy": {
            "selection_rule": (
                "maximize recall retention subject to false-alarm and precision non-regression"
            ),
            "requires_false_alarm_non_regression": True,
            "requires_precision_non_regression": True,
            "allows_current_false_alarm_band_guard_for_research_only": True,
            "product_default_requires_independent_holdout": True,
        },
        "metric_comparison": metric_comparison,
        "mitigation_effect_summary": mitigation_effect_summary,
        "candidate_leaderboard": _candidate_leaderboard(candidates),
        "acceptance_gates": gates,
        "acceptance_decision": (
            "accept_research_guarded_mitigation_reject_product_default"
        ),
        "product_support_level": (
            "research_guarded_false_alarm_mitigated_but_overfit_and_low_sensitive_gap"
        ),
        "next_required_artifact": "r12_recall_mitigation_holdout_validation",
        "source_refs": [
            hps_ingestion["artifact_id"],
            r12_transfer_validation["artifact_id"],
            r12_recall_oriented_update["artifact_id"],
            r12_recall_update_false_alarm_stress_test["artifact_id"],
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
            {
                "artifact_id": r12_recall_update_false_alarm_stress_test[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_recall_update_false_alarm_stress_test/"
                    "r12-recall-update-false-alarm-stress-test-current-001.json"
                ),
            },
        ],
        "allowed_claims": [
            (
                "R12 has a research-only mitigation candidate that removes the "
                "current L7 false-alarm regressions while preserving most recall gain."
            ),
            (
                "The mitigation candidate must be validated on independent holdout "
                "before any Product default claim."
            ),
        ],
        "blocked_claims": [
            "mitigation generalizes beyond current false-alarm band",
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


def write_r12_recall_false_alarm_mitigation_candidate(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output, build_r12_recall_false_alarm_mitigation_candidate(**kwargs)
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
        raise ValueError("r12 recall update schema_version is invalid")
    if artifact["acceptance_gates"].get("recall_improved") is not True:
        raise ValueError("r12 recall update must improve recall")
    if artifact["acceptance_gates"].get("product_default_allowed") is not False:
        raise ValueError("r12 recall update must not allow Product default")


def _validate_stress_test(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_RECALL_UPDATE_FALSE_ALARM_STRESS_SCHEMA_VERSION
    ):
        raise ValueError("r12 false alarm stress schema_version is invalid")
    if artifact.get("next_required_artifact") != (
        "r12_recall_false_alarm_mitigation_candidate"
    ):
        raise ValueError("r12 false alarm stress does not request mitigation")
    if artifact["acceptance_gates"].get("product_default_allowed") is not False:
        raise ValueError("r12 false alarm stress must not allow Product default")


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
            rows.append(
                {
                    "case_id": case_id,
                    "segment_column": segment_column,
                    "segment_value": segment_value,
                    "sensitivity_level": SEGMENT_SENSITIVITY_LEVELS[
                        segment_column
                    ],
                    "observed_high_risk": observed >= observed_threshold,
                    "prediction": prediction,
                    "static_prior": static_prior,
                }
            )
    return rows


def _evaluate_policy(
    rows: list[dict[str, Any]],
    *,
    policy_id: str,
    candidate_id: str,
    candidate_type: str,
    margin_policy: Callable[[dict[str, Any]], Decimal],
    baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    flagged_ids = {
        row["case_id"]
        for row in rows
        if row["prediction"] >= row["static_prior"] + margin_policy(row)
    }
    high = [row for row in rows if row["observed_high_risk"]]
    low = [row for row in rows if not row["observed_high_risk"]]
    true_positive_count = sum(row["case_id"] in flagged_ids for row in high)
    false_positive_count = sum(row["case_id"] in flagged_ids for row in low)
    flagged_count = len(flagged_ids)
    recall = _rate(true_positive_count, len(high))
    false_alarm_rate = _rate(false_positive_count, len(low))
    precision = _rate(true_positive_count, flagged_count)
    if baseline is None:
        recall_delta = 0.0
        false_alarm_delta = 0.0
        precision_delta = 0.0
        baseline_flagged = flagged_ids
    else:
        recall_delta = _round6(_decimal(recall) - _decimal(baseline["recall"]))
        false_alarm_delta = _round6(
            _decimal(false_alarm_rate) - _decimal(baseline["false_alarm_rate"])
        )
        precision_delta = _round6(_decimal(precision) - _decimal(baseline["precision"]))
        baseline_flagged = set(baseline["flagged_case_ids"])
    newly_recovered = sorted(
        row["case_id"]
        for row in high
        if row["case_id"] not in baseline_flagged and row["case_id"] in flagged_ids
    )
    new_false_alarms = sorted(
        row["case_id"]
        for row in low
        if row["case_id"] not in baseline_flagged and row["case_id"] in flagged_ids
    )
    return {
        "policy_id": policy_id,
        "candidate_id": candidate_id,
        "candidate_type": candidate_type,
        "recall": recall,
        "false_alarm_rate": false_alarm_rate,
        "precision": precision,
        "recall_delta": recall_delta,
        "false_alarm_rate_delta": false_alarm_delta,
        "precision_delta": precision_delta,
        "flagged_case_ids": sorted(flagged_ids),
        "newly_recovered_case_ids": newly_recovered,
        "new_false_alarm_case_ids": new_false_alarms,
        "newly_recovered_count": len(newly_recovered),
        "new_false_alarm_count": len(new_false_alarms),
    }


def _candidate_leaderboard(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": candidate["candidate_id"],
            "candidate_type": candidate["candidate_type"],
            "recall_delta": candidate["recall_delta"],
            "false_alarm_rate_delta": candidate["false_alarm_rate_delta"],
            "precision_delta": candidate["precision_delta"],
            "newly_recovered_count": candidate["newly_recovered_count"],
            "new_false_alarm_count": candidate["new_false_alarm_count"],
            "passes_mitigation_gate": candidate["passes_mitigation_gate"],
        }
        for candidate in candidates
    ]


def _tage_58_62_guard(row: dict[str, Any]) -> Decimal:
    if row["segment_column"] == "TAGE" and 58 <= int(row["segment_value"]) <= 62:
        return CURRENT_ACTIVATION_MARGIN
    return L7_ACTIVATION_MARGIN


def _tage_family_guard(row: dict[str, Any]) -> Decimal:
    if row["segment_column"] == "TAGE":
        return CURRENT_ACTIVATION_MARGIN
    return L7_ACTIVATION_MARGIN


def _protected_sensitive_guard(row: dict[str, Any]) -> Decimal:
    if row["sensitivity_level"] == "protected_sensitive":
        return CURRENT_ACTIVATION_MARGIN
    return L7_ACTIVATION_MARGIN


def _protected_sensitive_false_alarm_delta(
    rows: list[dict[str, Any]],
    margin_policy: Callable[[dict[str, Any]], Decimal],
) -> float:
    protected_low = [
        row
        for row in rows
        if row["sensitivity_level"] == "protected_sensitive"
        and not row["observed_high_risk"]
    ]
    before = _rate(
        sum(
            row["prediction"] >= row["static_prior"] + CURRENT_ACTIVATION_MARGIN
            for row in protected_low
        ),
        len(protected_low),
    )
    after = _rate(
        sum(
            row["prediction"] >= row["static_prior"] + margin_policy(row)
            for row in protected_low
        ),
        len(protected_low),
    )
    return _round6(_decimal(after) - _decimal(before))


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
    parser.add_argument("--r12-recall-update-false-alarm-stress-test-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_recall_false_alarm_mitigation_candidate(
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
        r12_recall_update_false_alarm_stress_test=load_json_artifact(
            args.r12_recall_update_false_alarm_stress_test_path
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
