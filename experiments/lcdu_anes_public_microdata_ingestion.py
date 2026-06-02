from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ANES_PUBLIC_MICRODATA_SCHEMA_VERSION = "lcdu-anes-public-microdata-ingestion-v1"
ANES_PUBLIC_MICRODATA_ARTIFACT_ID = "lcdu-anes-2024-sda-public-microdata-001"
ANES_SDA_DATASET_ID = "anes2024full"
ANES_SDA_ANALYSIS_URL = (
    "https://sda.berkeley.edu/sdaweb/analysis/?dataset=anes2024full"
)

SELECTED_VARIABLES = [
    "V240001",
    "V240103a",
    "V241245",
    "V241258",
    "V241458x",
    "V241465x",
    "V241566x",
    "V241177",
    "V241550",
    "V241501x",
]

TASK_BINDINGS: dict[str, dict[str, Any]] = {
    "public_health_medical_insurance_attitude_v1": {
        "target_variable_id": "V241245",
        "target_variable_label": (
            "7-point government-private medical insurance self-placement"
        ),
        "codebook_url": (
            "https://sda.berkeley.edu/sdaweb/docs/anes2024full/DOC/"
            "hcbk0011.htm"
        ),
        "policy_bins": {
            "government_insurance_plan": {1, 2, 3},
            "mixed_or_middle_position": {4},
            "private_insurance_plan": {5, 6, 7},
        },
        "required_axes": {
            "income",
            "age",
            "education",
            "party_or_ideology",
            "health_insurance_context",
        },
    },
    "climate_energy_regulation_attitude_v1": {
        "target_variable_id": "V241258",
        "target_variable_label": (
            "7-point environment-business tradeoff self-placement"
        ),
        "codebook_url": (
            "https://sda.berkeley.edu/sdaweb/docs/anes2024full/DOC/"
            "hcbk0012.htm"
        ),
        "policy_bins": {
            "support_more_regulation_or_spending": {1, 2, 3},
            "mixed_or_status_quo": {4},
            "oppose_more_regulation_or_spending": {5, 6, 7},
        },
        "required_axes": {
            "income",
            "region",
            "education",
            "party_or_ideology",
            "urbanicity",
        },
    },
}

AXIS_VARIABLE_BINDINGS = {
    "age": "V241458x",
    "education": "V241465x",
    "income": "V241566x",
    "party_or_ideology": "V241177",
    "sex": "V241550",
    "race_ethnicity": "V241501x",
}

AVAILABLE_REQUIRED_AXES = {
    "age",
    "education",
    "income",
    "party_or_ideology",
}


def load_anes_sda_subset_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle, skipinitialspace=True))
    if not rows:
        raise ValueError("ANES SDA subset rows must be non-empty")
    missing = [field for field in SELECTED_VARIABLES if field not in rows[0]]
    if missing:
        raise ValueError(f"ANES SDA subset missing fields: {missing}")
    return rows


