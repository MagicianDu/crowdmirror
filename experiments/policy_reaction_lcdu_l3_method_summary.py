from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


METHOD_SUMMARY_SCHEMA_VERSION = "policy-reaction-lcdu-l3-method-summary-v1"
STABILITY_SCHEMA_VERSION = "policy-reaction-s2pc-runtime-stability-v1"
EFFECT_MATRIX_SCHEMA_VERSION = "policy-reaction-s2pc-runtime-effect-matrix-v1"
AXIS_WEAKNESS_SCHEMA_VERSION = "policy-reaction-axis-weakness-v1"
RESIDUAL_WEAKNESS_SCHEMA_VERSION = "policy-reaction-lcdu-residual-weakness-v1"

DEFAULT_RESULTS_DIR = Path("experiments/results/policy_reaction_benchmark")
DEFAULT_CHALLENGER_MATRIX_PATHS = (
    DEFAULT_RESULTS_DIR
    / "policy-reaction-route-combo-r2b-lrp-narrowed-matrix-gpt-oss-20b-12x3-heldout-001.json",
    DEFAULT_RESULTS_DIR
    / "policy-reaction-route-combo-r2c-constraint-narrowed-matrix-gpt-oss-20b-12x3-heldout-001.json",
    DEFAULT_RESULTS_DIR
    / "policy-reaction-route-combo-r3a-segment-latent-matrix-gpt-oss-20b-12x3-heldout-001.json",
    DEFAULT_RESULTS_DIR
    / "policy-reaction-route-combo-r3b-segment-constraint-matrix-gpt-oss-20b-12x3-heldout-001.json",
    DEFAULT_RESULTS_DIR
    / "policy-reaction-route-combo-r3c-latent-prototype-matrix-gpt-oss-20b-12x3-heldout-001.json",
    DEFAULT_RESULTS_DIR
    / "policy-reaction-route-combo-r3d-constraint-prototype-matrix-gpt-oss-20b-12x3-heldout-001.json",
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_policy_reaction_lcdu_l3_method_summary(
    *,
    artifact_id: str,
    h02_stability: dict[str, Any],
    i01_stability: dict[str, Any],
    interaction_matrix: dict[str, Any],
    ablation_matrix: dict[str, Any],
    challenger_matrices: list[dict[str, Any]],
    axis_weakness: dict[str, Any],
    residual_weakness: dict[str, Any],
) -> dict[str, Any]:
    h02 = _stability_summary(h02_stability, label="h02")
    i01 = _stability_summary(i01_stability, label="i01")
    interaction = _effect_matrix_summary(interaction_matrix)
    ablation = _effect_matrix_summary(ablation_matrix)
    challengers = [_effect_matrix_summary(matrix) for matrix in challenger_matrices]
    axis = _axis_weakness_summary(axis_weakness)
    residual = _residual_weakness_summary(residual_weakness)

    lcdu_best_loss = _min_number(
        h02["runtime_loss_mean"],
        i01["runtime_loss_mean"],
        interaction["best_runtime_loss"],
    )
    route_coverage = _route_coverage_summary(
        challengers=challengers,
        lcdu_best_loss=lcdu_best_loss,
    )
    claim_boundaries = _unique_strings(
        [
            (
                "LCDU L3 method summary supports bounded product transfer only; "
                "not field validation."
            ),
            (
                "Stable held-out public-data alignment evidence does not establish "
                "customer-specific forecast accuracy."
            ),
            (
                "Route coverage is a finite project-defined grid, not exhaustive "
                "algorithm search."
            ),
            h02["claim_boundary"],
            i01["claim_boundary"],
            interaction["claim_boundary"],
            ablation["claim_boundary"],
            axis["claim_boundary"],
            residual["claim_boundary"],
        ]
        + [item["claim_boundary"] for item in challengers]
    )
    summary = {
        "schema_version": METHOD_SUMMARY_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "method_id": "LCDU-L3",
        "method_name": "Latent-Constraint Distribution Update L3",
        "overall_status": "active_mainline_bounded",
        "product_transfer_status": "bounded_transfer_ready",
        "accepted_candidate_ids": [
            h02["best_candidate_id"],
            i01["best_candidate_id"],
        ],
        "evidence": {
            "stability": {
                "status": "stable_repeat_evidence_available",
                "stable_repeat_count": 2,
                "runs": [h02, i01],
            },
            "mechanism": {
                "status": "prompt_anchor_interaction_supported",
                "best_candidate_id": interaction["best_candidate_id"],
                "best_runtime_loss": interaction["best_runtime_loss"],
                "interaction_best_loss": interaction["best_runtime_loss"],
                "ablation_best_candidate_id": ablation["best_candidate_id"],
                "ablation_best_runtime_loss": ablation["best_runtime_loss"],
                "ablation_regressed_count": ablation["regressed_count"],
            },
            "route_coverage": route_coverage,
            "residual_weakness": {
                "status": "open",
                "worst_axis_segment": axis["worst_jsd_segment"],
                "worst_rank_segment": axis["worst_rank_segment"],
                "residual_segment_id": residual["segment_id"],
                "recommended_repair_direction": residual[
                    "recommended_repair_direction"
                ],
            },
        },
        "ccf_a_gaps": [
            "ccf_a_external_validity_missing",
            "cross_provider_generalization_missing",
            "full_population_scale_validation_missing",
            "finer_schema_robustness_open",
            "theoretical_identification_needs_formalization",
        ],
        "product_gaps": [
            "customer_field_validation_missing",
            "product_scale_and_latency_sla_missing",
            "operator_workflow_integration_missing",
            "segment_level_failure_recovery_missing",
        ],
        "risk_flags": [
            "local_model_only",
            "not_customer_field_validated",
            "not_cross_provider_validated",
            "not_population_scale_proof",
            "lcdu_l3_residual_axis_weakness_open",
            "finite_route_grid_not_algorithm_space",
        ],
        "artifact_refs": _unique_strings(
            [
                h02["artifact_id"],
                i01["artifact_id"],
                interaction["artifact_id"],
                ablation["artifact_id"],
                axis["artifact_id"],
                residual["artifact_id"],
            ]
            + [item["artifact_id"] for item in challengers]
        ),
        "claim_boundary": claim_boundaries[0],
        "claim_boundaries": claim_boundaries,
    }
    _assert_strict_json(summary)
    return summary


def write_policy_reaction_lcdu_l3_method_summary(
    path: str | Path,
    *,
    artifact_id: str,
    h02_stability_path: str | Path,
    i01_stability_path: str | Path,
    interaction_matrix_path: str | Path,
    ablation_matrix_path: str | Path,
    axis_weakness_path: str | Path,
    residual_weakness_path: str | Path,
    challenger_matrix_paths: list[str | Path],
) -> Path:
    summary = build_policy_reaction_lcdu_l3_method_summary(
        artifact_id=artifact_id,
        h02_stability=load_json_artifact(h02_stability_path),
        i01_stability=load_json_artifact(i01_stability_path),
        interaction_matrix=load_json_artifact(interaction_matrix_path),
        ablation_matrix=load_json_artifact(ablation_matrix_path),
        axis_weakness=load_json_artifact(axis_weakness_path),
        residual_weakness=load_json_artifact(residual_weakness_path),
        challenger_matrices=[
            load_json_artifact(path) for path in challenger_matrix_paths
        ],
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-lcdu-l3-method-summary-current-001",
    )
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-lcdu-l3-method-summary-current-001.json"
        ),
    )
    parser.add_argument(
        "--h02-stability",
        default=(
            DEFAULT_RESULTS_DIR
            / "policy-reaction-lcdu-l3-stability-gpt-oss-20b-calibration-split-h02-heldout-001.json"
        ),
    )
    parser.add_argument(
        "--i01-stability",
        default=(
            DEFAULT_RESULTS_DIR
            / "policy-reaction-lcdu-l3-i01-stability-gpt-oss-20b-calibration-split-heldout-001.json"
        ),
    )
    parser.add_argument(
        "--interaction-matrix",
        default=(
            DEFAULT_RESULTS_DIR
            / "policy-reaction-lcdu-l3-interaction-matrix-gpt-oss-20b-12x3-heldout-001.json"
        ),
    )
    parser.add_argument(
        "--ablation-matrix",
        default=(
            DEFAULT_RESULTS_DIR
            / "policy-reaction-lcdu-l3-ablation-matrix-gpt-oss-20b-12x3-heldout-001.json"
        ),
    )
    parser.add_argument(
        "--axis-weakness",
        default=DEFAULT_RESULTS_DIR / "policy-reaction-axis-weakness-lcdu-l3-current-001.json",
    )
    parser.add_argument(
        "--residual-weakness",
        default=(
            DEFAULT_RESULTS_DIR
            / "policy-reaction-lcdu-l3-low-income-residual-weakness-current-001.json"
        ),
    )
    parser.add_argument(
        "--challenger-matrix",
        action="append",
        default=None,
        help="Non-LCDU challenger matrix. Defaults to finite route-combo coverage matrices.",
    )
    args = parser.parse_args()
    challenger_paths = args.challenger_matrix or list(DEFAULT_CHALLENGER_MATRIX_PATHS)
    output_path = write_policy_reaction_lcdu_l3_method_summary(
        args.output,
        artifact_id=args.artifact_id,
        h02_stability_path=args.h02_stability,
        i01_stability_path=args.i01_stability,
        interaction_matrix_path=args.interaction_matrix,
        ablation_matrix_path=args.ablation_matrix,
        axis_weakness_path=args.axis_weakness,
        residual_weakness_path=args.residual_weakness,
        challenger_matrix_paths=challenger_paths,
    )
    summary = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "artifact_id": summary["artifact_id"],
                "output": str(output_path),
                "overall_status": summary["overall_status"],
                "product_transfer_status": summary["product_transfer_status"],
                "best_runtime_loss": summary["evidence"]["mechanism"][
                    "best_runtime_loss"
                ],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _stability_summary(artifact: dict[str, Any], *, label: str) -> dict[str, Any]:
    _require_schema(artifact, STABILITY_SCHEMA_VERSION, f"{label} stability")
    if artifact.get("overall_status") != "stable_improvement":
        raise ValueError(f"{label} stability must be stable_improvement")
    loss_summary = artifact.get("loss_summary")
    if not isinstance(loss_summary, dict):
        raise ValueError(f"{label} stability missing loss_summary")
    return {
        "label": label,
        "artifact_id": _artifact_id(artifact),
        "overall_status": artifact["overall_status"],
        "best_candidate_id": _required_string(
            artifact,
            "best_candidate_id",
            f"{label} stability",
        ),
        "effect_count": _required_int(artifact, "effect_count", f"{label} stability"),
        "improved_count": _required_int(
            artifact,
            "improved_count",
            f"{label} stability",
        ),
        "regressed_count": _required_int(
            artifact,
            "regressed_count",
            f"{label} stability",
        ),
        "runtime_loss_mean": _required_number(
            loss_summary,
            "s2pc_runtime_loss_mean",
            f"{label} loss_summary",
        ),
        "relative_loss_reduction_mean": _optional_number(
            loss_summary,
            "relative_loss_reduction_mean",
        ),
        "claim_boundary": _required_string(
            artifact,
            "claim_boundary",
            f"{label} stability",
        ),
    }


