from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DECISION_SCHEMA_VERSION = "dcl-prs-strong-baseline-decision-matrix-v1"
DEFAULT_DCL_PRS_STRONG_BASELINE_MATRIX_PATH = Path(
    "experiments/results/dcl_prs_strong_baseline_matrix/"
    "dcl-prs-strong-baseline-current-001.json"
)
DEFAULT_GSS_REAL_REPAIR_EFFECT_VALIDATION_PATH = Path(
    "experiments/results/dcl_prs_gss_real_repair_effect_validation/"
    "dcl-prs-gss-real-repair-effect-current-001.json"
)
DEFAULT_MULTI_DATASET_GENERALIZATION_MATRIX_PATH = Path(
    "experiments/results/dcl_prs_multi_dataset_generalization_matrix/"
    "dcl-prs-multi-dataset-generalization-current-001.json"
)
DEFAULT_LCDU_STRONG_BASELINE_MATRIX_PATHS = [
    Path(
        "experiments/results/lcdu_lcr_segment_gate_strong_baseline/"
        "lcdu-anes-lcr-sg-strong-baseline-current-001.json"
    ),
    Path(
        "experiments/results/lcdu_llm_core_strong_baseline/"
        "lcdu-anes-llm-core-strong-baseline-current-001.json"
    ),
]

REQUIRED_BASELINE_FAMILIES = [
    "deterministic_anchor",
    "LCDU-LCR-SG",
    "fixed_party_or_ideology_prior",
]
NON_RUNTIME_RISK_FLAGS = {
    "prediction_scenarios_not_runtime_llm_outputs",
    "not_strong_baseline_evidence",
}


def build_dcl_prs_strong_baseline_decision_matrix(
    *,
    artifact_id: str,
    dcl_prs_strong_baseline_matrix: dict[str, Any] | None,
    gss_real_repair_effect_validation: dict[str, Any] | None,
    multi_dataset_generalization_matrix: dict[str, Any] | None,
    lcdU_strong_baseline_matrices: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    lcdU_strong_baseline_matrices = lcdU_strong_baseline_matrices or []
    dcl_win = _dcl_prs_strong_win(dcl_prs_strong_baseline_matrix)
    multi_closed = _multi_dataset_gate_closed(multi_dataset_generalization_matrix)
    runtime_or_strong_evidence = _has_runtime_or_strong_evidence(
        gss_real_repair_effect_validation
    )
    stable_win = dcl_win and multi_closed and runtime_or_strong_evidence
    stoploss_triggers = [] if stable_win else _stoploss_triggers(
        dcl_prs_strong_baseline_matrix=dcl_prs_strong_baseline_matrix,
        gss_real_repair_effect_validation=gss_real_repair_effect_validation,
        multi_dataset_generalization_matrix=multi_dataset_generalization_matrix,
    )
    artifact = {
        "schema_version": DECISION_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": _overall_status(
            stable_win=stable_win,
            has_decision_inputs=bool(dcl_prs_strong_baseline_matrix),
        ),
        "validation_type": "dcl_prs_strong_baseline_decision_matrix",
        "source_artifact_ids": _source_artifact_ids(
            dcl_prs_strong_baseline_matrix=dcl_prs_strong_baseline_matrix,
            gss_real_repair_effect_validation=gss_real_repair_effect_validation,
            multi_dataset_generalization_matrix=multi_dataset_generalization_matrix,
            lcdU_strong_baseline_matrices=lcdU_strong_baseline_matrices,
        ),
        "evidence_class": (
            "research_result_candidate" if stable_win else "engineering_result_only"
        ),
        "stable_strong_baseline_win_proven": stable_win,
        "required_baseline_families": REQUIRED_BASELINE_FAMILIES,
        "primary_decision": _primary_decision(stable_win=stable_win),
        "dcl_prs_evidence_summary": _dcl_prs_evidence_summary(
            dcl_prs_strong_baseline_matrix=dcl_prs_strong_baseline_matrix,
            gss_real_repair_effect_validation=gss_real_repair_effect_validation,
            multi_dataset_generalization_matrix=multi_dataset_generalization_matrix,
        ),
        "lcdU_reference_baseline_summary": _lcdU_reference_summary(
            lcdU_strong_baseline_matrices
        ),
        "stoploss_triggers": stoploss_triggers,
        "next_required_experiment": (
            "promote_to_full_paper_gate_audit"
            if stable_win
            else "run_dcl_prs_runtime_strong_baseline_trial_or_retire_algorithm_main_claim"
        ),
        "claim_boundary": (
            "This artifact is a decision layer over existing DCL-PRS and LCDU "
            "evidence. It separates engineering readiness from accuracy "
            "superiority and must not treat deterministic repair smoke as a "
            "stable strong-baseline win."
        ),
    }
    _assert_strict_json(artifact)
    return artifact


