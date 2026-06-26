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
from experiments.r12_high_risk_holdout_registry import (
    R12_HIGH_RISK_HOLDOUT_REGISTRY_SCHEMA_VERSION,
)
from experiments.r12_transfer_validation import (
    R12_TRANSFER_VALIDATION_SCHEMA_VERSION,
)


R12_HIGH_RISK_HOLDOUT_TRANSFER_REPLAY_SCHEMA_VERSION = (
    "r12-high-risk-holdout-transfer-replay-v1"
)
HIGH_RISK_MARGIN = Decimal("0.03")
INTERVAL_HALF_WIDTH = Decimal("0.1")


def build_r12_high_risk_holdout_transfer_replay(
    *,
    artifact_id: str,
    run_id: str,
    r12_high_risk_holdout_registry: dict[str, Any],
    r12_transfer_validation: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_high_risk_registry(r12_high_risk_holdout_registry)
    _validate_transfer_validation(r12_transfer_validation)
    before_weight = _infer_before_mechanism_weight(r12_transfer_validation)
    after_weight = _decimal(r12_transfer_validation["accepted_update"]["recommended_value"])
    case_replays = [
        _case_replay(
            case,
            before_weight=before_weight,
            after_weight=after_weight,
        )
        for case in r12_high_risk_holdout_registry["holdout_candidate_cases"]
    ]
    metrics = _metric_comparison(case_replays)
    gates = _acceptance_gates(
        metrics=metrics,
        registry=r12_high_risk_holdout_registry,
    )
    decision = _transfer_decision(gates)
    report = {
        "schema_version": R12_HIGH_RISK_HOLDOUT_TRANSFER_REPLAY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": (
            "r12_high_risk_holdout_transfer_replay_partial_research_positive"
            if decision == "r12_high_risk_replay_mae_positive_recall_flat_research_only"
            else "r12_high_risk_holdout_transfer_replay_blocked"
        ),
        "claim_level": "research_only_sensitive_public_proxy_replay",
        "replay_contract": {
            "source_backed_public_proxy": True,
            "uses_research_only_high_risk_candidates": True,
            "sensitive_or_high_governance_axes_present": any(
                not case["product_default_eligible"] for case in case_replays
            ),
            "product_default_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "parameter_replay": {
            "before_mechanism_weight": _round6(before_weight),
            "after_mechanism_weight": _round6(after_weight),
            "updated_target": r12_transfer_validation["accepted_update"]["target"],
            "train_metrics_used_as_replay_proof": False,
        },
        "replay_summary": {
            "candidate_case_count": len(case_replays),
            "recoverable_static_prior_miss_case_count": sum(
                1 for case in case_replays if case["after_static_prior_miss_recovered"]
            ),
            "product_default_eligible_case_count": sum(
                1 for case in case_replays if case["product_default_eligible"]
            ),
            "sensitive_or_high_governance_case_count": sum(
                1 for case in case_replays if not case["product_default_eligible"]
            ),
            "false_alarm_evaluable_case_count": sum(
                1 for case in case_replays if not case["observed_high_risk"]
            ),
        },
        "metric_comparison": metrics,
        "case_replays": case_replays,
        "acceptance_gates": gates,
        "transfer_decision": decision,
        "product_support_level": (
            "research_only_mae_positive_recall_and_product_default_gap"
            if gates["mae_improved"]
            else "research_only_high_risk_replay_blocked"
        ),
        "next_required_artifact": (
            "r12_product_eligible_high_risk_holdout_or_customer_outcome"
        ),
        "source_refs": [
            r12_high_risk_holdout_registry["artifact_id"],
            r12_transfer_validation["artifact_id"],
        ],
        "source_registry": [
            {
                "artifact_id": r12_high_risk_holdout_registry["artifact_id"],
                "path": (
                    "experiments/results/r12_high_risk_holdout_registry/"
                    "r12-high-risk-holdout-registry-current-001.json"
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
                "R12 high-risk replay shows a research-only public proxy MAE "
                "improvement on sensitive or high-governance high-risk candidates."
            ),
            (
                "The replay can guide further Research validation, not Product "
                "default use."
            ),
        ],
        "blocked_claims": [
            "R12 Product default high-risk recovery validated",
            "R12 Product core method ready",
            "static-prior miss recovery improved on high-risk replay",
            "abnormal segment recall improved on high-risk replay",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "customer outcome validated",
            "sensitive segment axes can be used as Product default",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_high_risk_holdout_transfer_replay(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_high_risk_holdout_transfer_replay(**kwargs),
    )


def _validate_high_risk_registry(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_HIGH_RISK_HOLDOUT_REGISTRY_SCHEMA_VERSION:
        raise ValueError("r12_high_risk_holdout_registry.schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 high-risk registry acceptance_gates required")
    if gates.get("high_risk_research_holdout_candidates_present") is not True:
        raise ValueError("r12 high-risk registry must include replay candidates")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 high-risk registry must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 high-risk registry must not allow runtime default")


def _validate_transfer_validation(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_TRANSFER_VALIDATION_SCHEMA_VERSION:
        raise ValueError("r12_transfer_validation.schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 transfer validation acceptance_gates required")
    if gates.get("train_metrics_used_for_transfer_decision") is not False:
        raise ValueError("r12 transfer validation must not use train metrics as proof")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r12 transfer validation must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 transfer validation must not allow runtime default")


def _case_replay(
    case: dict[str, Any],
    *,
    before_weight: Decimal,
    after_weight: Decimal,
) -> dict[str, Any]:
    static_prior = _decimal(case["static_prior_prediction"])
    source_delta = _decimal(case["source_signal_delta"])
    observed = _decimal(case["observed_outcome_proxy"])
    high_risk_threshold = static_prior + HIGH_RISK_MARGIN
    before = _clip(static_prior + source_delta * before_weight)
    after = _clip(static_prior + source_delta * after_weight)
    before_high = before >= high_risk_threshold
    after_high = after >= high_risk_threshold
    observed_high = bool(case["observed_high_risk"])
    return {
        "case_id": case["case_id"],
        "segment_labels": case["segment_labels"],
        "observed_value": _round6(observed),
        "before_prediction": _round6(before),
        "after_prediction": _round6(after),
        "static_prior_prediction": _round6(static_prior),
        "absolute_error_before": _round6(abs(observed - before)),
        "absolute_error_after": _round6(abs(observed - after)),
        "before_predicted_high_risk": before_high,
        "after_predicted_high_risk": after_high,
        "observed_high_risk": observed_high,
        "static_prior_missed_observed_high_risk": bool(
            case["static_prior_missed_observed_high_risk"]
        ),
        "before_static_prior_miss_recovered": (
            bool(case["static_prior_missed_observed_high_risk"]) and before_high
        ),
        "after_static_prior_miss_recovered": (
            bool(case["static_prior_missed_observed_high_risk"]) and after_high
        ),
        "before_interval_hit": _interval_hit(observed, before),
        "after_interval_hit": _interval_hit(observed, after),
        "product_default_eligible": bool(case["product_default_eligible"]),
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }


def _metric_comparison(case_replays: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "mean_absolute_error": _before_after_metric(
            case_replays,
            before_field="absolute_error_before",
            after_field="absolute_error_after",
            lower_is_better=True,
        ),
        "static_prior_miss_recovery": _recall_metric(
            [
                case
                for case in case_replays
                if case["static_prior_missed_observed_high_risk"]
            ],
            before_field="before_static_prior_miss_recovered",
            after_field="after_static_prior_miss_recovered",
        ),
        "abnormal_segment_recall": _recall_metric(
            [case for case in case_replays if case["observed_high_risk"]],
            before_field="before_predicted_high_risk",
            after_field="after_predicted_high_risk",
        ),
        "interval_coverage": _boolean_rate_metric(
            case_replays,
            before_field="before_interval_hit",
            after_field="after_interval_hit",
        ),
        "risk_ranking_quality": _ranking_metric(case_replays),
        "false_alarm_rate": _false_alarm_metric(case_replays),
    }


def _before_after_metric(
    rows: list[dict[str, Any]],
    *,
    before_field: str,
    after_field: str,
    lower_is_better: bool,
) -> dict[str, float]:
    before = _mean(_decimal(row[before_field]) for row in rows)
    after = _mean(_decimal(row[after_field]) for row in rows)
    delta = after - before
    return {
        "before": _round6(before),
        "after": _round6(after),
        "delta": _round6(delta),
    }


def _boolean_rate_metric(
    rows: list[dict[str, Any]],
    *,
    before_field: str,
    after_field: str,
) -> dict[str, float]:
    before = _rate(sum(1 for row in rows if row[before_field]), len(rows))
    after = _rate(sum(1 for row in rows if row[after_field]), len(rows))
    return {
        "before": before,
        "after": after,
        "delta": _round6(_decimal(after) - _decimal(before)),
    }


def _recall_metric(
    rows: list[dict[str, Any]],
    *,
    before_field: str,
    after_field: str,
) -> dict[str, Any]:
    if not rows:
        return {
            "eligible_case_count": 0,
            "before": None,
            "after": None,
            "delta": None,
        }
    before = _rate(sum(1 for row in rows if row[before_field]), len(rows))
    after = _rate(sum(1 for row in rows if row[after_field]), len(rows))
    return {
        "eligible_case_count": len(rows),
        "before": before,
        "after": after,
        "delta": _round6(_decimal(after) - _decimal(before)),
    }


def _ranking_metric(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    before = _pairwise_ranking_quality(rows, prediction_field="before_prediction")
    after = _pairwise_ranking_quality(rows, prediction_field="after_prediction")
    return {
        "before": before,
        "after": after,
        "delta": None
        if before is None or after is None
        else _round6(_decimal(after) - _decimal(before)),
    }


def _false_alarm_metric(rows: list[dict[str, Any]]) -> dict[str, Any]:
    evaluable = [row for row in rows if not row["observed_high_risk"]]
    if not evaluable:
        return {
            "evaluable_case_count": 0,
            "before": None,
            "after": None,
            "delta": None,
        }
    before = _rate(
        sum(1 for row in evaluable if row["before_predicted_high_risk"]),
        len(evaluable),
    )
    after = _rate(
        sum(1 for row in evaluable if row["after_predicted_high_risk"]),
        len(evaluable),
    )
    return {
        "evaluable_case_count": len(evaluable),
        "before": before,
        "after": after,
        "delta": _round6(_decimal(after) - _decimal(before)),
    }


def _acceptance_gates(
    *,
    metrics: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, bool]:
    return {
        "source_backed_public_proxy_present": True,
        "high_risk_replay_executed": True,
        "mae_improved": metrics["mean_absolute_error"]["delta"] < 0,
        "static_prior_miss_recovery_improved": (
            metrics["static_prior_miss_recovery"]["delta"] is not None
            and metrics["static_prior_miss_recovery"]["delta"] > 0
        ),
        "abnormal_segment_recall_improved": (
            metrics["abnormal_segment_recall"]["delta"] is not None
            and metrics["abnormal_segment_recall"]["delta"] > 0
        ),
        "interval_coverage_non_regression": metrics["interval_coverage"]["delta"] >= 0,
        "risk_ranking_non_regression": (
            metrics["risk_ranking_quality"]["delta"] is not None
            and metrics["risk_ranking_quality"]["delta"] >= 0
        ),
        "false_alarm_rate_evaluable": (
            metrics["false_alarm_rate"]["evaluable_case_count"] > 0
        ),
        "product_default_eligible_high_risk_holdout_present": registry[
            "acceptance_gates"
        ]["product_default_low_sensitive_high_risk_holdout_present"],
        "product_core_method_ready": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }


def _transfer_decision(gates: dict[str, bool]) -> str:
    if (
        gates["mae_improved"]
        and not gates["static_prior_miss_recovery_improved"]
        and not gates["abnormal_segment_recall_improved"]
    ):
        return "r12_high_risk_replay_mae_positive_recall_flat_research_only"
    return "r12_high_risk_replay_blocked_or_negative"


def _infer_before_mechanism_weight(transfer_validation: dict[str, Any]) -> Decimal:
    weights = []
    for case in transfer_validation["case_replays"]:
        source_delta = _decimal(case["source_signal_delta"])
        if source_delta == 0:
            continue
        before = _decimal(case["before_prediction"])
        static_prior = _decimal(case["static_prior_prediction"])
        weights.append((before - static_prior) / source_delta)
    if not weights:
        raise ValueError("cannot infer before mechanism weight")
    return _decimal(sum(weights, Decimal("0")) / Decimal(len(weights))).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


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


def _interval_hit(value: Decimal, median: Decimal) -> bool:
    return (
        _clip(median - INTERVAL_HALF_WIDTH)
        <= value
        <= _clip(median + INTERVAL_HALF_WIDTH)
    )


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return _round6(Decimal(numerator) / Decimal(denominator))


def _mean(values: Any) -> Decimal:
    items = list(values)
    if not items:
        raise ValueError("mean requires at least one value")
    return sum(items, Decimal("0")) / Decimal(len(items))


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
    parser.add_argument("--r12-high-risk-holdout-registry-path", required=True)
    parser.add_argument("--r12-transfer-validation-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_high_risk_holdout_transfer_replay(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_high_risk_holdout_registry=load_json_artifact(
            args.r12_high_risk_holdout_registry_path
        ),
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
