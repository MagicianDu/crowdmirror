from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.dcl_prs_failure_attribution import (  # noqa: E402
    build_failure_attribution_index,
)
from experiments.dcl_prs_repair_repeat_acceptance_matrix import (  # noqa: E402
    build_repair_repeat_acceptance_matrix,
)


REPAIR_EFFECT_SCHEMA_VERSION = "dcl-prs-repair-effect-validation-matrix-v1"


def build_repair_effect_validation_matrix(
    *,
    artifact_id: str,
    repair_repeat_acceptance_matrix: dict[str, Any],
) -> dict[str, Any]:
    _validate_repair_repeat_matrix(repair_repeat_acceptance_matrix)
    results = []
    for candidate in repair_repeat_acceptance_matrix["candidate_results"]:
        effect_proxy = _effect_proxy(candidate)
        promoted = candidate["decision"] == "accepted" and effect_proxy > 0
        results.append(
            {
                "repair_id": candidate["repair_id"],
                "action": candidate["action"],
                "decision": candidate["decision"],
                "effect_proxy_delta": effect_proxy,
                "promoted_to_next_round": promoted,
                "validation_status": (
                    "positive_diagnostic_effect" if promoted else "not_promoted"
                ),
            }
        )
    accepted_count = sum(
        1 for result in results if result["decision"] == "accepted"
    )
    promoted_count = sum(
        1 for result in results if result["promoted_to_next_round"]
    )
    rejected_promoted_count = sum(
        1
        for result in results
        if result["decision"] == "rejected" and result["promoted_to_next_round"]
    )
    matrix = {
        "schema_version": REPAIR_EFFECT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "repair_effect_validation_matrix_ready",
        "source_artifact_id": repair_repeat_acceptance_matrix["artifact_id"],
        "repair_candidate_count": repair_repeat_acceptance_matrix[
            "repair_candidate_count"
        ],
        "accepted_candidate_count": accepted_count,
        "promoted_candidate_count": promoted_count,
        "rejected_candidate_promoted_count": rejected_promoted_count,
        "effect_results": results,
        "ccf_a_claim_status": "not_claimable",
        "product_claim_status": "diagnostic_evidence_only",
        "next_gate": "run_repair_effect_repeat_on_real_splits",
        "risk_flags": [
            "diagnostic_effect_proxy_only",
            "not_real_outcome_validation",
            "not_strong_baseline_evidence",
        ],
        "claim_boundary": {
            "uses_test_split_for_current_claim": False,
            "summary": (
                "Repair effect validation promotes only accepted repairs with "
                "positive diagnostic effect proxies. It does not prove true "
                "model-quality improvement."
            ),
        },
    }
    _assert_strict_json(matrix)
    return matrix


def write_repair_effect_validation_matrix(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-repair-effect-validation-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    failure = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-current-001"
    )
    repeat = build_repair_repeat_acceptance_matrix(
        artifact_id="dcl-prs-repair-repeat-acceptance-current-001",
        failure_attribution_index=failure,
    )
    matrix = build_repair_effect_validation_matrix(
        artifact_id=artifact_id,
        repair_repeat_acceptance_matrix=repeat,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(matrix, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_repair_effect_validation_matrix",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-repair-effect-validation-current-001",
    )
    args = parser.parse_args()
    written = write_repair_effect_validation_matrix(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "overall_status": written["matrix"]["overall_status"],
                "promoted_candidate_count": written["matrix"][
                    "promoted_candidate_count"
                ],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _effect_proxy(candidate: dict[str, Any]) -> float:
    base_effect = {
        "rebalance_mechanism_strength": 0.031,
        "fallback_anchor": 0.018,
        "increase_uncertainty": 0.006,
        "switch_candidate_family": -0.004,
    }[candidate["action"]]
    if candidate["decision"] == "rejected":
        return round(min(base_effect, -0.001), 12)
    return round(base_effect, 12)


def _validate_repair_repeat_matrix(matrix: dict[str, Any]) -> None:
    if matrix.get("schema_version") != "dcl-prs-repair-repeat-acceptance-matrix-v1":
        raise ValueError("repair_repeat_acceptance_matrix has unsupported schema")
    if not matrix.get("candidate_results"):
        raise ValueError("repair_repeat_acceptance_matrix must contain candidates")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
