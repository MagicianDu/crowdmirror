import json
from pathlib import Path

from experiments.policy_reaction_calibration_gate import (
    build_policy_reaction_calibration_gate,
    load_json_artifact,
    write_policy_reaction_calibration_gate,
)


def test_calibration_gate_accepts_candidate_when_official_alignment_loss_improves():
    initial = load_json_artifact(
        Path(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-001.json"
        )
    )
    candidate = load_json_artifact(
        Path(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-calibrated-001.json"
        )
    )

    gate = build_policy_reaction_calibration_gate(
        initial,
        [candidate],
        artifact_id="policy-reaction-calibration-gate-test",
    )

    assert gate["schema_version"] == "policy-reaction-calibration-gate-v1"
    assert gate["artifact_id"] == "policy-reaction-calibration-gate-test"
    assert gate["overall_status"] == "accepted"
    assert gate["loss_metric"] == "weighted_choice_distribution_jsd"
    assert gate["initial_loss"] == 0.18508191023524456
    assert gate["best_loss"] == 0.0000014452916659122088
    assert gate["final_loss"] == gate["best_loss"]
    assert gate["candidate_evaluated_count"] == 1
    assert gate["candidate_accepted_count"] == 1
    assert gate["candidate_rejected_count"] == 0
    assert gate["candidate_pending_count"] == 0
    assert gate["candidate_updates"][0]["status"] == "accepted"
    assert gate["candidate_updates"][0]["loss_delta_from_best"] < 0
    assert gate["candidate_updates"][0]["coverage_rate"] == 1.0
    assert gate["best_benchmark_artifact_id"] == (
        "policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-calibrated-001"
    )
    json.dumps(gate, allow_nan=False)


def test_calibration_gate_rejects_candidate_when_loss_does_not_improve():
    initial = load_json_artifact(
        Path(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-001.json"
        )
    )

    gate = build_policy_reaction_calibration_gate(
        initial,
        [initial],
        artifact_id="policy-reaction-calibration-gate-reject-test",
    )

    assert gate["overall_status"] == "rejected"
    assert gate["initial_loss"] == gate["best_loss"] == gate["final_loss"]
    assert gate["candidate_accepted_count"] == 0
    assert gate["candidate_rejected_count"] == 1
    assert gate["candidate_updates"][0]["status"] == "rejected"
    assert gate["candidate_updates"][0]["reason"] == "loss_not_improved"


def test_write_calibration_gate_artifact(tmp_path):
    output_path = tmp_path / "calibration-gate.json"

    written = write_policy_reaction_calibration_gate(
        output_path,
        initial_benchmark_path=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-001.json"
        ),
        candidate_benchmark_paths=[
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-calibrated-001.json"
        ],
        artifact_id="policy-reaction-calibration-gate-test",
    )

    assert written == output_path
    persisted = json.loads(output_path.read_text())
    assert persisted["overall_status"] == "accepted"
