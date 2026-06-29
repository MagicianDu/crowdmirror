from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.policy_reaction_public_ingestion import (  # noqa: E402
    HTOPS_2506_PUF_MEMBER,
    HTOPS_2506_SOURCE_URL,
    HTOPS_2506_RELEASE_ID,
    _aggregate_observed_policy_reactions,
    _normalize_htops_2506_puf_row,
    _sha256_file,
    load_htops_2506_puf_rows,
)
from benchmarks.policy_reaction import (  # noqa: E402
    build_observed_policy_reaction_from_hps_row,
)


POLICY_REACTION_PUBLIC_AXIS_INGESTION_SCHEMA_VERSION = (
    "policy-reaction-public-axis-ingestion-v1"
)
POLICY_REACTION_PUBLIC_AXIS_INGESTION_CLAIM_BOUNDARY = (
    "Official HPS/HTOPS PUF axis-level ingestion evidence only; not model-quality validation."
)
SEGMENT_AXES = [
    "income_band",
    "employment_status",
    "household_with_children",
    "food_sufficiency_status",
    "price_stress_level",
]


def build_policy_reaction_public_axis_ingestion_artifact(
    rows: list[dict[str, Any]],
    *,
    artifact_id: str,
    source_url: str,
    source_file_name: str,
    source_file_sha256: str,
    zip_member: str,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("axis ingestion artifact requires at least one PUF row")

    observed_rows = []
    skipped_row_count = 0
    for row in rows:
        normalized = _normalize_htops_2506_puf_row(row)
        if normalized is None:
            skipped_row_count += 1
            continue
        observed_rows.append(
            {
                "weight": normalized["weight"],
                "observed_policy_reaction": build_observed_policy_reaction_from_hps_row(
                    normalized
                ),
                "axis_values": _product_compatible_axis_values(normalized),
            }
        )

    by_axis_segment = _aggregate_observed_policy_reactions_by_axis_segment(observed_rows)
    overall_status = "passed" if by_axis_segment else "blocked_for_public_axis_ingestion"
    artifact = {
        "schema_version": POLICY_REACTION_PUBLIC_AXIS_INGESTION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": overall_status,
        "source": {
            "source_id": "hps_htops_food_cost_core",
            "source_release_id": HTOPS_2506_RELEASE_ID,
            "source_url": source_url,
            "source_file_name": source_file_name,
            "source_file_sha256": source_file_sha256,
            "zip_member": zip_member,
        },
        "data_profile": {
            "puf_row_count": len(rows),
            "usable_row_count": len(observed_rows),
            "skipped_row_count": skipped_row_count,
            "segment_axes": SEGMENT_AXES,
            "axis_segment_count": len(by_axis_segment),
            "axis_segment_counts_by_axis": _axis_segment_counts(by_axis_segment),
        },
        "observed_policy_reaction_summary": {
            "by_axis_segment": by_axis_segment,
        },
        "claim_boundary": POLICY_REACTION_PUBLIC_AXIS_INGESTION_CLAIM_BOUNDARY,
        "claim_boundaries": [
            POLICY_REACTION_PUBLIC_AXIS_INGESTION_CLAIM_BOUNDARY,
            "This artifact is only for alternate segment-schema alignment within the same public source and release.",
            "It does not establish cross-task generalization or field validation.",
        ],
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_public_axis_ingestion_artifact(
    path: str | Path,
    *,
    puf_path: str | Path,
    artifact_id: str,
    source_url: str,
    source_file_name: str,
    source_file_sha256: str,
    zip_member: str,
) -> Path:
    rows = load_htops_2506_puf_rows(puf_path, zip_member=zip_member)
    artifact = build_policy_reaction_public_axis_ingestion_artifact(
        rows,
        artifact_id=artifact_id,
        source_url=source_url,
        source_file_name=source_file_name,
        source_file_sha256=source_file_sha256,
        zip_member=zip_member,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def _aggregate_observed_policy_reactions_by_axis_segment(
    observed_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    by_axis_segment: dict[str, list[dict[str, Any]]] = {}
    for row in observed_rows:
        for axis, value in row["axis_values"].items():
            key = f"{axis}={_segment_value(value)}"
            by_axis_segment.setdefault(key, []).append(
                {
                    "weight": row["weight"],
                    "observed_policy_reaction": row["observed_policy_reaction"],
                }
            )
    return {
        segment_key: _aggregate_observed_policy_reactions(rows)
        for segment_key, rows in sorted(by_axis_segment.items())
    }


def _axis_segment_counts(by_axis_segment: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for segment_key in by_axis_segment:
        axis, _, _ = segment_key.partition("=")
        counts[axis] = counts.get(axis, 0) + 1
    return dict(sorted(counts.items()))


def _segment_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _product_compatible_axis_values(normalized: dict[str, Any]) -> dict[str, Any]:
    return {
        "income_band": _canonical_income_band(normalized),
        "employment_status": _canonical_employment_status(normalized),
        "household_with_children": normalized["household_has_children"] == "yes",
        "food_sufficiency_status": _canonical_food_sufficiency_status(normalized),
        "price_stress_level": _canonical_price_stress_level(normalized),
    }


def _canonical_income_band(normalized: dict[str, Any]) -> str:
    bracket = normalized["household_income_bracket"]
    employment = normalized["employment_status"]
    if employment == "retired":
        return "fixed_income"
    if bracket == "less_than_25000":
        return "low"
    if bracket in {"25000_34999", "35000_49999"}:
        return "lower_middle"
    return "middle"


def _canonical_employment_status(normalized: dict[str, Any]) -> str:
    employment = normalized["employment_status"]
    if employment == "employed":
        return "full_time_worker"
    return "retired_or_unable_to_work"


def _canonical_food_sufficiency_status(normalized: dict[str, Any]) -> str:
    food = normalized["FD1_food_sufficiency_last_7_days"]
    child_food = normalized["FD2_child_recent_food_insufficiency_unaffordable_last_7_days"]
    if child_food in {"sometimes_not_enough", "often_not_enough"} or food in {
        "sometimes_not_enough",
        "often_not_enough",
    }:
        return "sometimes_not_enough_food"
    if food == "enough_but_not_always_kinds_wanted":
        return "enough_but_less_varied"
    if normalized["employment_status"] == "retired":
        return "enough_but_budget_constrained"
    return "enough_but_price_sensitive"


def _canonical_price_stress_level(normalized: dict[str, Any]) -> str:
    stress = normalized["INFLATE2_stress_from_price_increases_last_2_months"]
    if stress == "4":
        return "high"
    if stress == "3":
        return "moderate_high"
    return "moderate"


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--puf",
        default="data/raw/hps_htops_2506/HTOPS_HPS_2506_CSV.zip",
    )
    parser.add_argument("--zip-member", default=HTOPS_2506_PUF_MEMBER)
    parser.add_argument("--source-url", default=HTOPS_2506_SOURCE_URL)
    parser.add_argument("--source-file-name", default="HTOPS_HPS_2506_CSV.zip")
    parser.add_argument("--source-file-sha256", default=None)
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-htops-2506-public-axis-ingestion-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-htops-2506-public-axis-ingestion-001.json"
        ),
    )
    args = parser.parse_args()

    source_file_sha256 = args.source_file_sha256 or _sha256_file(args.puf)
    output_path = write_policy_reaction_public_axis_ingestion_artifact(
        args.output,
        puf_path=args.puf,
        artifact_id=args.artifact_id,
        source_url=args.source_url,
        source_file_name=args.source_file_name,
        source_file_sha256=source_file_sha256,
        zip_member=args.zip_member,
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


if __name__ == "__main__":
    raise SystemExit(main())
