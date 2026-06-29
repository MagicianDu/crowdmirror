import json
import subprocess
import sys

from experiments.lcdu_anes_public_microdata_ingestion import (
    build_lcdu_anes_public_microdata_ingestion_artifact,
    load_anes_sda_subset_rows,
    write_lcdu_anes_public_microdata_ingestion_artifact,
)


FIXTURE = "benchmarks/fixtures/anes2024_sda_lcdu_subset_smoke.csv"


def test_build_anes_microdata_ingestion_materializes_targets_and_segments():
    rows = load_anes_sda_subset_rows(FIXTURE)
    artifact = build_lcdu_anes_public_microdata_ingestion_artifact(
        rows,
        artifact_id="lcdu-anes-2024-sda-public-microdata-test",
        source_file_name="fixture.csv",
        source_file_sha256="fixture-sha256",
    )

    assert artifact["schema_version"] == "lcdu-anes-public-microdata-ingestion-v1"
    assert artifact["overall_status"] == (
        "segment_target_distributions_materialized_with_partial_schema"
    )
    assert artifact["data_profile"]["row_count"] == 8
    assert artifact["data_profile"]["unique_case_id_count"] == 8
    assert artifact["source"]["source_extract_type"] == (
        "sda_custom_subset_public_use_microdata"
    )
    assert artifact["segment_schema"]["segment_key_axes"] == [
        "party_or_ideology",
        "income",
    ]

    health = artifact["target_distributions"][
        "public_health_medical_insurance_attitude_v1"
    ]
    assert health["valid_substantive_n"] == 6
    assert health["overall"]["policy_counts"] == {
        "government_insurance_plan": 3,
        "mixed_or_middle_position": 1,
        "private_insurance_plan": 2,
    }
    assert health["segment_schema_coverage"]["missing_required_axes"] == [
        "health_insurance_context"
    ]

    climate = artifact["target_distributions"][
        "climate_energy_regulation_attitude_v1"
    ]
    assert climate["valid_substantive_n"] == 6
    assert climate["overall"]["policy_probabilities"] == {
        "support_more_regulation_or_spending": 0.5,
        "mixed_or_status_quo": 0.166666666667,
        "oppose_more_regulation_or_spending": 0.333333333333,
    }
    assert climate["segment_schema_coverage"]["missing_required_axes"] == [
        "region",
        "urbanicity",
    ]
    assert set(artifact["splits"]) == {"calibration", "heldout", "test"}
    assert "not_model_validation" in artifact["risk_flags"]
    json.dumps(artifact, allow_nan=False)


def test_write_anes_microdata_ingestion_artifact(tmp_path):
    output = tmp_path / "anes-ingestion.json"

    written = write_lcdu_anes_public_microdata_ingestion_artifact(
        output,
        input_csv=FIXTURE,
        artifact_id="lcdu-anes-2024-sda-public-microdata-test",
        source_file_sha256="fixture-sha256",
    )

    assert written["output_path"] == str(output)
    persisted = json.loads(output.read_text())
    assert persisted["artifact_id"] == "lcdu-anes-2024-sda-public-microdata-test"
    assert persisted["source"]["source_file_sha256"] == "fixture-sha256"


def test_anes_microdata_ingestion_script_writes_json(tmp_path):
    output = tmp_path / "anes-ingestion.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_anes_public_microdata_ingestion.py",
            "--input-csv",
            FIXTURE,
            "--output",
            str(output),
            "--artifact-id",
            "lcdu-anes-2024-sda-public-microdata-test",
            "--source-file-sha256",
            "fixture-sha256",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "artifact_id": "lcdu-anes-2024-sda-public-microdata-test",
        "output": str(output),
        "row_count": 8,
        "status": "segment_target_distributions_materialized_with_partial_schema",
        "task_count": 2,
    }
