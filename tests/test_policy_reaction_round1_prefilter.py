import json
from pathlib import Path

from experiments.policy_reaction_round1_prefilter import build_round1_prefilter_plan


def test_build_round1_prefilter_plan_generates_consistent_paths(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.json"
    candidate.write_text(
        json.dumps(
            {
                "schema_version": "policy-reaction-s2pc-candidate-v1",
                "candidate_id": "policy-reaction-constraint-program-l0-current-001-c01",
            }
        )
    )
    plan = build_round1_prefilter_plan(
        candidate_paths=[str(candidate)],
        route_slug="constraint-program-l0",
        model="openai/gpt-oss-20b",
        base_url="http://127.0.0.1:1234/v1",
        persona_count=12,
        strategy_count=3,
        seed=11,
        product_root="/tmp/product",
        research_root="/tmp/research",
    )
    assert plan["route_slug"] == "constraint-program-l0"
    assert len(plan["entries"]) == 1
    entry = plan["entries"][0]
    assert entry["run_id"].endswith("constraint-program-l0-c01-001")
    assert entry["prediction_artifact_id"] == "policy-reaction-segment-predictions-constraint-program-l0-c01-001"
    assert entry["benchmark_artifact_id"] == "policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-calibration-split-constraint-program-l0-c01-heldout-001"
    assert entry["effect_artifact_id"] == "policy-reaction-s2pc-runtime-effect-gpt-oss-20b-12x3-calibration-split-constraint-program-l0-c01-heldout-001"
