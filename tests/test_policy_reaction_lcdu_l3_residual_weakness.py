import json

from experiments.policy_reaction_lcdu_l3_residual_weakness import (
    build_policy_reaction_lcdu_l3_residual_weakness_artifact,
)


def test_build_residual_weakness_artifact_identifies_shape_problem():
    artifact = build_policy_reaction_lcdu_l3_residual_weakness_artifact(
        baseline_12x3=_benchmark(0.00159, 0.188421, 0.26992, 0.541659),
        h02_12x3=_benchmark(0.00159, 0.188421, 0.26992, 0.541659),
        i01_12x3=_benchmark(0.00159, 0.188421, 0.26992, 0.541659),
        baseline_16x3=_benchmark(0.00144, 0.187018, 0.2716, 0.541382),
        h02_16x3=_benchmark(0.00159, 0.188421, 0.26992, 0.541659),
        i01_16x3=_benchmark(0.00159, 0.188421, 0.26992, 0.541659),
        artifact_id="weakness-test",
    )

    assert artifact["schema_version"] == "policy-reaction-lcdu-residual-weakness-v1"
    assert artifact["weakness_summary"]["shape_not_rank_issue"] is True
    assert artifact["weakness_summary"]["main_drag_run_id"] == "h02_16x3_seed11"
    json.dumps(artifact, allow_nan=False)


def test_residual_weakness_artifact_tracks_policy_bias_signature():
    artifact = build_policy_reaction_lcdu_l3_residual_weakness_artifact(
        baseline_12x3=_benchmark(0.00159, 0.188421, 0.26992, 0.541659),
        h02_12x3=_benchmark(0.00159, 0.188421, 0.26992, 0.541659),
        i01_12x3=_benchmark(0.00159, 0.188421, 0.26992, 0.541659),
        baseline_16x3=_benchmark(0.00144, 0.187018, 0.2716, 0.541382),
        h02_16x3=_benchmark(0.00159, 0.188421, 0.26992, 0.541659),
        i01_16x3=_benchmark(0.00159, 0.188421, 0.26992, 0.541659),
        artifact_id="weakness-test",
    )

    signature = artifact["weakness_summary"]["policy_bias_signature"]
    assert signature["baseline_no_new_support"] == "over_predicted"
    assert signature["cash_cost_of_living_rebate"] == "under_predicted"
    assert signature["food_subsidy_expansion"] == "slightly_over_predicted"


def _benchmark(jsd: float, baseline: float, cash: float, food: float) -> dict:
    return {
        "schema_version": "policy-reaction-official-segment-benchmark-v1",
        "overall_status": "passed",
        "segment_metrics": {
            "low_income_food_insecure": {
                "choice_distribution_jsd": jsd,
                "rank_correlation": 1.0,
                "official_distribution": {
                    "baseline_no_new_support": 0.16287372992861077,
                    "cash_cost_of_living_rebate": 0.30732455696004657,
                    "food_subsidy_expansion": 0.5298017131113426,
                },
                "predicted_distribution": {
                    "baseline_no_new_support": baseline,
                    "cash_cost_of_living_rebate": cash,
                    "food_subsidy_expansion": food,
                },
            }
        },
    }
