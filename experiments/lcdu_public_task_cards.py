from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TASK_CARD_SCHEMA_VERSION = "lcdu-public-task-card-v1"
TASK_CARD_INDEX_SCHEMA_VERSION = "lcdu-public-task-card-index-v1"

RECOMMENDED_TASK_IDS = [
    "public_health_medical_insurance_attitude_v1",
    "climate_energy_regulation_attitude_v1",
]

TASK_DEFINITIONS: dict[str, dict[str, Any]] = {
    "public_health_medical_insurance_attitude_v1": {
        "file_name": "public-health-medical-insurance-attitude-v1.json",
        "policy_domain": "public_health",
        "task_label": "Public health and medical insurance policy attitude",
        "primary_data_source": {
            "source_name": "ANES 2024 Time Series",
            "source_url": (
                "https://sda.berkeley.edu/sdaweb/docs/anes2024full/DOC/"
                "anes_timeseries_2024_userguidecodebook_20250808.pdf"
            ),
            "source_type": "public_use_codebook_and_microdata",
            "source_status": "official_codebook_verified",
        },
        "supporting_data_sources": [
            {
                "source_name": "General Social Survey",
                "source_url": "https://www.norc.org/research/projects/gss.html",
                "source_type": "public_opinion_survey",
                "source_status": "candidate_harmonization_source",
            }
        ],
        "policy_options": [
            "government_insurance_plan",
            "mixed_or_middle_position",
            "private_insurance_plan",
        ],
        "target_distribution": {
            "target_type": "policy_attitude_scale",
            "candidate_variables": ["V241245"],
            "variable_notes": [
                "ANES codebook labels V241245 as the 7-point government-private medical insurance self-placement scale.",
                "Values can be binned into government, middle, and private insurance positions for segment-level target distributions.",
            ],
        },
        "segment_schema": {
            "required_axes": [
                "income",
                "age",
                "education",
                "party_or_ideology",
                "health_insurance_context",
            ],
            "minimum_segment_count": 6,
        },
        "lcdU_factor_hypotheses": [
            "institutional_trust",
            "benefit_accessibility",
            "public_private_preference",
            "medical_cost_exposure",
        ],
        "claim_boundary": (
            "Public health task card supports public opinion alignment only; "
            "not medical advice, policy impact estimation, or field validation."
        ),
    },
    "climate_energy_regulation_attitude_v1": {
        "file_name": "climate-energy-regulation-attitude-v1.json",
        "policy_domain": "climate_energy",
        "task_label": "Climate and energy regulation policy attitude",
        "primary_data_source": {
            "source_name": "ANES 2024 Time Series",
            "source_url": (
                "https://sda.berkeley.edu/sdaweb/docs/anes2024full/DOC/"
                "hcbk0012.htm"
            ),
            "source_type": "public_use_codebook_and_microdata",
            "source_status": "official_codebook_verified",
        },
        "supporting_data_sources": [
            {
                "source_name": "Cooperative Election Study cumulative common content",
                "source_url": (
                    "https://sda.ist.berkeley.edu/sdaweb/docs/ces-cumulative-2024-v10/"
                    "DOC/guide_cumulative_2006-2024.pdf"
                ),
                "source_type": "public_opinion_survey",
                "source_status": "candidate_harmonization_source",
            },
            {
                "source_name": "General Social Survey",
                "source_url": "https://www.norc.org/research/projects/gss.html",
                "source_type": "public_opinion_survey",
                "source_status": "candidate_harmonization_source",
            },
        ],
        "policy_options": [
            "support_more_regulation_or_spending",
            "mixed_or_status_quo",
            "oppose_more_regulation_or_spending",
        ],
        "target_distribution": {
            "target_type": "policy_support_distribution",
            "candidate_variables": [
                "V241258",
                "V241282",
            ],
            "variable_notes": [
                "ANES codebook labels V241258 as the 7-point environment-business tradeoff self-placement scale.",
                "V241258 can be binned into pro-regulation, middle, and pro-business positions for the first ingestion smoke target.",
                "V241282 is retained as a supporting spending item for later robustness checks.",
            ],
        },
        "segment_schema": {
            "required_axes": [
                "income",
                "region",
                "education",
                "party_or_ideology",
                "urbanicity",
            ],
            "minimum_segment_count": 6,
        },
        "lcdU_factor_hypotheses": [
            "energy_cost_exposure",
            "environmental_risk_salience",
            "party_or_ideology",
            "government_regulation_trust",
        ],
        "claim_boundary": (
            "Climate-energy task card supports public opinion alignment only; "
            "not climate impact forecasting, policy impact estimation, or field validation."
        ),
    },
}


