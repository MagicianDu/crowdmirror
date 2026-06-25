import csv
import io
import json
import subprocess
import sys
import zipfile

from experiments.r10_hps_policy_reaction_ingestion import (
    R10_HPS_POLICY_REACTION_INGESTION_SCHEMA_VERSION,
    build_r10_hps_policy_reaction_ingestion,
)


def test_r10_hps_policy_reaction_ingestion_reads_puf_zip_and_reports_coverage(tmp_path):
    zip_path = _write_hps_fixture_zip(tmp_path)

    artifact = build_r10_hps_policy_reaction_ingestion(
        artifact_id="r10-hps-policy-reaction-ingestion-test",
        run_id="r10-hps-l1-run",
        input_zip_path=zip_path,
    )

    assert artifact["schema_version"] == R10_HPS_POLICY_REACTION_INGESTION_SCHEMA_VERSION
    assert artifact["status"] == "r10_hps_policy_reaction_ingestion_ready_guarded"
    assert artifact["source_dataset"] == {
        "source_owner": "U.S. Census Bureau",
        "source_name": "HTOPS Household Pulse March 2026 PUF CSV",
        "release_window": "March 13, 2026 - March 30, 2026",
        "source_url": (
            "https://www2.census.gov/programs-surveys/demo/datasets/hhp/2026/"
            "topical/HTOPS_HPS_2603_CSV.zip"
        ),
    }
    assert artifact["ingestion_contract"] == {
        "source_backed_only": True,
        "actual_public_data_ingested": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
        "customer_visible": False,
    }
    assert artifact["data_inventory"]["zip_member_count"] == 3
    assert artifact["data_inventory"]["puf_csv_member"] == "HTOPS_HPS_2603_PUF.csv"
    assert artifact["data_profile"]["row_count"] == 3
    assert artifact["data_profile"]["column_count"] == 12
    assert artifact["data_profile"]["weight_columns_present"] == ["PWEIGHT", "HWEIGHT"]
    assert artifact["outcome_label_contract"]["outcome_columns"] == [
        "PRICECHANGE",
        "PRICESTRESS",
        "PRICECONCERN",
    ]
    assert artifact["outcome_summary"]["PRICECHANGE"] == {
        "valid_response_count": 3,
        "weighted_valid_total": 6.0,
        "response_distribution": {"1": 0.166667, "2": 0.333333, "3": 0.5},
    }
    assert artifact["outcome_summary"]["PRICECONCERN"]["valid_response_count"] == 2
    assert artifact["segment_coverage"]["REGION"] == {
        "present": True,
        "non_missing_count": 3,
        "unique_value_count": 2,
    }
    assert artifact["acceptance_gates"] == {
        "official_public_zip_read": True,
        "puf_csv_detected": True,
        "minimum_rows_present": True,
        "outcome_columns_present": True,
        "segment_columns_present": True,
        "actual_public_data_ingested": True,
        "field_outcome_validated": False,
        "runtime_default_allowed": False,
    }
    assert "field_outcome_validated=true" in artifact["blocked_claims"]
    json.dumps(artifact, allow_nan=False)


def test_r10_hps_policy_reaction_ingestion_cli_writes_artifact(tmp_path):
    zip_path = _write_hps_fixture_zip(tmp_path)
    output = tmp_path / "r10-hps-policy-reaction-ingestion.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r10_hps_policy_reaction_ingestion.py",
            "--artifact-id",
            "r10-hps-policy-reaction-ingestion-cli",
            "--run-id",
            "r10-hps-l1-run",
            "--input-zip",
            str(zip_path),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == "r10-hps-policy-reaction-ingestion-v1"
    assert json.loads(completed.stdout) == {
        "artifact_id": "r10-hps-policy-reaction-ingestion-cli",
        "output": str(output),
        "status": "r10_hps_policy_reaction_ingestion_ready_guarded",
    }


def _write_hps_fixture_zip(tmp_path):
    zip_path = tmp_path / "HTOPS_HPS_2603_CSV.zip"
    rows = [
        {
            "SCRAMID": "r1",
            "PWEIGHT": "1",
            "HWEIGHT": "1",
            "REGION": "1",
            "METRO_STATUS": "1",
            "RHHINCOME": "2",
            "RRACETH": "1",
            "TAGE": "35",
            "ESEX": "1",
            "PRICECHANGE": "1",
            "PRICESTRESS": "2",
            "PRICECONCERN": "1",
        },
        {
            "SCRAMID": "r2",
            "PWEIGHT": "2",
            "HWEIGHT": "2",
            "REGION": "2",
            "METRO_STATUS": "1",
            "RHHINCOME": "3",
            "RRACETH": "2",
            "TAGE": "42",
            "ESEX": "2",
            "PRICECHANGE": "2",
            "PRICESTRESS": "1",
            "PRICECONCERN": "2",
        },
        {
            "SCRAMID": "r3",
            "PWEIGHT": "3",
            "HWEIGHT": "3",
            "REGION": "2",
            "METRO_STATUS": "2",
            "RHHINCOME": "-88",
            "RRACETH": "1",
            "TAGE": "60",
            "ESEX": "1",
            "PRICECHANGE": "3",
            "PRICESTRESS": "-88",
            "PRICECONCERN": "-99",
        },
    ]
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("HTOPS_HPS_2603_PUF.csv", csv_buffer.getvalue())
        archive.writestr("HTOPS_HPS_2603_REPWGT_PUF.csv", "SCRAMID,PWGT1\nr1,1\n")
        archive.writestr("HTOPS_HPS_2603_PUF_DATA_DICTIONARY_CSV.xlsx", "fixture")
    return zip_path
