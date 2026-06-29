from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


POLICY_REACTION_AXIS_WEAKNESS_SCHEMA_VERSION = "policy-reaction-axis-weakness-v1"


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_axis_weakness_artifact(
    benchmarks: list[dict[str, Any]],
    *,
    artifact_id: str,
) -> dict[str, Any]:
    if not benchmarks:
        raise ValueError("axis weakness artifact requires at least one benchmark")

    candidates = []
    aggregate_jsd_by_segment: dict[str, list[float]] = {}
    aggregate_rank_by_segment: dict[str, list[float]] = {}
    aggregate_jsd_by_axis: dict[str, list[float]] = {}
    aggregate_rank_by_axis: dict[str, list[float]] = {}

    for benchmark in benchmarks:
        _validate_benchmark(benchmark)
        segment_metrics = benchmark["segment_metrics"]
        worst_jsd_segment, worst_jsd_metric = max(
            segment_metrics.items(),
            key=lambda item: item[1]["choice_distribution_jsd"],
        )
        worst_rank_segment, worst_rank_metric = min(
            segment_metrics.items(),
            key=lambda item: item[1]["rank_correlation"],
        )
        per_axis = _aggregate_by_axis(segment_metrics)
        candidates.append(
            {
                "artifact_id": benchmark["artifact_id"],
                "prediction_model": benchmark.get("prediction_model"),
                "worst_jsd_segment": worst_jsd_segment,
                "worst_jsd_value": worst_jsd_metric["choice_distribution_jsd"],
                "worst_rank_segment": worst_rank_segment,
                "worst_rank_value": worst_rank_metric["rank_correlation"],
                "per_axis_summary": per_axis,
            }
        )
        for segment_key, metric in segment_metrics.items():
            aggregate_jsd_by_segment.setdefault(segment_key, []).append(
                metric["choice_distribution_jsd"]
            )
            aggregate_rank_by_segment.setdefault(segment_key, []).append(
                metric["rank_correlation"]
            )
            axis = segment_key.partition("=")[0]
            aggregate_jsd_by_axis.setdefault(axis, []).append(
                metric["choice_distribution_jsd"]
            )
            aggregate_rank_by_axis.setdefault(axis, []).append(
                metric["rank_correlation"]
            )

    persistent_worst_jsd_segment = max(
        aggregate_jsd_by_segment.items(),
        key=lambda item: _mean(item[1]),
    )[0]
    persistent_worst_rank_segment = min(
        aggregate_rank_by_segment.items(),
        key=lambda item: _mean(item[1]),
    )[0]
    artifact = {
        "schema_version": POLICY_REACTION_AXIS_WEAKNESS_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "aggregate_axis_summary": {
            axis: {
                "mean_choice_distribution_jsd": _mean(values),
                "mean_rank_correlation": _mean(aggregate_rank_by_axis[axis]),
            }
            for axis, values in sorted(aggregate_jsd_by_axis.items())
        },
        "aggregate_segment_summary": {
            segment: {
                "mean_choice_distribution_jsd": _mean(values),
                "mean_rank_correlation": _mean(aggregate_rank_by_segment[segment]),
            }
            for segment, values in sorted(aggregate_jsd_by_segment.items())
        },
        "persistent_weakness": {
            "worst_jsd_segment": persistent_worst_jsd_segment,
            "worst_jsd_value_mean": _mean(
                aggregate_jsd_by_segment[persistent_worst_jsd_segment]
            ),
            "worst_rank_segment": persistent_worst_rank_segment,
            "worst_rank_value_mean": _mean(
                aggregate_rank_by_segment[persistent_worst_rank_segment]
            ),
        },
        "claim_boundary": (
            "Axis-level weakness artifact is same-task internal diagnostics only; "
            "not generalization proof."
        ),
    }
    json.dumps(artifact, allow_nan=False)
    return artifact


def write_policy_reaction_axis_weakness_artifact(
    path: str | Path,
    *,
    benchmark_paths: list[str | Path],
    artifact_id: str,
) -> Path:
    artifact = build_policy_reaction_axis_weakness_artifact(
        [load_json_artifact(path) for path in benchmark_paths],
        artifact_id=artifact_id,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def _validate_benchmark(benchmark: dict[str, Any]) -> None:
    if benchmark.get("schema_version") != "policy-reaction-axis-benchmark-v1":
        raise ValueError("unsupported axis benchmark schema_version")
    if not isinstance(benchmark.get("segment_metrics"), dict) or not benchmark["segment_metrics"]:
        raise ValueError("axis benchmark missing segment_metrics")


def _aggregate_by_axis(segment_metrics: dict[str, Any]) -> dict[str, dict[str, float]]:
    grouped_jsd: dict[str, list[float]] = {}
    grouped_rank: dict[str, list[float]] = {}
    for segment_key, metric in segment_metrics.items():
        axis = segment_key.partition("=")[0]
        grouped_jsd.setdefault(axis, []).append(metric["choice_distribution_jsd"])
        grouped_rank.setdefault(axis, []).append(metric["rank_correlation"])
    return {
        axis: {
            "mean_choice_distribution_jsd": _mean(grouped_jsd[axis]),
            "mean_rank_correlation": _mean(grouped_rank[axis]),
        }
        for axis in sorted(grouped_jsd)
    }


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("mean requires at least one value")
    return sum(values) / len(values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--benchmark",
        dest="benchmarks",
        action="append",
        required=True,
        help="Path to one axis benchmark artifact. Can be provided multiple times.",
    )
    parser.add_argument("--artifact-id", default="policy-reaction-axis-weakness-current-001")
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-axis-weakness-current-001.json"
        ),
    )
    args = parser.parse_args()
    output_path = write_policy_reaction_axis_weakness_artifact(
        args.output,
        benchmark_paths=args.benchmarks,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {"artifact_id": args.artifact_id, "output": str(output_path), "status": "passed"},
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
