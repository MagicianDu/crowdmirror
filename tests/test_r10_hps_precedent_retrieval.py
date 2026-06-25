import json
import subprocess
import sys

from experiments.r10_hps_policy_reaction_ingestion import (
    build_r10_hps_policy_reaction_ingestion,
)
from experiments.r10_hps_precedent_retrieval import (
    R10_HPS_PRECEDENT_RETRIEVAL_SCHEMA_VERSION,
    build_r10_hps_precedent_retrieval,
)
from tests.test_r10_hps_policy_reaction_ingestion import _write_hps_fixture_zip


def test_r10_hps_precedent_retrieval_turns_ingestion_into_route_b_signal(tmp_path):
    ingestion = build_r10_hps_policy_reaction_ingestion(
        artifact_id="r10-hps-policy-reaction-ingestion-test",
        run_id="r10-route-b-run",
        input_zip_path=_write_hps_fixture_zip(tmp_path),
    )

    retrieval = build_r10_hps_precedent_retrieval(
        artifact_id="r10-hps-precedent-retrieval-test",
        run_id="r10-route-b-run",
        hps_ingestion=ingestion,
    )

    assert retrieval["schema_version"] == R10_HPS_PRECEDENT_RETRIEVAL_SCHEMA_VERSION
    assert retrieval["status"] == "r10_hps_precedent_retrieval_ready_guarded"
    assert retrieval["route_id"] == "route_b_semantic_precedent_retrieval"
    assert retrieval["retrieval_contract"] == {
        "source_backed_only": True,
        "uses_real_public_data_ingestion": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "customer_visible": False,
    }
    assert retrieval["source_refs"] == ["r10-hps-policy-reaction-ingestion-test"]
    assert retrieval["scenario_query"] == {
        "scenario_family": "policy_reaction_survey",
        "query_terms": [
            "price pressure",
            "household stress",
            "policy reaction",
            "risk segment",
        ],
        "outcome_focus": ["PRICECHANGE", "PRICESTRESS", "PRICECONCERN"],
    }
    assert retrieval["precedent_cases"][0]["case_id"] == "hps_price_pressure_public_use_precedent"
    assert retrieval["precedent_cases"][0]["row_count"] == 3
    assert retrieval["risk_ranking"]["ranking_basis"] == "PRICECONCERN.segment_outcome_profiles"
    assert retrieval["risk_ranking"]["top_segments"][:2] == [
        {
            "segment_column": "REGION",
            "segment_value": "2",
            "risk_proxy_share": 1.0,
            "weighted_valid_total": 2.0,
        },
        {
            "segment_column": "METRO_STATUS",
            "segment_value": "1",
            "risk_proxy_share": 0.666667,
            "weighted_valid_total": 3.0,
        },
    ]
    assert retrieval["metric_candidates"] == {
        "trend_signal": "price_pressure_risk_present",
        "risk_interval_proxy": {"lower": 0.0, "median": 0.666667, "upper": 1.0},
        "risk_ranking_quality": "computable_after_holdout_or_outcome_mapping",
        "decision_value_score": "not_computed_until_policy_action_set",
    }
    assert retrieval["acceptance_gates"] == {
        "source_ingestion_available": True,
        "precedent_case_constructed": True,
        "risk_ranking_constructed": True,
        "metric_candidates_constructed": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert "field_outcome_validated=true" in retrieval["blocked_claims"]
    json.dumps(retrieval, allow_nan=False)


def test_r10_hps_precedent_retrieval_cli_writes_artifact(tmp_path):
    ingestion = build_r10_hps_policy_reaction_ingestion(
        artifact_id="r10-hps-policy-reaction-ingestion-cli-input",
        run_id="r10-route-b-run",
        input_zip_path=_write_hps_fixture_zip(tmp_path),
    )
    ingestion_path = tmp_path / "hps-ingestion.json"
    ingestion_path.write_text(json.dumps(ingestion, allow_nan=False))
    output = tmp_path / "r10-hps-precedent-retrieval.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r10_hps_precedent_retrieval.py",
            "--artifact-id",
            "r10-hps-precedent-retrieval-cli",
            "--run-id",
            "r10-route-b-run",
            "--hps-ingestion-path",
            str(ingestion_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r10-hps-precedent-retrieval-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r10-hps-precedent-retrieval-cli",
        "output": str(output),
        "status": "r10_hps_precedent_retrieval_ready_guarded",
    }
