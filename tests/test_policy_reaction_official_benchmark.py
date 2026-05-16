import json
from pathlib import Path

from experiments.policy_reaction_official_benchmark import (
    build_policy_reaction_official_segment_benchmark,
    load_json_artifact,
    write_policy_reaction_official_segment_benchmark,
)


def test_build_official_segment_benchmark_compares_ingestion_and_predictions():
    ingestion = load_json_artifact(
        Path(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-htops-2506-public-ingestion-001.json"
        )
    )
    predictions = load_json_artifact(
        Path("benchmarks/fixtures/policy_reaction_segment_predictions_smoke.json")
    )

    artifact = build_policy_reaction_official_segment_benchmark(
        ingestion,
        predictions,
        artifact_id="policy-reaction-official-segment-benchmark-smoke-test",
    )

    assert artifact["schema_version"] == "policy-reaction-official-segment-benchmark-v1"
    assert artifact["artifact_id"] == "policy-reaction-official-segment-benchmark-smoke-test"
    assert artifact["overall_status"] == "passed"
    assert artifact["calibration_status"] == "official_public_data_alignment_smoke"
    assert artifact["source_ingestion_artifact_id"] == (
        "policy-reaction-htops-2506-public-ingestion-001"
    )
    assert artifact["prediction_artifact_id"] == (
        "policy-reaction-segment-predictions-smoke-001"
    )
    assert artifact["segment_coverage"] == {
        "observed_segment_count": 4,
        "predicted_segment_count": 4,
        "matched_segment_count": 4,
        "coverage_rate": 1.0,
        "missing_predicted_segments": [],
        "extra_predicted_segments": [],
    }
    metrics = artifact["benchmark_metrics"]
    assert metrics["weighted_choice_distribution_jsd"] < 0.01
    assert metrics["worst_segment_choice_distribution_jsd"] < 0.01
    assert metrics["segment_rank_correlation"] >= 0.9
    assert metrics["worst_segment_rank_correlation"] >= 0.9
    assert artifact["segment_metrics"]["low_income_food_insecure"]["official_row_count"] == 123
    assert artifact["segment_metrics"]["low_income_food_insecure"][
        "choice_distribution_jsd"
    ] < 0.01
    assert artifact["claim_boundary"].endswith("not field validation.")
    json.dumps(artifact, allow_nan=False)


def test_official_segment_benchmark_blocks_when_prediction_segments_are_missing():
    ingestion = load_json_artifact(
        Path(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-htops-2506-public-ingestion-001.json"
        )
    )
    predictions = {
        "schema_version": "policy-reaction-segment-predictions-v1",
        "artifact_id": "missing-segment-predictions",
        "segment_predictions": {
            "low_income_food_insecure": {
                "policy_probabilities": {
                    "baseline_no_new_support": 0.2,
                    "cash_cost_of_living_rebate": 0.3,
                    "food_subsidy_expansion": 0.5,
                }
            }
        },
    }

    artifact = build_policy_reaction_official_segment_benchmark(
        ingestion,
        predictions,
        artifact_id="policy-reaction-official-segment-benchmark-missing-test",
    )

    assert artifact["overall_status"] == "blocked_for_model_quality_claim"
    assert artifact["segment_coverage"]["coverage_rate"] == 0.25
    assert artifact["segment_coverage"]["missing_predicted_segments"] == [
        "fixed_income_inflation_stressed",
        "general_population_cost_pressure",
        "working_family_price_stressed",
    ]


def test_write_official_segment_benchmark_artifact(tmp_path):
    output_path = tmp_path / "official-segment-benchmark.json"

    written = write_policy_reaction_official_segment_benchmark(
        output_path,
        ingestion_artifact_path=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-htops-2506-public-ingestion-001.json"
        ),
        predictions_artifact_path=(
            "benchmarks/fixtures/policy_reaction_segment_predictions_smoke.json"
        ),
        artifact_id="policy-reaction-official-segment-benchmark-smoke-test",
    )

    assert written == output_path
    persisted = json.loads(output_path.read_text())
    assert persisted["artifact_id"] == "policy-reaction-official-segment-benchmark-smoke-test"
    assert persisted["overall_status"] == "passed"
