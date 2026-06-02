import json

import pytest

from experiments.policy_reaction_lcdu_l3_method_summary import (
    build_policy_reaction_lcdu_l3_method_summary,
)


def test_build_lcdu_l3_method_summary_promotes_stable_mainline_with_boundaries():
    summary = build_policy_reaction_lcdu_l3_method_summary(
        artifact_id="policy-reaction-lcdu-l3-method-summary-test",
        h02_stability=_stability(
            "policy-reaction-lcdu-l3-current-001-h02",
            loss=0.000096,
        ),
        i01_stability=_stability(
            "policy-reaction-lcdu-l3-interaction-current-001-i01",
            loss=0.000092334757,
        ),
        interaction_matrix=_matrix(
            "policy-reaction-lcdu-l3-interaction-matrix-test",
            best_candidate_id="policy-reaction-lcdu-l3-interaction-current-001-i01",
            best_loss=0.000092334757,
            improved_count=3,
            regressed_count=1,
        ),
        ablation_matrix=_matrix(
            "policy-reaction-lcdu-l3-ablation-matrix-test",
            best_candidate_id="policy-reaction-lcdu-l3-ablation-current-001-a02",
            best_loss=0.000111545213,
            improved_count=1,
            regressed_count=3,
        ),
        challenger_matrices=[
            _matrix(
                "policy-reaction-route-combo-r3b-segment-constraint-matrix-test",
                best_candidate_id="route-combo-r3b-v01",
                best_loss=0.000111545213,
                improved_count=4,
                regressed_count=0,
            )
        ],
        axis_weakness=_axis_weakness(),
        residual_weakness=_residual_weakness(),
    )

    assert summary["schema_version"] == "policy-reaction-lcdu-l3-method-summary-v1"
    assert summary["overall_status"] == "active_mainline_bounded"
    assert summary["product_transfer_status"] == "bounded_transfer_ready"
    assert summary["accepted_candidate_ids"] == [
        "policy-reaction-lcdu-l3-current-001-h02",
        "policy-reaction-lcdu-l3-interaction-current-001-i01",
    ]
    assert summary["evidence"]["stability"]["stable_repeat_count"] == 2
    assert summary["evidence"]["mechanism"]["interaction_best_loss"] == 0.000092334757
    assert summary["evidence"]["route_coverage"]["challenger_count"] == 1
    assert summary["evidence"]["route_coverage"]["challenger_exceeds_lcdu_l3"] is False
    assert summary["evidence"]["residual_weakness"]["worst_axis_segment"] == (
        "price_stress_level=high"
    )
    assert "ccf_a_external_validity_missing" in summary["ccf_a_gaps"]
    assert "not_customer_field_validated" in summary["risk_flags"]
    assert any("not field validation" in item for item in summary["claim_boundaries"])
    json.dumps(summary, allow_nan=False)


def test_build_lcdu_l3_method_summary_rejects_unstable_mainline():
    with pytest.raises(ValueError, match="stable_improvement"):
        build_policy_reaction_lcdu_l3_method_summary(
            artifact_id="policy-reaction-lcdu-l3-method-summary-test",
            h02_stability=_stability(
                "policy-reaction-lcdu-l3-current-001-h02",
                loss=0.000096,
                status="mixed",
            ),
            i01_stability=_stability(
                "policy-reaction-lcdu-l3-interaction-current-001-i01",
                loss=0.000092334757,
            ),
            interaction_matrix=_matrix(
                "policy-reaction-lcdu-l3-interaction-matrix-test",
                best_candidate_id="policy-reaction-lcdu-l3-interaction-current-001-i01",
                best_loss=0.000092334757,
            ),
            ablation_matrix=_matrix(
                "policy-reaction-lcdu-l3-ablation-matrix-test",
                best_candidate_id="policy-reaction-lcdu-l3-ablation-current-001-a02",
                best_loss=0.000111545213,
            ),
            challenger_matrices=[],
            axis_weakness=_axis_weakness(),
            residual_weakness=_residual_weakness(),
        )


def _stability(candidate_id: str, *, loss: float, status: str = "stable_improvement") -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-runtime-stability-v1",
        "artifact_id": f"stability-{candidate_id}",
        "overall_status": status,
        "best_candidate_id": candidate_id,
        "effect_count": 3,
        "improved_count": 3 if status == "stable_improvement" else 1,
        "regressed_count": 0 if status == "stable_improvement" else 1,
        "loss_summary": {
            "s2pc_runtime_loss_mean": loss,
            "relative_loss_reduction_mean": 0.14,
        },
        "claim_boundary": (
            "S2PC runtime stability matrix is repeat evidence over local held-out "
            "public-data alignment, not field validation."
        ),
    }


def _matrix(
    artifact_id: str,
    *,
    best_candidate_id: str,
    best_loss: float,
    improved_count: int = 1,
    regressed_count: int = 0,
) -> dict:
    return {
        "schema_version": "policy-reaction-s2pc-runtime-effect-matrix-v1",
        "artifact_id": artifact_id,
        "overall_status": "candidate_improvements_available",
        "candidate_count": improved_count + regressed_count,
        "improved_count": improved_count,
        "regressed_count": regressed_count,
        "best_candidate_id": best_candidate_id,
        "best_s2pc_runtime_loss": best_loss,
        "claim_boundary": (
            "S2PC runtime effect matrix ranks held-out alignment outcomes across "
            "candidate variants; not field validation."
        ),
    }


def _axis_weakness() -> dict:
    return {
        "schema_version": "policy-reaction-axis-weakness-v1",
        "artifact_id": "policy-reaction-axis-weakness-test",
        "persistent_weakness": {
            "worst_jsd_segment": "price_stress_level=high",
            "worst_jsd_value_mean": 0.14925228029562396,
            "worst_rank_segment": "income_band=low",
            "worst_rank_value_mean": -1.0,
        },
        "claim_boundary": (
            "Axis-level weakness artifact is same-task internal diagnostics only; "
            "not generalization proof."
        ),
    }


def _residual_weakness() -> dict:
    return {
        "schema_version": "policy-reaction-lcdu-residual-weakness-v1",
        "artifact_id": "policy-reaction-lcdu-l3-low-income-residual-weakness-test",
        "segment_id": "low_income_food_insecure",
        "weakness_summary": {
            "main_drag_run_id": "h02_16x3_seed11",
            "shape_not_rank_issue": True,
            "recommended_repair_direction": (
                "raise cash_cost_of_living_rebate while trimming "
                "baseline_no_new_support"
            ),
        },
        "claim_boundary": (
            "Residual weakness artifact diagnoses segment-level distribution "
            "mismatch only."
        ),
    }
