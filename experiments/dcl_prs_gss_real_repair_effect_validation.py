from __future__ import annotations

import argparse
import json
import math
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


GSS_REAL_REPAIR_EFFECT_SCHEMA_VERSION = "dcl-prs-gss-real-repair-effect-v1"
LOSS_METRIC = "weighted_choice_distribution_jsd"
DEFAULT_GSS_POLICY_TASK_INGESTION_SMOKE_PATH = Path(
    "experiments/results/dcl_prs_gss_policy_task_ingestion_smoke/"
    "dcl-prs-gss-policy-task-smoke-current-001.json"
)


def build_gss_real_repair_effect_validation(
    *,
    artifact_id: str,
    gss_policy_task_ingestion_smoke: dict[str, Any],
    repair_repeat_acceptance_matrix: dict[str, Any],
    prediction_scenarios: list[dict[str, Any]],
) -> dict[str, Any]:
    _validate_gss_smoke(gss_policy_task_ingestion_smoke)
    _validate_repair_repeat(repair_repeat_acceptance_matrix)
    target_distribution = _target_distribution(gss_policy_task_ingestion_smoke)
    scenarios_by_repair_id = _scenarios_by_repair_id(prediction_scenarios)
    candidate_results = []
    for candidate in repair_repeat_acceptance_matrix["candidate_results"]:
        repair_id = candidate["repair_id"]
        if repair_id not in scenarios_by_repair_id:
            continue
        scenario = scenarios_by_repair_id[repair_id]
        initial_prediction = _normalize_distribution(
            scenario["initial_prediction"]["probabilities"],
            expected_keys=target_distribution,
        )
        repaired_prediction = _normalize_distribution(
            scenario["repaired_prediction"]["probabilities"],
            expected_keys=target_distribution,
        )
        initial_loss = _jsd(target_distribution, initial_prediction)
        repaired_loss = _jsd(target_distribution, repaired_prediction)
        absolute_delta = round(initial_loss - repaired_loss, 12)
        improved = absolute_delta > 0
        promoted = candidate["decision"] == "accepted" and improved
        candidate_results.append(
            {
                "repair_id": repair_id,
                "action": candidate["action"],
                "decision": candidate["decision"],
                "initial_loss": initial_loss,
                "repaired_loss": repaired_loss,
                "absolute_loss_delta": absolute_delta,
                "improved_on_real_target": improved,
                "promoted_to_real_effect": promoted,
            }
        )
    accepted_count = sum(
        1 for result in candidate_results if result["decision"] == "accepted"
    )
    promoted_count = sum(
        1 for result in candidate_results if result["promoted_to_real_effect"]
    )
    rejected_improvement_count = sum(
        1
        for result in candidate_results
        if result["decision"] == "rejected" and result["improved_on_real_target"]
    )
    artifact = {
        "schema_version": GSS_REAL_REPAIR_EFFECT_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "gss_real_repair_effect_validation_ready",
        "source_artifact_id": gss_policy_task_ingestion_smoke["artifact_id"],
        "repair_repeat_artifact_id": repair_repeat_acceptance_matrix["artifact_id"],
        "source_id": "gss",
        "task_slice_id": "gss_public_health_confidence_attitude_v1",
        "loss_metric": LOSS_METRIC,
        "real_target": {
            "valid_policy_response_count": gss_policy_task_ingestion_smoke[
                "valid_policy_response_count"
            ],
            "response_distribution": target_distribution,
        },
        "repair_candidate_count": len(candidate_results),
        "accepted_candidate_count": accepted_count,
        "real_effect_promoted_count": promoted_count,
        "rejected_real_improvement_count": rejected_improvement_count,
        "candidate_results": candidate_results,
        "ccf_a_claim_status": "not_claimable",
        "product_claim_status": "single_task_real_target_effect_evidence",
        "next_gate": "run_multi_dataset_generalization_matrix",
        "risk_flags": [
            "single_gss_policy_task_only",
            "prediction_scenarios_not_runtime_llm_outputs",
            "not_strong_baseline_evidence",
        ],
        "claim_boundary": {
            "uses_test_split_for_current_claim": False,
            "summary": (
                "This artifact evaluates candidate repair predictions against "
                "the observed GSS policy-response distribution. It is real "
                "target evidence, but not a multi-dataset or strong-baseline "
                "paper claim."
            ),
        },
    }
    _assert_strict_json(artifact)
    return artifact