def _effect_matrix_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    _require_schema(artifact, EFFECT_MATRIX_SCHEMA_VERSION, "effect matrix")
    return {
        "artifact_id": _artifact_id(artifact),
        "overall_status": _required_string(artifact, "overall_status", "effect matrix"),
        "candidate_count": _required_int(artifact, "candidate_count", "effect matrix"),
        "improved_count": _required_int(artifact, "improved_count", "effect matrix"),
        "regressed_count": _required_int(artifact, "regressed_count", "effect matrix"),
        "best_candidate_id": _required_string(
            artifact,
            "best_candidate_id",
            "effect matrix",
        ),
        "best_runtime_loss": _required_number(
            artifact,
            "best_s2pc_runtime_loss",
            "effect matrix",
        ),
        "claim_boundary": _required_string(
            artifact,
            "claim_boundary",
            "effect matrix",
        ),
    }


def _axis_weakness_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    _require_schema(artifact, AXIS_WEAKNESS_SCHEMA_VERSION, "axis weakness")
    persistent = artifact.get("persistent_weakness")
    if not isinstance(persistent, dict):
        raise ValueError("axis weakness missing persistent_weakness")
    return {
        "artifact_id": _artifact_id(artifact),
        "worst_jsd_segment": _required_string(
            persistent,
            "worst_jsd_segment",
            "axis weakness",
        ),
        "worst_jsd_value_mean": _required_number(
            persistent,
            "worst_jsd_value_mean",
            "axis weakness",
        ),
        "worst_rank_segment": _required_string(
            persistent,
            "worst_rank_segment",
            "axis weakness",
        ),
        "worst_rank_value_mean": _required_number(
            persistent,
            "worst_rank_value_mean",
            "axis weakness",
        ),
        "claim_boundary": _required_string(
            artifact,
            "claim_boundary",
            "axis weakness",
        ),
    }


