import json
import subprocess
import sys

from experiments.r10_external_evidence_registry import (
    R10_EXTERNAL_EVIDENCE_REGISTRY_SCHEMA_VERSION,
    build_r10_external_evidence_registry,
)


def test_r10_external_evidence_registry_defines_source_backed_case_candidates():
    registry = build_r10_external_evidence_registry(
        artifact_id="r10-external-evidence-registry-test",
        run_id="r10-l0-run",
    )

    assert registry["schema_version"] == R10_EXTERNAL_EVIDENCE_REGISTRY_SCHEMA_VERSION
    assert registry["status"] == "r10_external_evidence_registry_ready_guarded"
    assert registry["method_positioning"] == {
        "research_problem": "Research 方法缺少独立外部案例证据，无法全面支撑 Product core method。",
        "product_goal": "人群反应趋势与风险区间模拟器",
        "r10_l0_goal": "建立可审计外部案例证据 registry，作为 R10 路线 B 和后续 A/B/C 组合输入。",
    }
    assert registry["evidence_contract"] == {
        "source_backed_only": True,
        "external_case_evidence_required_for_escalation": True,
        "actual_public_data_ingested": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "customer_visible": False,
    }
    assert registry["acceptance_gates"] == {
        "minimum_external_sources_present": True,
        "policy_reaction_source_present": True,
        "transportation_price_demand_source_present": True,
        "air_travel_complaint_source_present": True,
        "route_b_precedent_inputs_present": True,
        "actual_public_data_ingested": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert len(registry["case_records"]) >= 3
    assert len({case["case_id"] for case in registry["case_records"]}) == len(
        registry["case_records"]
    )
    assert {case["scenario_family"] for case in registry["case_records"]} >= {
        "policy_reaction_survey",
        "transportation_price_demand",
        "air_travel_service_complaint",
    }
    assert all(case["source_url"].startswith("https://") for case in registry["case_records"])
    assert all(case["ingestion_status"] == "candidate_source_not_ingested" for case in registry["case_records"])
    assert "actual public data ingestion has completed" in registry["blocked_claims"]
    json.dumps(registry, allow_nan=False)


def test_r10_external_evidence_registry_maps_cases_to_r9_routes_and_product_values():
    registry = build_r10_external_evidence_registry(
        artifact_id="r10-external-evidence-registry-test",
        run_id="r10-l0-run",
    )

    assert registry["route_input_contract"] == {
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
    }
    for case in registry["case_records"]:
        assert case["supported_product_values"] == [
            "trend_direction",
            "risk_interval",
            "risk_distribution",
            "abnormal_segments",
            "mechanism_explanation",
            "outcome_feedback",
        ]
        assert case["mechanism_priors"]
        assert case["semantic_tags"]
        assert case["risk_observation_window"]
        assert case["evidence_strength"] in {
            "official_public_microdata_candidate",
            "official_public_operational_data_candidate",
            "official_public_report_data_candidate",
        }


def test_r10_external_evidence_registry_cli_writes_artifact(tmp_path):
    output = tmp_path / "r10-external-evidence-registry.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r10_external_evidence_registry.py",
            "--artifact-id",
            "r10-external-evidence-registry-cli",
            "--run-id",
            "r10-l0-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r10-external-evidence-registry-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r10-external-evidence-registry-cli",
        "output": str(output),
        "status": "r10_external_evidence_registry_ready_guarded",
    }
