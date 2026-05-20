from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for path in (REPO_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from circe.calibration.s2pc import (  # noqa: E402
    DEFAULT_LOSS_METRIC,
    S2PC_CANDIDATE_SCHEMA_VERSION,
    S2PC_GATE_SCHEMA_VERSION,
    build_s2pc_candidate_artifact,
    build_s2pc_l1_candidate_set_artifact,
    compile_semantic_matches_to_parameter_patches,
    default_semantic_factor_catalog,
    extract_s2pc_candidate_from_l1_set,
    mine_policy_reaction_residuals,
    retrieve_semantic_factors,
    run_constrained_parameter_beam_search,
)


OFFICIAL_SEGMENT_BENCHMARK_SCHEMA_VERSION = (
    "policy-reaction-official-segment-benchmark-v1"
)
S2PC_GATE_UPDATE_POLICY = (
    "accept_if_heldout_loss_improves_and_coverage_complete_else_reject"
)
S2PC_CLAIM_BOUNDARY = (
    "S2PC L0 gate is deterministic calibration-generated candidate evidence; "
    "held-out acceptance is required before Product runtime use."
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_s2pc_candidate(
    calibration_benchmark: dict[str, Any],
    *,
    candidate_id: str,
    min_residual_magnitude: float = 0.05,
    top_k: int = 2,
    beam_width: int = 3,
) -> dict[str, Any]:
    catalog = default_semantic_factor_catalog()
    residuals = mine_policy_reaction_residuals(
        calibration_benchmark,
        min_magnitude=min_residual_magnitude,
    )
    matches = retrieve_semantic_factors(residuals, catalog, top_k=top_k)
    patches = compile_semantic_matches_to_parameter_patches(matches, catalog)
    search = run_constrained_parameter_beam_search(patches, beam_width=beam_width)
    return build_s2pc_candidate_artifact(
        candidate_id=candidate_id,
        calibration_benchmark=calibration_benchmark,
        residual_artifact=residuals,
        semantic_matches=matches,
        parameter_patches=patches,
        search_result=search,
    )


def build_policy_reaction_s2pc_l1_candidate_set(
    calibration_benchmark: dict[str, Any],
    *,
    candidate_set_id: str,
    min_residual_magnitude: float = 0.05,
    top_k: int = 2,
    beam_width: int = 3,
    max_candidates: int | None = None,
) -> dict[str, Any]:
    catalog = default_semantic_factor_catalog()
    residuals = mine_policy_reaction_residuals(
        calibration_benchmark,
        min_magnitude=min_residual_magnitude,
    )
    matches = retrieve_semantic_factors(residuals, catalog, top_k=top_k)
    patches = compile_semantic_matches_to_parameter_patches(matches, catalog)
    search = run_constrained_parameter_beam_search(patches, beam_width=beam_width)
    return build_s2pc_l1_candidate_set_artifact(
        candidate_set_id=candidate_set_id,
        calibration_benchmark=calibration_benchmark,
        residual_artifact=residuals,
        semantic_matches=matches,
        parameter_patches=patches,
        search_result=search,
        max_candidates=max_candidates,
    )


def build_policy_reaction_s2pc_gate(
    candidate: dict[str, Any],
    *,
    initial_heldout_benchmark: dict[str, Any],
    candidate_heldout_benchmark: dict[str, Any] | None,
    artifact_id: str,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> dict[str, Any]:
    _validate_s2pc_candidate(candidate)
    _validate_official_heldout_benchmark(
        initial_heldout_benchmark,
        label="initial_heldout_benchmark",
        loss_metric=loss_metric,
    )
    if candidate_heldout_benchmark is not None:
        _validate_official_heldout_benchmark(
            candidate_heldout_benchmark,
            label="candidate_heldout_benchmark",
            loss_metric=loss_metric,
        )
        if initial_heldout_benchmark["source_ingestion_artifact_id"] != (
            candidate_heldout_benchmark["source_ingestion_artifact_id"]
        ):
            raise ValueError("S2PC gate requires the same held-out target")

    initial_loss = _benchmark_loss(initial_heldout_benchmark, loss_metric)
    candidate_loss = (
        _benchmark_loss(candidate_heldout_benchmark, loss_metric)
        if candidate_heldout_benchmark is not None
        else None
    )
    coverage_rate = (
        _coverage_rate(candidate_heldout_benchmark)
        if candidate_heldout_benchmark is not None
        else 0.0
    )
    accepted = (
        candidate_loss is not None
        and coverage_rate >= 1.0
        and candidate_loss < initial_loss
    )
    best_loss = (
        min(initial_loss, candidate_loss)
        if candidate_loss is not None
        else initial_loss
    )
    final_loss = candidate_loss if accepted else initial_loss

    gate = {
        "schema_version": S2PC_GATE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "accepted" if accepted else "rejected",
        "candidate_update_policy": S2PC_GATE_UPDATE_POLICY,
        "candidate_id": candidate["candidate_id"],
        "generator": candidate["generator"],
        "loss_metric": loss_metric,
        "initial_loss": _round_float(initial_loss),
        "candidate_loss": _round_float(candidate_loss),
        "best_loss": _round_float(best_loss),
        "final_loss": _round_float(final_loss),
        "absolute_loss_delta": (
            _round_float(initial_loss - candidate_loss)
            if candidate_loss is not None
            else None
        ),
        "relative_loss_reduction": (
            _round_float((initial_loss - candidate_loss) / initial_loss)
            if candidate_loss is not None and initial_loss > 0.0
            else None
        ),
        "candidate_accepted_count": 1 if accepted else 0,
        "candidate_rejected_count": 0 if accepted else 1,
        "candidate_pending_count": 0,
        "candidate_artifact": candidate,
        "initial_heldout_benchmark_artifact_id": initial_heldout_benchmark[
            "artifact_id"
        ],
        "candidate_heldout_benchmark_artifact_id": (
            candidate_heldout_benchmark["artifact_id"]
            if candidate_heldout_benchmark
            else None
        ),
        "initial_prediction_artifact_id": initial_heldout_benchmark.get(
            "prediction_artifact_id"
        ),
        "candidate_prediction_artifact_id": (
            candidate_heldout_benchmark.get("prediction_artifact_id")
            if candidate_heldout_benchmark
            else None
        ),
        "coverage_rate": _round_float(coverage_rate),
        "source_split_contract": {
            "residual_mining": "calibration",
            "semantic_factor_retrieval": "calibration",
            "parameter_search": "calibration",
            "candidate_acceptance": "heldout",
        },
        "claim_boundary": S2PC_CLAIM_BOUNDARY,
        "claim_boundaries": [
            S2PC_CLAIM_BOUNDARY,
            "S2PC L0 does not use LLM-generated semantic factors.",
            "Candidate acceptance requires matched held-out benchmark improvement.",
        ],
    }
    _assert_strict_json(gate)
    return gate


def write_policy_reaction_s2pc_gate(
    path: str | Path,
    *,
    candidate_output_path: str | Path,
    calibration_benchmark_path: str | Path,
    initial_heldout_benchmark_path: str | Path,
    candidate_heldout_benchmark_path: str | Path,
    candidate_id: str,
    artifact_id: str,
    min_residual_magnitude: float = 0.05,
    top_k: int = 2,
    beam_width: int = 3,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> Path:
    candidate = build_policy_reaction_s2pc_candidate(
        load_json_artifact(calibration_benchmark_path),
        candidate_id=candidate_id,
        min_residual_magnitude=min_residual_magnitude,
        top_k=top_k,
        beam_width=beam_width,
    )
    candidate_output = Path(candidate_output_path)
    candidate_output.parent.mkdir(parents=True, exist_ok=True)
    candidate_output.write_text(
        json.dumps(candidate, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )

    gate = build_policy_reaction_s2pc_gate(
        candidate,
        initial_heldout_benchmark=load_json_artifact(initial_heldout_benchmark_path),
        candidate_heldout_benchmark=load_json_artifact(
            candidate_heldout_benchmark_path
        ),
        artifact_id=artifact_id,
        loss_metric=loss_metric,
    )
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(gate, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return output


def write_policy_reaction_s2pc_l1_candidate_set(
    path: str | Path,
    *,
    calibration_benchmark_path: str | Path,
    candidate_set_id: str,
    min_residual_magnitude: float = 0.05,
    top_k: int = 2,
    beam_width: int = 3,
    max_candidates: int | None = None,
) -> Path:
    artifact = build_policy_reaction_s2pc_l1_candidate_set(
        load_json_artifact(calibration_benchmark_path),
        candidate_set_id=candidate_set_id,
        min_residual_magnitude=min_residual_magnitude,
        top_k=top_k,
        beam_width=beam_width,
        max_candidates=max_candidates,
    )
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return output


def write_policy_reaction_s2pc_candidate_from_l1_set(
    path: str | Path,
    *,
    candidate_set_path: str | Path,
    candidate_id: str,
) -> Path:
    artifact = extract_s2pc_candidate_from_l1_set(
        load_json_artifact(candidate_set_path),
        candidate_id=candidate_id,
    )
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["gate", "l1-candidate-set", "extract-candidate"],
        default="gate",
    )
    parser.add_argument("--calibration-benchmark", required=True)
    parser.add_argument("--initial-heldout-benchmark")
    parser.add_argument("--candidate-heldout-benchmark")
    parser.add_argument("--candidate-set")
    parser.add_argument(
        "--candidate-id",
        default="policy-reaction-s2pc-candidate-current-001",
    )
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-s2pc-gate-current-001",
    )
    parser.add_argument(
        "--candidate-output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-s2pc-candidate-current-001.json"
        ),
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-s2pc-gate-current-001.json"
        ),
    )
    parser.add_argument("--min-residual-magnitude", type=float, default=0.05)
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument("--beam-width", type=int, default=3)
    parser.add_argument("--max-candidates", type=int)
    parser.add_argument("--loss-metric", default=DEFAULT_LOSS_METRIC)
    args = parser.parse_args()

    if args.mode == "l1-candidate-set":
        output = write_policy_reaction_s2pc_l1_candidate_set(
            args.output,
            calibration_benchmark_path=args.calibration_benchmark,
            candidate_set_id=args.artifact_id,
            min_residual_magnitude=args.min_residual_magnitude,
            top_k=args.top_k,
            beam_width=args.beam_width,
            max_candidates=args.max_candidates,
        )
        artifact = load_json_artifact(output)
        print(
            json.dumps(
                {
                    "artifact_id": artifact["candidate_set_id"],
                    "output": str(output),
                    "status": "generated",
                    "candidate_count": artifact["candidate_count"],
                },
                sort_keys=True,
                allow_nan=False,
            )
        )
        return 0

    if args.mode == "extract-candidate":
        if not args.candidate_set:
            raise ValueError("extract-candidate mode requires --candidate-set")
        output = write_policy_reaction_s2pc_candidate_from_l1_set(
            args.output,
            candidate_set_path=args.candidate_set,
            candidate_id=args.candidate_id,
        )
        artifact = load_json_artifact(output)
        print(
            json.dumps(
                {
                    "artifact_id": artifact["candidate_id"],
                    "output": str(output),
                    "status": "generated",
                    "generator": artifact["generator"],
                },
                sort_keys=True,
                allow_nan=False,
            )
        )
        return 0

    if not args.initial_heldout_benchmark or not args.candidate_heldout_benchmark:
        raise ValueError(
            "gate mode requires --initial-heldout-benchmark and "
            "--candidate-heldout-benchmark"
        )

    output = write_policy_reaction_s2pc_gate(
        args.output,
        candidate_output_path=args.candidate_output,
        calibration_benchmark_path=args.calibration_benchmark,
        initial_heldout_benchmark_path=args.initial_heldout_benchmark,
        candidate_heldout_benchmark_path=args.candidate_heldout_benchmark,
        candidate_id=args.candidate_id,
        artifact_id=args.artifact_id,
        min_residual_magnitude=args.min_residual_magnitude,
        top_k=args.top_k,
        beam_width=args.beam_width,
        loss_metric=args.loss_metric,
    )
    gate = load_json_artifact(output)
    print(
        json.dumps(
            {
                "artifact_id": gate["artifact_id"],
                "output": str(output),
                "status": gate["overall_status"],
                "initial_loss": gate["initial_loss"],
                "best_loss": gate["best_loss"],
                "final_loss": gate["final_loss"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _validate_s2pc_candidate(candidate: dict[str, Any]) -> None:
    if candidate.get("schema_version") != S2PC_CANDIDATE_SCHEMA_VERSION:
        raise ValueError("candidate has unsupported schema_version")
    if not candidate.get("candidate_id"):
        raise ValueError("candidate missing candidate_id")
    if not candidate.get("generator"):
        raise ValueError("candidate missing generator")


def _validate_official_heldout_benchmark(
    artifact: dict[str, Any],
    *,
    label: str,
    loss_metric: str,
) -> None:
    if artifact.get("schema_version") != OFFICIAL_SEGMENT_BENCHMARK_SCHEMA_VERSION:
        raise ValueError(f"{label} has unsupported schema_version")
    if artifact.get("overall_status") != "passed":
        raise ValueError(f"{label} must be passed")
    for field_name in (
        "artifact_id",
        "source_ingestion_artifact_id",
        "benchmark_metrics",
        "segment_coverage",
    ):
        if field_name not in artifact:
            raise ValueError(f"{label} missing {field_name}")
    if _source_split(artifact) != "heldout":
        raise ValueError(f"{label} must use held-out evaluation split")
    _benchmark_loss(artifact, loss_metric)


def _source_split(artifact: dict[str, Any]) -> str:
    source = str(artifact.get("source_ingestion_artifact_id", "")).lower()
    if "calibration" in source:
        return "calibration"
    if "evaluation" in source or "heldout" in source or "held-out" in source:
        return "heldout"
    return "unknown"


def _benchmark_loss(artifact: dict[str, Any], loss_metric: str) -> float:
    return _numeric(
        artifact.get("benchmark_metrics", {}).get(loss_metric),
        loss_metric,
    )


def _coverage_rate(artifact: dict[str, Any]) -> float:
    return _numeric(
        artifact.get("segment_coverage", {}).get("coverage_rate"),
        "coverage_rate",
    )


def _numeric(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be numeric")
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise ValueError(f"{field_name} must be non-negative finite")
    return number


def _round_float(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 12)


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