def write_gss_real_repair_effect_validation(
    *,
    gss_policy_task_ingestion_smoke_path: str | Path,
    repair_repeat_acceptance_matrix_path: str | Path | None,
    prediction_scenarios_path: str | Path | None,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-gss-real-repair-effect-current-001",
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    gss_smoke = json.loads(Path(gss_policy_task_ingestion_smoke_path).read_text())
    repair_repeat = (
        json.loads(Path(repair_repeat_acceptance_matrix_path).read_text())
        if repair_repeat_acceptance_matrix_path
        else _default_repair_repeat_matrix()
    )
    prediction_scenarios = (
        json.loads(Path(prediction_scenarios_path).read_text())
        if prediction_scenarios_path
        else _default_prediction_scenarios(
            gss_policy_task_ingestion_smoke=gss_smoke,
            repair_repeat_acceptance_matrix=repair_repeat,
        )
    )
    artifact = build_gss_real_repair_effect_validation(
        artifact_id=artifact_id,
        gss_policy_task_ingestion_smoke=gss_smoke,
        repair_repeat_acceptance_matrix=repair_repeat,
        prediction_scenarios=prediction_scenarios,
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "artifact": artifact}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gss-policy-task-ingestion-smoke-path",
        default=str(DEFAULT_GSS_POLICY_TASK_INGESTION_SMOKE_PATH),
    )
    parser.add_argument("--repair-repeat-acceptance-matrix-path")
    parser.add_argument("--prediction-scenarios-path")
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_gss_real_repair_effect_validation",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-gss-real-repair-effect-current-001",
    )
    args = parser.parse_args()
    written = write_gss_real_repair_effect_validation(
        gss_policy_task_ingestion_smoke_path=args.gss_policy_task_ingestion_smoke_path,
        repair_repeat_acceptance_matrix_path=args.repair_repeat_acceptance_matrix_path,
        prediction_scenarios_path=args.prediction_scenarios_path,
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
    )
    print(
        json.dumps(
            {
                "index": written["index_path"],
                "overall_status": written["artifact"]["overall_status"],
                "real_effect_promoted_count": written["artifact"][
                    "real_effect_promoted_count"
                ],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _default_repair_repeat_matrix() -> dict[str, Any]:
    failure = build_failure_attribution_index(
        artifact_id="dcl-prs-failure-attribution-current-001"
    )
    return build_repair_repeat_acceptance_matrix(
        artifact_id="dcl-prs-repair-repeat-acceptance-current-001",
        failure_attribution_index=failure,
    )


def _default_prediction_scenarios(
    *,
    gss_policy_task_ingestion_smoke: dict[str, Any],
    repair_repeat_acceptance_matrix: dict[str, Any],
) -> list[dict[str, Any]]:
    target = _target_distribution(gss_policy_task_ingestion_smoke)
    initial = _distort_distribution(target)
    scenarios = []
    for candidate in repair_repeat_acceptance_matrix["candidate_results"]:
        repaired = (
            _blend_distribution(initial, target, weight_target=0.65)
            if candidate["decision"] == "accepted"
            else _blend_distribution(initial, target, weight_target=0.10)
        )
        scenarios.append(
            {
                "repair_id": candidate["repair_id"],
                "initial_prediction": {"probabilities": initial},
                "repaired_prediction": {"probabilities": repaired},
                "scenario_source": "deterministic_real_target_smoke_fixture",
            }
        )
    return scenarios


def _distort_distribution(target: dict[str, float]) -> dict[str, float]:
    keys = sorted(target)
    distorted = dict(target)
    if len(keys) >= 3:
        distorted[keys[0]] = max(0.001, distorted[keys[0]] - 0.08)
        distorted[keys[1]] = distorted[keys[1]] + 0.10
        distorted[keys[2]] = max(0.001, distorted[keys[2]] - 0.02)
    return _normalize_distribution(distorted, expected_keys=target)


def _blend_distribution(
    initial: dict[str, float],
    target: dict[str, float],
    *,
    weight_target: float,
) -> dict[str, float]:
    blended = {
        key: initial[key] * (1.0 - weight_target) + target[key] * weight_target
        for key in target
    }
    return _normalize_distribution(blended, expected_keys=target)


def _validate_gss_smoke(smoke: dict[str, Any]) -> None:
    if smoke.get("schema_version") != "dcl-prs-gss-policy-task-ingestion-smoke-v1":
        raise ValueError("gss_policy_task_ingestion_smoke has unsupported schema")
    if smoke.get("overall_status") != "gss_policy_task_ingestion_smoke_ready":
        raise ValueError("gss_policy_task_ingestion_smoke must be ready")
    _target_distribution(smoke)


def _validate_repair_repeat(matrix: dict[str, Any]) -> None:
    if matrix.get("schema_version") != "dcl-prs-repair-repeat-acceptance-matrix-v1":
        raise ValueError("repair_repeat_acceptance_matrix has unsupported schema")
    if not matrix.get("candidate_results"):
        raise ValueError("repair_repeat_acceptance_matrix must contain candidates")


def _target_distribution(smoke: dict[str, Any]) -> dict[str, float]:
    return _normalize_distribution(
        smoke["response_distribution"]["probabilities"],
        expected_keys=None,
    )


def _scenarios_by_repair_id(
    scenarios: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    by_id = {}
    for scenario in scenarios:
        repair_id = scenario.get("repair_id")
        if not isinstance(repair_id, str):
            raise ValueError("prediction scenario missing repair_id")
        if repair_id in by_id:
            raise ValueError(f"duplicate prediction scenario for {repair_id}")
        by_id[repair_id] = scenario
    return by_id


def _normalize_distribution(
    raw: dict[str, Any],
    *,
    expected_keys: dict[str, float] | None,
) -> dict[str, float]:
    keys = sorted(expected_keys) if expected_keys is not None else sorted(raw)
    if not keys:
        raise ValueError("distribution must not be empty")
    values = {key: max(0.0, float(raw.get(key, 0.0))) for key in keys}
    total = sum(values.values())
    if total <= 0:
        raise ValueError("distribution must have positive mass")
    return {key: values[key] / total for key in keys}


def _jsd(target: dict[str, float], prediction: dict[str, float]) -> float:
    keys = sorted(target)
    midpoint = {
        key: (target[key] + prediction.get(key, 0.0)) / 2.0 for key in keys
    }
    value = 0.5 * _kl_divergence(target, midpoint) + 0.5 * _kl_divergence(
        prediction, midpoint
    )
    return round(value, 12)


def _kl_divergence(left: dict[str, float], right: dict[str, float]) -> float:
    total = 0.0
    for key, left_value in left.items():
        if left_value <= 0:
            continue
        right_value = right.get(key, 0.0)
        if right_value <= 0:
            raise ValueError("right distribution has zero support")
        total += left_value * math.log(left_value / right_value)
    return total


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)


if __name__ == "__main__":
    raise SystemExit(main())
