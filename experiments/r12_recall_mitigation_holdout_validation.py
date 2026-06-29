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
from experiments.r12_recall_false_alarm_mitigation_candidate import (
    CURRENT_ACTIVATION_MARGIN,
    L7_ACTIVATION_MARGIN,
    R12_RECALL_FALSE_ALARM_MITIGATION_SCHEMA_VERSION,
    _evaluate_policy,
    _evaluation_cases,
    _global_risk_share,
    _decimal,
    _round6,
    _tage_58_62_guard,
    _tage_family_guard,
)
from experiments.r12_recall_oriented_update import (
    OUTCOME_PROXY,
    R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION,
    SOURCE_SIGNAL,
)
from experiments.r12_transfer_validation import (
    R12_TRANSFER_VALIDATION_SCHEMA_VERSION,
)


R12_RECALL_MITIGATION_HOLDOUT_VALIDATION_SCHEMA_VERSION = (
    "r12-recall-mitigation-holdout-validation-v1"
)
REQUIRED_LEAVE_ONE_PASS_RATE = Decimal("0.666667")
REQUIRED_STABLE_RECALL_RETENTION = Decimal("0.5")


def build_r12_recall_mitigation_holdout_validation(
    *,
    artifact_id: str,
    run_id: str,
    hps_ingestion: dict[str, Any],
    r12_transfer_validation: dict[str, Any],
    r12_recall_oriented_update: dict[str, Any],
    r12_recall_false_alarm_mitigation_candidate: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_hps_ingestion(hps_ingestion)
    _validate_transfer_validation(r12_transfer_validation)
    _validate_recall_update(r12_recall_oriented_update)
    _validate_mitigation_candidate(r12_recall_false_alarm_mitigation_candidate)

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
    selected = _evaluate_policy(
        rows,
        policy_id="r12-tage-58-62-activation-guard-001",
        candidate_id="r12-tage-58-62-activation-guard-001",
        candidate_type="segment_value_band_activation_margin_guard",
        margin_policy=_tage_58_62_guard,
        baseline=baseline,
    )
    family = _evaluate_policy(
        rows,
        policy_id="r12-tage-family-conservative-cap-001",
        candidate_id="r12-tage-family-conservative-cap-001",
        candidate_type="segment_family_activation_margin_guard",
        margin_policy=_tage_family_guard,
        baseline=baseline,
    )
    current_replay_metrics = {
        "candidate_id": selected["candidate_id"],
        "recall_delta": selected["recall_delta"],
        "l7_recall_gain_retained": _gain_retained(selected, l7),
        "false_alarm_rate_delta": selected["false_alarm_rate_delta"],
        "precision_delta": selected["precision_delta"],
        "new_false_alarm_count": selected["new_false_alarm_count"],
    }
    leave_one = _leave_one_false_alarm_validation(
        rows=rows,
        baseline=baseline,
        l7=l7,
    )
    stable_alternative = {
        "candidate_id": family["candidate_id"],
        "recall_delta": family["recall_delta"],
        "l7_recall_gain_retained": _gain_retained(family, l7),
        "false_alarm_rate_delta": family["false_alarm_rate_delta"],
        "precision_delta": family["precision_delta"],
        "new_false_alarm_count": family["new_false_alarm_count"],
        "stable_but_recall_retention_too_low": (
            _decimal(_gain_retained(family, l7))
            < REQUIRED_STABLE_RECALL_RETENTION
        ),
    }
    gates = {
        "source_backed_public_proxy_present": True,
        "current_replay_positive": (
            current_replay_metrics["recall_delta"] > 0
            and current_replay_metrics["false_alarm_rate_delta"] <= 0
            and current_replay_metrics["precision_delta"] >= 0
        ),
        "independent_holdout_present": False,
        "leave_one_false_alarm_band_stable": (
            _decimal(leave_one["pass_rate"]) >= REQUIRED_LEAVE_ONE_PASS_RATE
        ),
        "holdout_pass_rate_sufficient": (
            _decimal(leave_one["pass_rate"]) >= REQUIRED_LEAVE_ONE_PASS_RATE
        ),
        "low_sensitive_recall_evaluable": (
            r12_recall_false_alarm_mitigation_candidate["acceptance_gates"][
                "low_sensitive_recall_evaluable"
            ]
        ),
        "stable_alternative_retains_required_recall": not stable_alternative[
            "stable_but_recall_retention_too_low"
        ],
        "mitigation_holdout_validated": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    report = {
        "schema_version": R12_RECALL_MITIGATION_HOLDOUT_VALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_recall_mitigation_holdout_validation_blocked_overfit",
        "claim_level": "mitigation_candidate_not_holdout_validated",
        "validation_contract": {
            "validates_mitigation_candidate": True,
            "requires_independent_holdout_for_product_default": True,
            "requires_low_sensitive_or_customer_approved_slice": True,
            "requires_leave_one_false_alarm_stability": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "validation_summary": {
            "evaluated_case_count": len(rows),
            "independent_dataset_present": False,
            "independent_holdout_case_count": 0,
            "customer_approved_holdout_case_count": 0,
            "low_sensitive_recall_evaluable": gates[
                "low_sensitive_recall_evaluable"
            ],
            "false_alarm_band_derivation_case_count": len(
                l7["new_false_alarm_case_ids"]
            ),
            "leave_one_false_alarm_trial_count": leave_one["trial_count"],
        },
        "current_replay_metrics": current_replay_metrics,
        "leave_one_false_alarm_band_validation": leave_one,
        "stable_alternative_check": stable_alternative,
        "acceptance_gates": gates,
        "acceptance_decision": (
            "reject_product_default_retain_as_failure_diagnosis_candidate"
        ),
        "product_support_level": (
            "failure_diagnosis_candidate_only_until_independent_holdout"
        ),
        "next_required_artifact": "r12_recall_mitigation_independent_holdout_data",
        "source_refs": [
            hps_ingestion["artifact_id"],
            r12_transfer_validation["artifact_id"],
            r12_recall_oriented_update["artifact_id"],
            r12_recall_false_alarm_mitigation_candidate["artifact_id"],
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
                "artifact_id": r12_recall_false_alarm_mitigation_candidate[
                    "artifact_id"
                ],
                "path": (
                    "experiments/results/r12_recall_false_alarm_mitigation_candidate/"
                    "r12-recall-false-alarm-mitigation-candidate-current-001.json"
                ),
            },
        ],
        "allowed_claims": [
            (
                "R12 mitigation candidate remains useful as a failure diagnosis "
                "candidate for the current public proxy replay."
            ),
            (
                "The current evidence explicitly blocks Product default until "
                "independent or customer-approved holdout data exists."
            ),
        ],
        "blocked_claims": [
            "mitigation holdout validated",
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


def write_r12_recall_mitigation_holdout_validation(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output, build_r12_recall_mitigation_holdout_validation(**kwargs)
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
    if artifact["acceptance_gates"].get("field_outcome_validated") is not False:
        raise ValueError("r12 transfer validation must not be field validated")
    if artifact["acceptance_gates"].get("runtime_default_allowed") is not False:
        raise ValueError("r12 transfer validation must not allow runtime default")


def _validate_recall_update(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_RECALL_ORIENTED_UPDATE_SCHEMA_VERSION:
        raise ValueError("r12 recall update schema_version is invalid")
    if artifact["acceptance_gates"].get("recall_improved") is not True:
        raise ValueError("r12 recall update must improve recall")
    if artifact["acceptance_gates"].get("product_default_allowed") is not False:
        raise ValueError("r12 recall update must not allow Product default")


def _validate_mitigation_candidate(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R12_RECALL_FALSE_ALARM_MITIGATION_SCHEMA_VERSION:
        raise ValueError("r12 mitigation candidate schema_version is invalid")
    if artifact.get("next_required_artifact") != (
        "r12_recall_mitigation_holdout_validation"
    ):
        raise ValueError("r12 mitigation candidate does not request holdout validation")
    if artifact["acceptance_gates"].get("product_default_allowed") is not False:
        raise ValueError("r12 mitigation candidate must not allow Product default")


def _leave_one_false_alarm_validation(
    *,
    rows: list[dict[str, Any]],
    baseline: dict[str, Any],
    l7: dict[str, Any],
) -> dict[str, Any]:
    false_alarm_values = [
        int(case_id.split("_")[-1])
        for case_id in l7["new_false_alarm_case_ids"]
    ]
    trials = []
    for held_out in sorted(false_alarm_values):
        training_values = [value for value in false_alarm_values if value != held_out]
        derived_min = min(training_values)
        derived_max = max(training_values)
        policy = _tage_band_guard(derived_min, derived_max)
        candidate = _evaluate_policy(
            rows,
            policy_id=f"leave-one-hps-TAGE-{held_out}",
            candidate_id=f"leave-one-hps-TAGE-{held_out}",
            candidate_type="leave_one_false_alarm_band_guard",
            margin_policy=policy,
            baseline=baseline,
        )
        held_out_case_id = f"hps_TAGE_{held_out}"
        holdout_removed = held_out_case_id not in candidate["new_false_alarm_case_ids"]
        passes_trial = (
            holdout_removed
            and candidate["false_alarm_rate_delta"] <= 0
            and candidate["precision_delta"] >= 0
            and candidate["recall_delta"] > 0
        )
        trials.append(
            {
                "held_out_false_alarm_case_id": held_out_case_id,
                "derived_guard_min": derived_min,
                "derived_guard_max": derived_max,
                "holdout_false_alarm_removed": holdout_removed,
                "recall_delta": candidate["recall_delta"],
                "false_alarm_rate_delta": candidate["false_alarm_rate_delta"],
                "precision_delta": candidate["precision_delta"],
                "passes_trial": passes_trial,
            }
        )
    pass_count = sum(1 for trial in trials if trial["passes_trial"])
    return {
        "trial_count": len(trials),
        "pass_count": pass_count,
        "pass_rate": _round6(Decimal(pass_count) / Decimal(len(trials))),
        "endpoint_holdout_failure_count": sum(
            1
            for trial in trials
            if not trial["passes_trial"]
            and trial["held_out_false_alarm_case_id"]
            in {"hps_TAGE_58", "hps_TAGE_62"}
        ),
        "required_pass_rate": _round6(REQUIRED_LEAVE_ONE_PASS_RATE),
        "trials": trials,
    }


def _tage_band_guard(
    lower: int,
    upper: int,
) -> Callable[[dict[str, Any]], Decimal]:
    def _policy(row: dict[str, Any]) -> Decimal:
        if row["segment_column"] == "TAGE" and lower <= int(row["segment_value"]) <= upper:
            return CURRENT_ACTIVATION_MARGIN
        return L7_ACTIVATION_MARGIN

    return _policy


def _gain_retained(candidate: dict[str, Any], l7: dict[str, Any]) -> float:
    l7_recovered = set(l7["newly_recovered_case_ids"])
    if not l7_recovered:
        return 0.0
    candidate_recovered = set(candidate["newly_recovered_case_ids"])
    retained_count = len(candidate_recovered & l7_recovered)
    return _round6(Decimal(retained_count) / Decimal(len(l7_recovered)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--hps-ingestion-path", required=True)
    parser.add_argument("--r12-transfer-validation-path", required=True)
    parser.add_argument("--r12-recall-oriented-update-path", required=True)
    parser.add_argument("--r12-recall-false-alarm-mitigation-candidate-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_recall_mitigation_holdout_validation(
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
        r12_recall_false_alarm_mitigation_candidate=load_json_artifact(
            args.r12_recall_false_alarm_mitigation_candidate_path
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
