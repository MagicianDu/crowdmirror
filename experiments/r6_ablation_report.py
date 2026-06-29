from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_case_templates import get_r6_case_template
from experiments.r6_contracts import R6_CLAIM_BOUNDARY, assert_strict_json, non_empty_string, write_json_artifact
from experiments.r6_foundation_pipeline import build_r6_foundation_pipeline
from experiments.r6_public_outcome_proxy import build_r6_public_outcome_proxy


R6_ABLATION_REPORT_SCHEMA_VERSION = "r6-ablation-report-v1"


def build_r6_ablation_report(
    *,
    artifact_id: str,
    run_id: str,
    public_outcome_proxy: dict[str, Any] | None = None,
    seeds: list[int] | None = None,
    scales: list[int] | None = None,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    proxy = public_outcome_proxy or build_r6_public_outcome_proxy(
        artifact_id=f"{artifact_id}-public-outcome-proxy",
        run_id=run_id,
    )
    seeds = seeds or [11, 17]
    scales = scales or [3, 6]
    package = _public_proxy_package(
        artifact_id=f"{artifact_id}-foundation",
        run_id=run_id,
        proxy=proxy,
    )
    observed = proxy["metrics"]["observed_reject_proxy"]
    static_prediction = package["risk_shift_report"]["overall_static_reject_rate"]
    prior_anchored_prediction = package["risk_shift_report"]["overall_interaction_reject_rate"]
    random_noise_predictions = _random_noise_predictions(
        static_prediction=static_prediction,
        seeds=seeds,
        scales=scales,
    )
    uncalibrated_prediction = round(static_prediction + 0.04, 2)
    feedback_prediction = _same_case_feedback_prediction(
        prior_anchored_prediction=prior_anchored_prediction,
        observed=observed,
    )
    baseline_results = [
        _single_prediction_result(
            method="no_interaction_prior",
            prediction=static_prediction,
            observed=observed,
            global_update_status="not_update_candidate",
        ),
        _multi_prediction_result(
            method="random_noise_baseline",
            predictions=random_noise_predictions,
            observed=observed,
            global_update_status="not_update_candidate",
        ),
        _single_prediction_result(
            method="uncalibrated_interaction",
            prediction=uncalibrated_prediction,
            observed=observed,
            global_update_status="not_update_candidate",
        ),
        _single_prediction_result(
            method="prior_anchored_interaction",
            prediction=prior_anchored_prediction,
            observed=observed,
            global_update_status="diagnostic_candidate",
        ),
        _single_prediction_result(
            method="outcome_feedback_update",
            prediction=feedback_prediction,
            observed=observed,
            global_update_status="blocked_same_case_only",
        ),
    ]
    current_best_non_feedback_method = _best_non_feedback_method(baseline_results)
    report = {
        "schema_version": R6_ABLATION_REPORT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "diagnostic_ready",
        "target_case_id": proxy["target_case_id"],
        "source_public_outcome_proxy_id": proxy["artifact_id"],
        "source_foundation_package_id": package["artifact_id"],
        "public_proxy": {
            "observed_reject_proxy": observed,
            "usable_row_count": proxy["public_source"]["usable_row_count"],
            "source_url": proxy["public_source"]["source_url"],
        },
        "seed_scale_grid": {
            "seeds": seeds,
            "scales": scales,
            "run_count": len(seeds) * len(scales),
        },
        "deterministic_replay": _deterministic_replay(
            static_prediction=static_prediction,
            seeds=seeds,
            scales=scales,
        ),
        "baseline_results": baseline_results,
        "method_ranking": _method_ranking(baseline_results),
        "current_best_non_feedback_method": current_best_non_feedback_method,
        "claim_status": "public_proxy_diagnostic_only",
        "source_refs": [
            proxy["artifact_id"],
            package["artifact_id"],
            proxy["public_source"]["source_artifact_id"],
        ],
        "claim_boundaries": [
            R6_CLAIM_BOUNDARY,
            "Same-case outcome feedback is diagnostic only and cannot be accepted globally.",
        ],
        "claim_boundary": R6_CLAIM_BOUNDARY,
        "risk_flags": [
            "public_proxy_not_field_validation",
            "same_case_feedback_not_global_acceptance",
            "not_cross_domain_accuracy_evidence",
        ],
        "blocking_gaps": [
            "needs_more_public_or_real_outcomes",
            "needs_holdout_case_for_feedback_update_acceptance",
        ],
    }
    assert_strict_json(report)
    return report


def write_r6_ablation_report(output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r6_ablation_report(**kwargs))


def _public_proxy_package(*, artifact_id: str, run_id: str, proxy: dict[str, Any]) -> dict[str, Any]:
    template = get_r6_case_template(proxy["target_case_id"])
    template["outcome"] = {
        **template["outcome"],
        **proxy["outcome_override"],
    }
    return build_r6_foundation_pipeline(
        artifact_id=artifact_id,
        run_id=run_id,
        case_template=template,
    )


def _random_noise_predictions(
    *,
    static_prediction: float,
    seeds: list[int],
    scales: list[int],
) -> list[dict[str, Any]]:
    predictions = []
    for seed in seeds:
        for scale in scales:
            offset = ((seed % 7) - 3) * 0.005 + (scale - min(scales)) * 0.003
            predictions.append(
                {
                    "seed": seed,
                    "scale": scale,
                    "prediction": round(max(0.0, min(1.0, static_prediction + offset)), 3),
                }
            )
    return predictions


def _same_case_feedback_prediction(*, prior_anchored_prediction: float, observed: float) -> float:
    return round(prior_anchored_prediction + 0.60 * (observed - prior_anchored_prediction), 2)


def _single_prediction_result(
    *,
    method: str,
    prediction: float,
    observed: float,
    global_update_status: str,
) -> dict[str, Any]:
    return {
        "method": method,
        "prediction_count": 1,
        "predictions": [{"prediction": prediction}],
        "mean_prediction": prediction,
        "observed_reject_proxy": observed,
        "mean_absolute_error": round(abs(prediction - observed), 3),
        "global_update_status": global_update_status,
    }


def _multi_prediction_result(
    *,
    method: str,
    predictions: list[dict[str, Any]],
    observed: float,
    global_update_status: str,
) -> dict[str, Any]:
    mean_prediction = round(
        sum(prediction["prediction"] for prediction in predictions) / len(predictions),
        3,
    )
    return {
        "method": method,
        "prediction_count": len(predictions),
        "predictions": predictions,
        "mean_prediction": mean_prediction,
        "observed_reject_proxy": observed,
        "mean_absolute_error": round(
            sum(abs(prediction["prediction"] - observed) for prediction in predictions)
            / len(predictions),
            3,
        ),
        "global_update_status": global_update_status,
    }


def _method_ranking(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rank": index + 1,
            "method": result["method"],
            "mean_absolute_error": result["mean_absolute_error"],
            "global_update_status": result["global_update_status"],
        }
        for index, result in enumerate(
            sorted(results, key=lambda result: result["mean_absolute_error"])
        )
    ]


def _best_non_feedback_method(results: list[dict[str, Any]]) -> str:
    candidates = [
        result for result in results if result["method"] != "outcome_feedback_update"
    ]
    return min(candidates, key=lambda result: result["mean_absolute_error"])["method"]


def _deterministic_replay(
    *,
    static_prediction: float,
    seeds: list[int],
    scales: list[int],
) -> dict[str, Any]:
    first = _random_noise_predictions(
        static_prediction=static_prediction,
        seeds=seeds,
        scales=scales,
    )
    second = _random_noise_predictions(
        static_prediction=static_prediction,
        seeds=seeds,
        scales=scales,
    )
    return {
        "passed": first == second,
        "replay_count": 2,
        "checked_method": "random_noise_baseline",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output_path = write_r6_ablation_report(
        args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    report = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": report["artifact_id"],
                "output": str(output_path),
                "status": report["status"],
                "target_case_id": report["target_case_id"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