def build_lcdu_public_task_card(*, task_id: str) -> dict[str, Any]:
    if task_id not in TASK_DEFINITIONS:
        raise ValueError("unsupported task_id")
    definition = TASK_DEFINITIONS[task_id]
    card = {
        "schema_version": TASK_CARD_SCHEMA_VERSION,
        "task_id": task_id,
        "task_label": definition["task_label"],
        "task_status": "task_card_smoke_passed",
        "policy_domain": definition["policy_domain"],
        "primary_data_source": definition["primary_data_source"],
        "supporting_data_sources": definition["supporting_data_sources"],
        "policy_options": definition["policy_options"],
        "target_distribution": definition["target_distribution"],
        "segment_schema": definition["segment_schema"],
        "lcdU_factor_hypotheses": definition["lcdU_factor_hypotheses"],
        "split_contract": {
            "candidate_generation": "calibration",
            "candidate_acceptance": "heldout",
            "final_claim_check": "test",
        },
        "ingestion_smoke": {
            "status": "ready_for_microdata_variable_audit",
            "required_next_step": "bind_exact_public_use_variables_and_generate_target_distribution",
            "microdata_loaded": False,
            "target_distribution_materialized": False,
        },
        "risk_flags": [
            "public_opinion_alignment_not_field_validation",
            "exact_microdata_variable_binding_pending",
            "target_distribution_not_materialized",
        ],
        "claim_boundary": definition["claim_boundary"],
    }
    _validate_card(card)
    _assert_strict_json(card)
    return card


def build_lcdu_public_task_card_index(
    *,
    artifact_id: str,
    task_ids: list[str],
) -> dict[str, Any]:
    cards = [build_lcdu_public_task_card(task_id=task_id) for task_id in task_ids]
    index = {
        "schema_version": TASK_CARD_INDEX_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "recommended_task_cards_ready",
        "task_count": len(cards),
        "task_ids": [card["task_id"] for card in cards],
        "policy_domains": [card["policy_domain"] for card in cards],
        "next_gate": "run_public_task_ingestion_smoke",
        "risk_flags": sorted(
            {
                flag
                for card in cards
                for flag in card["risk_flags"]
            }
        ),
        "claim_boundary": (
            "Public task card index records candidate external-validation tasks; "
            "it does not provide model-quality or field-validation evidence."
        ),
    }
    _assert_strict_json(index)
    return index


def write_lcdu_public_task_cards(
    *,
    output_dir: str | Path,
    task_ids: list[str] | None = None,
    artifact_id: str = "lcdu-public-task-card-index-current-001",
) -> dict[str, Any]:
    task_ids = task_ids or RECOMMENDED_TASK_IDS
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for task_id in task_ids:
        card = build_lcdu_public_task_card(task_id=task_id)
        file_name = TASK_DEFINITIONS[task_id]["file_name"]
        (output_path / file_name).write_text(
            json.dumps(card, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
    index = build_lcdu_public_task_card_index(
        artifact_id=artifact_id,
        task_ids=task_ids,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(index, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "index": index}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="experiments/results/lcdu_public_task_cards",
    )
    parser.add_argument(
        "--artifact-id",
        default="lcdu-public-task-card-index-current-001",
    )
    args = parser.parse_args()
    written = write_lcdu_public_task_cards(
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


def _validate_card(card: dict[str, Any]) -> None:
    required_fields = (
        "schema_version",
        "task_id",
        "policy_domain",
        "primary_data_source",
        "policy_options",
        "target_distribution",
        "segment_schema",
        "split_contract",
        "claim_boundary",
    )
    for field_name in required_fields:
        if field_name not in card:
            raise ValueError(f"task card missing {field_name}")
    if len(card["policy_options"]) < 2:
        raise ValueError("task card requires at least two policy options")
    if not card["target_distribution"].get("candidate_variables"):
        raise ValueError("task card requires candidate target variables")
    if not card["segment_schema"].get("required_axes"):
        raise ValueError("task card requires segment axes")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU public task card must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
