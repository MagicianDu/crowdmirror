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


REPAIR_REPEAT_SCHEMA_VERSION = "dcl-prs-repair-repeat-acceptance-matrix-v1"
SPLIT_SALTS = ["s0", "s1", "s2"]


def build_repair_repeat_acceptance_matrix(
    *,
    artifact_id: str,
    failure_attribution_index: dict[str, Any],
) -> dict[str, Any]:
    _validate_failure_attribution_index(failure_attribution_index)
    candidate_results = []
    for attribution in failure_attribution_index["attributions"]:
        for repair in attribution["repair_candidates"]:
            repeat_results = [
                _evaluate_repair_on_salt(repair=repair, salt=salt)
                for salt in SPLIT_SALTS
            ]
            accepted_repeats = sum(
                1 for repeat in repeat_results if repeat["accepted_by_heldout"]
            )
            decision = "accepted" if accepted_repeats >= 2 else "rejected"
            candidate_results.append(
                {
                    "repair_id": repair["repair_id"],
                    "task_id": attribution["task_id"],
                    "segment_key": attribution["segment_key"],
                    "action": repair["action"],
                    "target": repair["target"],
                    "repeat_count": len(repeat_results),
                    "accepted_repeat_count": accepted_repeats,
                    "decision": decision,
                    "repeat_results": repeat_results,
                }
            )
    accepted = [
        candidate
        for candidate in candidate_results
        if candidate["decision"] == "accepted"
    ]
    rejected = [
        candidate
        for candidate in candidate_results
        if candidate["decision"] == "rejected"
    ]
    matrix = {
        "schema_version": REPAIR_REPEAT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "repair_repeat_acceptance_matrix_ready",
        "source_artifact_id": failure_attribution_index["artifact_id"],
        "split_salts": SPLIT_SALTS,
        "repair_candidate_count": len(candidate_results),
        "accepted_candidate_count": len(accepted),
        "rejected_candidate_count": len(rejected),
        "acceptance_rate": round(len(accepted) / len(candidate_results), 12),
        "candidate_results": candidate_results,
        "ccf_a_claim_status": "not_claimable",
        "product_claim_status": "diagnostic_evidence_only",
        "next_gate": "run_repair_effect_validation_matrix",
        "risk_flags": [
            "deterministic_repeat_smoke_only",
            "heldout_proxy_not_real_repeat_validation",
            "not_strong_baseline_evidence",
        ],
        "claim_boundary": {
            "uses_test_split_for_current_claim": False,
            "summary": (
                "Repair repeat acceptance distinguishes accepted and rejected "
                "repair families using deterministic heldout-repeat smoke only."
            ),
        },
    }
    _assert_strict_json(matrix)
    return matrix


def write_repair_repeat_acceptance_matrix(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-repair-repeat-acceptance-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    matrix = build_repair_repeat_acceptance_matrix(
        artifact_id=artifact_id,
        failure_attribution_index=build_failure_attribution_index(
            artifact_id="dcl-prs-failure-attribution-current-001"
        ),
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
        default="experiments/results/dcl_prs_repair_repeat_acceptance_matrix",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-repair-repeat-acceptance-current-001",
    )
    args = parser.parse_args()
    written = write_repair_repeat_acceptance_matrix(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "accepted_candidate_count": written["matrix"][
                    "accepted_candidate_count"
                ],
                "index": written["index_path"],
                "repair_candidate_count": written["matrix"][
                    "repair_candidate_count"
                ],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _evaluate_repair_on_salt(*, repair: dict[str, Any], salt: str) -> dict[str, Any]:
    base_score = {
        "rebalance_mechanism_strength": 0.74,
        "fallback_anchor": 0.69,
        "increase_uncertainty": 0.57,
        "switch_candidate_family": 0.43,
    }[repair["action"]]
    salt_adjustment = {"s0": 0.02, "s1": -0.01, "s2": 0.0}[salt]
    if repair["signed_delta"] < 0:
        salt_adjustment -= 0.03
    heldout_proxy_score = round(base_score + salt_adjustment, 12)
    return {
        "salt": salt,
        "acceptance_gate": "heldout_repeat_gate",
        "heldout_proxy_score": heldout_proxy_score,
        "accepted_by_heldout": heldout_proxy_score >= 0.6,
    }


def _validate_failure_attribution_index(index: dict[str, Any]) -> None:
    if index.get("schema_version") != "dcl-prs-failure-attribution-index-v1":
        raise ValueError("failure_attribution_index has unsupported schema_version")
    if not index.get("attributions"):
        raise ValueError("failure_attribution_index must contain attributions")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
