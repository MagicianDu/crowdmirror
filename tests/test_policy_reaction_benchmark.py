import json
from pathlib import Path

import pytest

from benchmarks.policy_reaction import (
    compute_policy_reaction_metrics,
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
