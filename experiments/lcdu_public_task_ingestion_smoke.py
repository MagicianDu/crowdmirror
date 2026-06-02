from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SMOKE_SCHEMA_VERSION = "lcdu-public-task-ingestion-smoke-v1"
SMOKE_INDEX_SCHEMA_VERSION = "lcdu-public-task-ingestion-smoke-index-v1"
TASK_CARD_SCHEMA_VERSION = "lcdu-public-task-card-v1"


SMOKE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "public_health_medical_insurance_attitude_v1": {
        "file_name": "public-health-medical-insurance-attitude-v1-smoke.json",
        "source_extract": {
            "source_extract_type": "official_codebook_frequency_table",
            "source_name": "ANES 2024 Time Series",
            "source_url": (
                "https://sda.berkeley.edu/sdaweb/docs/anes2024full/DOC/"
                "hcbk0011.htm"
            ),
            "target_variable_id": "V241245",
            "target_variable_label": (
                "7-point government-private medical insurance self-placement"
            ),
            "valid_substantive_n": 4778,
            "omitted_response_count": 743,
            "code_counts": {
                "1": 1075,
                "2": 590,
                "3": 623,
                "4": 833,
                "5": 568,
                "6": 438,
                "7": 651,
                "99": 483,
            },
        },
        "policy_bins": {
            "government_insurance_plan": ["1", "2", "3"],
            "mixed_or_middle_position": ["4"],
            "private_insurance_plan": ["5", "6", "7"],
        },
    },
    "climate_energy_regulation_attitude_v1": {
        "file_name": "climate-energy-regulation-attitude-v1-smoke.json",
        "source_extract": {
            "source_extract_type": "official_codebook_frequency_table",
            "source_name": "ANES 2024 Time Series",
            "source_url": (
                "https://sda.berkeley.edu/sdaweb/docs/anes2024full/DOC/"
                "hcbk0012.htm"
            ),
            "target_variable_id": "V241258",
            "target_variable_label": (
                "7-point environment-business tradeoff self-placement"
            ),
            "valid_substantive_n": 4577,
            "omitted_response_count": 944,
            "code_counts": {
                "1": 1312,
                "2": 681,
                "3": 677,
                "4": 738,
                "5": 444,
                "6": 297,
                "7": 428,
                "99": 681,
            },
        },
        "policy_bins": {
            "support_more_regulation_or_spending": ["1", "2", "3"],
            "mixed_or_status_quo": ["4"],
            "oppose_more_regulation_or_spending": ["5", "6", "7"],
        },
    },
}


def build_lcdu_public_task_ingestion_smoke(
    *,
    task_card: dict[str, Any],
) -> dict[str, Any]:
    _validate_task_card(task_card)
    task_id = task_card["task_id"]
    definition = SMOKE_DEFINITIONS.get(task_id)
    if definition is None:
        raise ValueError("unsupported task_id")

    source_extract = dict(definition["source_extract"])
    policy_probabilities = _build_policy_probabilities(
        policy_options=task_card["policy_options"],
        code_counts=source_extract["code_counts"],
        valid_substantive_n=source_extract["valid_substantive_n"],
        policy_bins=definition["policy_bins"],
    )
    smoke = {
        "schema_version": SMOKE_SCHEMA_VERSION,
        "artifact_id": f"{task_id}-ingestion-smoke-current-001",
        "task_id": task_id,
        "overall_status": "target_distribution_skeleton_materialized",
        "source_extract": source_extract,
        "target_distribution_skeleton": {
            "target_type": task_card["target_distribution"]["target_type"],
            "policy_options": task_card["policy_options"],
            "policy_probabilities": policy_probabilities,
            "valid_substantive_n": source_extract["valid_substantive_n"],
            "omitted_response_count": source_extract["omitted_response_count"],
            "binning_rule": _build_binning_rule(definition["policy_bins"]),
        },
        "split_contract": task_card["split_contract"],
        "ingestion_boundary": {
            "microdata_loaded": False,
            "source_extract_type": source_extract["source_extract_type"],
            "target_distribution_materialized": "codebook_frequency_skeleton_only",
            "segment_distribution_materialized": False,
        },
        "risk_flags": [
            "codebook_frequency_only",
            "not_cross_task_validation_evidence",
            "not_microdata_ingestion_completed",
            "segment_distribution_not_materialized",
        ],
        "claim_boundary": (
            "Public task ingestion smoke materializes official codebook-level "
            "target skeletons only; it is not microdata ingestion, segment "
            "distribution construction, or model-quality validation."
        ),
    }
    _assert_strict_json(smoke)
    return smoke


