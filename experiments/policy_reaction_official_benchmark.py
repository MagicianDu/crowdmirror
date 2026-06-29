from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


POLICY_REACTION_OFFICIAL_SEGMENT_BENCHMARK_SCHEMA_VERSION = (
    "policy-reaction-official-segment-benchmark-v1"
)
POLICY_REACTION_SEGMENT_PREDICTIONS_SCHEMA_VERSION = (
    "policy-reaction-segment-predictions-v1"
)
POLICY_REACTION_OFFICIAL_SEGMENT_BENCHMARK_CLAIM_BOUNDARY = (
    "Official public-use segment alignment smoke benchmark only; not field validation."
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_official_segment_benchmark(
    ingestion_artifact: dict[str, Any],
    prediction_artifact: dict[str, Any],
    *,
    artifact_id: str,
) -> dict[str, Any]:
    _validate_ingestion_artifact(ingestion_artifact)
    _validate_prediction_artifact(prediction_artifact)

    observed_by_segment = ingestion_artifact["observed_policy_reaction_summary"][
        "by_segment"
    ]
    predictions_by_segment = prediction_artifact["segment_predictions"]
    observed_segments = sorted(observed_by_segment)
    predicted_segments = sorted(predictions_by_segment)
    matched_segments = sorted(set(observed_segments) & set(predicted_segments))
    missing_predicted_segments = sorted(set(observed_segments) - set(predicted_segments))
    extra_predicted_segments = sorted(set(predicted_segments) - set(observed_segments))

    segment_metrics = {
        segment: _segment_metric(
            segment,
            observed_by_segment[segment],
            predictions_by_segment[segment],
        )
        for segment in matched_segments
    }
    coverage = {
        "observed_segment_count": len(observed_segments),
        "predicted_segment_count": len(predicted_segments),
        "matched_segment_count": len(matched_segments),
        "coverage_rate": (
            len(matched_segments) / len(observed_segments) if observed_segments else 0.0
        ),
        "missing_predicted_segments": missing_predicted_segments,
        "extra_predicted_segments": extra_predicted_segments,
    }
    overall_status = (
        "passed"
        if ingestion_artifact["overall_status"] == "passed"
        and not missing_predicted_segments
        and segment_metrics
        else "blocked_for_model_quality_claim"
    )
    artifact = {
        "schema_version": POLICY_REACTION_OFFICIAL_SEGMENT_BENCHMARK_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": overall_status,
        "calibration_status": "official_public_data_alignment_smoke",
        "source_ingestion_artifact_id": ingestion_artifact["artifact_id"],
        "prediction_artifact_id": prediction_artifact["artifact_id"],
        "prediction_model": prediction_artifact.get("model"),
        "segment_coverage": coverage,
        "benchmark_metrics": _benchmark_metrics(segment_metrics),
        "segment_metrics": segment_metrics,
        "claim_boundary": POLICY_REACTION_OFFICIAL_SEGMENT_BENCHMARK_CLAIM_BOUNDARY,
        "claim_boundaries": [
            POLICY_REACTION_OFFICIAL_SEGMENT_BENCHMARK_CLAIM_BOUNDARY,
            "The official side is an observed distribution proxy derived from "
            "public-use HTOPS/HPS survey fields.",
            "The prediction side must come from a separately auditable LLM cohort "
            "or product segment report.",
            "This artifact does not establish causal policy effects or China "
            "policy forecast validity.",
        ],
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_official_segment_benchmark(
    path: str | Path,
    *,
    ingestion_artifact_path: str | Path,
    predictions_artifact_path: str | Path,
    artifact_id: str,
) -> Path:
    ingestion_artifact = load_json_artifact(ingestion_artifact_path)
    prediction_artifact = load_json_artifact(predictions_artifact_path)
    artifact = build_policy_reaction_official_segment_benchmark(
        ingestion_artifact,
        prediction_artifact,
        artifact_id=artifact_id,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ingestion-artifact",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-htops-2506-public-ingestion-001.json"
        ),
    )
    parser.add_argument(
        "--predictions-artifact",
        default="benchmarks/fixtures/policy_reaction_segment_predictions_smoke.json",
    )
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-official-segment-benchmark-smoke-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-official-segment-benchmark-smoke-001.json"
        ),
    )
    args = parser.parse_args()
    output_path = write_policy_reaction_official_segment_benchmark(
        args.output,
        ingestion_artifact_path=args.ingestion_artifact,
        predictions_artifact_path=args.predictions_artifact,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "output": str(output_path),
                "status": "passed",
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_ingestion_artifact(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != "policy-reaction-public-data-ingestion-v1":
        raise ValueError("unsupported ingestion artifact schema_version")
    if not isinstance(
        artifact.get("observed_policy_reaction_summary", {}).get("by_segment"),
        dict,
    ):
        raise ValueError("ingestion artifact missing observed by_segment summary")


def _validate_prediction_artifact(artifact: dict[str, Any]) -> None:
    if artifact.get("schema_version") != POLICY_REACTION_SEGMENT_PREDICTIONS_SCHEMA_VERSION:
        raise ValueError("unsupported prediction artifact schema_version")
    if not isinstance(artifact.get("segment_predictions"), dict):
        raise ValueError("prediction artifact missing segment_predictions")


def _segment_metric(
    segment: str,
    observed_summary: dict[str, Any],
    prediction_summary: dict[str, Any],
) -> dict[str, Any]:
    observed = _policy_distribution(
        observed_summary["weighted_mean_policy_reaction"],
        f"{segment}.weighted_mean_policy_reaction",
    )
    predicted = _policy_distribution(
        _prediction_distribution(prediction_summary),
        f"{segment}.policy_probabilities",
    )
    return {
        "official_row_count": observed_summary["row_count"],
        "official_weighted_row_mass": observed_summary["weighted_row_mass"],
        "official_distribution": observed,
        "predicted_distribution": predicted,
        "choice_distribution_jsd": _jsd(observed, predicted),
        "rank_correlation": _rank_correlation(observed, predicted),
    }


def _prediction_distribution(prediction_summary: dict[str, Any]) -> dict[str, Any]:
    for field_name in (
        "policy_probabilities",
        "mean_policy_reaction",
        "weighted_mean_policy_reaction",
    ):
        value = prediction_summary.get(field_name)
        if isinstance(value, dict):
            return value
    raise ValueError("prediction segment missing policy distribution")


def _benchmark_metrics(segment_metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not segment_metrics:
        return {
            "matched_segment_count": 0,
            "weighted_choice_distribution_jsd": None,
            "mean_choice_distribution_jsd": None,
            "worst_segment_choice_distribution_jsd": None,
            "segment_rank_correlation": None,
            "worst_segment_rank_correlation": None,
        }
    weighted_mass = sum(
        metric["official_row_count"] for metric in segment_metrics.values()
    )
    jsd_values = [
        metric["choice_distribution_jsd"] for metric in segment_metrics.values()
    ]
    rank_values = [metric["rank_correlation"] for metric in segment_metrics.values()]
    return {
        "matched_segment_count": len(segment_metrics),
        "weighted_choice_distribution_jsd": sum(
            metric["choice_distribution_jsd"] * metric["official_row_count"]
            for metric in segment_metrics.values()
        )
        / weighted_mass,
        "mean_choice_distribution_jsd": _mean(jsd_values),
        "worst_segment_choice_distribution_jsd": max(jsd_values),
        "segment_rank_correlation": _mean(rank_values),
        "worst_segment_rank_correlation": min(rank_values),
    }


def _policy_distribution(raw: dict[str, Any], context: str) -> dict[str, float]:
    if not raw:
        raise ValueError(f"{context} must be non-empty")
    values = {}
    for policy_id, value in raw.items():
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError(f"{context} probabilities must be numeric")
        probability = float(value)
        if not math.isfinite(probability) or probability < 0:
            raise ValueError(f"{context} probabilities must be finite and non-negative")
        values[str(policy_id)] = probability
    total = sum(values.values())
    if total <= 0:
        raise ValueError(f"{context} must have positive probability mass")
    return {policy_id: probability / total for policy_id, probability in values.items()}


def _jsd(observed: dict[str, float], predicted: dict[str, float]) -> float:
    policies = sorted(set(observed) | set(predicted))
    midpoint = {
        policy: (observed.get(policy, 0.0) + predicted.get(policy, 0.0)) / 2
        for policy in policies
    }
    return (_kl(observed, midpoint, policies) + _kl(predicted, midpoint, policies)) / 2


def _kl(
    distribution: dict[str, float],
    reference: dict[str, float],
    policies: list[str],
) -> float:
    divergence = 0.0
    for policy in policies:
        probability = distribution.get(policy, 0.0)
        if probability == 0:
            continue
        divergence += probability * math.log2(probability / reference[policy])
    return divergence


def _rank_correlation(observed: dict[str, float], predicted: dict[str, float]) -> float:
    policies = sorted(set(observed) | set(predicted))
    observed_ranks = _ranks([observed.get(policy, 0.0) for policy in policies])
    predicted_ranks = _ranks([predicted.get(policy, 0.0) for policy in policies])
    return _pearson(observed_ranks, predicted_ranks)


def _ranks(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0 for _ in values]
    position = 0
    while position < len(ordered):
        end = position + 1
        while end < len(ordered) and ordered[end][1] == ordered[position][1]:
            end += 1
        average_rank = (position + 1 + end) / 2
        for index, _ in ordered[position:end]:
            ranks[index] = average_rank
        position = end
    return ranks


def _pearson(left: list[float], right: list[float]) -> float:
    left_mean = _mean(left)
    right_mean = _mean(right)
    numerator = sum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left, right)
    )
    left_variance = sum((value - left_mean) ** 2 for value in left)
    right_variance = sum((value - right_mean) ** 2 for value in right)
    denominator = math.sqrt(left_variance * right_variance)
    if denominator == 0:
        return 1.0 if left == right else 0.0
    return numerator / denominator


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("mean requires at least one value")
    return sum(values) / len(values)


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
