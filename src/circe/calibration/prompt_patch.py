"""Structured prompt patching with acceptance-gated updates."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
import json
import math
from typing import Any


PROMPT_PATCH_SCHEMA_VERSION = "circe-prompt-patch-gate-v1"
PROMPT_PATCH_MULTI_CANDIDATE_SCHEMA_VERSION = (
    "circe-prompt-patch-multi-candidate-gate-v1"
)
PROMPT_PATCH_UPDATE_POLICY = (
    "accept_if_loss_decreases_and_segment_coverage_is_complete_else_revert"
)
PROMPT_PATCH_MULTI_CANDIDATE_UPDATE_POLICY = (
    "select_lowest_heldout_loss_candidate_if_coverage_complete_else_revert"
)
PROMPT_PATCH_CLAIM_BOUNDARY = (
    "Automated prompt patch evidence only; accepted patches require held-out "
    "evaluation improvement and are not field validation."
)
PROMPT_PATCH_MULTI_CANDIDATE_CLAIM_BOUNDARY = (
    "Multi-source prompt/persona patch evidence only; candidate generation uses "
    "calibration feedback, and acceptance requires held-out loss improvement."
)
ALLOWED_TARGET_ROOTS = {
    "global_instruction",
    "segment_prompt",
    "persona_prompt",
    "policy_interpretation_prompt",
    "calibration_anchor",
    "response_contract",
}


@dataclass(frozen=True)
class PromptPatch:
    target: str
    operation: str
    reason: str
    patch: str
    expected_effect: dict[str, str]
    source_split: str = "calibration"
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        _assert_strict_json(payload)
        return payload


@dataclass(frozen=True)
class PromptPatchCandidate:
    candidate_id: str
    generator: str
    rationale: str
    patches: list[PromptPatch]
    source_split: str = "calibration"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        _validate_candidate(self)
        payload = {
            "candidate_id": self.candidate_id,
            "generator": self.generator,
            "rationale": self.rationale,
            "source_split": self.source_split,
            "metadata": copy.deepcopy(self.metadata),
            "patches": [patch.to_dict() for patch in self.patches],
        }
        _assert_strict_json(payload)
        return payload


def generate_residual_prompt_patches(
    *,
    observed_by_segment: dict[str, dict[str, float]],
    predicted_by_segment: dict[str, dict[str, float]],
    threshold: float = 0.05,
    source_split: str = "calibration",
) -> list[PromptPatch]:
    if source_split != "calibration":
        raise ValueError("prompt patches must be generated from calibration split")
    patches = []
    for segment, observed_distribution in sorted(observed_by_segment.items()):
        predicted_distribution = predicted_by_segment.get(segment)
        if predicted_distribution is None:
            continue
        residuals = _policy_residuals(
            observed_distribution=observed_distribution,
            predicted_distribution=predicted_distribution,
        )
        material_residuals = {
            policy_id: residual
            for policy_id, residual in residuals.items()
            if abs(residual) >= threshold
        }
        if not material_residuals:
            continue
        primary_policy, primary_residual = max(
            material_residuals.items(),
            key=lambda item: abs(item[1]),
        )
        direction = "under-predicted" if primary_residual > 0 else "over-predicted"
        expected_effect = {
            policy_id: "increase" if residual > 0 else "decrease"
            for policy_id, residual in sorted(material_residuals.items())
        }
        patches.append(
            PromptPatch(
                target=f"segment_prompt.{segment}",
                operation="tighten",
                reason=(
                    f"{primary_policy} is {direction} for {segment} "
                    f"by {abs(primary_residual):.6f} on calibration residuals"
                ),
                patch=_segment_patch_text(
                    segment=segment,
                    expected_effect=expected_effect,
                ),
                expected_effect=expected_effect,
                source_split=source_split,
                evidence={
                    "residuals": material_residuals,
                    "threshold": threshold,
                },
            )
        )
    return patches


def generate_parameter_prompt_patches(
    *,
    segment_parameter_deltas: dict[str, dict[str, float]],
    threshold: float = 0.05,
    source_split: str = "calibration",
) -> list[PromptPatch]:
    if source_split != "calibration":
        raise ValueError("prompt patches must be generated from calibration split")
    patches = []
    for segment, deltas in sorted(segment_parameter_deltas.items()):
        material_deltas = {
            parameter: _finite_delta(delta)
            for parameter, delta in sorted(deltas.items())
            if abs(_finite_delta(delta)) >= threshold
        }
        if not material_deltas:
            continue
        expected_effect = {
            parameter: "increase" if delta > 0 else "decrease"
            for parameter, delta in material_deltas.items()
        }
        patches.append(
            PromptPatch(
                target=f"calibration_anchor.{segment}",
                operation="tighten",
                reason=(
                    f"parameter search produced material calibration deltas for "
                    f"{segment}"
                ),
                patch=_parameter_patch_text(
                    segment=segment,
                    parameter_deltas=material_deltas,
                ),
                expected_effect=expected_effect,
                source_split=source_split,
                evidence={
                    "generator": "parameter_search",
                    "parameter_deltas": material_deltas,
                    "threshold": threshold,
                },
            )
        )
    return patches


def apply_prompt_patch(
    prompt_components: dict[str, Any],
    patch: PromptPatch,
) -> dict[str, Any]:
    _validate_patch(patch)
    updated = copy.deepcopy(prompt_components)
    parent, field_name = _resolve_patch_target(updated, patch.target)
    current_value = parent.get(field_name, "")
    if not isinstance(current_value, str):
        raise ValueError("prompt patch target must resolve to a string component")
    if patch.operation == "replace":
        parent[field_name] = patch.patch
    elif patch.operation in {"append", "tighten"}:
        parent[field_name] = _append_patch_text(current_value, patch.patch)
    else:
        raise ValueError("prompt patch operation must be append, tighten, or replace")
    _assert_strict_json(updated)
    return updated


def apply_prompt_patches(
    prompt_components: dict[str, Any],
    patches: list[PromptPatch],
) -> dict[str, Any]:
    updated = copy.deepcopy(prompt_components)
    for patch in patches:
        updated = apply_prompt_patch(updated, patch)
    return updated


def build_prompt_patch_gate(
    prompt_components: dict[str, Any],
    patches: list[PromptPatch],
    *,
    artifact_id: str,
    initial_loss: float,
    candidate_loss: float,
    coverage_rate: float,
    min_improvement: float = 0.0,
) -> dict[str, Any]:
    _validate_loss(initial_loss, "initial_loss")
    _validate_loss(candidate_loss, "candidate_loss")
    _validate_coverage_rate(coverage_rate)
    if not patches:
        raise ValueError("prompt patch gate requires at least one candidate patch")

    candidate_prompt_components = apply_prompt_patches(prompt_components, patches)
    loss_delta = candidate_loss - initial_loss
    accepted = coverage_rate >= 1.0 and loss_delta < -min_improvement
    final_prompt_components = (
        candidate_prompt_components if accepted else copy.deepcopy(prompt_components)
    )
    final_loss = candidate_loss if accepted else initial_loss
    artifact = {
        "schema_version": PROMPT_PATCH_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "accepted" if accepted else "rejected",
        "candidate_update_policy": PROMPT_PATCH_UPDATE_POLICY,
        "initial_loss": initial_loss,
        "candidate_loss": candidate_loss,
        "best_loss": min(initial_loss, candidate_loss) if accepted else initial_loss,
        "final_loss": final_loss,
        "coverage_rate": coverage_rate,
        "loss_delta": loss_delta,
        "candidate_update_count": len(patches),
        "candidate_evaluated_count": 1,
        "candidate_accepted_count": 1 if accepted else 0,
        "candidate_rejected_count": 0 if accepted else 1,
        "candidate_pending_count": 0,
        "candidate_update_status": "accepted" if accepted else "rejected",
        "patches": [patch.to_dict() for patch in patches],
        "initial_prompt_components": copy.deepcopy(prompt_components),
        "candidate_prompt_components": candidate_prompt_components,
        "final_prompt_components": final_prompt_components,
        "claim_boundary": PROMPT_PATCH_CLAIM_BOUNDARY,
        "claim_boundaries": [
            PROMPT_PATCH_CLAIM_BOUNDARY,
            "Patch generation may use calibration feedback only.",
            "Patch acceptance must be decided by a separate held-out evaluation gate.",
        ],
    }
    _assert_strict_json(artifact)
    return artifact


def build_multi_candidate_prompt_patch_gate(
    prompt_components: dict[str, Any],
    candidates: list[PromptPatchCandidate],
    *,
    artifact_id: str,
    initial_loss: float,
    candidate_evaluations: dict[str, dict[str, Any]],
    min_improvement: float = 0.0,
) -> dict[str, Any]:
    _validate_loss(initial_loss, "initial_loss")
    _validate_loss(min_improvement, "min_improvement")
    if not candidates:
        raise ValueError("multi-candidate prompt patch gate requires candidates")

    seen_candidate_ids: set[str] = set()
    candidate_records = []
    best_candidate: PromptPatchCandidate | None = None
    best_candidate_loss = float(initial_loss)
    generator_counts: dict[str, int] = {}

    for index, candidate in enumerate(candidates):
        _validate_candidate(candidate)
        if candidate.candidate_id in seen_candidate_ids:
            raise ValueError(f"duplicate candidate_id: {candidate.candidate_id}")
        seen_candidate_ids.add(candidate.candidate_id)
        generator_counts[candidate.generator] = (
            generator_counts.get(candidate.generator, 0) + 1
        )

        evaluation = candidate_evaluations.get(candidate.candidate_id)
        if evaluation is None:
            raise ValueError(f"missing evaluation for {candidate.candidate_id}")
        evaluation_split = str(evaluation.get("evaluation_split", "heldout"))
        if evaluation_split not in {"heldout", "evaluation"}:
            raise ValueError("candidate acceptance requires heldout evaluation split")
        candidate_loss = float(evaluation.get("loss"))
        coverage_rate = float(evaluation.get("coverage_rate", 0.0))
        _validate_loss(candidate_loss, "candidate_loss")
        _validate_coverage_rate(coverage_rate)

        loss_delta = candidate_loss - float(initial_loss)
        provisional_status = "rejected"
        reason = "loss_not_improved"
        if coverage_rate < 1.0:
            reason = "segment_coverage_incomplete"
        elif loss_delta < -min_improvement:
            provisional_status = "eligible"
            reason = "eligible_loss_improved"
            if candidate_loss < best_candidate_loss:
                best_candidate = candidate
                best_candidate_loss = candidate_loss

        candidate_prompt_components = apply_prompt_patches(
            prompt_components,
            candidate.patches,
        )
        candidate_records.append(
            {
                "candidate_index": index,
                "candidate_id": candidate.candidate_id,
                "generator": candidate.generator,
                "loss": candidate_loss,
                "initial_loss": float(initial_loss),
                "loss_delta": loss_delta,
                "coverage_rate": coverage_rate,
                "evaluation_split": evaluation_split,
                "status": provisional_status,
                "reason": reason,
                "metadata": copy.deepcopy(candidate.metadata),
                "patches": [patch.to_dict() for patch in candidate.patches],
                "candidate_prompt_components": candidate_prompt_components,
            }
        )

    accepted_candidate_id = best_candidate.candidate_id if best_candidate else None
    for record in candidate_records:
        if record["candidate_id"] == accepted_candidate_id:
            record["status"] = "accepted"
            record["reason"] = "lowest_heldout_loss"
        elif record["status"] == "eligible":
            record["status"] = "rejected"
            record["reason"] = "not_best_improving_candidate"

    if best_candidate is None:
        final_prompt_components = copy.deepcopy(prompt_components)
        final_loss = float(initial_loss)
    else:
        final_prompt_components = apply_prompt_patches(
            prompt_components,
            best_candidate.patches,
        )
        final_loss = best_candidate_loss

    accepted_count = 1 if best_candidate is not None else 0
    artifact = {
        "schema_version": PROMPT_PATCH_MULTI_CANDIDATE_SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "overall_status": "accepted" if accepted_count else "rejected",
        "candidate_update_policy": PROMPT_PATCH_MULTI_CANDIDATE_UPDATE_POLICY,
        "initial_loss": float(initial_loss),
        "best_loss": best_candidate_loss if accepted_count else float(initial_loss),
        "final_loss": final_loss,
        "accepted_candidate_id": accepted_candidate_id,
        "candidate_update_count": len(candidates),
        "candidate_evaluated_count": len(candidate_records),
        "candidate_accepted_count": accepted_count,
        "candidate_rejected_count": len(candidate_records) - accepted_count,
        "candidate_pending_count": 0,
        "generator_counts": dict(sorted(generator_counts.items())),
        "candidates": [candidate.to_dict() for candidate in candidates],
        "candidate_updates": candidate_records,
        "initial_prompt_components": copy.deepcopy(prompt_components),
        "final_prompt_components": final_prompt_components,
        "claim_boundary": PROMPT_PATCH_MULTI_CANDIDATE_CLAIM_BOUNDARY,
        "claim_boundaries": [
            PROMPT_PATCH_MULTI_CANDIDATE_CLAIM_BOUNDARY,
            "TextGrad, residual rules, and parameter search are candidate generators only.",
            "No candidate is accepted unless held-out loss improves with complete segment coverage.",
        ],
    }
    _assert_strict_json(artifact)
    return artifact


def _validate_patch(patch: PromptPatch) -> None:
    if patch.source_split != "calibration":
        raise ValueError("prompt patches must come from calibration split")
    if not patch.target or "." not in patch.target:
        raise ValueError("prompt patch target must be a dotted component path")
    root = patch.target.split(".", 1)[0]
    if root not in ALLOWED_TARGET_ROOTS:
        raise ValueError(f"unsupported prompt patch target root: {root}")
    if not patch.reason:
        raise ValueError("prompt patch reason is required")
    if not patch.patch:
        raise ValueError("prompt patch text is required")


def _validate_candidate(candidate: PromptPatchCandidate) -> None:
    if not candidate.candidate_id:
        raise ValueError("prompt patch candidate_id is required")
    if not candidate.generator:
        raise ValueError("prompt patch candidate generator is required")
    if not candidate.rationale:
        raise ValueError("prompt patch candidate rationale is required")
    if candidate.source_split != "calibration":
        raise ValueError("prompt patch candidates must come from calibration split")
    if not candidate.patches:
        raise ValueError("prompt patch candidate requires at least one patch")
    for patch in candidate.patches:
        _validate_patch(patch)


def _resolve_patch_target(
    prompt_components: dict[str, Any],
    target: str,
) -> tuple[dict[str, Any], str]:
    parts = target.split(".")
    cursor: Any = prompt_components
    for part in parts[:-1]:
        if not isinstance(cursor, dict):
            raise ValueError("prompt patch target path must resolve through objects")
        cursor = cursor.setdefault(part, {})
    if not isinstance(cursor, dict):
        raise ValueError("prompt patch target parent must be an object")
    return cursor, parts[-1]


def _append_patch_text(current_value: str, patch_text: str) -> str:
    if not current_value:
        return patch_text
    return f"{current_value.rstrip()}\n{patch_text.strip()}"


def _policy_residuals(
    *,
    observed_distribution: dict[str, float],
    predicted_distribution: dict[str, float],
) -> dict[str, float]:
    policy_ids = sorted(set(observed_distribution) | set(predicted_distribution))
    return {
        policy_id: _probability(observed_distribution.get(policy_id, 0.0)) -
        _probability(predicted_distribution.get(policy_id, 0.0))
        for policy_id in policy_ids
    }


def _segment_patch_text(
    *,
    segment: str,
    expected_effect: dict[str, str],
) -> str:
    effects = "; ".join(
        f"{policy_id}: {direction}"
        for policy_id, direction in sorted(expected_effect.items())
    )
    return (
        f"Calibration residual adjustment for {segment}. When persona details are "
        f"consistent with this segment, adjust policy choice sensitivity as follows: "
        f"{effects}. Keep probabilities normalized and preserve the response contract."
    )


def _parameter_patch_text(
    *,
    segment: str,
    parameter_deltas: dict[str, float],
) -> str:
    deltas = "; ".join(
        f"{parameter} {'+=' if delta > 0 else '-='} {abs(delta):.6f}"
        for parameter, delta in sorted(parameter_deltas.items())
    )
    return (
        f"Structured calibration parameter adjustment for {segment}. Apply these "
        f"persona-level deltas before producing policy reaction probabilities: "
        f"{deltas}. Keep the response contract unchanged and do not expose these "
        f"parameters in the final JSON response."
    )


def _probability(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("policy probabilities must be numeric")
    probability = float(value)
    if not math.isfinite(probability) or probability < 0.0:
        raise ValueError("policy probabilities must be non-negative finite values")
    return probability


def _finite_delta(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("parameter deltas must be numeric")
    delta = float(value)
    if not math.isfinite(delta):
        raise ValueError("parameter deltas must be finite")
    return delta


def _validate_loss(value: float, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be numeric")
    if not math.isfinite(float(value)) or float(value) < 0.0:
        raise ValueError(f"{field_name} must be non-negative finite")


def _validate_coverage_rate(value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("coverage_rate must be numeric")
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError("coverage_rate must be between 0 and 1")


def _assert_strict_json(payload: dict[str, Any]) -> None:
    json.dumps(payload, allow_nan=False)