def _residual_weakness_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    _require_schema(artifact, RESIDUAL_WEAKNESS_SCHEMA_VERSION, "residual weakness")
    weakness = artifact.get("weakness_summary")
    if not isinstance(weakness, dict):
        raise ValueError("residual weakness missing weakness_summary")
    return {
        "artifact_id": _artifact_id(artifact),
        "segment_id": _required_string(artifact, "segment_id", "residual weakness"),
        "recommended_repair_direction": _required_string(
            weakness,
            "recommended_repair_direction",
            "residual weakness",
        ),
        "claim_boundary": _required_string(
            artifact,
            "claim_boundary",
            "residual weakness",
        ),
    }


def _route_coverage_summary(
    *,
    challengers: list[dict[str, Any]],
    lcdu_best_loss: float,
) -> dict[str, Any]:
    best_challenger_loss = _min_number(
        *[item["best_runtime_loss"] for item in challengers]
    )
    return {
        "status": (
            "finite_grid_covered" if challengers else "challenger_matrices_missing"
        ),
        "coverage_scope": (
            "Project-defined finite route-combo grid; not full algorithmic universe."
        ),
        "challenger_count": len(challengers),
        "best_challenger_loss": best_challenger_loss,
        "lcdu_l3_best_loss": lcdu_best_loss,
        "challenger_exceeds_lcdu_l3": (
            bool(challengers) and best_challenger_loss < lcdu_best_loss
        ),
        "challengers": challengers,
    }


