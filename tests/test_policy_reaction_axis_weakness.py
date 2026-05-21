import json

from experiments.policy_reaction_axis_weakness import (
    build_policy_reaction_axis_weakness_artifact,
    write_policy_reaction_axis_weakness_artifact,
)


def test_build_axis_weakness_identifies_persistent_worst_segments():
    artifact = build_policy_reaction_axis_weakness_artifact(
        [_benchmark("h02"), _benchmark("i01")],
        artifact_id="axis-weakness-test",
    )

    assert artifact["schema_version"] == "policy-reaction-axis-weakness-v1"
    assert artifact["candidate_count"] == 2
    assert artifact["persistent_weakness"]["worst_jsd_segment"] == "price_stress_level=high"
    assert artifact["persistent_weakness"]["worst_rank_segment"] == "income_band=low"
    assert artifact["aggregate_axis_summary"]["income_band"]["mean_rank_correlation"] < 0
    json.dumps(artifact, allow_nan=False)


def test_write_axis_weakness_artifact(tmp_path):
    output_path = tmp_path / "axis-weakness.json"
    benchmark_path = tmp_path / "benchmark.json"
    benchmark_path.write_text(json.dumps(_benchmark("h02")) + "\n")

    written = write_policy_reaction_axis_weakness_artifact(
        output_path,
        benchmark_paths=[benchmark_path],
        artifact_id="axis-weakness-write-test",
    )

    assert written == output_path
    persisted = json.loads(output_path.read_text())
    assert persisted["artifact_id"] == "axis-weakness-write-test"


def _benchmark(name: str) -> dict:
    return {
        "schema_version": "policy-reaction-axis-benchmark-v1",
        "artifact_id": f"axis-benchmark-{name}",
        "segment_metrics": {
            "income_band=low": {
                "choice_distribution_jsd": 0.05,
                "rank_correlation": -1.0,
            },
            "price_stress_level=high": {
                "choice_distribution_jsd": 0.15,
                "rank_correlation": 1.0,
            },
            "employment_status=retired_or_unable_to_work": {
                "choice_distribution_jsd": 0.01,
                "rank_correlation": 1.0,
            },
        },
        "prediction_model": "openai/gpt-oss-20b",
    }
