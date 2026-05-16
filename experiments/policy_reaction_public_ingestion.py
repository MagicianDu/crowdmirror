from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
from typing import Any
import zipfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmarks.policy_reaction import (  # noqa: E402
    build_observed_policy_reaction_from_hps_row,
    segment_hps_public_row,
)


POLICY_REACTION_PUBLIC_INGESTION_SCHEMA_VERSION = (
    "policy-reaction-public-data-ingestion-v1"
)
POLICY_REACTION_PUBLIC_INGESTION_CLAIM_BOUNDARY = (
    "Official HPS/HTOPS PUF ingestion evidence only; not model-quality validation."
)
HTOPS_2506_RELEASE_ID = "htops_hps_2506"
HTOPS_2506_PUF_MEMBER = "HTOPS_HPS_2506_PUF.csv"
HTOPS_2506_SOURCE_URL = (
    "https://www2.census.gov/programs-surveys/demo/datasets/hhp/2025/topical/"
    "HTOPS_HPS_2506_CSV.zip"
)
HTOPS_PUF_REQUIRED_FIELDS = (
    "SCRAMID",
    "CURFOODSUF",
    "CHILDFOOD",
    "EXPNS_DIF",
    "PRICECHNG",
    "PRICESTRESS",
    "WRKLOSSRV",
    "RFAM_INCOME",
    "THHLD_NUMKID_TOPICAL",
    "ANYWORK",
    "TAGE1",
    "PWEIGHT",
    "DIVISION",
    "METRO_STATUS",
)


def load_htops_2506_puf_rows(
    path: str | Path,
    *,
    zip_member: str = HTOPS_2506_PUF_MEMBER,
) -> list[dict[str, Any]]:
    input_path = Path(path)
    if input_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(input_path) as archive:
            with archive.open(zip_member) as handle:
                text = io.TextIOWrapper(handle, encoding="utf-8-sig", newline="")
                rows = list(csv.DictReader(text))
    else:
        with input_path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("HTOPS/HPS PUF rows must be non-empty")
    return rows


