from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.r6_case_templates import R6_CASE_TEMPLATES
from experiments.r13_llm_rule_structured_rollout import (
    build_r13_llm_rule_structured_rollout,
    write_r13_llm_rule_structured_rollout,
)


def test_r13_rollout_uses_llm_rules_once_and_expands_to_10k_individuals():
    calls: list[dict[str, str]] = []

    def fake_llm_rule_generator(system: str, user: str) -> str:
        calls.append({"system": system, "user": user})
        return json.dumps(
            {
                "rules": [
                    {
                        "segment_id": "sensitive_low_trust",
                        "persona_rule": "低信任高敏感人群会放大公平感知与替代压力。",
                        "reject_delta": 0.16,
                        "volatility": 0.08,
                        "mechanisms": ["fairness_concern", "peer_amplification"],
                    },
                    {
                        "segment_id": "stable_high_trust",
                        "persona_rule": "高信任稳定人群主要受官方解释缓冲。",
                        "reject_delta": 0.03,
                        "volatility": 0.03,
                        "mechanisms": ["official_trust_buffer"],
                    },
                    {
                        "segment_id": "pragmatic_switchers",
                        "persona_rule": "实用换乘人群会根据替代选项调整接受度。",
                        "reject_delta": 0.09,
                        "volatility": 0.05,
                        "mechanisms": ["substitution_pressure"],
                    },
                ]
            },
            ensure_ascii=False,
        )

    artifact = build_r13_llm_rule_structured_rollout(
        artifact_id="r13-test-rollout",
        run_id="r13-test-run",
        case_template=R6_CASE_TEMPLATES[0],
        synthetic_individual_count=10_000,
        rule_completion_fn=fake_llm_rule_generator,
        seed=123,
    )

    assert artifact["schema_version"] == "r13-llm-rule-structured-rollout-v1"
    assert artifact["status"] == "r13_llm_rule_structured_rollout_ready_guarded"
    assert artifact["synthetic_population"]["individual_count"] == 10_000
    assert artifact["synthetic_population"]["segment_count"] == 3
    assert artifact["llm_rule_generation"]["llm_call_count"] == 1
    assert len(calls) == 1
    assert artifact["llm_rule_generation"]["max_allowed_llm_calls"] == 3
    assert artifact["acceptance_gates"]["llm_calls_not_per_individual"] is True
    assert artifact["acceptance_gates"]["synthetic_population_10k_met"] is True
    assert artifact["acceptance_gates"]["field_outcome_validated"] is False
    assert artifact["acceptance_gates"]["product_default_allowed"] is False
    assert artifact["acceptance_gates"]["runtime_default_allowed"] is False
    assert artifact["structured_rollout"]["individuals_evaluated"] == 10_000
    assert artifact["structured_rollout"]["interaction_reject_rate"] > artifact[
        "structured_rollout"
    ]["static_reject_rate"]
    assert artifact["structured_rollout"]["risk_interval"]["lower"] <= artifact[
        "structured_rollout"
    ]["interaction_reject_rate"] <= artifact["structured_rollout"]["risk_interval"][
        "upper"
    ]
    assert artifact["structured_rollout"]["top_risk_segments"][0]["segment_id"] == (
        "sensitive_low_trust"
    )
    assert "fairness_concern" in artifact["structured_rollout"]["mechanism_summary"]
    assert "not_field_validated" in artifact["risk_flags"]


def test_r13_rollout_rejects_unknown_or_missing_segment_rules():
    def bad_rule_generator(system: str, user: str) -> str:
        return json.dumps(
            {
                "rules": [
                    {
                        "segment_id": "unknown_segment",
                        "persona_rule": "bad",
                        "reject_delta": 0.1,
                        "volatility": 0.1,
                        "mechanisms": ["bad"],
                    }
                ]
            }
        )

    with pytest.raises(ValueError, match="unknown segment_id"):
        build_r13_llm_rule_structured_rollout(
            artifact_id="r13-bad-rollout",
            run_id="r13-bad-run",
            case_template=R6_CASE_TEMPLATES[0],
            synthetic_individual_count=10_000,
            rule_completion_fn=bad_rule_generator,
        )


def test_r13_rollout_writer_outputs_current_artifact(tmp_path: Path):
    output = tmp_path / "r13-rollout.json"

    written = write_r13_llm_rule_structured_rollout(
        output,
        artifact_id="r13-writer-test",
        run_id="r13-writer-run",
        case_template=R6_CASE_TEMPLATES[0],
        synthetic_individual_count=12_000,
        seed=7,
    )

    artifact = json.loads(written.read_text())
    assert written == output
    assert artifact["synthetic_population"]["individual_count"] == 12_000
    assert artifact["llm_rule_generation"]["rule_source"] == "offline_fixture_llm_shape"
    assert artifact["acceptance_gates"]["llm_rule_generation_present"] is True
    assert artifact["claim_boundary"].startswith("R13 structured rollout")
