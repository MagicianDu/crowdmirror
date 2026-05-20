from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
from typing import Any


UPDATE_METHOD_GATE_SCHEMA_VERSION = "policy-reaction-update-method-gate-v1"
OFFICIAL_SEGMENT_BENCHMARK_SCHEMA_VERSION = (
    "policy-reaction-official-segment-benchmark-v1"
)
RUNTIME_PATCH_STABILITY_SCHEMA_VERSION = (
    "policy-reaction-runtime-patch-stability-v1"
)
S2PC_GATE_SCHEMA_VERSION = "policy-reaction-s2pc-gate-v1"
S2PC_RUNTIME_EFFECT_SCHEMA_VERSION = "policy-reaction-s2pc-runtime-effect-v1"
S2PC_RUNTIME_STABILITY_SCHEMA_VERSION = "policy-reaction-s2pc-runtime-stability-v1"
S2PC_RUNTIME_EFFECT_MATRIX_SCHEMA_VERSION = (
    "policy-reaction-s2pc-runtime-effect-matrix-v1"
)
TEXTGRAD_EVIDENCE_SCHEMA_VERSION = "circe-evidence-v1"
DEFAULT_LOSS_METRIC = "weighted_choice_distribution_jsd"
UPDATE_METHOD_POLICY = (
    "accept_matched_heldout_loss_improvement_with_complete_segment_coverage_"
    "else_reject_or_mark_diagnostic"
)
UPDATE_METHOD_CLAIM_BOUNDARY = (
    "Policy-reaction update-method gate compares automated prompt/persona update "
    "methods using matched held-out public-data evidence where available; "
    "diagnostic-only TextGrad evidence is not accepted as policy-reaction "
    "calibration effectiveness."
)


