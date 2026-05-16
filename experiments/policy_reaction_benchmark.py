from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmarks.policy_reaction import (
    build_policy_reaction_records_from_hps_rows,
    compute_policy_reaction_metrics,
    load_hps_public_rows,
    load_policy_reaction_records,
)


POLICY_REACTION_BENCHMARK_SCHEMA_VERSION = "policy-reaction-benchmark-v0"
POLICY_REACTION_BENCHMARK_CLAIM_BOUNDARY = (
    "Policy-reaction public-data smoke benchmark only; not field validation."
)


def build_policy_reaction_benchmark_artifact(
    records: list[dict[str, Any]],
    *,
    artifact_id: str,
    source_manifest_path: str,
) -> dict[str, Any]:
    metrics = compute_policy_reaction_metrics(records)
    row_boundary = _benchmark_row_boundary(metrics["provenance"])
    artifact = {
        "schema_version": POLICY_REACTION_BENCHMARK_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "passed",
        "calibration_status": "public_data_smoke",
        "source_manifest_path": source_manifest_path,
        "benchmark_data": {
            "record_count": metrics["record_count"],
            "source_ids": metrics["source_ids"],
            "provenance": metrics["provenance"],
        },
        "benchmark_metrics": {
            "choice_distribution_jsd": metrics["choice_distribution_jsd"],
            "choice_distribution_jsd_record_count": metrics[
                "choice_distribution_jsd_record_count"
            ],
            "ate_direction_accuracy": metrics["ate_direction_accuracy"],
            "ate_direction_counts": metrics["ate_direction_counts"],
            "segment_count": metrics["segment_count"],
            "segment_rank_correlation": metrics["segment_rank_correlation"],
            "worst_segment_rank_correlation": metrics[
                "worst_segment_rank_correlation"
            ],
            "segment_rank_correlation_by_segment": metrics[
                "segment_rank_correlation_by_segment"
            ],
        },
        "claim_boundary": POLICY_REACTION_BENCHMARK_CLAIM_BOUNDARY,
        "claim_boundaries": [
            POLICY_REACTION_BENCHMARK_CLAIM_BOUNDARY,
            row_boundary,
            "This artifact is not a calibrated China policy forecast.",
        ],
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_benchmark_artifact(
    path: str | Path,
    *,
    records: list[dict[str, Any]],
    artifact_id: str,
    source_manifest_path: str,
) -> Path:
    artifact = build_policy_reaction_benchmark_artifact(
        records,
        artifact_id=artifact_id,
        source_manifest_path=source_manifest_path,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def write_policy_reaction_benchmark_artifact_from_hps_rows(
    path: str | Path,
    *,
    rows_path: str | Path,
    artifact_id: str,
    source_manifest_path: str,
) -> Path:
    rows = load_hps_public_rows(rows_path)
    records = build_policy_reaction_records_from_hps_rows(rows)
    return write_policy_reaction_benchmark_artifact(
        path,
        records=records,
        artifact_id=artifact_id,
        source_manifest_path=source_manifest_path,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--records",
        default="benchmarks/fixtures/policy_reaction_hps_smoke_records.json",
    )
    parser.add_argument(
        "--hps-public-rows",
        default=None,
        help="Optional HPS/HTOPS-shaped public row CSV or JSON to convert before scoring.",
    )
    parser.add_argument(
        "--source-manifest",
        default="experiments/results/policy_data_intake/hps-htops-food-cost-intake.json",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-hps-smoke-001.json"
        ),
    )
    parser.add_argument("--artifact-id", default="policy-reaction-hps-smoke-001")
    args = parser.parse_args()

    if args.hps_public_rows:
        rows = load_hps_public_rows(args.hps_public_rows)
        records = build_policy_reaction_records_from_hps_rows(rows)
    else:
        records = load_policy_reaction_records(args.records)
    output_path = write_policy_reaction_benchmark_artifact(
        args.output,
        records=records,
        artifact_id=args.artifact_id,
        source_manifest_path=args.source_manifest,
    )
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "output": str(output_path),
                "record_count": len(records),
                "status": "passed",
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


def _benchmark_row_boundary(provenance: list[str]) -> str:
    if "hps_htops_public_row_converter_smoke_fixture" in provenance:
        return (
            "HPS/HTOPS public-row converter smoke records are not paper-grade "
            "field validation."
        )
    return "HPS/HTOPS-shaped smoke records are not paper-grade field validation."


if __name__ == "__main__":
    raise SystemExit(main())