def build_lcdu_anes_public_microdata_ingestion_artifact(
    rows: list[dict[str, str]],
    *,
    artifact_id: str,
    source_file_name: str,
    source_file_sha256: str,
    source_url: str = ANES_SDA_ANALYSIS_URL,
    dataset_id: str = ANES_SDA_DATASET_ID,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("microdata ingestion artifact requires rows")
    normalized_rows = [_normalize_row(row) for row in rows]
    target_distributions = {
        task_id: _build_task_target_distribution(
            normalized_rows=normalized_rows,
            task_id=task_id,
        )
        for task_id in TASK_BINDINGS
    }
    split_projection = _build_split_projection(normalized_rows)
    artifact = {
        "schema_version": ANES_PUBLIC_MICRODATA_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "segment_target_distributions_materialized_with_partial_schema",
        "source": {
            "source_id": "anes_2024_time_series_sda_subset",
            "dataset_id": dataset_id,
            "source_url": source_url,
            "source_file_name": source_file_name,
            "source_file_sha256": source_file_sha256,
            "source_extract_type": "sda_custom_subset_public_use_microdata",
            "selected_variables": SELECTED_VARIABLES,
        },
        "data_profile": {
            "row_count": len(normalized_rows),
            "unique_case_id_count": len({row["case_id"] for row in normalized_rows}),
            "selected_variable_count": len(SELECTED_VARIABLES),
            "required_field_coverage": {
                "all_present": True,
                "missing_fields": [],
            },
        },
        "segment_schema": {
            "available_axes": sorted(AXIS_VARIABLE_BINDINGS),
            "available_required_axes": sorted(AVAILABLE_REQUIRED_AXES),
            "axis_variable_bindings": AXIS_VARIABLE_BINDINGS,
            "axis_grouping_contract": {
                "age": ["18_34", "35_64", "65_plus", "unknown"],
                "education": [
                    "high_school_or_less",
                    "some_college",
                    "college_degree",
                    "postgraduate",
                    "unknown",
                ],
                "income": ["lower", "middle", "upper", "unknown"],
                "party_or_ideology": [
                    "liberal",
                    "moderate",
                    "conservative",
                    "unknown",
                ],
            },
            "segment_key_axes": ["party_or_ideology", "income"],
        },
        "target_distributions": target_distributions,
        "split_contract": {
            "assignment_field": "V240001",
            "assignment_method": "sha256_modulo",
            "modulus": 5,
            "candidate_generation": {
                "split_name": "calibration",
                "remainders": [0, 1, 2],
            },
            "candidate_acceptance": {
                "split_name": "heldout",
                "remainders": [3],
            },
            "final_claim_check": {
                "split_name": "test",
                "remainders": [4],
            },
        },
        "splits": split_projection,
        "risk_flags": [
            "not_model_validation",
            "not_cross_task_lcdu_validation",
            "segment_schema_partial_coverage",
            "sda_subset_not_full_raw_release_archive",
        ],
        "claim_boundary": (
            "ANES SDA public-use subset ingestion materializes microdata-derived "
            "aggregate and segment-level target distributions only; it does not "
            "evaluate LCDU, prove cross-task generalization, or establish field "
            "validation."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_lcdu_anes_public_microdata_ingestion_artifact(
    output: str | Path,
    *,
    input_csv: str | Path,
    artifact_id: str = ANES_PUBLIC_MICRODATA_ARTIFACT_ID,
    source_url: str = ANES_SDA_ANALYSIS_URL,
    source_file_name: str | None = None,
    source_file_sha256: str | None = None,
) -> dict[str, Any]:
    rows = load_anes_sda_subset_rows(input_csv)
    source_path = Path(input_csv)
    artifact = build_lcdu_anes_public_microdata_ingestion_artifact(
        rows,
        artifact_id=artifact_id,
        source_url=source_url,
        source_file_name=source_file_name or source_path.name,
        source_file_sha256=source_file_sha256 or _sha256_file(source_path),
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"output_path": str(output_path), "artifact": artifact}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-csv",
        default="data/raw/anes_2024/anes2024_sda_lcdu_subset.csv",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/lcdu_public_task_microdata/"
            "lcdu-anes-2024-sda-public-microdata-001.json"
        ),
    )
    parser.add_argument("--artifact-id", default=ANES_PUBLIC_MICRODATA_ARTIFACT_ID)
    parser.add_argument("--source-url", default=ANES_SDA_ANALYSIS_URL)
    parser.add_argument("--source-file-name", default=None)
    parser.add_argument("--source-file-sha256", default=None)
    args = parser.parse_args()
    written = write_lcdu_anes_public_microdata_ingestion_artifact(
        args.output,
        input_csv=args.input_csv,
        artifact_id=args.artifact_id,
        source_url=args.source_url,
        source_file_name=args.source_file_name,
        source_file_sha256=args.source_file_sha256,
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": written["output_path"],
                "row_count": artifact["data_profile"]["row_count"],
                "status": artifact["overall_status"],
                "task_count": len(artifact["target_distributions"]),
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _normalize_row(row: dict[str, str]) -> dict[str, Any]:
    case_id = str(_parse_int(row["V240001"]))
    normalized = {
        "case_id": case_id,
        "weight": _parse_float(row.get("V240103a")),
        "targets": {
            "V241245": _parse_int(row["V241245"]),
            "V241258": _parse_int(row["V241258"]),
        },
        "axes": {
            "age": _age_group(_parse_int(row["V241458x"])),
            "education": _education_group(_parse_int(row["V241465x"])),
            "income": _income_group(_parse_int(row["V241566x"])),
            "party_or_ideology": _ideology_group(_parse_int(row["V241177"])),
            "sex": _sex_group(_parse_int(row["V241550"])),
            "race_ethnicity": _race_group(_parse_int(row["V241501x"])),
        },
    }
    normalized["segment_key"] = _segment_key(normalized["axes"])
    normalized["split"] = _assign_split(case_id)
    return normalized


def _build_task_target_distribution(
    *,
    normalized_rows: list[dict[str, Any]],
    task_id: str,
) -> dict[str, Any]:
    binding = TASK_BINDINGS[task_id]
    target_variable_id = binding["target_variable_id"]
    target_rows = [
        row
        for row in normalized_rows
        if row["targets"][target_variable_id] in {1, 2, 3, 4, 5, 6, 7}
    ]
    by_segment = {}
    for segment_key in sorted({row["segment_key"] for row in target_rows}):
        segment_rows = [row for row in target_rows if row["segment_key"] == segment_key]
        by_segment[segment_key] = _policy_distribution(
            values=[row["targets"][target_variable_id] for row in segment_rows],
            policy_bins=binding["policy_bins"],
        )
    missing_axes = sorted(binding["required_axes"] - AVAILABLE_REQUIRED_AXES)
    available_required_axes = sorted(binding["required_axes"] & AVAILABLE_REQUIRED_AXES)
    return {
        "task_id": task_id,
        "target_variable_id": target_variable_id,
        "target_variable_label": binding["target_variable_label"],
        "codebook_url": binding["codebook_url"],
        "valid_substantive_n": len(target_rows),
        "omitted_or_invalid_n": len(normalized_rows) - len(target_rows),
        "overall": _policy_distribution(
            values=[row["targets"][target_variable_id] for row in target_rows],
            policy_bins=binding["policy_bins"],
        ),
        "by_segment": by_segment,
        "segment_schema_coverage": {
            "required_axes": sorted(binding["required_axes"]),
            "available_required_axes": available_required_axes,
            "missing_required_axes": missing_axes,
            "coverage_status": (
                "partial" if missing_axes else "complete_for_task_card_axes"
            ),
        },
    }


def _build_split_projection(normalized_rows: list[dict[str, Any]]) -> dict[str, Any]:
    splits = {}
    for split_name in ("calibration", "heldout", "test"):
        split_rows = [row for row in normalized_rows if row["split"] == split_name]
        splits[split_name] = {
            "row_count": len(split_rows),
            "unique_case_id_count": len({row["case_id"] for row in split_rows}),
            "task_target_valid_n": {
                task_id: sum(
                    1
                    for row in split_rows
                    if row["targets"][binding["target_variable_id"]]
                    in {1, 2, 3, 4, 5, 6, 7}
                )
                for task_id, binding in TASK_BINDINGS.items()
            },
            "target_distributions": {
                task_id: _build_task_target_distribution(
                    normalized_rows=split_rows,
                    task_id=task_id,
                )
                for task_id in TASK_BINDINGS
            },
        }
    return splits


def _policy_distribution(
    *,
    values: list[int],
    policy_bins: dict[str, set[int]],
) -> dict[str, Any]:
    counts = {
        policy_option: sum(1 for value in values if value in codes)
        for policy_option, codes in policy_bins.items()
    }
    total = sum(counts.values())
    probabilities = {
        policy_option: (round(count / total, 12) if total else 0.0)
        for policy_option, count in counts.items()
    }
    return {
        "row_count": total,
        "policy_counts": counts,
        "policy_probabilities": probabilities,
    }


def _segment_key(axes: dict[str, str]) -> str:
    return (
        f"party_or_ideology={axes['party_or_ideology']}|"
        f"income={axes['income']}"
    )


def _assign_split(case_id: str) -> str:
    remainder = int(hashlib.sha256(case_id.encode("utf-8")).hexdigest(), 16) % 5
    if remainder in {0, 1, 2}:
        return "calibration"
    if remainder == 3:
        return "heldout"
    return "test"


def _age_group(value: int | None) -> str:
    if value is None or value < 18:
        return "unknown"
    if value <= 34:
        return "18_34"
    if value <= 64:
        return "35_64"
    return "65_plus"


def _education_group(value: int | None) -> str:
    if value in {1, 2}:
        return "high_school_or_less"
    if value == 3:
        return "some_college"
    if value == 4:
        return "college_degree"
    if value == 5:
        return "postgraduate"
    return "unknown"


def _income_group(value: int | None) -> str:
    if value is None or value <= 0:
        return "unknown"
    if value <= 10:
        return "lower"
    if value <= 20:
        return "middle"
    return "upper"


def _ideology_group(value: int | None) -> str:
    if value in {1, 2, 3}:
        return "liberal"
    if value == 4:
        return "moderate"
    if value in {5, 6, 7}:
        return "conservative"
    return "unknown"


def _sex_group(value: int | None) -> str:
    if value == 1:
        return "male"
    if value == 2:
        return "female"
    return "unknown"


def _race_group(value: int | None) -> str:
    return {
        1: "white_non_hispanic",
        2: "black_non_hispanic",
        3: "hispanic",
        4: "asian_or_pacific_islander",
        5: "native_american_or_alaska_native",
        6: "other_or_multiple",
    }.get(value, "unknown")


def _parse_int(value: str | int | float | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _parse_float(value: str | int | float | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU ANES microdata artifact must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
