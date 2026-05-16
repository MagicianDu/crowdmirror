import json
from pathlib import Path

from experiments.policy_reaction_public_ingestion import load_htops_2506_puf_rows
from experiments.policy_reaction_split_ingestion import (
    build_policy_reaction_split_ingestion_artifact,
    extract_split_ingestion_artifact,
    write_policy_reaction_split_ingestion_artifacts,
)


def test_build_split_ingestion_artifact_separates_calibration_and_evaluation():
    rows = load_htops_2506_puf_rows(
        Path("benchmarks/fixtures/htops_hps_2506_puf_split_shape_smoke.csv")
    )

    artifact = build_policy_reaction_split_ingestion_artifact(
        rows,
        artifact_id="policy-reaction-htops-2506-split-smoke-test",
        source_url="https://example.invalid/HTOPS_HPS_2506_CSV.zip",
        source_file_name="HTOPS_HPS_2506_CSV.zip",
        source_file_sha256="test-sha256",
        zip_member="HTOPS_HPS_2506_PUF.csv",
    )

    assert artifact["schema_version"] == "policy-reaction-public-data-split-v1"
    assert artifact["overall_status"] == "passed"
    assert artifact["split_config"] == {
        "assignment_field": "SCRAMID",
        "assignment_method": "sha256_modulo",
        "calibration_remainders": [0],
        "evaluation_remainders": [1],
        "modulus": 2,
    }
    assert artifact["splits"]["calibration"]["data_profile"]["puf_row_count"] == 2
    assert artifact["splits"]["evaluation"]["data_profile"]["puf_row_count"] == 2
    assert artifact["splits"]["calibration"]["overall_status"] == "passed"
    assert artifact["splits"]["evaluation"]["overall_status"] == "passed"
    assert set(
        artifact["splits"]["evaluation"]["observed_policy_reaction_summary"][
            "by_segment"
        ]
    )
    json.dumps(artifact, allow_nan=False)


def test_extract_split_ingestion_artifact_returns_benchmark_compatible_projection():
    rows = load_htops_2506_puf_rows(
        Path("benchmarks/fixtures/htops_hps_2506_puf_split_shape_smoke.csv")
    )
    artifact = build_policy_reaction_split_ingestion_artifact(
        rows,
        artifact_id="policy-reaction-htops-2506-split-smoke-test",
        source_url="https://example.invalid/HTOPS_HPS_2506_CSV.zip",
        source_file_name="HTOPS_HPS_2506_CSV.zip",
        source_file_sha256="test-sha256",
        zip_member="HTOPS_HPS_2506_PUF.csv",
    )

    evaluation = extract_split_ingestion_artifact(artifact, "evaluation")

    assert evaluation["schema_version"] == "policy-reaction-public-data-ingestion-v1"
    assert evaluation["artifact_id"] == (
        "policy-reaction-htops-2506-split-smoke-test-evaluation"
    )
    assert evaluation["source"]["source_split"] == "evaluation"
    assert evaluation["claim_boundaries"][0].startswith(
        "Held-out official HPS/HTOPS split"
    )


def test_write_split_ingestion_artifacts(tmp_path):
    output = tmp_path / "split.json"
    calibration_output = tmp_path / "calibration.json"
    evaluation_output = tmp_path / "evaluation.json"

    written = write_policy_reaction_split_ingestion_artifacts(
        output,
        calibration_output_path=calibration_output,
        evaluation_output_path=evaluation_output,
        puf_path="benchmarks/fixtures/htops_hps_2506_puf_split_shape_smoke.csv",
        artifact_id="policy-reaction-htops-2506-split-smoke-test",
        source_url="https://example.invalid/HTOPS_HPS_2506_CSV.zip",
        source_file_name="HTOPS_HPS_2506_CSV.zip",
        source_file_sha256="test-sha256",
        zip_member="HTOPS_HPS_2506_PUF.csv",
    )

    assert written == {
        "calibration_output_path": str(calibration_output),
        "evaluation_output_path": str(evaluation_output),
        "output_path": str(output),
        "status": "passed",
    }
    assert json.loads(output.read_text())["schema_version"] == (
        "policy-reaction-public-data-split-v1"
    )
    assert json.loads(evaluation_output.read_text())["source"]["source_split"] == (
        "evaluation"
    )
