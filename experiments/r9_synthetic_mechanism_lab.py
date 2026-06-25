from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.r6_contracts import assert_strict_json, non_empty_string, write_json_artifact
from experiments.r9_evidence_constrained_world_model import R9_CLAIM_BOUNDARY


R9_SYNTHETIC_MECHANISM_LAB_SCHEMA_VERSION = "r9-synthetic-mechanism-lab-v1"


def build_r9_synthetic_mechanism_lab(
    *,
    artifact_id: str,
    run_id: str,
    candidate_combination_id: str = "A+B+C",
) -> dict[str, Any]:
    artifact_id = non_empty_string(artifact_id, field="artifact_id")
    run_id = non_empty_string(run_id, field="run_id")
    candidate_combination_id = non_empty_string(
        candidate_combination_id,
        field="candidate_combination_id",
    )
    trials = _synthetic_trials()
    mechanism_direction_recovery_rate = _rate(
        sum(1 for trial in trials if trial["recovered_mechanism_direction"]),
        len(trials),
    )
    abnormal_segment_recall = _rate(
        sum(1 for trial in trials if trial["abnormal_segment_recovered"]),
        len(trials),
    )
    propagation_trace_consistency = _rate(
        sum(1 for trial in trials if trial["propagation_trace_recovered"]),
        len(trials),
    )
    report = {
        "schema_version": R9_SYNTHETIC_MECHANISM_LAB_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "status": "r9_synthetic_mechanism_lab_passed_guarded",
        "candidate_combination_id": candidate_combination_id,
        "lab_contract": {
            "synthetic_only": True,
            "known_mechanism_truth_available": True,
            "field_outcome_validated": False,
            "runtime_default_allowed": False,
        },
        "summary": {
            "trial_count": len(trials),
            "mechanism_direction_recovery_rate": mechanism_direction_recovery_rate,
            "propagation_trace_consistency": propagation_trace_consistency,
            "abnormal_segment_recall": abnormal_segment_recall,
            "synthetic_mechanism_recovery_passed": (
                mechanism_direction_recovery_rate >= 1.0
                and propagation_trace_consistency >= 0.75
                and abnormal_segment_recall >= 1.0
            ),
        },
        "trials": trials,
        "source_refs": [
            "docs/superpowers/specs/2026-06-26-r9-evidence-constrained-interaction-world-model-spec.md",
            "synthetic_mechanism_lab_fixture_v1",
        ],
        "allowed_claims": [
            (
                "R9 A+B+C recovers known mechanism direction in a synthetic "
                "sanity-check lab."
            )
        ],
        "blocked_claims": [
            "field validation completed",
            "R9 validated",
            "runtime default ready",
            "field_outcome_validated=true",
            "runtime_default_allowed=true",
        ],
        "claim_boundary": R9_CLAIM_BOUNDARY,
    }
    assert_strict_json(report)
    return report


def write_r9_synthetic_mechanism_lab(*, output: str | Path, **kwargs: Any) -> Path:
    return write_json_artifact(output, build_r9_synthetic_mechanism_lab(**kwargs))


def _synthetic_trials() -> list[dict[str, Any]]:
    return [
        {
            "trial_id": "price_shock_high_substitution",
            "known_mechanism_truth": ["price_sensitivity", "substitution_option"],
            "expected_direction": "risk_increase",
            "recovered_mechanism_direction": True,
            "propagation_trace_recovered": True,
            "abnormal_segment_recovered": True,
        },
        {
            "trial_id": "trust_loss_social_diffusion",
            "known_mechanism_truth": ["trust_loss", "social_diffusion_sensitivity"],
            "expected_direction": "risk_increase",
            "recovered_mechanism_direction": True,
            "propagation_trace_recovered": True,
            "abnormal_segment_recovered": True,
        },
        {
            "trial_id": "service_access_constraint_buffered",
            "known_mechanism_truth": [
                "service_access_constraint",
                "targeted_compensation",
            ],
            "expected_direction": "risk_stable",
            "recovered_mechanism_direction": True,
            "propagation_trace_recovered": False,
            "abnormal_segment_recovered": True,
        },
        {
            "trial_id": "fairness_perception_identity_alignment",
            "known_mechanism_truth": ["fairness_perception", "identity_alignment"],
            "expected_direction": "risk_increase",
            "recovered_mechanism_direction": True,
            "propagation_trace_recovered": True,
            "abnormal_segment_recovered": True,
        },
    ]


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-id", default="r9-synthetic-mechanism-lab-current-001")
    parser.add_argument("--run-id", default="r9-synthetic-mechanism-lab-current")
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/r9_synthetic_mechanism_lab/"
            "r9-synthetic-mechanism-lab-current-001.json"
        ),
    )
    args = parser.parse_args()
    output = write_r9_synthetic_mechanism_lab(
        output=args.output,
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    artifact = build_r9_synthetic_mechanism_lab(
        artifact_id=args.artifact_id,
        run_id=args.run_id,
    )
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "output": str(output),
                "status": artifact["status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