def load_json_artifact(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("artifact must be a JSON object")
    return payload


def build_heldout_benchmark_method_record(
    *,
    method_id: str,
    generator: str,
    baseline_benchmark: dict[str, Any],
    candidate_benchmark: dict[str, Any],
    loss_metric: str = DEFAULT_LOSS_METRIC,
    min_improvement: float = 0.0,
) -> dict[str, Any]:
    _validate_method_id(method_id)
    _validate_generator(generator)
    _validate_official_heldout_benchmark(
        baseline_benchmark,
        label="baseline_benchmark",
        loss_metric=loss_metric,
    )
    _validate_official_heldout_benchmark(
        candidate_benchmark,
        label="candidate_benchmark",
        loss_metric=loss_metric,
    )
    if baseline_benchmark["source_ingestion_artifact_id"] != candidate_benchmark[
        "source_ingestion_artifact_id"
    ]:
        raise ValueError("method record requires the same held-out target")

    initial_loss = _benchmark_loss(baseline_benchmark, loss_metric)
    candidate_loss = _benchmark_loss(candidate_benchmark, loss_metric)
    coverage_rate = _coverage_rate(candidate_benchmark)
    absolute_loss_delta = _round_float(initial_loss - candidate_loss)
    relative_loss_reduction = (
        _round_float(absolute_loss_delta / initial_loss)
        if initial_loss > 0.0
        else None
    )
    accepted = coverage_rate >= 1.0 and absolute_loss_delta > min_improvement
    reason = "heldout_loss_improved" if accepted else "heldout_loss_not_improved"
    if coverage_rate < 1.0:
        reason = "segment_coverage_incomplete"

    return _strict_record(
        {
            "method_id": method_id,
            "generator": generator,
            "evidence_type": "matched_heldout_segment_benchmark",
            "eligibility": "heldout_candidate",
            "status": "accepted" if accepted else "rejected",
            "reason": reason,
            "loss_metric": loss_metric,
            "initial_loss": _round_float(initial_loss),
            "candidate_loss": _round_float(candidate_loss),
            "best_loss": _round_float(candidate_loss if accepted else initial_loss),
            "final_loss": _round_float(candidate_loss if accepted else initial_loss),
            "absolute_loss_delta": absolute_loss_delta,
            "relative_loss_reduction": relative_loss_reduction,
            "coverage_rate": _round_float(coverage_rate),
            "baseline_artifact_id": baseline_benchmark["artifact_id"],
            "candidate_artifact_id": candidate_benchmark["artifact_id"],
            "baseline_prediction_artifact_id": baseline_benchmark.get(
                "prediction_artifact_id"
            ),
            "candidate_prediction_artifact_id": candidate_benchmark.get(
                "prediction_artifact_id"
            ),
            "model_id": candidate_benchmark.get("prediction_model"),
            "source_split_contract": {
                "candidate_generation": "calibration_or_runtime_method",
                "candidate_acceptance": "heldout",
            },
        }
    )


def build_runtime_stability_method_record(
    *,
    method_id: str,
    generator: str,
    stability_matrix: dict[str, Any],
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> dict[str, Any]:
    _validate_method_id(method_id)
    _validate_generator(generator)
    if (
        stability_matrix.get("schema_version")
        != RUNTIME_PATCH_STABILITY_SCHEMA_VERSION
    ):
        raise ValueError("stability_matrix has unsupported schema_version")
    if stability_matrix.get("loss_metric", loss_metric) != loss_metric:
        raise ValueError(f"stability_matrix loss_metric must be {loss_metric}")
    loss_summary = stability_matrix.get("loss_summary")
    if not isinstance(loss_summary, dict):
        raise ValueError("stability_matrix missing loss_summary")

    initial_loss = _numeric(loss_summary.get("baseline_loss_mean"), "baseline_loss_mean")
    candidate_loss = _numeric(
        loss_summary.get("runtime_patch_loss_mean"),
        "runtime_patch_loss_mean",
    )
    relative_loss_reduction = _finite_number(
        loss_summary.get("relative_loss_reduction_mean"),
        "relative_loss_reduction_mean",
    )
    status = (
        "accepted"
        if stability_matrix.get("overall_status") == "stable_improvement"
        else "rejected"
    )
    return _strict_record(
        {
            "method_id": method_id,
            "generator": generator,
            "evidence_type": "runtime_patch_stability_matrix",
            "eligibility": "heldout_candidate",
            "status": status,
            "reason": (
                "runtime_patch_stability_improved"
                if status == "accepted"
                else "runtime_patch_stability_not_improved"
            ),
            "loss_metric": loss_metric,
            "initial_loss": _round_float(initial_loss),
            "candidate_loss": _round_float(candidate_loss),
            "best_loss": _round_float(
                candidate_loss if status == "accepted" else initial_loss
            ),
            "final_loss": _round_float(
                candidate_loss if status == "accepted" else initial_loss
            ),
            "absolute_loss_delta": _round_float(initial_loss - candidate_loss),
            "relative_loss_reduction": _round_float(relative_loss_reduction),
            "coverage_rate": 1.0,
            "candidate_artifact_id": stability_matrix["artifact_id"],
            "model_ids": stability_matrix.get("model_ids", []),
            "scale_axes": stability_matrix.get("scale_axes", {}),
            "effect_count": stability_matrix.get("effect_count"),
            "improved_count": stability_matrix.get("improved_count"),
            "regressed_count": stability_matrix.get("regressed_count"),
            "source_split_contract": {
                "candidate_generation": "calibration",
                "candidate_acceptance": "heldout_runtime_effect_stability",
            },
        }
    )


def build_s2pc_gate_method_record(
    *,
    method_id: str,
    s2pc_gate: dict[str, Any],
) -> dict[str, Any]:
    _validate_method_id(method_id)
    if s2pc_gate.get("schema_version") != S2PC_GATE_SCHEMA_VERSION:
        raise ValueError("s2pc_gate has unsupported schema_version")
    status = "accepted" if s2pc_gate.get("overall_status") == "accepted" else "rejected"
    initial_loss = _numeric(s2pc_gate.get("initial_loss"), "initial_loss")
    candidate_loss = _numeric(s2pc_gate.get("candidate_loss"), "candidate_loss")
    best_loss = _numeric(s2pc_gate.get("best_loss"), "best_loss")
    final_loss = _numeric(s2pc_gate.get("final_loss"), "final_loss")
    coverage_rate = _numeric(s2pc_gate.get("coverage_rate"), "coverage_rate")
    absolute_loss_delta = _round_float(initial_loss - candidate_loss)
    return _strict_record(
        {
            "method_id": method_id,
            "generator": s2pc_gate.get(
                "generator",
                "s2pc_l0_deterministic_catalog_beam_search",
            ),
            "evidence_type": "s2pc_heldout_gate",
            "eligibility": "heldout_candidate",
            "status": status,
            "reason": (
                "s2pc_heldout_loss_improved"
                if status == "accepted"
                else "s2pc_heldout_loss_not_improved"
            ),
            "loss_metric": s2pc_gate.get("loss_metric", DEFAULT_LOSS_METRIC),
            "initial_loss": _round_float(initial_loss),
            "candidate_loss": _round_float(candidate_loss),
            "best_loss": _round_float(best_loss),
            "final_loss": _round_float(final_loss),
            "absolute_loss_delta": absolute_loss_delta,
            "relative_loss_reduction": (
                _round_float(absolute_loss_delta / initial_loss)
                if initial_loss > 0.0 and absolute_loss_delta is not None
                else None
            ),
            "coverage_rate": _round_float(coverage_rate),
            "candidate_artifact_id": s2pc_gate["artifact_id"],
            "candidate_id": s2pc_gate.get("candidate_id"),
            "source_split_contract": copy.deepcopy(
                s2pc_gate["source_split_contract"]
            ),
        }
    )


def build_s2pc_runtime_effect_method_record(
    *,
    method_id: str,
    s2pc_runtime_effect: dict[str, Any],
) -> dict[str, Any]:
    _validate_method_id(method_id)
    if s2pc_runtime_effect.get("schema_version") != S2PC_RUNTIME_EFFECT_SCHEMA_VERSION:
        raise ValueError("s2pc_runtime_effect has unsupported schema_version")
    status = (
        "accepted"
        if s2pc_runtime_effect.get("overall_status") == "improved"
        else "rejected"
    )
    initial_loss = _numeric(s2pc_runtime_effect.get("baseline_loss"), "baseline_loss")
    candidate_loss = _numeric(
        s2pc_runtime_effect.get("s2pc_runtime_loss"),
        "s2pc_runtime_loss",
    )
    absolute_loss_delta = _round_float(initial_loss - candidate_loss)
    final_loss = candidate_loss if status == "accepted" else initial_loss
    return _strict_record(
        {
            "method_id": method_id,
            "generator": "s2pc_l0_deterministic_catalog_beam_search_runtime",
            "evidence_type": "s2pc_runtime_effect_gate",
            "eligibility": "heldout_candidate",
            "status": status,
            "reason": (
                "s2pc_runtime_loss_improved"
                if status == "accepted"
                else "s2pc_runtime_loss_not_improved"
            ),
            "loss_metric": s2pc_runtime_effect.get(
                "loss_metric",
                DEFAULT_LOSS_METRIC,
            ),
            "initial_loss": _round_float(initial_loss),
            "candidate_loss": _round_float(candidate_loss),
            "best_loss": _round_float(min(initial_loss, candidate_loss)),
            "final_loss": _round_float(final_loss),
            "absolute_loss_delta": absolute_loss_delta,
            "relative_loss_reduction": (
                _round_float(absolute_loss_delta / initial_loss)
                if initial_loss > 0.0 and absolute_loss_delta is not None
                else None
            ),
            "coverage_rate": _round_float(
                _numeric(
                    s2pc_runtime_effect.get("coverage", {}).get(
                        "s2pc_runtime_coverage_rate"
                    ),
                    "s2pc_runtime_coverage_rate",
                )
            ),
            "candidate_artifact_id": s2pc_runtime_effect["artifact_id"],
            "candidate_id": s2pc_runtime_effect.get("s2pc_candidate_id"),
            "model_id": s2pc_runtime_effect.get("product_runtime_model"),
            "scale": s2pc_runtime_effect.get("product_runtime_scale", {}),
            "source_split_contract": copy.deepcopy(
                s2pc_runtime_effect["source_split_contract"]
            ),
        }
    )


def build_s2pc_runtime_effect_matrix_method_record(
    *,
    method_id: str,
    s2pc_runtime_effect_matrix: dict[str, Any],
) -> dict[str, Any]:
    _validate_method_id(method_id)
    if (
        s2pc_runtime_effect_matrix.get("schema_version")
        != S2PC_RUNTIME_EFFECT_MATRIX_SCHEMA_VERSION
    ):
        raise ValueError("s2pc_runtime_effect_matrix has unsupported schema_version")
    if not isinstance(s2pc_runtime_effect_matrix.get("candidate_results"), list) or not (
        s2pc_runtime_effect_matrix["candidate_results"]
    ):
        raise ValueError("s2pc_runtime_effect_matrix missing candidate_results")
    best_result = s2pc_runtime_effect_matrix["candidate_results"][0]
    initial_loss = _numeric(best_result.get("baseline_loss"), "baseline_loss")
    candidate_loss = _numeric(
        best_result.get("s2pc_runtime_loss"),
        "s2pc_runtime_loss",
    )
    absolute_loss_delta = _round_float(initial_loss - candidate_loss)
    status = (
        "accepted"
        if s2pc_runtime_effect_matrix.get("improved_count", 0) > 0
        else "rejected"
    )
    return _strict_record(
        {
            "method_id": method_id,
            "generator": "s2pc_l1_multi_candidate_runtime_search_runtime",
            "evidence_type": "s2pc_runtime_effect_matrix",
            "eligibility": "heldout_candidate",
            "status": status,
            "reason": (
                "s2pc_runtime_matrix_best_candidate_improved"
                if status == "accepted"
                else "s2pc_runtime_matrix_no_candidate_improved"
            ),
            "loss_metric": s2pc_runtime_effect_matrix.get(
                "loss_metric",
                DEFAULT_LOSS_METRIC,
            ),
            "initial_loss": _round_float(initial_loss),
            "candidate_loss": _round_float(candidate_loss),
            "best_loss": _round_float(candidate_loss if status == "accepted" else initial_loss),
            "final_loss": _round_float(candidate_loss if status == "accepted" else initial_loss),
            "absolute_loss_delta": absolute_loss_delta,
            "relative_loss_reduction": (
                _round_float(absolute_loss_delta / initial_loss)
                if initial_loss > 0.0
                else None
            ),
            "coverage_rate": 1.0,
            "candidate_artifact_id": s2pc_runtime_effect_matrix["artifact_id"],
            "candidate_id": best_result.get("s2pc_candidate_id"),
            "candidate_count": s2pc_runtime_effect_matrix.get("candidate_count"),
            "improved_count": s2pc_runtime_effect_matrix.get("improved_count"),
            "regressed_count": s2pc_runtime_effect_matrix.get("regressed_count"),
            "best_candidate_id": s2pc_runtime_effect_matrix.get("best_candidate_id"),
            "best_runtime_effect_artifact_id": best_result.get("artifact_id"),
            "model_id": "openai/gpt-oss-20b",
            "source_split_contract": {
                "candidate_generation": "calibration",
                "candidate_acceptance": "heldout_runtime_effect_matrix",
                "runtime_effect_evaluation": "heldout",
            },
        }
    )


def build_s2pc_runtime_stability_method_record(
    *,
    method_id: str,
    s2pc_runtime_stability: dict[str, Any],
) -> dict[str, Any]:
    _validate_method_id(method_id)
    if (
        s2pc_runtime_stability.get("schema_version")
        != S2PC_RUNTIME_STABILITY_SCHEMA_VERSION
    ):
        raise ValueError("s2pc_runtime_stability has unsupported schema_version")
    loss_summary = s2pc_runtime_stability.get("loss_summary")
    if not isinstance(loss_summary, dict):
        raise ValueError("s2pc_runtime_stability missing loss_summary")
    candidate_ids = s2pc_runtime_stability.get("candidate_ids")
    if not isinstance(candidate_ids, list) or not candidate_ids:
        raise ValueError("s2pc_runtime_stability missing candidate_ids")
    initial_loss = _numeric(loss_summary.get("baseline_loss_mean"), "baseline_loss_mean")
    candidate_loss = _numeric(
        loss_summary.get("s2pc_runtime_loss_mean"),
        "s2pc_runtime_loss_mean",
    )
    absolute_loss_delta = _round_float(initial_loss - candidate_loss)
    status = (
        "accepted"
        if s2pc_runtime_stability.get("overall_status") == "stable_improvement"
        else "rejected"
    )
    return _strict_record(
        {
            "method_id": method_id,
            "generator": "s2pc_l1_multi_candidate_runtime_search_runtime_stability",
            "evidence_type": "s2pc_runtime_stability_matrix",
            "eligibility": "heldout_candidate",
            "status": status,
            "reason": (
                "s2pc_runtime_candidate_stably_improved"
                if status == "accepted"
                else "s2pc_runtime_candidate_not_stable"
            ),
            "loss_metric": s2pc_runtime_stability.get(
                "loss_metric",
                DEFAULT_LOSS_METRIC,
            ),
            "initial_loss": _round_float(initial_loss),
            "candidate_loss": _round_float(candidate_loss),
            "best_loss": _round_float(candidate_loss if status == "accepted" else initial_loss),
            "final_loss": _round_float(candidate_loss if status == "accepted" else initial_loss),
            "absolute_loss_delta": absolute_loss_delta,
            "relative_loss_reduction": (
                _round_float(absolute_loss_delta / initial_loss)
                if initial_loss > 0.0
                else None
            ),
            "coverage_rate": 1.0,
            "candidate_artifact_id": s2pc_runtime_stability["artifact_id"],
            "candidate_id": str(candidate_ids[0]),
            "effect_count": s2pc_runtime_stability.get("effect_count"),
            "improved_count": s2pc_runtime_stability.get("improved_count"),
            "regressed_count": s2pc_runtime_stability.get("regressed_count"),
            "scale_axes": s2pc_runtime_stability.get("scale_axes", {}),
            "source_split_contract": {
                "candidate_generation": "calibration",
                "candidate_acceptance": "heldout_runtime_effect_stability",
                "runtime_effect_evaluation": "heldout",
            },
        }
    )
def build_textgrad_manifest_method_record(
    *,
    method_id: str,
    generator: str,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    _validate_method_id(method_id)
    _validate_generator(generator)
    if manifest.get("schema_version") != TEXTGRAD_EVIDENCE_SCHEMA_VERSION:
        raise ValueError("manifest has unsupported schema_version")
    metrics = manifest.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("manifest missing metrics")
    initial_loss = _numeric(metrics.get("initial_loss"), "initial_loss")
    best_loss = _numeric(metrics.get("best_loss"), "best_loss")
    final_loss = _numeric(metrics.get("final_loss"), "final_loss")

    return _strict_record(
        {
            "method_id": method_id,
            "generator": generator,
            "evidence_type": "textgrad_candidate_update_manifest",
            "eligibility": "diagnostic_only",
            "status": "diagnostic_only",
            "reason": "missing_policy_reaction_heldout_evaluation",
            "loss_metric": "causal_calibration_loss",
            "initial_loss": initial_loss,
            "candidate_loss": None,
            "best_loss": best_loss,
            "final_loss": final_loss,
            "absolute_loss_delta": _round_float(initial_loss - best_loss),
            "relative_loss_reduction": (
                _round_float((initial_loss - best_loss) / initial_loss)
                if initial_loss > 0.0
                else None
            ),
            "run_id": manifest.get("run_id"),
            "lane": manifest.get("lane"),
            "mode": manifest.get("mode"),
            "model_id": manifest.get("config", {}).get("model"),
            "config": manifest.get("config", {}),
            "textgrad_metrics": {
                key: metrics.get(key)
                for key in (
                    "candidate_update_count",
                    "candidate_evaluated_count",
                    "candidate_accepted_count",
                    "candidate_rejected_count",
                    "candidate_pending_count",
                    "candidate_acceptance_rate",
                    "candidate_update_policy",
                    "textgrad_effect_status",
                    "textgrad_output_budget_saturated",
                )
                if key in metrics
            },
        }
    )


def build_policy_reaction_update_method_gate(
    method_records: list[dict[str, Any]],
    *,
    artifact_id: str,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> dict[str, Any]:
    if not method_records:
        raise ValueError("update method gate requires at least one method record")
    _validate_method_id(artifact_id)
    records = [_validate_method_record(record) for record in method_records]

    heldout_records = [
        record for record in records if record["eligibility"] == "heldout_candidate"
    ]
    diagnostic_records = [
        record for record in records if record["eligibility"] == "diagnostic_only"
    ]
    accepted_records = [
        record for record in heldout_records if record["status"] == "accepted"
    ]
    rejected_records = [
        record for record in heldout_records if record["status"] == "rejected"
    ]
    best_record = _best_accepted_record(accepted_records)
    representative = best_record or _lowest_initial_loss_record(heldout_records) or records[0]

    artifact = {
        "schema_version": UPDATE_METHOD_GATE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            accepted_count=len(accepted_records),
            heldout_count=len(heldout_records),
            diagnostic_count=len(diagnostic_records),
        ),
        "loss_metric": loss_metric,
        "loss_scope": (
            "Top-level initial/best/final loss follows the best accepted "
            "held-out method record when available; per-method records preserve "
            "their matched baseline and candidate losses."
        ),
        "candidate_update_policy": UPDATE_METHOD_POLICY,
        "method_count": len(records),
        "candidate_update_count": len(heldout_records),
        "candidate_evaluated_count": len(heldout_records),
        "candidate_accepted_count": len(accepted_records),
        "candidate_rejected_count": len(rejected_records),
        "candidate_pending_count": 0,
        "diagnostic_only_count": len(diagnostic_records),
        "candidate_acceptance_rate": (
            len(accepted_records) / len(heldout_records)
            if heldout_records
            else None
        ),
        "accepted_method_ids": [record["method_id"] for record in accepted_records],
        "rejected_method_ids": [record["method_id"] for record in rejected_records],
        "diagnostic_method_ids": [
            record["method_id"] for record in diagnostic_records
        ],
        "best_method_id": best_record["method_id"] if best_record else None,
        "initial_loss": representative.get("initial_loss"),
        "best_loss": (
            best_record.get("candidate_loss")
            if best_record is not None
            else representative.get("best_loss")
        ),
        "final_loss": (
            best_record.get("candidate_loss")
            if best_record is not None
            else representative.get("final_loss")
        ),
        "method_generator_counts": _generator_counts(records),
        "generator_summaries": _generator_summaries(records),
        "method_updates": records,
        "risk_flags": _risk_flags(
            accepted_count=len(accepted_records),
            rejected_count=len(rejected_records),
            diagnostic_count=len(diagnostic_records),
            heldout_count=len(heldout_records),
        ),
        "claim_boundary": UPDATE_METHOD_CLAIM_BOUNDARY,
        "claim_boundaries": [
            UPDATE_METHOD_CLAIM_BOUNDARY,
            "Accepted update methods require matched held-out loss reduction and complete segment coverage.",
            "Runtime-patch stability matrices count as held-out method evidence only when stable improvement is recorded.",
            "TextGrad or DeepSeek candidate-update runs without policy-reaction held-out evaluation remain diagnostic only.",
        ],
    }
    _assert_strict_json(artifact)
    return artifact


def write_policy_reaction_update_method_gate(
    path: str | Path,
    *,
    method_records: list[dict[str, Any]],
    artifact_id: str,
    loss_metric: str = DEFAULT_LOSS_METRIC,
) -> Path:
    artifact = build_policy_reaction_update_method_gate(
        method_records,
        artifact_id=artifact_id,
        loss_metric=loss_metric,
    )
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artifact-id",
        default="policy-reaction-update-method-gate-current-001",
    )
    parser.add_argument("--loss-metric", default=DEFAULT_LOSS_METRIC)
    parser.add_argument(
        "--output",
        default=(
            "experiments/results/policy_reaction_benchmark/"
            "policy-reaction-update-method-gate-current-001.json"
        ),
    )
    args = parser.parse_args()
    records = _default_current_method_records(loss_metric=args.loss_metric)
    output_path = write_policy_reaction_update_method_gate(
        args.output,
        method_records=records,
        artifact_id=args.artifact_id,
        loss_metric=args.loss_metric,
    )
    artifact = load_json_artifact(output_path)
    print(
        json.dumps(
            {
                "artifact_id": artifact["artifact_id"],
                "output": str(output_path),
                "status": artifact["overall_status"],
                "candidate_accepted_count": artifact["candidate_accepted_count"],
                "candidate_rejected_count": artifact["candidate_rejected_count"],
                "diagnostic_only_count": artifact["diagnostic_only_count"],
                "best_method_id": artifact["best_method_id"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _default_current_method_records(*, loss_metric: str) -> list[dict[str, Any]]:
    benchmark_dir = Path("experiments/results/policy_reaction_benchmark")
    manifest_dir = Path("experiments/results/manifests")
    gpt_oss_baseline = load_json_artifact(
        benchmark_dir
        / "policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-heldout-001.json"
    )
    deepseek_baseline = load_json_artifact(
        benchmark_dir
        / "policy-reaction-official-segment-benchmark-deepseek-v4-flash-12x3-smoke-heldout-001.json"
    )
    records = [
        build_heldout_benchmark_method_record(
            method_id="gpt_oss_20b_calibration_split_prompting_12x3_seed11",
            generator="calibration_split_prompting",
            baseline_benchmark=gpt_oss_baseline,
            candidate_benchmark=load_json_artifact(
                benchmark_dir
                / "policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-calibration-split-heldout-001.json"
            ),
            loss_metric=loss_metric,
        ),
        build_heldout_benchmark_method_record(
            method_id="deepseek_v4_flash_calibration_split_prompting_12x3_seed11",
            generator="calibration_split_prompting",
            baseline_benchmark=deepseek_baseline,
            candidate_benchmark=load_json_artifact(
                benchmark_dir
                / "policy-reaction-official-segment-benchmark-deepseek-v4-flash-12x3-calibration-split-heldout-001.json"
            ),
            loss_metric=loss_metric,
        ),
        build_heldout_benchmark_method_record(
            method_id="deepseek_v4_flash_calibration_split_prompting_12x3_seed17",
            generator="calibration_split_prompting",
            baseline_benchmark=deepseek_baseline,
            candidate_benchmark=load_json_artifact(
                benchmark_dir
                / "policy-reaction-official-segment-benchmark-deepseek-v4-flash-12x3-calibration-split-seed17-heldout-001.json"
            ),
            loss_metric=loss_metric,
        ),
        build_heldout_benchmark_method_record(
            method_id="deepseek_v4_flash_calibration_split_prompting_16x3_seed11",
            generator="calibration_split_prompting",
            baseline_benchmark=deepseek_baseline,
            candidate_benchmark=load_json_artifact(
                benchmark_dir
                / "policy-reaction-official-segment-benchmark-deepseek-v4-flash-16x3-calibration-split-seed11-heldout-001.json"
            ),
            loss_metric=loss_metric,
        ),
        build_runtime_stability_method_record(
            method_id="gpt_oss_20b_runtime_prompt_patch_stability",
            generator="structured_persona_parameter_patch",
            stability_matrix=load_json_artifact(
                benchmark_dir
                / "policy-reaction-runtime-patch-stability-gpt-oss-20b-calibration-split-heldout-001.json"
            ),
            loss_metric=loss_metric,
        ),
        build_s2pc_gate_method_record(
            method_id="s2pc_l0_current_policy_reaction_candidate",
            s2pc_gate=load_json_artifact(
                benchmark_dir / "policy-reaction-s2pc-gate-current-001.json"
            ),
        ),
        build_s2pc_runtime_effect_method_record(
            method_id="s2pc_l0_current_policy_reaction_runtime_probe",
            s2pc_runtime_effect=load_json_artifact(
                benchmark_dir
                / "policy-reaction-s2pc-runtime-effect-gpt-oss-20b-12x3-calibration-split-heldout-001.json"
            ),
        ),
        build_s2pc_runtime_effect_matrix_method_record(
            method_id="s2pc_l1_runtime_matrix_gpt_oss_20b_12x3_seed11",
            s2pc_runtime_effect_matrix=load_json_artifact(
                benchmark_dir
                / "policy-reaction-s2pc-runtime-effect-matrix-gpt-oss-20b-12x3-calibration-split-l1-heldout-001.json"
            ),
        ),
        build_s2pc_runtime_stability_method_record(
            method_id="s2pc_l1_runtime_stability_gpt_oss_20b_c01",
            s2pc_runtime_stability=load_json_artifact(
                benchmark_dir
                / "policy-reaction-s2pc-runtime-stability-gpt-oss-20b-calibration-split-c01-heldout-001.json"
            ),
        ),
        build_s2pc_runtime_effect_matrix_method_record(
            method_id="s2pc_l1_sparse_subset_matrix_gpt_oss_20b_12x3_seed11",
            s2pc_runtime_effect_matrix=load_json_artifact(
                benchmark_dir
                / "policy-reaction-s2pc-c01-sparse-subset-matrix-gpt-oss-20b-12x3-heldout-001.json"
            ),
        ),
        build_s2pc_runtime_stability_method_record(
            method_id="s2pc_l1_sparse_selector_stability_gpt_oss_20b_s02",
            s2pc_runtime_stability=load_json_artifact(
                benchmark_dir
                / "policy-reaction-s2pc-runtime-stability-gpt-oss-20b-calibration-split-s02-heldout-001.json"
            ),
        ),
        build_textgrad_manifest_method_record(
            method_id="deepseek_v4_pro_textgrad_w3w4_candidate_update",
            generator="deepseek_v4_pro_textgrad_candidate_update",
            manifest=load_json_artifact(
                manifest_dir
                / "w3w4-deepseek-v4-pro-eval2-seed42-structured-smoke-001.json"
            ),
        ),
    ]
    return records


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


def _validate_method_record(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("method record must be a JSON object")
    _validate_method_id(record.get("method_id"))
    _validate_generator(record.get("generator"))
    status = record.get("status")
    if status not in {"accepted", "rejected", "diagnostic_only"}:
        raise ValueError("method record status must be accepted, rejected, or diagnostic_only")
    eligibility = record.get("eligibility")
    if eligibility not in {"heldout_candidate", "diagnostic_only"}:
        raise ValueError("method record eligibility is unsupported")
    if eligibility == "diagnostic_only" and status != "diagnostic_only":
        raise ValueError("diagnostic-only method records must have diagnostic_only status")
    if eligibility == "heldout_candidate" and status == "diagnostic_only":
        raise ValueError("heldout method records cannot have diagnostic_only status")
    for field_name in ("initial_loss", "best_loss", "final_loss"):
        _numeric(record.get(field_name), field_name)
    _assert_strict_json(record)
    return dict(record)


def _best_accepted_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not records:
        return None
    return min(records, key=lambda record: float(record["candidate_loss"]))


def _lowest_initial_loss_record(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not records:
        return None
    return min(records, key=lambda record: float(record["initial_loss"]))


def _overall_status(
    *,
    accepted_count: int,
    heldout_count: int,
    diagnostic_count: int,
) -> str:
    if accepted_count > 0:
        return "accepted_methods_available"
    if heldout_count > 0:
        return "no_accepted_methods"
    if diagnostic_count > 0:
        return "diagnostic_only"
    return "empty"


def _risk_flags(
    *,
    accepted_count: int,
    rejected_count: int,
    diagnostic_count: int,
    heldout_count: int,
) -> list[str]:
    flags = ["update_method_gate_not_field_validation"]
    if accepted_count == 0 and heldout_count > 0:
        flags.append("no_accepted_update_method")
    if rejected_count > 0:
        flags.append("candidate_methods_rejected")
    if diagnostic_count > 0:
        flags.append("policy_reaction_heldout_evidence_missing")
    return flags


def _generator_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        generator = str(record["generator"])
        counts[generator] = counts.get(generator, 0) + 1
    return dict(sorted(counts.items()))


def _generator_summaries(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for generator in sorted({str(record["generator"]) for record in records}):
        generator_records = [
            record for record in records if record["generator"] == generator
        ]
        heldout_records = [
            record
            for record in generator_records
            if record["eligibility"] == "heldout_candidate"
        ]
        accepted_records = [
            record for record in heldout_records if record["status"] == "accepted"
        ]
        rejected_records = [
            record for record in heldout_records if record["status"] == "rejected"
        ]
        diagnostic_records = [
            record
            for record in generator_records
            if record["eligibility"] == "diagnostic_only"
        ]
        best_record = _best_accepted_record(accepted_records)
        summaries[generator] = {
            "record_count": len(generator_records),
            "heldout_candidate_count": len(heldout_records),
            "accepted_count": len(accepted_records),
            "rejected_count": len(rejected_records),
            "diagnostic_only_count": len(diagnostic_records),
            "best_method_id": best_record["method_id"] if best_record else None,
            "best_loss": best_record["candidate_loss"] if best_record else None,
        }
    return summaries


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


def _validate_method_id(value: Any) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError("method_id is required")


def _validate_generator(value: Any) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError("generator is required")


def _numeric(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be numeric")
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise ValueError(f"{field_name} must be non-negative finite")
    return number


def _finite_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field_name} must be finite")
    return number


def _round_float(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 12)


def _strict_record(record: dict[str, Any]) -> dict[str, Any]:
    _assert_strict_json(record)
    return record


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
