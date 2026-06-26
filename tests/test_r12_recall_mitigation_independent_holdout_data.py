import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_recall_mitigation_independent_holdout_data import (
    R12_RECALL_MITIGATION_INDEPENDENT_HOLDOUT_DATA_SCHEMA_VERSION,
    build_r12_recall_mitigation_independent_holdout_data,
)


def test_r12_recall_mitigation_independent_holdout_data_blocks_product_default():
    report = build_r12_recall_mitigation_independent_holdout_data(
        artifact_id="r12-recall-mitigation-independent-holdout-data-test",
        run_id="r12-l11-test",
        hps_ingestion=_load_current_hps_ingestion(),
        r12_transfer_validation=_load_current_transfer_validation(),
        r12_recall_mitigation_holdout_validation=_load_current_holdout_validation(),
        r10_external_evidence_registry=_load_current_external_registry(),
    )

    assert report["schema_version"] == (
        R12_RECALL_MITIGATION_INDEPENDENT_HOLDOUT_DATA_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_recall_mitigation_independent_holdout_data_blocked_needs_external_or_customer_slice"
    )
    assert report["claim_level"] == "data_gap_audit_product_default_blocked"
    assert report["data_summary"] == {
        "hps_public_proxy_ingested": True,
        "evaluated_hps_case_count": 70,
        "derivation_band_case_count": 5,
        "same_dataset_non_derivation_case_count": 65,
        "same_dataset_non_derivation_recall_candidate_count": 5,
        "low_sensitive_case_count": 4,
        "low_sensitive_observed_high_risk_count": 0,
        "low_sensitive_recall_candidate_count": 0,
        "customer_approved_holdout_case_count": 0,
        "external_registry_candidate_count": 3,
        "ingested_external_independent_dataset_count": 0,
    }
    assert report["same_dataset_non_derivation_recall_candidates"] == [
        "hps_ESEX_1",
        "hps_RRACETH_1",
        "hps_TAGE_46",
        "hps_TAGE_64",
        "hps_TAGE_73",
    ]
    assert report["data_availability_ledger"] == [
        {
            "source_id": "current_hps_same_dataset_non_derivation_segments",
            "status": "available_but_not_independent_dataset",
            "case_count": 65,
            "recall_candidate_count": 5,
            "product_default_allowed": False,
            "block_reason": "same_public_proxy_dataset_not_independent_holdout",
        },
        {
            "source_id": "current_hps_low_sensitive_slice",
            "status": "available_but_no_observed_high_risk_recall_case",
            "case_count": 4,
            "observed_high_risk_count": 0,
            "recall_candidate_count": 0,
            "product_default_allowed": False,
            "block_reason": "low_sensitive_recall_not_evaluable",
        },
        {
            "source_id": "external_public_source_candidates",
            "status": "candidate_sources_registered_not_ingested",
            "case_count": 3,
            "ingested_case_count": 0,
            "product_default_allowed": False,
            "block_reason": "external_independent_data_not_ingested",
        },
        {
            "source_id": "customer_approved_holdout_slice",
            "status": "not_present",
            "case_count": 0,
            "product_default_allowed": False,
            "block_reason": "customer_outcome_or_approval_missing",
        },
    ]
    assert report["external_source_candidates"] == [
        {
            "case_id": "census_hps_policy_reaction_public_use_candidate",
            "domain": "public_policy_household_response",
            "ingestion_status": "candidate_source_not_ingested",
            "recommended_next_action": "ingest_or_slice_for_independent_holdout",
        },
        {
            "case_id": "bts_db1b_route_price_demand_candidate",
            "domain": "air_travel_price_and_demand",
            "ingestion_status": "candidate_source_not_ingested",
            "recommended_next_action": "ingest_or_slice_for_independent_holdout",
        },
        {
            "case_id": "dot_air_travel_consumer_report_complaint_candidate",
            "domain": "air_travel_service_quality",
            "ingestion_status": "candidate_source_not_ingested",
            "recommended_next_action": "ingest_or_slice_for_independent_holdout",
        },
    ]
    assert report["acceptance_gates"] == {
        "source_backed_public_proxy_present": True,
        "same_dataset_non_derivation_candidates_present": True,
        "independent_dataset_present": False,
        "independent_holdout_case_count_positive": False,
        "low_sensitive_recall_evaluable": False,
        "customer_approved_holdout_present": False,
        "external_candidate_sources_registered": True,
        "external_independent_data_ingested": False,
        "mitigation_independent_data_ready": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "block_product_default_prepare_external_or_customer_holdout_ingestion"
    )
    assert report["next_required_artifact"] == (
        "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice"
    )
    assert "independent holdout data exists" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_recall_mitigation_independent_holdout_data_cli_writes_artifact(tmp_path):
    hps_path = tmp_path / "hps-ingestion.json"
    transfer_path = tmp_path / "r12-transfer-validation.json"
    holdout_path = tmp_path / "r12-mitigation-holdout-validation.json"
    external_path = tmp_path / "r10-external-evidence-registry.json"
    output = tmp_path / "r12-recall-mitigation-independent-holdout-data.json"
    hps_path.write_text(json.dumps(_load_current_hps_ingestion(), allow_nan=False))
    transfer_path.write_text(
        json.dumps(_load_current_transfer_validation(), allow_nan=False)
    )
    holdout_path.write_text(
        json.dumps(_load_current_holdout_validation(), allow_nan=False)
    )
    external_path.write_text(
        json.dumps(_load_current_external_registry(), allow_nan=False)
    )

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_recall_mitigation_independent_holdout_data.py",
            "--artifact-id",
            "r12-recall-mitigation-independent-holdout-data-cli",
            "--run-id",
            "r12-l11-test",
            "--hps-ingestion-path",
            str(hps_path),
            "--r12-transfer-validation-path",
            str(transfer_path),
            "--r12-recall-mitigation-holdout-validation-path",
            str(holdout_path),
            "--r10-external-evidence-registry-path",
            str(external_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == (
        "r12-recall-mitigation-independent-holdout-data-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-recall-mitigation-independent-holdout-data-cli",
        "output": str(output),
        "status": (
            "r12_recall_mitigation_independent_holdout_data_blocked_needs_external_or_customer_slice"
        ),
    }


def _load_current_hps_ingestion():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r10_hps_policy_reaction_ingestion/"
            "r10-hps-policy-reaction-ingestion-current-001.json"
        ).read_text()
    )


def _load_current_transfer_validation():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_transfer_validation/"
            "r12-transfer-validation-current-001.json"
        ).read_text()
    )


def _load_current_holdout_validation():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_recall_mitigation_holdout_validation/"
            "r12-recall-mitigation-holdout-validation-current-001.json"
        ).read_text()
    )


def _load_current_external_registry():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r10_external_evidence_registry/"
            "r10-external-evidence-registry-current-001.json"
        ).read_text()
    )
