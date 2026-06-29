from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import (
    assert_strict_json,
    non_empty_string,
    write_json_artifact,
)


R10_EXTERNAL_EVIDENCE_REGISTRY_SCHEMA_VERSION = (
    "r10-external-evidence-registry-v1"
)
R10_EXTERNAL_EVIDENCE_REGISTRY_CLAIM_BOUNDARY = (
    "R10 external evidence registry artifact. It records official public data "
    "source candidates for precedent-constrained method development only; it "
    "does not prove data ingestion, field validation, method superiority, or "
    "runtime default readiness."
)


def build_r10_external_evidence_registry(
    *,
    artifact_id: str,
    run_id: str,
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    case_records = _case_records()
    registry = {
        "schema_version": R10_EXTERNAL_EVIDENCE_REGISTRY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r10_external_evidence_registry_ready_guarded",
        "method_positioning": {
            "research_problem": (
                "Research 方法缺少独立外部案例证据，无法全面支撑 Product core method。"
            ),
            "product_goal": "人群反应趋势与风险区间模拟器",
            "r10_l0_goal": (
                "建立可审计外部案例证据 registry，作为 R10 路线 B 和后续 A/B/C 组合输入。"
            ),
        },
        "claim_boundary": R10_EXTERNAL_EVIDENCE_REGISTRY_CLAIM_BOUNDARY,
        "evidence_contract": {
            "source_backed_only": True,
            "external_case_evidence_required_for_escalation": True,
            "actual_public_data_ingested": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
            "customer_visible": False,
        },
        "route_input_contract": {
            "route_a_evidence_constrained_mechanism_operator": [
                "mechanism_priors",
                "outcome_signal_type",
                "evidence_strength",
            ],
            "route_b_semantic_precedent_retrieval": [
                "scenario_family",
                "semantic_tags",
                "source_url",
                "outcome_signal_type",
            ],
            "route_c_constrained_multi_agent_rollout": [
                "affected_segments",
                "mechanism_priors",
                "risk_observation_window",
            ],
        },
        "case_records": case_records,
        "coverage_summary": _coverage_summary(case_records),
        "acceptance_gates": {
            "minimum_external_sources_present": True,
            "policy_reaction_source_present": True,
            "transportation_price_demand_source_present": True,
            "air_travel_complaint_source_present": True,
            "route_b_precedent_inputs_present": True,
            "actual_public_data_ingested": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "next_tasks": [
            {
                "task_id": "r10_l1_ingest_hps_policy_reaction_slice",
                "goal": (
                    "下载或切片 Census HPS/HTOPS public-use 数据，形成政策反应 "
                    "survey outcome proxy。"
                ),
                "acceptance": (
                    "生成 source-backed ingestion artifact，报告样本量、权重字段、"
                    "outcome label 和 segment coverage。"
                ),
            },
            {
                "task_id": "r10_l1_ingest_bts_route_price_demand_slice",
                "goal": (
                    "接入 BTS O&D/DB1B 公开航线票价与客流数据，形成价格变更 "
                    "revealed-demand precedent。"
                ),
                "acceptance": (
                    "生成 route-level price/demand evidence artifact，明确航线、"
                    "时间窗、票价指标、客流指标和缺失字段。"
                ),
            },
            {
                "task_id": "r10_l1_ingest_dot_air_travel_complaint_slice",
                "goal": (
                    "接入 DOT Air Travel Consumer Reports 中 complaint/consumer "
                    "submission 信号，形成服务变更或摩擦风险 precedent。"
                ),
                "acceptance": (
                    "生成 complaint-rate evidence artifact，并把 complaint 类别映射到 "
                    "mechanism priors 与 abnormal segment hypotheses。"
                ),
            },
        ],
        "allowed_claims": [
            "R10 L0 records official public source candidates for method strengthening.",
            "R10 L0 can feed route B semantic precedent retrieval and later A/B/C combinations.",
        ],
        "blocked_claims": [
            "actual public data ingestion has completed",
            "R10 validated",
            "R10 supports Product core method by default",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
            "runtime default ready",
            "accuracy superiority",
            "精准预测系统",
        ],
    }
    _validate_unique_case_ids(case_records)
    assert_strict_json(registry)
    return registry


def write_r10_external_evidence_registry(
    *,
    output: str | Path,
    **kwargs: Any,
) -> Path:
    return write_json_artifact(
        output,
        build_r10_external_evidence_registry(**kwargs),
    )


def _case_records() -> list[dict[str, Any]]:
    supported_product_values = [
        "trend_direction",
        "risk_interval",
        "risk_distribution",
        "abnormal_segments",
        "mechanism_explanation",
        "outcome_feedback",
    ]
    return [
        {
            "case_id": "census_hps_policy_reaction_public_use_candidate",
            "scenario_family": "policy_reaction_survey",
            "domain": "public_policy_household_response",
            "source_owner": "U.S. Census Bureau",
            "source_name": "Household Pulse Survey Public Use File",
            "source_url": (
                "https://www.census.gov/programs-surveys/household-pulse-survey/"
                "data/datasets.html"
            ),
            "source_type": "official_public_use_microdata",
            "outcome_signal_type": "survey_response_distribution",
            "evidence_strength": "official_public_microdata_candidate",
            "ingestion_status": "candidate_source_not_ingested",
            "semantic_tags": [
                "policy_reaction",
                "household_survey",
                "public_use_file",
                "segment_weighting",
            ],
            "affected_segments": [
                "income_group",
                "employment_status",
                "household_composition",
                "geography",
            ],
            "mechanism_priors": [
                "economic_stress",
                "trust_in_institution",
                "access_constraint",
                "policy_salience",
            ],
            "risk_observation_window": "survey_release_or_weekly_phase_window",
            "supported_product_values": supported_product_values,
            "blocked_claims": [
                "HPS slice has been ingested",
                "policy reaction field validation is complete",
            ],
        },
        {
            "case_id": "bts_db1b_route_price_demand_candidate",
            "scenario_family": "transportation_price_demand",
            "domain": "air_travel_price_and_demand",
            "source_owner": "Bureau of Transportation Statistics",
            "source_name": "Origin and Destination Survey Data / DB1B",
            "source_url": (
                "https://www.bts.gov/topics/airlines-and-airports/"
                "origin-and-destination-survey-data"
            ),
            "source_type": "official_public_operational_data",
            "outcome_signal_type": "revealed_demand_and_price_distribution",
            "evidence_strength": "official_public_operational_data_candidate",
            "ingestion_status": "candidate_source_not_ingested",
            "semantic_tags": [
                "route_price_change",
                "airline_fare",
                "passenger_flow",
                "revealed_demand",
            ],
            "affected_segments": [
                "origin_destination_market",
                "carrier",
                "fare_bucket",
                "roundtrip_indicator",
            ],
            "mechanism_priors": [
                "price_sensitivity",
                "substitution_pressure",
                "route_dependence",
                "capacity_constraint",
            ],
            "risk_observation_window": "quarterly_route_market_window",
            "supported_product_values": supported_product_values,
            "blocked_claims": [
                "DB1B route slice has been ingested",
                "airfare change outcome validation is complete",
            ],
        },
        {
            "case_id": "dot_air_travel_consumer_report_complaint_candidate",
            "scenario_family": "air_travel_service_complaint",
            "domain": "air_travel_service_quality",
            "source_owner": "U.S. Department of Transportation",
            "source_name": "Air Travel Consumer Reports",
            "source_url": (
                "https://www.transportation.gov/individuals/"
                "aviation-consumer-protection/air-travel-consumer-reports"
            ),
            "source_type": "official_public_report_data",
            "outcome_signal_type": "complaint_or_submission_rate",
            "evidence_strength": "official_public_report_data_candidate",
            "ingestion_status": "candidate_source_not_ingested",
            "semantic_tags": [
                "air_travel_complaint",
                "service_friction",
                "consumer_submission",
                "operational_disruption",
            ],
            "affected_segments": [
                "passenger_category",
                "complaint_category",
                "carrier",
                "service_touchpoint",
            ],
            "mechanism_priors": [
                "service_friction",
                "fairness_perception",
                "accessibility_risk",
                "trust_loss",
            ],
            "risk_observation_window": "monthly_air_travel_consumer_report_window",
            "supported_product_values": supported_product_values,
            "blocked_claims": [
                "ATCR complaint slice has been ingested",
                "complaint-risk field validation is complete",
            ],
        },
    ]


def _coverage_summary(case_records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "external_source_count": len(case_records),
        "scenario_families": sorted({case["scenario_family"] for case in case_records}),
        "domains": sorted({case["domain"] for case in case_records}),
        "outcome_signal_types": sorted(
            {case["outcome_signal_type"] for case in case_records}
        ),
        "actual_public_data_ingested": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }


def _validate_unique_case_ids(case_records: list[dict[str, Any]]) -> None:
    seen = set()
    for index, case in enumerate(case_records):
        case_id = non_empty_string(case.get("case_id"), field=f"case_records[{index}].case_id")
        if case_id in seen:
            raise ValueError(f"duplicate case_id: {case_id}")
        seen.add(case_id)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output_path = write_r10_external_evidence_registry(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    artifact = json.loads(Path(output_path).read_text())
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["status"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
