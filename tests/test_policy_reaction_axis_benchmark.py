import json

from experiments.policy_reaction_axis_benchmark import (
    build_policy_reaction_axis_benchmark,
    write_policy_reaction_axis_benchmark,
)


def test_build_axis_benchmark_aligns_official_and_product_axes():
    artifact = build_policy_reaction_axis_benchmark(
        _axis_ingestion(),
        _segment_report(),
        artifact_id="axis-benchmark-test",
    )

    assert artifact["schema_version"] == "policy-reaction-axis-benchmark-v1"
    assert artifact["overall_status"] == "passed"
    assert artifact["segment_coverage"]["matched_segment_count"] == 3
    assert artifact["segment_coverage"]["coverage_rate"] == 1.0
    assert artifact["benchmark_metrics"]["weighted_choice_distribution_jsd"] < 0.01
    assert artifact["benchmark_metrics"]["segment_rank_correlation"] >= 0.9
    assert artifact["segment_metrics"]["income_band=low"]["official_row_count"] == 20
    json.dumps(artifact, allow_nan=False)


def test_axis_benchmark_blocks_when_axis_segment_is_missing():
    report = _segment_report()
    report["segments"].pop("employment_status=retired")

    artifact = build_policy_reaction_axis_benchmark(
        _axis_ingestion(),
        report,
        artifact_id="axis-benchmark-missing-test",
    )

    assert artifact["overall_status"] == "blocked_for_axis_alignment_claim"
    assert artifact["segment_coverage"]["missing_predicted_segments"] == [
        "employment_status=retired"
    ]
    assert artifact["segment_coverage"]["missing_segment_count_by_axis"] == {
        "employment_status": 1
    }


def test_write_axis_benchmark_artifact(tmp_path):
    ingestion_path = tmp_path / "axis-ingestion.json"
    segment_report_path = tmp_path / "segment-report.json"
    output_path = tmp_path / "axis-benchmark.json"
    ingestion_path.write_text(json.dumps(_axis_ingestion()) + "\n")
    segment_report_path.write_text(json.dumps(_segment_report()) + "\n")

    written = write_policy_reaction_axis_benchmark(
        output_path,
        ingestion_artifact_path=ingestion_path,
        segment_report_path=segment_report_path,
        artifact_id="axis-benchmark-write-test",
    )

    assert written == output_path
    persisted = json.loads(output_path.read_text())
    assert persisted["artifact_id"] == "axis-benchmark-write-test"
    assert persisted["overall_status"] == "passed"


def _axis_ingestion() -> dict:
    return {
        "schema_version": "policy-reaction-public-axis-ingestion-v1",
        "artifact_id": "axis-ingestion-test",
        "overall_status": "passed",
        "data_profile": {
            "segment_axes": [
                "income_band",
                "employment_status",
                "household_with_children",
            ]
        },
        "observed_policy_reaction_summary": {
            "by_axis_segment": {
                "income_band=low": {
                    "row_count": 20,
                    "weighted_row_mass": 25.0,
                    "weighted_mean_policy_reaction": {
                        "baseline_no_new_support": 0.12,
                        "food_subsidy_expansion": 0.68,
                        "cash_cost_of_living_rebate": 0.20,
                    },
                },
                "employment_status=retired": {
                    "row_count": 15,
                    "weighted_row_mass": 18.0,
                    "weighted_mean_policy_reaction": {
                        "baseline_no_new_support": 0.35,
                        "food_subsidy_expansion": 0.25,
                        "cash_cost_of_living_rebate": 0.40,
                    },
                },
                "household_with_children=true": {
                    "row_count": 30,
                    "weighted_row_mass": 35.0,
                    "weighted_mean_policy_reaction": {
                        "baseline_no_new_support": 0.18,
                        "food_subsidy_expansion": 0.50,
                        "cash_cost_of_living_rebate": 0.32,
                    },
                },
            }
        },
    }


def _segment_report() -> dict:
    return {
        "schema_version": "crowdmirror-segment-policy-report-v1",
        "run_id": "segment-report-test",
        "status": "completed",
        "source_model": "openai/gpt-oss-20b",
        "segments": {
            "income_band=low": {
                "policy_support_scores": {
                    "baseline_no_new_support": 0.13,
                    "food_subsidy_expansion": 0.66,
                    "cash_cost_of_living_rebate": 0.21,
                }
            },
            "employment_status=retired": {
                "policy_support_scores": {
                    "baseline_no_new_support": 0.34,
                    "food_subsidy_expansion": 0.26,
                    "cash_cost_of_living_rebate": 0.40,
                }
            },
            "household_with_children=true": {
                "policy_support_scores": {
                    "baseline_no_new_support": 0.19,
                    "food_subsidy_expansion": 0.49,
                    "cash_cost_of_living_rebate": 0.32,
                }
            },
        },
    }