def build_policy_reaction_public_ingestion_artifact(
    rows: list[dict[str, Any]],
    *,
    artifact_id: str,
    source_url: str,
    source_file_name: str,
    source_file_sha256: str,
    zip_member: str,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("public ingestion artifact requires at least one PUF row")

    missing_fields = _missing_required_fields(rows)
    observed_rows = []
    skipped_row_count = 0
    for row in rows:
        normalized = _normalize_htops_2506_puf_row(row)
        if normalized is None:
            skipped_row_count += 1
            continue
        observed_rows.append(
            {
                "segment": segment_hps_public_row(normalized),
                "weight": normalized["weight"],
                "observed_policy_reaction": build_observed_policy_reaction_from_hps_row(
                    normalized
                ),
            }
        )

    overall_status = (
        "passed"
        if observed_rows and not missing_fields
        else "blocked_for_public_data_ingestion"
    )
    artifact = {
        "schema_version": POLICY_REACTION_PUBLIC_INGESTION_SCHEMA_VERSION,
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
            "required_field_coverage": {
                "all_present": not missing_fields,
                "missing_fields": missing_fields,
            },
            "source_fields": list(HTOPS_PUF_REQUIRED_FIELDS),
            "segment_counts": _segment_counts(observed_rows),
        },
        "observed_policy_reaction_summary": {
            "overall": _aggregate_observed_policy_reactions(observed_rows),
            "by_segment": _aggregate_observed_policy_reactions_by_segment(
                observed_rows
            ),
        },
        "claim_boundary": POLICY_REACTION_PUBLIC_INGESTION_CLAIM_BOUNDARY,
        "claim_boundaries": [
            POLICY_REACTION_PUBLIC_INGESTION_CLAIM_BOUNDARY,
            "This artifact reports public-use survey ingestion and derived observed "
            "policy-reaction proxies only.",
            "It does not report LLM prediction quality, field validation, or a China "
            "policy forecast.",
        ],
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_public_ingestion_artifact(
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
    artifact = build_policy_reaction_public_ingestion_artifact(
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
        default="policy-reaction-htops-2506-public-ingestion-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-htops-2506-public-ingestion-001.json"
        ),
    )
    args = parser.parse_args()

    source_file_sha256 = args.source_file_sha256 or _sha256_file(args.puf)
    output_path = write_policy_reaction_public_ingestion_artifact(
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


def _normalize_htops_2506_puf_row(row: dict[str, Any]) -> dict[str, Any] | None:
    if not _has_required_values(row):
        return None
    return {
        "record_id": _record_hash(row["SCRAMID"]),
        "household_has_children": _household_has_children(
            row["THHLD_NUMKID_TOPICAL"]
        ),
        "household_income_bracket": _income_bracket(row["RFAM_INCOME"]),
        "employment_status": _employment_status(row["ANYWORK"], row["TAGE1"]),
        "FD1_food_sufficiency_last_7_days": row["CURFOODSUF"],
        "FD2_child_recent_food_insufficiency_unaffordable_last_7_days": (
            _child_food_value(row["CHILDFOOD"])
        ),
        "SPN4_difficulty_paying_usual_household_expenses_last_2_months": row[
            "EXPNS_DIF"
        ],
        "INFLATE2_stress_from_price_increases_last_2_months": _price_stress_value(
            row["PRICESTRESS"]
        ),
        "EMP1_household_loss_employment_income_last_4_weeks": _yes_no_value(
            row["WRKLOSSRV"]
        ),
        "weight": _parse_weight(row["PWEIGHT"]),
    }


def _has_required_values(row: dict[str, Any]) -> bool:
    if any(
        field not in row or row[field] == ""
        for field in HTOPS_PUF_REQUIRED_FIELDS
    ):
        return False
    core_fields = (
        "CURFOODSUF",
        "EXPNS_DIF",
        "PRICESTRESS",
        "WRKLOSSRV",
        "RFAM_INCOME",
        "THHLD_NUMKID_TOPICAL",
        "ANYWORK",
        "TAGE1",
        "PWEIGHT",
    )
    if any(row[field] == "-99" for field in core_fields):
        return False
    return row["CURFOODSUF"] != "-88" and row["EXPNS_DIF"] != "-88"


def _missing_required_fields(rows: list[dict[str, Any]]) -> list[str]:
    available = set(rows[0])
    return sorted(field for field in HTOPS_PUF_REQUIRED_FIELDS if field not in available)


def _household_has_children(value: Any) -> str:
    return "yes" if int(str(value)) > 0 else "no"


def _income_bracket(value: Any) -> str:
    brackets = {
        "1": "less_than_25000",
        "2": "25000_34999",
        "3": "35000_49999",
        "4": "50000_74999",
        "5": "75000_99999",
        "6": "100000_149999",
        "7": "150000_199999",
        "8": "200000_or_more",
    }
    return brackets[str(value)]


def _employment_status(anywork: Any, age: Any) -> str:
    if int(str(age)) >= 65:
        return "retired"
    return "employed" if str(anywork) == "1" else "not_in_labor_force"


def _child_food_value(value: Any) -> str:
    if str(value) in {"-88", "-99"}:
        return "no"
    values = {
        "1": "often_not_enough",
        "2": "sometimes_not_enough",
        "3": "no",
    }
    if str(value) in values:
        return values[str(value)]
    return str(value)


def _price_stress_value(value: Any) -> str:
    if str(value) == "-88":
        return "not_at_all_stressed"
    return str(value)


def _yes_no_value(value: Any) -> str:
    return "yes" if str(value) == "1" else "no"


def _parse_weight(value: Any) -> float:
    weight = float(value)
    return weight if weight > 0 else 0.0


def _record_hash(scramid: Any) -> str:
    digest = hashlib.sha256(str(scramid).encode("utf-8")).hexdigest()[:16]
    return f"htops-2506-{digest}"


def _segment_counts(observed_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in observed_rows:
        counts[row["segment"]] = counts.get(row["segment"], 0) + 1
    return dict(sorted(counts.items()))


def _aggregate_observed_policy_reactions(
    observed_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if not observed_rows:
        return {
            "row_count": 0,
            "weighted_row_mass": 0.0,
            "mean_policy_reaction": {},
            "weighted_mean_policy_reaction": {},
        }
    policies = sorted(
        {
            policy_id
            for row in observed_rows
            for policy_id in row["observed_policy_reaction"]
        }
    )
    row_count = len(observed_rows)
    weight_total = sum(row["weight"] for row in observed_rows)
    return {
        "row_count": row_count,
        "weighted_row_mass": weight_total,
        "mean_policy_reaction": {
            policy_id: sum(
                row["observed_policy_reaction"][policy_id] for row in observed_rows
            )
            / row_count
            for policy_id in policies
        },
        "weighted_mean_policy_reaction": {
            policy_id: (
                sum(
                    row["observed_policy_reaction"][policy_id] * row["weight"]
                    for row in observed_rows
                )
                / weight_total
                if weight_total > 0
                else 0.0
            )
            for policy_id in policies
        },
    }


def _aggregate_observed_policy_reactions_by_segment(
    observed_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    by_segment: dict[str, list[dict[str, Any]]] = {}
    for row in observed_rows:
        by_segment.setdefault(row["segment"], []).append(row)
    return {
        segment: _aggregate_observed_policy_reactions(rows)
        for segment, rows in sorted(by_segment.items())
    }


def _sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
