import json

from experiments.r6_product_scenario_intake import build_r6_product_scenario_intake
from experiments.r6_product_story_package import build_r6_product_story_package


def test_r6_product_story_package_is_artifact_backed_and_no_static_fallback():
    intake = build_r6_product_scenario_intake(
        artifact_id="r6-story-intake-test",
        run_id="r6-product-first-run",
    )
    package = build_r6_product_story_package(
        artifact_id="r6-product-story-package-test",
        run_id="r6-product-first-run",
        scenario_intake=intake,
    )

    assert package["schema_version"] == "r6-product-story-package-v1"
    assert package["status"] == "product_story_package_ready_guarded"
    assert package["sections"] == [
        "scenario",
        "static_prior_baseline",
        "interaction_risk_shift",
        "evidence_cards",
        "gap_closure",
        "blocked_claims",
        "next_measurement_plan",
    ]
    assert package["ui_contract"]["static_narrative_fallback_allowed"] is False
    assert package["ui_contract"]["all_customer_visible_claims_require_source_artifact"] is True
    assert "r6-gap-closure-status" in package["evidence_card_ids"]
    assert package["source_refs"]
    json.dumps(package, allow_nan=False)
