import json
from pathlib import Path

from experiments.policy_reaction_public_ingestion import (
    build_policy_reaction_public_ingestion_artifact,
    load_htops_2506_puf_rows,
    write_policy_reaction_public_ingestion_artifact,
)


def test_build_public_ingestion_artifact_from_official_shape_puf_rows():
    rows = load_htops_2506_puf_rows(
        Path("benchmarks/fixtures/htops_hps_2506_puf_official_shape_smoke.csv")
    )

    artifact = build_policy_reaction_public_ingestion_artifact(
        rows,
        artifact_id="policy-reaction-htops-2506-ingestion-smoke-test",
        source_url=(
            "https://www2.census.gov/programs-surveys/demo/datasets/hhp/2025/"
            "topical/HTOPS_HPS_2506_CSV.zip"
        ),
        source_file_name="HTOPS_HPS_2506_CSV.zip",
        source_file_sha256="test-sha256",
        zip_member="HTOPS_HPS_2506_PUF.csv",
    )

    assert artifact["schema_version"] == "policy-reaction-public-data-ingestion-v1"
    assert artifact["artifact_id"] == "policy-reaction-htops-2506-ingestion-smoke-test"
    assert artifact["source"]["source_id"] == "hps_htops_food_cost_core"
    assert artifact["source"]["source_release_id"] == "htops_hps_2506"
    assert artifact["source"]["source_file_sha256"] == "test-sha256"
    assert artifact["data_profile"]["puf_row_count"] == 4
    assert artifact["data_profile"]["usable_row_count"] == 3
    assert artifact["data_profile"]["skipped_row_count"] == 1
    assert artifact["data_profile"]["segment_counts"] == {
        "fixed_income_inflation_stressed": 1,
        "low_income_food_insecure": 1,
        "working_family_price_stressed": 1,
    }
    assert artifact["data_profile"]["required_field_coverage"] == {
        "all_present": True,
        "missing_fields": [],
    }
    assert set(artifact["observed_policy_reaction_summary"]["by_segment"]) == {
        "fixed_income_inflation_stressed",
        "low_income_food_insecure",
        "working_family_price_stressed",
    }
    low_income = artifact["observed_policy_reaction_summary"]["by_segment"][
        "low_income_food_insecure"
    ]
    assert low_income["row_count"] == 1
    assert low_income["mean_policy_reaction"]["food_subsidy_expansion"] > low_income[
        "mean_policy_reaction"
    ]["baseline_no_new_support"]
    assert artifact["claim_boundary"].endswith("not model-quality validation.")
    json.dumps(artifact, allow_nan=False)


def test_write_public_ingestion_artifact_from_official_shape_rows(tmp_path):
    output_path = tmp_path / "policy-reaction-ingestion.json"

    written = write_policy_reaction_public_ingestion_artifact(
        output_path,
        puf_path="benchmarks/fixtures/htops_hps_2506_puf_official_shape_smoke.csv",
        artifact_id="policy-reaction-htops-2506-ingestion-smoke-test",
        source_url="https://example.invalid/official.zip",
        source_file_name="official.zip",
        source_file_sha256="test-sha256",
        zip_member="HTOPS_HPS_2506_PUF.csv",
    )

    assert written == output_path
    persisted = json.loads(output_path.read_text())
    assert persisted["artifact_id"] == "policy-reaction-htops-2506-ingestion-smoke-test"
    assert persisted["overall_status"] == "passed"
