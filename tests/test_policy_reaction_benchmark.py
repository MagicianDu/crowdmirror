import json
from pathlib import Path

import pytest

from benchmarks.policy_reaction import (
    build_policy_reaction_records_from_hps_rows,
    compute_policy_reaction_metrics,
    load_hps_public_rows,
    load_policy_reaction_records,
)


def test_compute_policy_reaction_metrics_from_hps_shaped_records():
    records = load_policy_reaction_records(
        Path("benchmarks/fixtures/policy_reaction_hps_smoke_records.json")
    )

    metrics = compute_policy_reaction_metrics(records)

    assert metrics["record_count"] == 4
    assert 0 <= metrics["choice_distribution_jsd"] < 0.01
    assert metrics["choice_distribution_jsd_record_count"] == 4
    assert metrics["ate_direction_accuracy"] == 1.0
    assert metrics["ate_direction_counts"] == {"correct": 4, "total": 4}
    assert metrics["segment_count"] == 3
    assert metrics["segment_rank_correlation"] >= 0.5
    assert metrics["worst_segment_rank_correlation"] >= 0.5
    assert metrics["segment_rank_correlation_by_segment"][
        "low_income_food_insecure"
    ] == 1.0
    assert metrics["source_ids"] == ["hps_htops_food_cost_core"]
    assert metrics["provenance"] == ["hps_htops_public_data_shaped_smoke_fixture"]
    json.dumps(metrics, allow_nan=False)


def test_build_policy_reaction_records_from_hps_public_rows():
    rows = load_hps_public_rows(
        Path("benchmarks/fixtures/policy_reaction_hps_public_rows_smoke.csv")
    )

    records = build_policy_reaction_records_from_hps_rows(rows)

    assert len(records) == 4
    first = records[0]
    assert first["record_id"] == "hps-public-row-001"
    assert first["source_id"] == "hps_htops_food_cost_core"
    assert first["segment"] == "low_income_food_insecure"
    assert first["provenance"] == "hps_htops_public_row_converter_smoke_fixture"
    assert set(first["observed_policy_reaction"]) == {
        "baseline_no_new_support",
        "food_subsidy_expansion",
        "cash_cost_of_living_rebate",
    }
    assert sum(first["observed_policy_reaction"].values()) == pytest.approx(1.0)
    assert first["observed_policy_reaction"]["food_subsidy_expansion"] > first[
        "observed_policy_reaction"
    ]["cash_cost_of_living_rebate"]
    assert first["predicted_policy_reaction"] == {
        "baseline_no_new_support": 0.14,
        "food_subsidy_expansion": 0.66,
        "cash_cost_of_living_rebate": 0.2,
    }
    assert first["true_ate"] > 0
    assert first["predicted_ate"] > 0

    metrics = compute_policy_reaction_metrics(records)
    assert metrics["record_count"] == 4
    assert metrics["source_ids"] == ["hps_htops_food_cost_core"]
    assert metrics["provenance"] == ["hps_htops_public_row_converter_smoke_fixture"]
    assert metrics["choice_distribution_jsd"] < 0.05
    assert metrics["ate_direction_accuracy"] == 1.0
    assert metrics["segment_count"] == 3
    json.dumps(metrics, allow_nan=False)


def test_policy_reaction_records_reject_missing_policy_distribution():
    with pytest.raises(ValueError, match="observed_policy_reaction"):
        compute_policy_reaction_metrics(
            [
                {
                    "record_id": "bad-record",
                    "source_id": "hps_htops_food_cost_core",
                    "segment": "low_income_food_insecure",
                    "predicted_policy_reaction": {
                        "baseline_no_new_support": 1.0,
                    },
                    "true_ate": 1.0,
                    "predicted_ate": 1.0,
                }
            ]
        )


def test_load_policy_reaction_records_rejects_empty_payload(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text("[]")

    with pytest.raises(ValueError, match="non-empty JSON list"):
        load_policy_reaction_records(path)


def test_build_policy_reaction_benchmark_artifact_is_strict_json():
    from experiments.policy_reaction_benchmark import (
        build_policy_reaction_benchmark_artifact,
    )

    records = load_policy_reaction_records(
        Path("benchmarks/fixtures/policy_reaction_hps_smoke_records.json")
    )
    artifact = build_policy_reaction_benchmark_artifact(
        records,
        artifact_id="policy-reaction-hps-smoke-001",
        source_manifest_path=(
            "experiments/results/policy_data_intake/hps-htops-food-cost-intake.json"
        ),
    )

    assert artifact["schema_version"] == "policy-reaction-benchmark-v0"
    assert artifact["artifact_id"] == "policy-reaction-hps-smoke-001"
    assert artifact["overall_status"] == "passed"
    assert artifact["calibration_status"] == "public_data_smoke"
    assert artifact["source_manifest_path"] == (
        "experiments/results/policy_data_intake/hps-htops-food-cost-intake.json"
    )
    assert artifact["benchmark_data"] == {
        "record_count": 4,
        "source_ids": ["hps_htops_food_cost_core"],
        "provenance": ["hps_htops_public_data_shaped_smoke_fixture"],
    }
    assert artifact["benchmark_metrics"]["choice_distribution_jsd"] < 0.01
    assert artifact["benchmark_metrics"]["ate_direction_accuracy"] == 1.0
    assert artifact["benchmark_metrics"]["segment_rank_correlation"] == 1.0
    assert artifact["claim_boundary"].endswith("not field validation.")
    json.dumps(artifact, allow_nan=False)


def test_write_policy_reaction_benchmark_artifact(tmp_path):
    from experiments.policy_reaction_benchmark import (
        write_policy_reaction_benchmark_artifact,
    )

    records = load_policy_reaction_records(
        Path("benchmarks/fixtures/policy_reaction_hps_smoke_records.json")
    )
    output_path = tmp_path / "policy-reaction-benchmark.json"

    written = write_policy_reaction_benchmark_artifact(
        output_path,
        records=records,
        artifact_id="policy-reaction-hps-smoke-test",
        source_manifest_path="experiments/results/policy_data_intake/hps-htops-food-cost-intake.json",
    )

    assert written == output_path
    persisted = json.loads(output_path.read_text())
    assert persisted["artifact_id"] == "policy-reaction-hps-smoke-test"
    assert persisted["overall_status"] == "passed"


def test_write_policy_reaction_benchmark_artifact_from_hps_public_rows(tmp_path):
    from experiments.policy_reaction_benchmark import (
        write_policy_reaction_benchmark_artifact_from_hps_rows,
    )

    output_path = tmp_path / "policy-reaction-public-rows.json"

    written = write_policy_reaction_benchmark_artifact_from_hps_rows(
        output_path,
        rows_path="benchmarks/fixtures/policy_reaction_hps_public_rows_smoke.csv",
        artifact_id="policy-reaction-hps-public-rows-smoke-test",
        source_manifest_path="experiments/results/policy_data_intake/hps-htops-food-cost-intake.json",
    )

    assert written == output_path
    persisted = json.loads(output_path.read_text())
    assert persisted["artifact_id"] == "policy-reaction-hps-public-rows-smoke-test"
    assert persisted["overall_status"] == "passed"
    assert persisted["benchmark_data"] == {
        "record_count": 4,
        "source_ids": ["hps_htops_food_cost_core"],
        "provenance": ["hps_htops_public_row_converter_smoke_fixture"],
    }
    assert persisted["claim_boundaries"][1].startswith("HPS/HTOPS public-row")
