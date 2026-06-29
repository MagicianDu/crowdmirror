from __future__ import annotations

import argparse
import csv
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
from experiments.r12_customer_field_slice_intake_validation import (
    R12_CUSTOMER_FIELD_SLICE_INTAKE_VALIDATION_SCHEMA_VERSION,
)


R12_CUSTOMER_FIELD_SLICE_REVALIDATION_SCHEMA_VERSION = (
    "r12-customer-field-slice-revalidation-v1"
)
DEFAULT_MAE_THRESHOLD = 0.05
DEFAULT_RISK_RANKING_QUALITY_THRESHOLD = 0.8


def build_r12_customer_field_slice_revalidation(
    *,
    artifact_id: str,
    run_id: str,
    r12_customer_field_slice_intake_validation: dict[str, Any],
    revalidation_checked_at: str,
    mae_threshold: float = DEFAULT_MAE_THRESHOLD,
    risk_ranking_quality_threshold: float = DEFAULT_RISK_RANKING_QUALITY_THRESHOLD,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    revalidation_checked_at = non_empty_string(
        revalidation_checked_at,
        field="revalidation_checked_at",
    )
    _validate_l22_intake(r12_customer_field_slice_intake_validation)

    intake = r12_customer_field_slice_intake_validation
    intake_gates = intake["acceptance_gates"]
    intake_summary = intake["intake_summary"]
    if intake_gates["ready_for_revalidation"] is True:
        rows = _read_customer_field_slice(Path(intake_summary["slice_path"]))
        metric_results = _metric_results(
            rows=rows,
            mae_threshold=mae_threshold,
            risk_ranking_quality_threshold=risk_ranking_quality_threshold,
        )
        metrics_computed = True
        mae_passed = metric_results["mean_absolute_error"] <= mae_threshold
        ranking_passed = (
            metric_results["risk_ranking_quality"]
            >= risk_ranking_quality_threshold
        )
        field_outcome_validated = mae_passed and ranking_passed
        status = "r12_customer_field_slice_revalidation_metrics_ready_guarded"
        claim_level = "customer_field_revalidation_metrics_ready_no_product_default"
        acceptance_decision = (
            "accept_customer_field_revalidation_metrics_keep_product_default_blocked"
        )
        allowed_claims = [
            (
                "Customer field slice revalidation metrics were computed from "
                "validated intake."
            ),
            (
                "Passing field metrics may be reviewed as customer outcome "
                "evidence, but Product default remains blocked."
            ),
        ]
    else:
        rows = []
        metric_results = {}
        metrics_computed = False
        mae_passed = False
        ranking_passed = False
        field_outcome_validated = False
        status = "r12_customer_field_slice_revalidation_blocked_no_validated_intake"
        claim_level = "customer_field_revalidation_blocked"
        acceptance_decision = "reject_customer_field_revalidation_no_validated_intake"
        allowed_claims = [
            (
                "Customer field slice revalidation harness is ready, but no "
                "validated intake is available."
            )
        ]

    report = {
        "schema_version": R12_CUSTOMER_FIELD_SLICE_REVALIDATION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": status,
        "claim_level": claim_level,
        "revalidation_summary": {
            "intake_artifact_id": intake["artifact_id"],
            "revalidation_checked_at": revalidation_checked_at,
            "slice_path": intake_summary["slice_path"],
            "case_count": len(rows),
            "metrics_computed": metrics_computed,
            "field_outcome_validated": field_outcome_validated,
        },
        "metric_results": metric_results,
        "acceptance_gates": {
            "validated_intake_ready": intake_gates["ready_for_revalidation"],
            "customer_field_slice_present": bool(rows),
            "metrics_computed": metrics_computed,
            "mae_threshold_passed": mae_passed,
            "risk_ranking_quality_threshold_passed": ranking_passed,
            "field_outcome_validated": field_outcome_validated,
            "product_default_allowed": False,
            "runtime_default_allowed": False,
        },
        "acceptance_decision": acceptance_decision,
        "next_required_artifact": (
            "r12_customer_field_outcome_feedback_update"
            if field_outcome_validated
            else "validated_customer_field_slice_intake"
        ),
        "source_refs": [
            intake["artifact_id"],
            *(
                [f"customer_field_slice:{intake_summary['slice_path']}"]
                if intake_summary["slice_path"]
                else []
            ),
        ],
        "source_registry": [
            {
                "artifact_id": intake["artifact_id"],
                "path": (
                    "experiments/results/"
                    "r12_customer_field_slice_intake_validation/"
                    "r12-customer-field-slice-intake-validation-current-001.json"
                ),
            },
            *(
                [
                    {
                        "artifact_id": (
                            f"customer_field_slice:{intake_summary['slice_path']}"
                        ),
                        "path": intake_summary["slice_path"],
                    }
                ]
                if intake_summary["slice_path"]
                else []
            ),
        ],
        "allowed_claims": allowed_claims,
        "blocked_claims": [
            *(
                ["metrics_computed=true"]
                if metrics_computed is False
                else []
            ),
            *(
                ["field_outcome_validated=true"]
                if field_outcome_validated is False
                else []
            ),
            "Product default can use customer field validation by default",
            "runtime_default_allowed=true",
            "精准预测系统",
        ],
    }
    assert_strict_json(report)
    return report


def write_r12_customer_field_slice_revalidation(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r12_customer_field_slice_revalidation(**kwargs),
    )


def _validate_l22_intake(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != (
        R12_CUSTOMER_FIELD_SLICE_INTAKE_VALIDATION_SCHEMA_VERSION
    ):
        raise ValueError("r12 L22 intake schema_version is invalid")
    gates = artifact.get("acceptance_gates")
    if not isinstance(gates, dict):
        raise ValueError("r12 L22 intake acceptance_gates required")
    if gates.get("metrics_computed") is not False:
        raise ValueError("r12 L22 intake must not compute metrics")
    if gates.get("product_default_allowed") is not False:
        raise ValueError("r12 L22 intake must block Product default")
    if gates.get("runtime_default_allowed") is not False:
        raise ValueError("r12 L22 intake must block runtime default")


def _read_customer_field_slice(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".csv":
        with path.open(newline="") as fh:
            return [dict(row) for row in csv.DictReader(fh)]
    if path.suffix == ".jsonl":
        rows = []
        for line in path.read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows
    raise ValueError("customer field slice must be csv or jsonl")


def _metric_results(
    *,
    rows: list[dict[str, Any]],
    mae_threshold: float,
    risk_ranking_quality_threshold: float,
) -> dict[str, float]:
    predictions = [float(row["prediction_share_or_score"]) for row in rows]
    observed = [float(row["observed_outcome"]) for row in rows]
    errors = [prediction - outcome for prediction, outcome in zip(predictions, observed)]
    absolute_errors = [abs(error) for error in errors]
    return {
        "mean_absolute_error": _round(sum(absolute_errors) / len(absolute_errors)),
        "mean_signed_error": _round(sum(errors) / len(errors)),
        "risk_ranking_quality": _round(
            _pairwise_ranking_quality(predictions, observed)
        ),
        "top_quintile_overlap": _round(_top_quintile_overlap(predictions, observed)),
        "mae_threshold": _round(mae_threshold),
        "risk_ranking_quality_threshold": _round(risk_ranking_quality_threshold),
    }


def _pairwise_ranking_quality(predictions: list[float], observed: list[float]) -> float:
    concordant = 0
    comparable = 0
    for left in range(len(predictions)):
        for right in range(left + 1, len(predictions)):
            predicted_delta = predictions[left] - predictions[right]
            observed_delta = observed[left] - observed[right]
            if predicted_delta == 0 or observed_delta == 0:
                continue
            comparable += 1
            if predicted_delta * observed_delta > 0:
                concordant += 1
    if comparable == 0:
        return 0.0
    return concordant / comparable


def _top_quintile_overlap(predictions: list[float], observed: list[float]) -> float:
    if not predictions:
        return 0.0
    top_k = max(1, round(len(predictions) * 0.2))
    predicted_top = set(_top_indices(predictions, top_k))
    observed_top = set(_top_indices(observed, top_k))
    return len(predicted_top & observed_top) / top_k


def _top_indices(values: list[float], top_k: int) -> list[int]:
    return [
        index
        for index, _value in sorted(
            enumerate(values),
            key=lambda item: item[1],
            reverse=True,
        )[:top_k]
    ]


def _round(value: float) -> float:
    return round(value, 6)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--r12-customer-field-slice-intake-validation-path",
        required=True,
    )
    parser.add_argument("--revalidation-checked-at", required=True)
    parser.add_argument("--mae-threshold", type=float, default=DEFAULT_MAE_THRESHOLD)
    parser.add_argument(
        "--risk-ranking-quality-threshold",
        type=float,
        default=DEFAULT_RISK_RANKING_QUALITY_THRESHOLD,
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r12_customer_field_slice_revalidation(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
        r12_customer_field_slice_intake_validation=load_json_artifact(
            args.r12_customer_field_slice_intake_validation_path
        ),
        revalidation_checked_at=args.revalidation_checked_at,
        mae_threshold=args.mae_threshold,
        risk_ranking_quality_threshold=args.risk_ranking_quality_threshold,
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "field_outcome_validated": artifact["acceptance_gates"][
                    "field_outcome_validated"
                ],
                "metrics_computed": artifact["acceptance_gates"][
                    "metrics_computed"
                ],
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
