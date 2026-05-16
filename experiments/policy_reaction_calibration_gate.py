from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


POLICY_REACTION_CALIBRATION_GATE_SCHEMA_VERSION = (
    "policy-reaction-calibration-gate-v1"
)
DEFAULT_LOSS_METRIC = "weighted_choice_distribution_jsd"
CALIBRATION_UPDATE_POLICY = (
    "accept_if_weighted_jsd_decreases_and_segment_coverage_is_complete"
)
POLICY_REACTION_CALIBRATION_GATE_CLAIM_BOUNDARY = (
    "Acceptance-gated policy-reaction calibration evidence only; not field validation."
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_calibration_gate(
    initial_benchmark: dict[str, Any],
    candidate_benchmarks: list[dict[str, Any]],
    *,
    artifact_id: str,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> dict[str, Any]:
    initial_loss = _benchmark_loss(initial_benchmark, loss_metric)
    best_loss = initial_loss
    best_artifact_id = _artifact_id(initial_benchmark)
    candidate_updates = []

    for index, candidate in enumerate(candidate_benchmarks):
        candidate_loss = _benchmark_loss(candidate, loss_metric)
        coverage_rate = _coverage_rate(candidate)
        best_loss_before = best_loss
        status = "rejected"
        reason = "loss_not_improved"
        if not _benchmark_passed(candidate):
            reason = "benchmark_not_passed"
        elif coverage_rate < 1.0:
            reason = "segment_coverage_incomplete"
        elif candidate_loss < best_loss:
            status = "accepted"
            reason = "loss_improved"
            best_loss = candidate_loss
            best_artifact_id = _artifact_id(candidate)

        candidate_updates.append(
            {
                "candidate_index": index,
                "benchmark_artifact_id": _artifact_id(candidate),
                "prediction_artifact_id": candidate.get("prediction_artifact_id"),
                "loss": candidate_loss,
                "best_loss_before": best_loss_before,
                "best_loss_after": best_loss,
                "loss_delta_from_best": candidate_loss - best_loss_before,
                "coverage_rate": coverage_rate,
                "status": status,
                "reason": reason,
                "benchmark_metrics": candidate.get("benchmark_metrics", {}),
            }
        )

    accepted_count = sum(
        1 for update in candidate_updates if update["status"] == "accepted"
    )
    rejected_count = sum(
        1 for update in candidate_updates if update["status"] == "rejected"
    )
    artifact = {
        "schema_version": POLICY_REACTION_CALIBRATION_GATE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "accepted" if accepted_count else "rejected",
        "candidate_update_policy": CALIBRATION_UPDATE_POLICY,
        "loss_metric": loss_metric,
        "initial_benchmark_artifact_id": _artifact_id(initial_benchmark),
        "initial_prediction_artifact_id": initial_benchmark.get(
            "prediction_artifact_id"
        ),
        "initial_loss": initial_loss,
        "best_benchmark_artifact_id": best_artifact_id,
        "best_loss": best_loss,
        "final_benchmark_artifact_id": best_artifact_id,
        "final_loss": best_loss,
        "candidate_evaluated_count": len(candidate_updates),
        "candidate_accepted_count": accepted_count,
        "candidate_rejected_count": rejected_count,
        "candidate_pending_count": 0,
        "candidate_updates": candidate_updates,
        "claim_boundary": POLICY_REACTION_CALIBRATION_GATE_CLAIM_BOUNDARY,
        "claim_boundaries": [
            POLICY_REACTION_CALIBRATION_GATE_CLAIM_BOUNDARY,
            "Candidates are accepted only when official-data alignment loss improves "
            "and segment coverage is complete.",
            "Accepted candidates remain local Product cohort evidence until repeated "
            "across seeds, scales, and model configurations.",
        ],
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_calibration_gate(
    path: str | Path,
    *,
    initial_benchmark_path: str | Path,
    candidate_benchmark_paths: list[str | Path],
    artifact_id: str,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> Path:
    initial_benchmark = load_json_artifact(initial_benchmark_path)
    candidate_benchmarks = [
        load_json_artifact(candidate_path)
        for candidate_path in candidate_benchmark_paths
    ]
    artifact = build_policy_reaction_calibration_gate(
        initial_benchmark,
        candidate_benchmarks,
        artifact_id=artifact_id,
        loss_metric=loss_metric,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--initial-benchmark", required=True)
    parser.add_argument(
        "--candidate-benchmark",
        action="append",
        default=[],
        help="Candidate official segment benchmark artifact. Repeat for multiple candidates.",
    )
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-calibration-gate-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-calibration-gate-001.json"
        ),
    )
    parser.add_argument("--loss-metric", default=DEFAULT_LOSS_METRIC)
    args = parser.parse_args()
    output_path = write_policy_reaction_calibration_gate(
        args.output,
        initial_benchmark_path=args.initial_benchmark,
        candidate_benchmark_paths=args.candidate_benchmark,
        artifact_id=args.artifact_id,
        loss_metric=args.loss_metric,
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


def _artifact_id(artifact: dict[str, Any]) -> str:
    artifact_id = artifact.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        raise ValueError("benchmark artifact missing artifact_id")
    return artifact_id


def _benchmark_loss(artifact: dict[str, Any], loss_metric: str) -> float:
    metrics = artifact.get("benchmark_metrics")
    if not isinstance(metrics, dict):
        raise ValueError("benchmark artifact missing benchmark_metrics")
    value = metrics.get(loss_metric)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"benchmark artifact missing numeric {loss_metric}")
    return float(value)


def _coverage_rate(artifact: dict[str, Any]) -> float:
    coverage = artifact.get("segment_coverage", {})
    value = coverage.get("coverage_rate")
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0.0
    return float(value)


def _benchmark_passed(artifact: dict[str, Any]) -> bool:
    return artifact.get("overall_status") == "passed"


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
