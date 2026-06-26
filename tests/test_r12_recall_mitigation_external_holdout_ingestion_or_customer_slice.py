import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_recall_mitigation_external_holdout_ingestion_or_customer_slice import (
    R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_INGESTION_OR_CUSTOMER_SLICE_SCHEMA_VERSION,
    build_r12_recall_mitigation_external_holdout_ingestion_or_customer_slice,
)


def test_r12_external_holdout_or_customer_slice_contract_blocks_default():
    report = build_r12_recall_mitigation_external_holdout_ingestion_or_customer_slice(
        artifact_id=(
            "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-test"
        ),
        run_id="r12-l12-test",
        r12_recall_mitigation_independent_holdout_data=(
            _load_current_independent_data()
        ),
        r10_external_evidence_registry=_load_current_external_registry(),
    )

    assert report["schema_version"] == (
        R12_RECALL_MITIGATION_EXTERNAL_HOLDOUT_INGESTION_OR_CUSTOMER_SLICE_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice_ready_contract_blocked_no_raw_slice"
    )
    assert report["claim_level"] == "ingestion_or_customer_slice_contract_only"
    assert report["route_selection"] == {
        "selected_route": "external_public_holdout_first_customer_slice_compatible",
        "selection_reason": (
            "L11 found no independent dataset, no low-sensitive recall slice, "
            "and no customer-approved holdout; use registered official sources "
            "or a customer-approved slice before revalidation."
        ),
        "preferred_external_source_id": (
            "dot_air_travel_consumer_report_complaint_candidate"
        ),
        "customer_slice_fallback_enabled": True,
    }
    assert report["prioritized_source_handoff"] == [
        {
            "priority": 1,
            "case_id": "dot_air_travel_consumer_report_complaint_candidate",
            "domain": "air_travel_service_quality",
            "ingestion_status": "candidate_source_not_ingested",
            "target_next_artifact": "r12_dot_atcr_complaint_holdout_ingestion",
            "product_use": "service_change_complaint_risk_external_holdout",
        },
        {
            "priority": 2,
            "case_id": "bts_db1b_route_price_demand_candidate",
            "domain": "air_travel_price_and_demand",
            "ingestion_status": "candidate_source_not_ingested",
            "target_next_artifact": "r12_bts_db1b_price_demand_holdout_ingestion",
            "product_use": "price_change_revealed_demand_external_holdout",
        },
        {
            "priority": 3,
            "case_id": "census_hps_policy_reaction_public_use_candidate",
            "domain": "public_policy_household_response",
            "ingestion_status": "candidate_source_not_ingested",
            "target_next_artifact": "r12_hps_independent_wave_holdout_ingestion",
            "product_use": "policy_reaction_survey_external_holdout",
        },
    ]
    assert report["customer_slice_contract"] == {
        "accepted_file_types": ["csv", "jsonl"],
        "minimum_case_count": 10,
        "required_columns": [
            "case_id",
            "scenario_family",
            "segment_column",
            "segment_value",
            "static_prior_prediction",
            "interaction_prediction",
            "observed_outcome",
            "outcome_window_start",
            "outcome_window_end",
            "customer_approval_id",
            "source_ref",
        ],
        "optional_columns": [
            "complaint_count",
            "exposure_count",
            "price_change_pct",
            "policy_change_label",
            "mechanism_tags",
            "segment_sensitivity_level",
        ],
        "must_include_low_sensitive_or_customer_approved_axis": True,
        "must_exclude_l9_derivation_band_as_proof": True,
        "manual_prompt_or_persona_patch_allowed": False,
    }
    assert report["acceptance_gates"] == {
        "l11_data_gap_confirmed": True,
        "external_candidate_sources_registered": True,
        "ingestion_contract_ready": True,
        "customer_slice_contract_ready": True,
        "raw_external_or_customer_slice_present": False,
        "minimum_case_count_met": False,
        "customer_approval_present": False,
        "independent_holdout_revalidation_ready": False,
        "product_default_allowed": False,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert report["acceptance_decision"] == (
        "ready_to_ingest_external_or_customer_slice_keep_product_default_blocked"
    )
    assert report["next_required_artifact"] == (
        "r12_external_or_customer_holdout_raw_slice"
    )
    assert "raw external or customer holdout slice present" in report["blocked_claims"]
    json.dumps(report, allow_nan=False)


def test_r12_external_holdout_or_customer_slice_contract_cli_writes_artifact(tmp_path):
    independent_path = tmp_path / "r12-independent-data.json"
    external_path = tmp_path / "r10-external-evidence-registry.json"
    output = tmp_path / "r12-external-or-customer-slice.json"
    independent_path.write_text(
        json.dumps(_load_current_independent_data(), allow_nan=False)
    )
    external_path.write_text(
        json.dumps(_load_current_external_registry(), allow_nan=False)
    )

    completed = subprocess.run(
        [
            sys.executable,
            (
                "experiments/"
                "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice.py"
            ),
            "--artifact-id",
            "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-cli",
            "--run-id",
            "r12-l12-test",
            "--r12-recall-mitigation-independent-holdout-data-path",
            str(independent_path),
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
        "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": (
            "r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-cli"
        ),
        "output": str(output),
        "status": (
            "r12_recall_mitigation_external_holdout_ingestion_or_customer_slice_ready_contract_blocked_no_raw_slice"
        ),
    }


def _load_current_independent_data():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/r12_recall_mitigation_independent_holdout_data/"
            "r12-recall-mitigation-independent-holdout-data-current-001.json"
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
