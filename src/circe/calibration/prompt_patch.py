"""Structured prompt patching with acceptance-gated updates."""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
import json
import math
from typing import Any


PROMPT_PATCH_SCHEMA_VERSION = "circe-prompt-patch-gate-v1"
PROMPT_PATCH_UPDATE_POLICY = (
    "accept_if_loss_decreases_and_segment_coverage_is_complete_else_revert"
)
PROMPT_PATCH_CLAIM_BOUNDARY = (
    "Automated prompt patch evidence only; accepted patches require held-out "
    "evaluation improvement and are not field validation."
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


def _probability(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("policy probabilities must be numeric")
    probability = float(value)
    if not math.isfinite(probability) or probability < 0.0:
        raise ValueError("policy probabilities must be non-negative finite values")
    return probability


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
