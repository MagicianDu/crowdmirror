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
from experiments.r12_causal_interaction_operator import (
    R12_CAUSAL_INTERACTION_OPERATOR_SCHEMA_VERSION,
)
from experiments.r12_outcome_case_registry import (
    R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION,
)
from experiments.r12_outcome_supervised_update import (
    R12_OUTCOME_SUPERVISED_UPDATE_SCHEMA_VERSION,
)


R12_TRANSFER_VALIDATION_SCHEMA_VERSION = "r12-transfer-validation-v1"
HIGH_RISK_THRESHOLD = Decimal("0.484619")
INTERVAL_HALF_WIDTH = Decimal("0.1")


def build_r12_transfer_validation(
    *,
    artifact_id: str,
    run_id: str,
    r12_outcome_case_registry: dict[str, Any],
    r12_causal_interaction_operator: dict[str, Any],
    r12_outcome_supervised_update: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_case_registry(r12_outcome_case_registry)
    _validate_operator(r12_causal_interaction_operator)
    _validate_update(r12_outcome_supervised_update)
    accepted_update = _accepted_mechanism_update(r12_outcome_supervised_update)
    case_replays = [
        _case_replay(case, accepted_update=accepted_update)
        for case in r12_outcome_case_registry["cases"]
    ]
    split_metrics = {
        split: _split_metrics(case_replays, split=split)
        for split in ("train", "validation", "holdout")
    }
    extended_transfer_metrics = _extended_transfer_metrics(case_replays, split_metrics)
    extended_metric_gates = _extended_metric_gates(extended_transfer_metrics)
    gates = _acceptance_gates(split_metrics)
    decision = (
        "r12_update_transfer_positive_guarded"
        if gates["positive_transfer_guarded"]
        else "r12_update_transfer_blocked_same_case_only"
    )
    report = {
        "schema_version": R12_TRANSFER_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_transfer_validation_positive_guarded"
            if gates["positive_transfer_guarded"]
            else "r12_transfer_validation_blocked_same_case_only"
        ),
        "claim_level": "guarded_public_proxy_transfer_signal",
        "accepted_update": {
            "update_id": accepted_update["update_id"],
            "update_type": accepted_update["update_type"],
            "target": accepted_update["target"],
            "recommended_value": accepted_update["recommended_value"],
            "runtime_default_allowed": False,
        },
        "transfer_accounting": {
            "train_metrics_reported": True,
            "train_metrics_used_for_transfer_decision": False,
            "validation_metrics_used_for_transfer_decision": True,
            "holdout_metrics_used_for_transfer_decision": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "case_replays": case_replays,
        "split_metrics": split_metrics,
        "extended_transfer_metrics": extended_transfer_metrics,
        "extended_metric_gates": extended_metric_gates,
        "update_transfer_gain": _update_transfer_gain(split_metrics),
        "transfer_decision": decision,
        "acceptance_gates": gates,
        "source_refs": [
            r12_outcome_case_registry["artifact_id"],
            r12_causal_interaction_operator["artifact_id"],
            r12_outcome_supervised_update["artifact_id"],
        ],
        "next_required_artifact": "r12_product_guarded_report",
        "blocked_claims": [
            "R12 field validated",
            "R12 Product core method ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "customer outcome validated",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_transfer_validation(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r12_transfer_validation(**kwargs))


def _validate_case_registry(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION:
        raise ValueError("r12_outcome_case_registry.schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12_outcome_case_registry.acceptance_gates must be an object")
    if gates.get("outcome_leakage_blocked") is not True:
        raise ValueError("r12 outcome case registry must block outcome leakage")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 outcome case registry must not allow runtime default")


def _validate_operator(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_CAUSAL_INTERACTION_OPERATOR_SCHEMA_VERSION:
        raise ValueError("r12_causal_interaction_operator.schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12_causal_interaction_operator.acceptance_gates must be an object")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 causal interaction operator must not allow runtime default")


def _validate_update(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_OUTCOME_SUPERVISED_UPDATE_SCHEMA_VERSION:
        raise ValueError("r12_outcome_supervised_update.schema_version is invalid")
    gate = artifact.get("update_gate")
    if not isinstance(gate, dict):
        raise ValueError("r12_outcome_supervised_update.update_gate must be an object")
    if gate.get("outcome_leakage_blocked") is not True:
        raise ValueError("r12 outcome update must block outcome leakage")
    if gate.get("runtime_default_allowed") is not False:
        raise ValueError("r12 outcome update must not allow runtime default")


def _accepted_mechanism_update(artifact: dict[str, Any]) -> dict[str, Any]:
    accepted = [
        candidate
        for candidate in artifact["update_candidates"]
        if candidate["update_type"] == "mechanism_weight"
        and candidate["status"] == "accepted"
    ]
    if len(accepted) != 1:
        raise ValueError("exactly one accepted mechanism update is required")
    update = accepted[0]
    if update["default_runtime_enabled"] is not False:
        raise ValueError("accepted mechanism update must not be runtime default")
    return update


def _case_replay(
    case: dict[str, Any],
    *,
    accepted_update: dict[str, Any],
) -> dict[str, Any]:
    observed = _decimal(case["outcome_proxy"]["observed_value"])
    before = _decimal(case["prediction_state"]["interaction_prediction"])
    static_prior = _decimal(case["prediction_state"]["static_prior_prediction"])
    source_delta = _decimal(case["source_signal"]["delta"])
    weight = _decimal(accepted_update["recommended_value"])
    after = _clip_probability(static_prior + source_delta * weight)
    before_interval = case["risk_interval"]
    after_interval = _interval(after)
    return {
        "case_id": case["case_id"],
        "split": case["split"],
        "observed_value": _round6(observed),
        "before_prediction": _round6(before),
        "after_prediction": _round6(after),
        "static_prior_prediction": _round6(static_prior),
        "source_signal_delta": _round6(source_delta),
        "absolute_error_before": _round6(abs(observed - before)),
        "absolute_error_after": _round6(abs(observed - after)),
        "before_interval": before_interval,
        "after_interval": after_interval,
        "before_interval_hit": _interval_hit(observed, before_interval),
        "after_interval_hit": _interval_hit(observed, after_interval),
        "before_predicted_high_risk": before >= HIGH_RISK_THRESHOLD,
        "after_predicted_high_risk": after >= HIGH_RISK_THRESHOLD,
        "static_prior_predicted_high_risk": static_prior >= HIGH_RISK_THRESHOLD,
        "observed_high_risk": case["outcome_proxy"]["observed_high_risk"],
        "static_prior_missed_observed_high_risk": (
            case["outcome_proxy"]["observed_high_risk"]
            and static_prior < HIGH_RISK_THRESHOLD
        ),
        "before_false_alarm": _false_alarm(
            predicted_high=before >= HIGH_RISK_THRESHOLD,
            observed_high=case["outcome_proxy"]["observed_high_risk"],
        ),
        "after_false_alarm": _false_alarm(
            predicted_high=after >= HIGH_RISK_THRESHOLD,
            observed_high=case["outcome_proxy"]["observed_high_risk"],
        ),
    }


def _split_metrics(
    case_replays: list[dict[str, Any]],
    *,
    split: str,
) -> dict[str, Any]:
    rows = [row for row in case_replays if row["split"] == split]
    if not rows:
        raise ValueError(f"split has no rows: {split}")
    mae_before = _mean(row["absolute_error_before"] for row in rows)
    mae_after = _mean(row["absolute_error_after"] for row in rows)
    interval_before = _mean(1.0 if row["before_interval_hit"] else 0.0 for row in rows)
    interval_after = _mean(1.0 if row["after_interval_hit"] else 0.0 for row in rows)
    false_alarm_before = _mean(1.0 if row["before_false_alarm"] else 0.0 for row in rows)
    false_alarm_after = _mean(1.0 if row["after_false_alarm"] else 0.0 for row in rows)
    return {
        "case_count": len(rows),
        "mean_absolute_error_before": _round6(mae_before),
        "mean_absolute_error_after": _round6(mae_after),
        "mean_absolute_error_delta": _round6(mae_after - mae_before),
        "interval_coverage_before": _round6(interval_before),
        "interval_coverage_after": _round6(interval_after),
        "interval_coverage_delta": _round6(interval_after - interval_before),
        "false_alarm_rate_before": _round6(false_alarm_before),
        "false_alarm_rate_after": _round6(false_alarm_after),
        "false_alarm_rate_delta": _round6(false_alarm_after - false_alarm_before),
    }


def _acceptance_gates(split_metrics: dict[str, dict[str, Any]]) -> dict[str, bool]:
    validation = split_metrics["validation"]
    holdout = split_metrics["holdout"]
    validation_mae_improved = validation["mean_absolute_error_delta"] < 0
    holdout_mae_improved = holdout["mean_absolute_error_delta"] < 0
    interval_coverage_non_regression = (
        validation["interval_coverage_delta"] >= 0
        and holdout["interval_coverage_delta"] >= 0
    )
    false_alarm_rate_non_regression = (
        validation["false_alarm_rate_delta"] <= 0
        and holdout["false_alarm_rate_delta"] <= 0
    )
    return {
        "positive_transfer_guarded": (
            validation_mae_improved
            and holdout_mae_improved
            and interval_coverage_non_regression
            and false_alarm_rate_non_regression
        ),
        "validation_mae_improved": validation_mae_improved,
        "holdout_mae_improved": holdout_mae_improved,
        "interval_coverage_non_regression": interval_coverage_non_regression,
        "false_alarm_rate_non_regression": false_alarm_rate_non_regression,
        "train_metrics_used_for_transfer_decision": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }


def _extended_transfer_metrics(
    case_replays: list[dict[str, Any]],
    split_metrics: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "risk_ranking_quality": {
            split: _ranking_metric(case_replays, split=split)
            for split in ("train", "validation", "holdout")
        },
        "static_prior_miss_recovery": {
            split: _static_prior_miss_recovery(case_replays, split=split)
            for split in ("train", "validation", "holdout")
        },
        "abnormal_segment_recall": {
            split: _abnormal_segment_recall(case_replays, split=split)
            for split in ("train", "validation", "holdout")
        },
        "decision_value_score": {
            split: _decision_value_metric(
                case_replays,
                split_metrics=split_metrics,
                split=split,
            )
            for split in ("train", "validation", "holdout")
        },
    }


def _extended_metric_gates(extended_metrics: dict[str, Any]) -> dict[str, Any]:
    risk_ranking = extended_metrics["risk_ranking_quality"]
    decision_value = extended_metrics["decision_value_score"]
    static_prior_miss = extended_metrics["static_prior_miss_recovery"]
    abnormal_recall = extended_metrics["abnormal_segment_recall"]
    return {
        "risk_ranking_non_regression": (
            risk_ranking["validation"]["delta"] >= 0
            and risk_ranking["holdout"]["delta"] >= 0
        ),
        "decision_value_non_regression": (
            decision_value["validation"]["delta"] >= 0
            and decision_value["holdout"]["delta"] >= 0
        ),
        "static_prior_miss_recovery_holdout_covered": (
            static_prior_miss["holdout"]["eligible_case_count"] > 0
        ),
        "abnormal_segment_recall_holdout_covered": (
            abnormal_recall["holdout"]["eligible_case_count"] > 0
        ),
        "extended_product_metric_support_level": (
            "guarded_mae_positive_extended_metric_coverage_gap"
        ),
    }


def _ranking_metric(
    case_replays: list[dict[str, Any]],
    *,
    split: str,
) -> dict[str, float | None]:
    rows = [row for row in case_replays if row["split"] == split]
    before = _pairwise_ranking_quality(rows, prediction_field="before_prediction")
    after = _pairwise_ranking_quality(rows, prediction_field="after_prediction")
    return {
        "before": before,
        "after": after,
        "delta": _nullable_delta(after, before),
    }


def _static_prior_miss_recovery(
    case_replays: list[dict[str, Any]],
    *,
    split: str,
) -> dict[str, Any]:
    rows = [
        row
        for row in case_replays
        if row["split"] == split and row["static_prior_missed_observed_high_risk"]
    ]
    before = _high_risk_recall(rows, prediction_field="before_predicted_high_risk")
    after = _high_risk_recall(rows, prediction_field="after_predicted_high_risk")
    return {
        "eligible_case_count": len(rows),
        "before": before,
        "after": after,
        "delta": _nullable_delta(after, before),
    }


def _abnormal_segment_recall(
    case_replays: list[dict[str, Any]],
    *,
    split: str,
) -> dict[str, Any]:
    rows = [
        row
        for row in case_replays
        if row["split"] == split and row["observed_high_risk"]
    ]
    before = _high_risk_recall(rows, prediction_field="before_predicted_high_risk")
    after = _high_risk_recall(rows, prediction_field="after_predicted_high_risk")
    return {
        "eligible_case_count": len(rows),
        "before": before,
        "after": after,
        "delta": _nullable_delta(after, before),
    }


def _decision_value_metric(
    case_replays: list[dict[str, Any]],
    *,
    split_metrics: dict[str, dict[str, Any]],
    split: str,
) -> dict[str, float | None]:
    ranking = _ranking_metric(case_replays, split=split)
    before = _nullable_minus(
        ranking["before"],
        split_metrics[split]["false_alarm_rate_before"],
    )
    after = _nullable_minus(
        ranking["after"],
        split_metrics[split]["false_alarm_rate_after"],
    )
    return {
        "before": before,
        "after": after,
        "delta": _nullable_delta(after, before),
    }


def _pairwise_ranking_quality(
    rows: list[dict[str, Any]],
    *,
    prediction_field: str,
) -> float | None:
    total = 0
    correct = Decimal("0")
    for left_index, left in enumerate(rows):
        for right in rows[left_index + 1 :]:
            left_observed = _decimal(left["observed_value"])
            right_observed = _decimal(right["observed_value"])
            if left_observed == right_observed:
                continue
            total += 1
            left_prediction = _decimal(left[prediction_field])
            right_prediction = _decimal(right[prediction_field])
            if left_prediction == right_prediction:
                correct += Decimal("0.5")
            elif (left_observed > right_observed) == (
                left_prediction > right_prediction
            ):
                correct += Decimal("1")
    if total == 0:
        return None
    return _round6(correct / Decimal(total))


def _high_risk_recall(
    rows: list[dict[str, Any]],
    *,
    prediction_field: str,
) -> float | None:
    if not rows:
        return None
    recovered = sum(1 for row in rows if row[prediction_field])
    return _round6(Decimal(recovered) / Decimal(len(rows)))


def _nullable_minus(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return _round6(_decimal(left) - _decimal(right))


def _nullable_delta(after: float | None, before: float | None) -> float | None:
    return _nullable_minus(after, before)


def _update_transfer_gain(split_metrics: dict[str, dict[str, Any]]) -> float:
    validation_gain = -_decimal(split_metrics["validation"]["mean_absolute_error_delta"])
    holdout_gain = -_decimal(split_metrics["holdout"]["mean_absolute_error_delta"])
    return _round6(validation_gain + holdout_gain)


def _mean(values: Any) -> Decimal:
    items = [_decimal(value) for value in values]
    return sum(items, Decimal("0")) / Decimal(len(items))


def _interval(value: Decimal) -> dict[str, float]:
    return {
        "median": _round6(value),
        "p10": _round6(_clip_probability(value - INTERVAL_HALF_WIDTH)),
        "p90": _round6(_clip_probability(value + INTERVAL_HALF_WIDTH)),
    }


def _interval_hit(value: Decimal, interval: dict[str, Any]) -> bool:
    return _decimal(interval["p10"]) <= value <= _decimal(interval["p90"])


def _false_alarm(*, predicted_high: bool, observed_high: bool) -> bool:
    return predicted_high and not observed_high


def _clip_probability(value: Decimal) -> Decimal:
    return min(Decimal("1"), max(Decimal("0"), value))


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _round6(value: Decimal | float) -> float:
    return float(_decimal(value).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r12-outcome-case-registry-path", required=True)
    parser.add_argument("--r12-causal-interaction-operator-path", required=True)
    parser.add_argument("--r12-outcome-supervised-update-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_transfer_validation(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_outcome_case_registry=load_json_artifact(
            args.r12_outcome_case_registry_path
        ),
        r12_causal_interaction_operator=load_json_artifact(
            args.r12_causal_interaction_operator_path
        ),
        r12_outcome_supervised_update=load_json_artifact(
            args.r12_outcome_supervised_update_path
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
