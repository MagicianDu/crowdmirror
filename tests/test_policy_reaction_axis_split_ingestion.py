import json

from experiments.policy_reaction_axis_split_ingestion import (
    build_policy_reaction_axis_split_ingestion_artifact,
    extract_axis_split_ingestion_artifact,
)


def test_build_axis_split_ingestion_artifact_projects_both_splits():
    rows = [
        _row("1001", "1", "1", "1"),
        _row("1002", "3", "0", "4"),
        _row("1003", "5", "0", "2"),
        _row("1004", "1", "1", "3"),
    ]
    artifact = build_policy_reaction_axis_split_ingestion_artifact(
        rows,
        artifact_id="axis-split-test",
        source_url="https://example.com/puf.zip",
        source_file_name="puf.zip",
        source_file_sha256="abc123",
        zip_member="puf.csv",
        modulus=2,
        calibration_remainders=(0,),
        evaluation_remainders=(1,),
    )

    assert artifact["schema_version"] == "policy-reaction-public-axis-split-v1"
    assert artifact["overall_status"] == "passed"
    assert artifact["data_profile"]["puf_row_count"] == 4
    assert artifact["splits"]["calibration"]["schema_version"] == "policy-reaction-public-axis-ingestion-v1"
    assert artifact["splits"]["evaluation"]["schema_version"] == "policy-reaction-public-axis-ingestion-v1"
    json.dumps(artifact, allow_nan=False)


def test_extract_axis_split_projection_returns_strict_json_copy():
    rows = [
        _row("1001", "1", "1", "1"),
        _row("1002", "3", "0", "4"),
        _row("1003", "5", "0", "2"),
        _row("1004", "1", "1", "3"),
    ]
    artifact = build_policy_reaction_axis_split_ingestion_artifact(
        rows,
        artifact_id="axis-split-test",
        source_url="https://example.com/puf.zip",
        source_file_name="puf.zip",
        source_file_sha256="abc123",
        zip_member="puf.csv",
        modulus=2,
        calibration_remainders=(0,),
        evaluation_remainders=(1,),
    )
    projection = extract_axis_split_ingestion_artifact(artifact, "evaluation")
    assert projection["schema_version"] == "policy-reaction-public-axis-ingestion-v1"
    assert projection["source"]["source_split"] == "evaluation"


def _row(scramid: str, income_code: str, anywork_code: str, price_stress_code: str) -> dict[str, str]:
    return {
        "SCRAMID": scramid,
        "CURFOODSUF": "3",
        "CHILDFOOD": "2",
        "EXPNS_DIF": "3",
        "PRICECHNG": "1",
        "PRICESTRESS": price_stress_code,
        "WRKLOSSRV": "2",
        "RFAM_INCOME": income_code,
        "THHLD_NUMKID_TOPICAL": "1",
        "ANYWORK": anywork_code,
        "TAGE1": "40",
        "PWEIGHT": "1.0",
        "DIVISION": "1",
        "METRO_STATUS": "1",
    }