def build_lcdu_public_task_ingestion_smoke_index(
    *,
    artifact_id: str,
    task_cards: list[dict[str, Any]],
) -> dict[str, Any]:
    smokes = [
        build_lcdu_public_task_ingestion_smoke(task_card=task_card)
        for task_card in task_cards
    ]
    if len(smokes) < 2:
        raise ValueError("ingestion smoke index requires at least two tasks")
    index = {
        "schema_version": SMOKE_INDEX_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "target_distribution_skeletons_ready",
        "task_count": len(smokes),
        "task_ids": [smoke["task_id"] for smoke in smokes],
        "smoke_artifact_ids": [smoke["artifact_id"] for smoke in smokes],
        "next_gate": "load_public_use_microdata_or_verified_sample_slice",
        "risk_flags": sorted(
            {
                risk_flag
                for smoke in smokes
                for risk_flag in smoke["risk_flags"]
            }
        ),
        "claim_boundary": (
            "Ingestion smoke evidence closes exact-variable and aggregate target "
            "skeleton readiness only; cross-task LCDU validation remains open."
        ),
    }
    _assert_strict_json(index)
    return index


def write_lcdu_public_task_ingestion_smokes(
    *,
    task_card_dir: str | Path,
    output_dir: str | Path,
    artifact_id: str = "lcdu-public-task-ingestion-smoke-index-current-001",
) -> dict[str, Any]:
    task_cards = _load_task_cards(Path(task_card_dir))
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for task_card in task_cards:
        task_id = task_card["task_id"]
        smoke = build_lcdu_public_task_ingestion_smoke(task_card=task_card)
        file_name = SMOKE_DEFINITIONS[task_id]["file_name"]
        (output_path / file_name).write_text(
            json.dumps(smoke, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
    index = build_lcdu_public_task_ingestion_smoke_index(
        artifact_id=artifact_id,
        task_cards=task_cards,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(index, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "index": index}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--task-card-dir",
        default="experiments/results/lcdu_public_task_cards",
    )
    parser.add_argument(
        "--output-dir",
        default="experiments/results/lcdu_public_task_ingestion_smoke",
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-public-task-ingestion-smoke-index-current-001",
    )
    args = parser.parse_args()
    written = write_lcdu_public_task_ingestion_smokes(
        task_card_dir=args.task_card_dir,
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "task_count": written["index"]["task_count"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _load_task_cards(task_card_dir: Path) -> list[dict[str, Any]]:
    task_cards = []
    for path in sorted(task_card_dir.glob("*.json")):
        payload = json.loads(path.read_text())
        if payload.get("schema_version") == TASK_CARD_SCHEMA_VERSION:
            task_cards.append(payload)
    if not task_cards:
        raise ValueError("task_card_dir does not contain task cards")
    return task_cards


def _validate_task_card(task_card: dict[str, Any]) -> None:
    if task_card.get("schema_version") != TASK_CARD_SCHEMA_VERSION:
        raise ValueError("task_card has unsupported schema_version")
    for field_name in (
        "task_id",
        "policy_options",
        "target_distribution",
        "split_contract",
    ):
        if field_name not in task_card:
            raise ValueError(f"task_card missing {field_name}")
    if task_card["task_id"] not in SMOKE_DEFINITIONS:
        raise ValueError("unsupported task_id")


def _build_policy_probabilities(
    *,
    policy_options: list[str],
    code_counts: dict[str, int],
    valid_substantive_n: int,
    policy_bins: dict[str, list[str]],
) -> dict[str, float]:
    if set(policy_options) != set(policy_bins):
        raise ValueError("policy options must match smoke policy bins")
    probabilities = {}
    for policy_option in policy_options:
        option_count = sum(code_counts[code] for code in policy_bins[policy_option])
        probabilities[policy_option] = round(option_count / valid_substantive_n, 12)
    return probabilities


def _build_binning_rule(policy_bins: dict[str, list[str]]) -> list[dict[str, Any]]:
    return [
        {
            "policy_option": policy_option,
            "source_code_values": code_values,
        }
        for policy_option, code_values in policy_bins.items()
    ]


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU public task ingestion smoke must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
