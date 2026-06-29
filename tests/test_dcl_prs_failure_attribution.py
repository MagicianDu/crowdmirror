import json
import subprocess
import sys

from experiments.dcl_prs_failure_attribution import (
    ERROR_TYPES,
    build_failure_attribution_index,
)


def test_failure_attribution_index_has_finite_error_taxonomy_and_repair_candidates():
    index = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-test"
    )

    assert index["schema_version"] == "dcl-prs-failure-attribution-index-v1"
    assert index["overall_status"] == "failure_attribution_ready_for_l0_gate"
    assert index["error_taxonomy"] == ERROR_TYPES
    assert index["attribution_count"] >= 2
    assert index["repair_candidate_count"] >= 2
    assert index["claim_boundary"]["uses_test_split_for_current_claim"] is False
    json.dumps(index, allow_nan=False)


def test_failure_attributions_reference_known_error_types_and_repair_actions():
    index = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-test"
    )

    for attribution in index["attributions"]:
        for error in attribution["error_attribution"]:
            assert error["type"] in ERROR_TYPES
            assert 0.0 <= error["confidence"] <= 1.0
        for repair in attribution["repair_candidates"]:
            assert repair["action"] in {
                "rebalance_mechanism_strength",
                "fallback_anchor",
                "increase_uncertainty",
                "switch_candidate_family",
            }
            assert repair["acceptance_gate"] == "heldout_repeat_gate"


def test_failure_attribution_script_writes_artifact(tmp_path):
    output_dir = tmp_path / "dcl_prs_failure_attribution"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/dcl_prs_failure_attribution.py",
            "--output-dir",
            str(output_dir),
            "--artifact-id",
            "dcl-prs-failure-attribution-test",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "attribution_count": 2,
        "index": str(output_dir / "dcl-prs-failure-attribution-test.json"),
        "repair_candidate_count": 4,
    }
    assert (output_dir / "dcl-prs-failure-attribution-test.json").exists()