def write_dcl_prs_strong_baseline_decision_matrix(
    *,
    output_dir: str | Path,
    artifact_id: str = "dcl-prs-strong-baseline-decision-current-001",
    dcl_prs_strong_baseline_matrix_path: str | Path = (
        DEFAULT_DCL_PRS_STRONG_BASELINE_MATRIX_PATH
    ),
    gss_real_repair_effect_validation_path: str | Path = (
        DEFAULT_GSS_REAL_REPAIR_EFFECT_VALIDATION_PATH
    ),
    multi_dataset_generalization_matrix_path: str | Path = (
        DEFAULT_MULTI_DATASET_GENERALIZATION_MATRIX_PATH
    ),
    lcdU_strong_baseline_matrix_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    lcdU_paths = (
        [Path(path) for path in lcdU_strong_baseline_matrix_paths]
        if lcdU_strong_baseline_matrix_paths
        else DEFAULT_LCDU_STRONG_BASELINE_MATRIX_PATHS
    )
    artifact = build_dcl_prs_strong_baseline_decision_matrix(
        artifact_id=artifact_id,
        dcl_prs_strong_baseline_matrix=_load_json_if_exists(
            Path(dcl_prs_strong_baseline_matrix_path)
        ),
        gss_real_repair_effect_validation=_load_json_if_exists(
            Path(gss_real_repair_effect_validation_path)
        ),
        multi_dataset_generalization_matrix=_load_json_if_exists(
            Path(multi_dataset_generalization_matrix_path)
        ),
        lcdU_strong_baseline_matrices=[
            matrix for path in lcdU_paths if (matrix := _load_json_if_exists(path))
        ],
    )
    index_path = output_path / f"{artifact_id}.json"
    index_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return {"index_path": str(index_path), "artifact": artifact}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dcl-prs-strong-baseline-matrix-path",
        default=str(DEFAULT_DCL_PRS_STRONG_BASELINE_MATRIX_PATH),
    )
    parser.add_argument(
        "--gss-real-repair-effect-validation-path",
        default=str(DEFAULT_GSS_REAL_REPAIR_EFFECT_VALIDATION_PATH),
    )
    parser.add_argument(
        "--multi-dataset-generalization-matrix-path",
        default=str(DEFAULT_MULTI_DATASET_GENERALIZATION_MATRIX_PATH),
    )
    parser.add_argument(
        "--lcdu-strong-baseline-matrix-path",
        action="append",
        default=[],
    )
    parser.add_argument(
        "--output-dir",
        default="experiments/results/dcl_prs_strong_baseline_decision",
    )
    parser.add_argument(
        "--artifact-id",
        default="dcl-prs-strong-baseline-decision-current-001",
    )
    args = parser.parse_args()
    written = write_dcl_prs_strong_baseline_decision_matrix(
        output_dir=args.output_dir,
        artifact_id=args.artifact_id,
        dcl_prs_strong_baseline_matrix_path=(
            args.dcl_prs_strong_baseline_matrix_path
        ),
        gss_real_repair_effect_validation_path=(
            args.gss_real_repair_effect_validation_path
        ),
        multi_dataset_generalization_matrix_path=(
            args.multi_dataset_generalization_matrix_path
        ),
        lcdU_strong_baseline_matrix_paths=(
            args.lcdu_strong_baseline_matrix_path or None
        ),
    )
    artifact = written["artifact"]
    print(
        json.dumps(
            {
                "evidence_class": artifact["evidence_class"],
                "index": written["index_path"],
                "overall_status": artifact["overall_status"],
                "stable_strong_baseline_win_proven": artifact[
                    "stable_strong_baseline_win_proven"
                ],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


def _dcl_prs_strong_win(artifact: dict[str, Any] | None) -> bool:
    if artifact is None:
        return False
    if artifact.get("schema_version") != "dcl-prs-strong-baseline-matrix-v1":
        return False
    if artifact.get("overall_status") != "strong_baseline_dcl_prs_leads":
        return False
    if artifact.get("paper_gate_eligible") is not True:
        return False
    if artifact.get("dcl_prs_leads_covered_baselines") is not True:
        return False
    return _beats_required_baselines(artifact)


def _beats_required_baselines(artifact: dict[str, Any]) -> bool:
    results = artifact.get("baseline_results", [])
    by_family = {
        row.get("baseline_family"): row.get("dcl_prs_beats_baseline")
        for row in results
        if isinstance(row, dict)
    }
    return all(by_family.get(family) is True for family in REQUIRED_BASELINE_FAMILIES)


def _multi_dataset_gate_closed(artifact: dict[str, Any] | None) -> bool:
    return (
        artifact is not None
        and artifact.get("schema_version")
        == "dcl-prs-multi-dataset-generalization-matrix-v1"
        and artifact.get("generalization_gate_closed") is True
        and int(artifact.get("available_real_effect_dataset_count", 0)) >= 2
    )


def _has_runtime_or_strong_evidence(artifact: dict[str, Any] | None) -> bool:
    if artifact is None:
        return False
    if artifact.get("schema_version") != "dcl-prs-gss-real-repair-effect-v1":
        return False
    if artifact.get("overall_status") != "gss_real_repair_effect_validation_ready":
        return False
    return not (set(artifact.get("risk_flags", [])) & NON_RUNTIME_RISK_FLAGS)


def _stoploss_triggers(
    *,
    dcl_prs_strong_baseline_matrix: dict[str, Any] | None,
    gss_real_repair_effect_validation: dict[str, Any] | None,
    multi_dataset_generalization_matrix: dict[str, Any] | None,
) -> list[str]:
    triggers = []
    if dcl_prs_strong_baseline_matrix is None:
        triggers.append("dcl_prs_strong_baseline_matrix_missing")
    else:
        for gap in dcl_prs_strong_baseline_matrix.get("blocking_gaps", []):
            _append_unique(triggers, gap)
        if not _dcl_prs_strong_win(dcl_prs_strong_baseline_matrix):
            _append_unique(triggers, "strong_baseline_win_missing")
    if gss_real_repair_effect_validation is None:
        _append_unique(triggers, "real_effect_validation_missing")
    else:
        for flag in gss_real_repair_effect_validation.get("risk_flags", []):
            if flag in {
                "single_gss_policy_task_only",
                "prediction_scenarios_not_runtime_llm_outputs",
                "not_strong_baseline_evidence",
            }:
                _append_unique(triggers, flag)
    if not _multi_dataset_gate_closed(multi_dataset_generalization_matrix):
        _append_unique(triggers, "multi_dataset_generalization_incomplete")
    return triggers


def _primary_decision(*, stable_win: bool) -> dict[str, str]:
    if stable_win:
        return {
            "research_claim": "promote_dcl_prs_as_research_result_candidate",
            "ccf_a_gate": "conditional_candidate_pending_full_paper_audit",
            "product_claim": (
                "candidate_core_calibration_claim_pending_product_runtime_validation"
            ),
        }
    return {
        "research_claim": "stoploss_dcl_prs_as_algorithm_main_claim",
        "ccf_a_gate": "not_passed_under_accuracy_superiority_criterion",
        "product_claim": "retain_as_auditable_diagnostic_evidence_not_market_core",
    }


def _overall_status(*, stable_win: bool, has_decision_inputs: bool) -> str:
    if stable_win:
        return "decision_boundary_research_candidate"
    if has_decision_inputs:
        return "decision_boundary_stoploss_recommended"
    return "decision_boundary_incomplete"


def _dcl_prs_evidence_summary(
    *,
    dcl_prs_strong_baseline_matrix: dict[str, Any] | None,
    gss_real_repair_effect_validation: dict[str, Any] | None,
    multi_dataset_generalization_matrix: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "strong_baseline_status": (
            dcl_prs_strong_baseline_matrix or {}
        ).get("overall_status"),
        "paper_gate_eligible": (
            dcl_prs_strong_baseline_matrix or {}
        ).get("paper_gate_eligible"),
        "dcl_prs_leads_covered_baselines": (
            dcl_prs_strong_baseline_matrix or {}
        ).get("dcl_prs_leads_covered_baselines"),
        "baseline_results": (dcl_prs_strong_baseline_matrix or {}).get(
            "baseline_results", []
        ),
        "real_effect_status": (gss_real_repair_effect_validation or {}).get(
            "overall_status"
        ),
        "real_effect_promoted_count": (
            gss_real_repair_effect_validation or {}
        ).get("real_effect_promoted_count"),
        "real_effect_risk_flags": (gss_real_repair_effect_validation or {}).get(
            "risk_flags", []
        ),
        "generalization_status": (multi_dataset_generalization_matrix or {}).get(
            "overall_status"
        ),
        "available_real_effect_dataset_count": (
            multi_dataset_generalization_matrix or {}
        ).get("available_real_effect_dataset_count"),
        "generalization_gate_closed": (
            multi_dataset_generalization_matrix or {}
        ).get("generalization_gate_closed"),
    }


def _lcdU_reference_summary(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = []
    for artifact in artifacts:
        if artifact.get("schema_version") != "lcdu-anes-strong-baseline-matrix-v1":
            continue
        summary.append(
            {
                "artifact_id": artifact.get("artifact_id"),
                "method_family_under_test": artifact.get(
                    "method_family_under_test",
                    artifact.get("lcdU_method_id"),
                ),
                "overall_status": artifact.get("overall_status"),
                "paper_gate_eligible": artifact.get("paper_gate_eligible"),
                "lcdU_leads_covered_baselines": artifact.get(
                    "lcdU_leads_covered_baselines"
                ),
                "fixed_party_prior_gate_pass": artifact.get(
                    "strong_baseline_gates", {}
                ).get("fixed_party_prior_gate_pass"),
                "risk_flags": artifact.get("risk_flags", []),
            }
        )
    return summary


def _source_artifact_ids(
    *,
    dcl_prs_strong_baseline_matrix: dict[str, Any] | None,
    gss_real_repair_effect_validation: dict[str, Any] | None,
    multi_dataset_generalization_matrix: dict[str, Any] | None,
    lcdU_strong_baseline_matrices: list[dict[str, Any]],
) -> list[str]:
    refs = []
    for artifact in (
        dcl_prs_strong_baseline_matrix,
        gss_real_repair_effect_validation,
        multi_dataset_generalization_matrix,
        *lcdU_strong_baseline_matrices,
    ):
        if artifact is not None and isinstance(artifact.get("artifact_id"), str):
            refs.append(artifact["artifact_id"])
    return refs


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _assert_strict_json(payload: dict[str, Any]) -> None:
    try:
        json.dumps(payload, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "DCL-PRS strong baseline decision matrix must be strict JSON"
        ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
