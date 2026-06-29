from __future__ import annotations

import copy
from typing import Any

from experiments.r6_contracts import R6_CLAIM_BOUNDARY, assert_strict_json, non_empty_string


R6_CASE_TEMPLATE_SCHEMA_VERSION = "r6-case-template-v1"


R6_CASE_TEMPLATES: list[dict[str, Any]] = [
    {
        "schema_version": R6_CASE_TEMPLATE_SCHEMA_VERSION,
        "case_id": "generic-price-change",
        "case_type": "price_change",
        "industry_binding": "generic",
        "prior_segments": [
            {
                "segment_id": "sensitive_low_trust",
                "weight": 0.30,
                "static_traits": {"sensitivity": "high", "trust": "low", "substitution": "high"},
                "static_response_prior": {"accept": 0.28, "neutral": 0.25, "reject": 0.47},
                "uncertainty": 0.18,
                "source_refs": ["fixture:generic_price_change_prior"],
            },
            {
                "segment_id": "stable_high_trust",
                "weight": 0.45,
                "static_traits": {"sensitivity": "low", "trust": "high", "substitution": "low"},
                "static_response_prior": {"accept": 0.65, "neutral": 0.25, "reject": 0.10},
                "uncertainty": 0.10,
                "source_refs": ["fixture:generic_price_change_prior"],
            },
            {
                "segment_id": "pragmatic_switchers",
                "weight": 0.25,
                "static_traits": {"sensitivity": "medium", "trust": "medium", "substitution": "medium"},
                "static_response_prior": {"accept": 0.38, "neutral": 0.25, "reject": 0.37},
                "uncertainty": 0.14,
                "source_refs": ["fixture:generic_price_change_prior"],
            },
        ],
        "scenario": {
            "scenario_id": "generic_price_change_001",
            "change_type": "price",
            "impact_dimensions": ["cost_increase", "fairness_concern", "substitution_pressure"],
            "communication_plan": {
                "source": "official",
                "message_frame": "cost_pass_through",
                "mitigation": "loyalty_compensation",
            },
            "alternative_scenarios": ["no_compensation", "phased_release"],
            "source_refs": ["fixture:generic_price_change_scenario"],
        },
        "interaction_profile": {
            "delta_distribution": {"accept": -0.04, "neutral": -0.03, "reject": 0.07},
            "segment_shifts": [
                {
                    "segment_id": "sensitive_low_trust",
                    "mechanisms": ["fairness_concern", "peer_amplification", "substitution_pressure"],
                    "delta_distribution": {"accept": -0.07, "neutral": -0.05, "reject": 0.12},
                },
                {
                    "segment_id": "pragmatic_switchers",
                    "mechanisms": ["substitution_pressure"],
                    "delta_distribution": {"accept": -0.04, "neutral": -0.02, "reject": 0.06},
                },
                {
                    "segment_id": "stable_high_trust",
                    "mechanisms": ["official_trust_buffer"],
                    "delta_distribution": {"accept": -0.01, "neutral": -0.01, "reject": 0.02},
                },
            ],
        },
        "outcome": {
            "release_id": "generic_price_change_release_001",
            "metrics": {
                "observed_reject_proxy": 0.41,
                "complaint_rate": 0.042,
                "negative_sentiment_rate": 0.36,
                "conversion_delta": -0.11,
            },
        },
        "claim_boundaries": [R6_CLAIM_BOUNDARY],
    },
    {
        "schema_version": R6_CASE_TEMPLATE_SCHEMA_VERSION,
        "case_id": "generic-rights-rule-change",
        "case_type": "rights_rule_change",
        "industry_binding": "generic",
        "prior_segments": [
            {
                "segment_id": "rights_dependent_low_trust",
                "weight": 0.34,
                "static_traits": {"sensitivity": "high", "trust": "low", "substitution": "medium"},
                "static_response_prior": {"accept": 0.20, "neutral": 0.30, "reject": 0.50},
                "uncertainty": 0.20,
                "source_refs": ["fixture:generic_rule_change_prior"],
            },
            {
                "segment_id": "low_usage_high_trust",
                "weight": 0.40,
                "static_traits": {"sensitivity": "low", "trust": "high", "substitution": "low"},
                "static_response_prior": {"accept": 0.58, "neutral": 0.28, "reject": 0.14},
                "uncertainty": 0.12,
                "source_refs": ["fixture:generic_rule_change_prior"],
            },
            {
                "segment_id": "rule_watchers",
                "weight": 0.26,
                "static_traits": {"sensitivity": "medium", "trust": "medium", "substitution": "medium"},
                "static_response_prior": {"accept": 0.34, "neutral": 0.32, "reject": 0.34},
                "uncertainty": 0.16,
                "source_refs": ["fixture:generic_rule_change_prior"],
            },
        ],
        "scenario": {
            "scenario_id": "generic_rights_rule_change_001",
            "change_type": "rule",
            "impact_dimensions": ["rights_reduction", "fairness_concern", "trust_shock"],
            "communication_plan": {
                "source": "official",
                "message_frame": "policy_consistency",
                "mitigation": "grandfathering_window",
            },
            "alternative_scenarios": ["immediate_change", "appeal_channel"],
            "source_refs": ["fixture:generic_rule_change_scenario"],
        },
        "interaction_profile": {
            "delta_distribution": {"accept": -0.03, "neutral": -0.04, "reject": 0.07},
            "segment_shifts": [
                {
                    "segment_id": "rights_dependent_low_trust",
                    "mechanisms": ["rights_loss_salience", "peer_amplification", "trust_shock"],
                    "delta_distribution": {"accept": -0.08, "neutral": -0.04, "reject": 0.12},
                },
                {
                    "segment_id": "rule_watchers",
                    "mechanisms": ["procedural_fairness_discussion"],
                    "delta_distribution": {"accept": -0.04, "neutral": -0.02, "reject": 0.06},
                },
                {
                    "segment_id": "low_usage_high_trust",
                    "mechanisms": ["official_trust_buffer"],
                    "delta_distribution": {"accept": -0.01, "neutral": -0.01, "reject": 0.02},
                },
            ],
        },
        "outcome": {
            "release_id": "generic_rule_change_release_001",
            "metrics": {
                "observed_reject_proxy": 0.43,
                "complaint_rate": 0.048,
                "negative_sentiment_rate": 0.39,
                "conversion_delta": -0.08,
            },
        },
        "claim_boundaries": [R6_CLAIM_BOUNDARY],
    },
    {
        "schema_version": R6_CASE_TEMPLATE_SCHEMA_VERSION,
        "case_id": "generic-public-service-policy-change",
        "case_type": "public_service_policy_change",
        "industry_binding": "generic",
        "prior_segments": [
            {
                "segment_id": "service_dependent_low_trust",
                "weight": 0.32,
                "static_traits": {"sensitivity": "high", "trust": "low", "substitution": "low"},
                "static_response_prior": {"accept": 0.24, "neutral": 0.29, "reject": 0.47},
                "uncertainty": 0.19,
                "source_refs": ["fixture:generic_policy_change_prior"],
            },
            {
                "segment_id": "low_dependency_high_trust",
                "weight": 0.37,
                "static_traits": {"sensitivity": "low", "trust": "high", "substitution": "medium"},
                "static_response_prior": {"accept": 0.62, "neutral": 0.26, "reject": 0.12},
                "uncertainty": 0.12,
                "source_refs": ["fixture:generic_policy_change_prior"],
            },
            {
                "segment_id": "community_watchers",
                "weight": 0.31,
                "static_traits": {"sensitivity": "medium", "trust": "medium", "substitution": "low"},
                "static_response_prior": {"accept": 0.36, "neutral": 0.33, "reject": 0.31},
                "uncertainty": 0.15,
                "source_refs": ["fixture:generic_policy_change_prior"],
            },
        ],
        "scenario": {
            "scenario_id": "generic_public_service_policy_change_001",
            "change_type": "policy",
            "impact_dimensions": ["access_constraint", "service_reliability_concern", "equity_concern"],
            "communication_plan": {
                "source": "official",
                "message_frame": "capacity_management",
                "mitigation": "priority_support_channel",
            },
            "alternative_scenarios": ["no_support_channel", "community_explanation"],
            "source_refs": ["fixture:generic_policy_change_scenario"],
        },
        "interaction_profile": {
            "delta_distribution": {"accept": -0.02, "neutral": -0.05, "reject": 0.07},
            "segment_shifts": [
                {
                    "segment_id": "service_dependent_low_trust",
                    "mechanisms": ["access_anxiety", "community_amplification", "equity_concern"],
                    "delta_distribution": {"accept": -0.07, "neutral": -0.05, "reject": 0.12},
                },
                {
                    "segment_id": "community_watchers",
                    "mechanisms": ["equity_concern_discussion"],
                    "delta_distribution": {"accept": -0.03, "neutral": -0.03, "reject": 0.06},
                },
                {
                    "segment_id": "low_dependency_high_trust",
                    "mechanisms": ["official_trust_buffer"],
                    "delta_distribution": {"accept": -0.01, "neutral": -0.01, "reject": 0.02},
                },
            ],
        },
        "outcome": {
            "release_id": "generic_policy_change_release_001",
            "metrics": {
                "observed_reject_proxy": 0.40,
                "complaint_rate": 0.044,
                "negative_sentiment_rate": 0.37,
                "conversion_delta": -0.05,
            },
        },
        "claim_boundaries": [R6_CLAIM_BOUNDARY],
    },
]


def get_r6_case_template(case_id: str) -> dict[str, Any]:
    case_id = non_empty_string(case_id, field="case_id")
    for template in R6_CASE_TEMPLATES:
        if template["case_id"] == case_id:
            payload = copy.deepcopy(template)
            assert_strict_json(payload)
            return payload
    raise ValueError(f"unknown R6 case template: {case_id}")
