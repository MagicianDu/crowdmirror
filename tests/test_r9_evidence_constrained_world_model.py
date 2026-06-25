import json
import subprocess
import sys

from experiments.r9_evidence_constrained_world_model import (
    R9_CLAIM_BOUNDARY,
    R9_COMBINATION_IDS,
    R9_ROUTE_IDS,
    build_r9_world_model_bundle,
)


def test_r9_world_model_bundle_contains_routes_combinations_and_guard():
    bundle = build_r9_world_model_bundle(
        artifact_id="r9-world-model-bundle-test",
        run_id="r9-l0-run",
    )

    assert bundle["schema_version"] == "r9-world-model-bundle-v1"
    assert bundle["status"] == "r9_route_mvp_ready_guarded"
    assert bundle["product_positioning"] == "人群反应趋势与风险区间模拟器"
    assert bundle["claim_boundary"] == R9_CLAIM_BOUNDARY
    assert bundle["acceptance_gates"] == {
        "artifact_contracts_present": True,
        "route_artifacts_present": True,
        "route_mvp_outputs_present": True,
        "combination_matrix_present": True,
        "source_refs_present": True,
        "product_guard_consumable": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert set(bundle["artifacts"]) == {
        "r9_world_model_manifest",
        "r9_route_outputs",
        "r9_combination_matrix",
        "r9_product_support_gate",
    }
    assert set(bundle["artifacts"]["r9_route_outputs"]["routes"]) == set(R9_ROUTE_IDS)
    assert [
        item["combination_id"]
        for item in bundle["artifacts"]["r9_combination_matrix"]["combinations"]
    ] == R9_COMBINATION_IDS
    assert "R9 supports Product core method by default" in bundle["blocked_claims"]
    json.dumps(bundle, allow_nan=False)


def test_r9_routes_have_uniform_source_backed_metric_structure():
    bundle = build_r9_world_model_bundle(
        artifact_id="r9-world-model-bundle-test",
        run_id="r9-l0-run",
    )
    routes = bundle["artifacts"]["r9_route_outputs"]["routes"]

    for route_id in R9_ROUTE_IDS:
        route = routes[route_id]
        assert route["route_id"] == route_id
        assert route["source_refs"]
        assert route["claim_boundary"] == R9_CLAIM_BOUNDARY
        assert route["route_contract"] == {
            "source_backed_only": True,
            "llm_direct_prediction_allowed": False,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        }
        assert set(route["metrics"]) == {
            "trend_direction_accuracy",
            "interval_coverage",
            "risk_ranking_quality",
            "false_alarm_rate",
            "static_prior_miss_recovery_rate",
            "decision_value_score",
        }
        for metric in route["metrics"].values():
            assert metric["value"] is None
            assert metric["status"] == "not_computed_l0_contract_only"


def test_r9_routes_emit_minimum_trend_interval_risk_segment_mechanism_outputs():
    bundle = build_r9_world_model_bundle(
        artifact_id="r9-world-model-bundle-test",
        run_id="r9-task2-run",
    )
    routes = bundle["artifacts"]["r9_route_outputs"]["routes"]

    for route_id in R9_ROUTE_IDS:
        route = routes[route_id]
        assert route["route_status"] == "r9_route_mvp_output_ready_guarded"
        assert route["output_contract"] == {
            "trend_output_present": True,
            "risk_interval_present": True,
            "risk_distribution_present": True,
            "abnormal_segments_present": True,
            "mechanism_trace_present": True,
            "failure_reasons_present": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        }
        assert route["trend_output"]["direction"] in {
            "risk_increase",
            "risk_decrease",
            "risk_stable",
        }
        assert 0 <= route["trend_output"]["confidence"] <= 1
        interval = route["risk_interval"]
        assert interval["lower"] <= interval["median"] <= interval["upper"]
        assert 0 <= interval["lower"] <= 1
        assert 0 <= interval["upper"] <= 1
        assert route["risk_distribution"]
        assert all("segment_id" in item for item in route["risk_distribution"])
        assert route["abnormal_segments"]
        assert route["mechanism_trace"]
        assert route["failure_reasons"]
        assert route["field_outcome_validated"] is False
        assert route["runtime_default_allowed"] is False


def test_r9_combination_matrix_records_all_combinations_without_success_claims():
    bundle = build_r9_world_model_bundle(
        artifact_id="r9-world-model-bundle-test",
        run_id="r9-l0-run",
    )
    matrix = bundle["artifacts"]["r9_combination_matrix"]

    assert matrix["status"] == "r9_combination_matrix_contract_ready"
    assert matrix["baseline_ids"] == [
        "static_prior",
        "r6_learning_counterfactual",
        "r7_v2_guarded_baseline",
        "r8_diagnostic_method",
    ]
    for combination in matrix["combinations"]:
        assert combination["combination_id"] in R9_COMBINATION_IDS
        assert combination["route_ids"]
        assert combination["source_refs"]
        assert combination["metrics_schema"] == matrix["metrics_schema"]
        assert combination["claim_status"] == "not_evaluated_l0_contract_only"
        assert combination["field_outcome_validated"] is False
        assert combination["runtime_default_allowed"] is False


def test_r9_product_support_gate_blocks_field_and_runtime_claims():
    bundle = build_r9_world_model_bundle(
        artifact_id="r9-world-model-bundle-test",
        run_id="r9-l0-run",
    )
    gate = bundle["artifacts"]["r9_product_support_gate"]

    assert gate["status"] == "r9_product_support_gate_ready_guarded"
    assert gate["product_support_status"] == "contract_ready_not_method_validated"
    assert gate["field_outcome_validated"] is False
    assert gate["runtime_default_allowed"] is False
    assert gate["source_refs"]
    assert gate["allowed_claims"] == [
        "R9 artifact contract defines evidence-constrained routes and combination matrix.",
        "R9 can be evaluated against R6/R7/R8 baselines before Product escalation.",
    ]
    assert "R9 validated" in gate["blocked_claims"]
    assert "runtime default ready" in gate["blocked_claims"]


def test_r9_world_model_cli_writes_current_artifact(tmp_path):
    output = tmp_path / "r9-world-model-bundle.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r9_evidence_constrained_world_model.py",
            "--artifact-id",
            "r9-world-model-bundle-cli",
            "--run-id",
            "r9-l0-run",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r9-world-model-bundle-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r9-world-model-bundle-cli",
        "output": str(output),
        "status": "r9_route_mvp_ready_guarded",
    }
