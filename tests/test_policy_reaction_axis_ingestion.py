import json

from experiments.policy_reaction_axis_ingestion import (
    build_policy_reaction_public_axis_ingestion_artifact,
    write_policy_reaction_public_axis_ingestion_artifact,
)


def test_build_axis_ingestion_aggregates_product_compatible_axes():
    rows = [
        _puf_row("1", "1", "1", "3", "1", "2.0"),
        _puf_row("1", "2", "1", "3", "1", "1.0"),
        _puf_row("5", "1", "2", "4", "0", "3.0"),
    ]

    artifact = build_policy_reaction_public_axis_ingestion_artifact(
        rows,
        artifact_id="axis-ingestion-test",
        source_url="https://example.com/puf.zip",
        source_file_name="puf.zip",
        source_file_sha256="abc123",
        zip_member="puf.csv",
    )

    assert artifact["schema_version"] == "policy-reaction-public-axis-ingestion-v1"
    assert artifact["overall_status"] == "passed"
    assert artifact["data_profile"]["usable_row_count"] == 3
    assert artifact["data_profile"]["axis_segment_counts_by_axis"]["income_band"] >= 2
    income_low = artifact["observed_policy_reaction_summary"]["by_axis_segment"]["income_band=low"]
    assert income_low["row_count"] == 2
    assert income_low["weighted_row_mass"] == 3.0
    assert income_low["weighted_mean_policy_reaction"]["food_subsidy_expansion"] > 0.4
    json.dumps(artifact, allow_nan=False)


def test_write_axis_ingestion_artifact_writes_strict_json(tmp_path):
    csv_path = tmp_path / "mini.csv"
    csv_path.write_text(
        ",".join(_csv_header()) + "\n"
        + ",".join(_csv_row("1", "1", "1", "3", "1", "2.0")) + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "axis-ingestion.json"

    written = write_policy_reaction_public_axis_ingestion_artifact(
        output_path,
        puf_path=csv_path,
        artifact_id="axis-ingestion-write-test",
        source_url="https://example.com/puf.zip",
        source_file_name="puf.zip",
        source_file_sha256="abc123",
        zip_member="unused.csv",
    )

    assert written == output_path
    persisted = json.loads(output_path.read_text())
    assert persisted["artifact_id"] == "axis-ingestion-write-test"
    assert persisted["overall_status"] == "passed"


def _puf_row(
    income_code: str,
    child_food_code: str,
    kid_count: str,
    price_stress_code: str,
    anywork_code: str,
    weight: str,
) -> dict[str, str]:
    return dict(zip(_csv_header(), _csv_row(income_code, child_food_code, kid_count, price_stress_code, anywork_code, weight), strict=True))


def _csv_header() -> list[str]:
    return [
        "SCRAMID",
        "CURFOODSUF",
        "CHILDFOOD",
        "EXPNS_DIF",
        "PRICECHNG",
        "PRICESTRESS",
        "WRKLOSSRV",
        "RFAM_INCOME",
        "THHLD_NUMKID_TOPICAL",
        "ANYWORK",
        "TAGE1",
        "PWEIGHT",
        "DIVISION",
        "METRO_STATUS",
    ]


def _csv_row(
    income_code: str,
    child_food_code: str,
    kid_count: str,
    price_stress_code: str,
    anywork_code: str,
    weight: str,
) -> list[str]:
    return [
        "1001",
        "3",
        child_food_code,
        "3",
        "1",
        price_stress_code,
        "2",
        income_code,
        kid_count,
        anywork_code,
        "40",
        weight,
        "1",
        "1",
    ]
