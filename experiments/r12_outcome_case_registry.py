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
from experiments.r11_external_holdout_validation import (
    R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION,
)


R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION = "r12-outcome-case-registry-v1"
TRAIN_CASE_IDS = ["hps_REGION_2", "hps_METRO_STATUS_2"]
VALIDATION_CASE_IDS = ["hps_REGION_1", "hps_METRO_STATUS_1"]
HOLDOUT_CASE_IDS = ["hps_REGION_3", "hps_REGION_4"]


def build_r12_outcome_case_registry(
    *,
    artifact_id: str,
    run_id: str,
    r11_external_holdout_validation: dict[str, Any],
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    _validate_r11_external_holdout(r11_external_holdout_validation)
    raw_cases = r11_external_holdout_validation["external_holdout_cases"]
    cases = [_registry_case(case) for case in raw_cases]
    cases.sort(key=lambda item: (item["split_order"], item["case_id"]))
    for case in cases:
        del case["split_order"]
    report = {
        "schema_version": R12_OUTCOME_CASE_REGISTRY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r12_outcome_case_registry_ready_guarded",
        "claim_level": "outcome_supervised_learning_material_only",
        "case_registry_contract": {
            "source_backed_public_proxy": True,
            "split_strategy": "fixed_hps_segment_split_v1",
            "train_outcome_read_allowed": True,
            "validation_outcome_read_allowed_for_training": False,
            "holdout_outcome_read_allowed_for_training": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "split_summary": _split_summary(cases),
        "leakage_guard": _leakage_guard(cases),
        "cases": cases,
        "acceptance_gates": {
            "case_registry_ready": True,
            "minimum_case_count_present": len(cases) >= 6,
            "train_validation_holdout_split_present": _split_set(cases)
            == {"train", "validation", "holdout"},
            "outcome_leakage_blocked": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "source_refs": [r11_external_holdout_validation["artifact_id"]],
        "blocked_claims": [
            "R12 field validated",
            "R12 Product core method ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "validation or holdout outcome used for training",
            "prompt/persona manual patch as automatic calibration",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_outcome_case_registry(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(output, build_r12_outcome_case_registry(**kwargs))


def _validate_r11_external_holdout(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != R11_EXTERNAL_HOLDOUT_VALIDATION_SCHEMA_VERSION:
        raise ValueError("r11_external_holdout_validation.schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r11_external_holdout_validation.acceptance_gates must be an object")
    if gates.get("field_outcome_validated") is not False:
        raise ValueError("r11 external holdout must not be field validated")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r11 external holdout must not allow runtime default")
    cases = artifact.get("external_holdout_cases")
    if not isinstance(cases, list) or len(cases) < 6:
        raise ValueError("r11 external holdout must contain at least 6 cases")


def _registry_case(case: dict[str, Any]) -> dict[str, Any]:
    case_id = non_empty_string(case.get("case_id"), field="case.case_id")
    split, learning_role, order = _split(case_id)
    observed = round(float(case["holdout_outcome_proxy"]), 6)
    interaction = round(float(case["r11_prediction"]), 6)
    static_prior = round(float(case["static_prior_prediction"]), 6)
    return {
        "case_id": case_id,
        "split": split,
        "split_order": order,
        "learning_role": learning_role,
        "scenario_shock": "hps_price_pressure_proxy",
        "segment_labels": {
            "segment_column": case["segment_column"],
            "segment_value": str(case["segment_value"]),
        },
        "mechanism_labels": ["price_pressure"],
        "source_signal": {
            "name": "PRICECONCERN",
            "risk_share": round(float(case["source_signal_risk_share"]), 6),
            "delta": round(float(case["source_signal_delta"]), 6),
        },
        "outcome_proxy": {
            "name": "PRICESTRESS",
            "observed_value": observed,
            "observed_high_risk": bool(case["observed_high_risk"]),
        },
        "prediction_state": {
            "static_prior_prediction": static_prior,
            "interaction_prediction": interaction,
            "residual_vs_interaction": round(observed - interaction, 6),
            "residual_vs_static_prior": round(observed - static_prior, 6),
        },
        "risk_interval": case["risk_interval"],
        "guard_flags": {
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
            "eligible_for_runtime_update": False,
        },
    }


def _split(case_id: str) -> tuple[str, str, int]:
    if case_id in TRAIN_CASE_IDS:
        return "train", "train_outcome_supervision", 0
    if case_id in VALIDATION_CASE_IDS:
        return "validation", "validation_transfer_check", 1
    if case_id in HOLDOUT_CASE_IDS:
        return "holdout", "holdout_transfer_check", 2
    raise ValueError(f"case id is not assigned to an R12 split: {case_id}")


def _split_summary(cases: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "case_count": len(cases),
        "train_count": sum(1 for case in cases if case["split"] == "train"),
        "validation_count": sum(1 for case in cases if case["split"] == "validation"),
        "holdout_count": sum(1 for case in cases if case["split"] == "holdout"),
        "observed_high_risk_train_count": sum(
            1
            for case in cases
            if case["split"] == "train" and case["outcome_proxy"]["observed_high_risk"]
        ),
        "observed_high_risk_validation_count": sum(
            1
            for case in cases
            if case["split"] == "validation" and case["outcome_proxy"]["observed_high_risk"]
        ),
        "observed_high_risk_holdout_count": sum(
            1
            for case in cases
            if case["split"] == "holdout" and case["outcome_proxy"]["observed_high_risk"]
        ),
    }


def _leakage_guard(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "train_case_ids_with_observed_outcome_available": sorted(
            case["case_id"] for case in cases if case["split"] == "train"
        ),
        "validation_case_ids_blocked_for_training": sorted(
            case["case_id"] for case in cases if case["split"] == "validation"
        ),
        "holdout_case_ids_blocked_for_training": sorted(
            case["case_id"] for case in cases if case["split"] == "holdout"
        ),
        "outcome_leakage_blocked": True,
    }


def _split_set(cases: list[dict[str, Any]]) -> set[str]:
    return {case["split"] for case in cases}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--r11-external-holdout-validation-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_outcome_case_registry(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r11_external_holdout_validation=load_json_artifact(
            args.r11_external_holdout_validation_path
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