def _artifact_id(artifact: dict[str, Any]) -> str:
    for field_name in ("artifact_id", "matrix_id", "run_id"):
        value = artifact.get(field_name)
        if isinstance(value, str) and value:
            return value
    raise ValueError("artifact missing identifier")


def _require_schema(artifact: dict[str, Any], schema_version: str, label: str) -> None:
    if artifact.get("schema_version") != schema_version:
        raise ValueError(f"{label} has unsupported schema_version")


def _required_string(payload: dict[str, Any], field_name: str, label: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} missing {field_name}")
    return value


def _required_int(payload: dict[str, Any], field_name: str, label: str) -> int:
    value = payload.get(field_name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{label} missing {field_name}")
    return value


def _required_number(payload: dict[str, Any], field_name: str, label: str) -> float:
    value = payload.get(field_name)
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{label} missing {field_name}")
    return round(float(value), 12)


def _optional_number(payload: dict[str, Any], field_name: str) -> float | None:
    value = payload.get(field_name)
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        return None
    return round(float(value), 12)


def _min_number(*values: float) -> float:
    finite_values = [
        float(value)
        for value in values
        if isinstance(value, (int, float)) and math.isfinite(float(value))
    ]
    if not finite_values:
        return 0.0
    return round(min(finite_values), 12)


def _unique_strings(values: list[str | None]) -> list[str]:
    unique = []
    for value in values:
        if isinstance(value, str) and value and value not in unique:
            unique.append(value)
    return unique


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("LCDU L3 method summary must be strict JSON") from exc


if __name__ == "__main__":
    raise SystemExit(main())
