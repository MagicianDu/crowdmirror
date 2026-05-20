import json

import pytest

from circe.calibration.s2pc import (
    S2PC_L1_CANDIDATE_SET_SCHEMA_VERSION,
    S2PC_SCHEMA_VERSION,
    build_s2pc_candidate_artifact,
    build_s2pc_l1_candidate_set_artifact,
    compile_semantic_matches_to_parameter_patches,
    default_semantic_factor_catalog,
    extract_s2pc_candidate_from_l1_set,
    mine_policy_reaction_residuals,
    retrieve_semantic_factors,
    run_constrained_parameter_beam_search,
    validate_semantic_factor_catalog,
)
from experiments.policy_reaction_s2pc_gate import (
    build_policy_reaction_s2pc_candidate,
    build_policy_reaction_s2pc_gate,
    write_policy_reaction_s2pc_candidate_from_l1_set,
    write_policy_reaction_s2pc_l1_candidate_set,
    write_policy_reaction_s2pc_gate,
)


def test_default_semantic_factor_catalog_is_strict_json_and_bounded():
    catalog = default_semantic_factor_catalog()

    assert catalog["schema_version"] == S2PC_SCHEMA_VERSION
    assert catalog["factor_count"] == 8
    assert {
        factor["factor_id"] for factor in catalog["factors"]
    } == {
        "food_insecurity_salience",
        "cash_liquidity_preference",
        "benefit_immediacy",
        "eligibility_uncertainty",
        "institutional_trust",
        "household_budget_rigidity",
        "policy_complexity_aversion",
        "inflation_stress_sensitivity",
    }
    for factor in catalog["factors"]:
        assert factor["claim_boundary"]
        assert factor["parameter_bounds"]
        for parameter_name, bounds in factor["parameter_bounds"].items():
            assert set(bounds) == {"min", "max"}
            assert bounds["min"] <= bounds["max"], parameter_name

    validate_semantic_factor_catalog(catalog)
    json.dumps(catalog, allow_nan=False)


def test_mine_policy_reaction_residuals_uses_only_calibration_split():
    residuals = mine_policy_reaction_residuals(_calibration_benchmark())

    assert residuals["schema_version"] == "circe-s2pc-residuals-v1"
    assert residuals["source_split"] == "calibration"
    assert residuals["residual_count"] == 6
    first = residuals["residuals"][0]
    assert first == {
        "segment": "general_population_cost_pressure",
        "policy_id": "baseline_no_new_support",
        "official_probability": 0.55,
        "predicted_probability": 0.10,
        "residual": 0.45,
        "direction": "under_predicted",
        "magnitude": 0.45,
    }
    json.dumps(residuals, allow_nan=False)


def test_mine_policy_reaction_residuals_rejects_heldout_generation():
    artifact = _calibration_benchmark()
    artifact["source_ingestion_artifact_id"] = (
        "policy-reaction-htops-evaluation-ingestion"
    )

    with pytest.raises(ValueError, match="calibration split"):
        mine_policy_reaction_residuals(artifact)


def test_retrieve_semantic_factors_matches_segment_policy_and_direction():
    residuals = mine_policy_reaction_residuals(
        _calibration_benchmark(),
        min_magnitude=0.05,
    )
    matches = retrieve_semantic_factors(
        residuals,
        default_semantic_factor_catalog(),
        top_k=2,
    )

    assert matches["schema_version"] == "circe-s2pc-semantic-matches-v1"
    assert matches["match_count"] > 0
    low_income_food = [
        match
        for match in matches["matches"]
        if match["segment"] == "low_income_food_insecure"
        and match["policy_id"] == "food_subsidy_expansion"
    ]
    assert low_income_food
    assert low_income_food[0]["factor_id"] == "food_insecurity_salience"
    assert low_income_food[0]["score"] > 0
    json.dumps(matches, allow_nan=False)


def test_compile_semantic_matches_to_parameter_patches_is_bounded():
    residuals = mine_policy_reaction_residuals(
        _calibration_benchmark(),
        min_magnitude=0.10,
    )
    matches = retrieve_semantic_factors(
        residuals,
        default_semantic_factor_catalog(),
        top_k=1,
    )

    patches = compile_semantic_matches_to_parameter_patches(
        matches,
        default_semantic_factor_catalog(),
    )

    assert patches["schema_version"] == "circe-s2pc-parameter-patches-v1"
    assert patches["parameter_patch_count"] > 0
    first = patches["parameter_patches"][0]
    assert {
        "segment",
        "policy_id",
        "factor_id",
        "parameter_name",
        "parameter_value",
        "parameter_bounds",
        "expected_effect",
        "provenance",
    } <= set(first)
    assert (
        first["parameter_bounds"]["min"]
        <= first["parameter_value"]
        <= first["parameter_bounds"]["max"]
    )
    json.dumps(patches, allow_nan=False)


def test_run_constrained_parameter_beam_search_keeps_top_candidates():
    residuals = mine_policy_reaction_residuals(
        _calibration_benchmark(),
        min_magnitude=0.10,
    )
    matches = retrieve_semantic_factors(
        residuals,
        default_semantic_factor_catalog(),
        top_k=1,
    )
    patches = compile_semantic_matches_to_parameter_patches(
        matches,
        default_semantic_factor_catalog(),
    )

    search = run_constrained_parameter_beam_search(patches, beam_width=3)

    assert search["schema_version"] == "circe-s2pc-beam-search-v1"
    assert search["beam_width"] == 3
    assert 1 <= search["candidate_count"] <= 3
    assert (
        search["candidates"][0]["proxy_score"]
        >= search["candidates"][-1]["proxy_score"]
    )
    assert search["candidates"][0]["parameter_patches"]
    json.dumps(search, allow_nan=False)


def test_build_s2pc_candidate_artifact_preserves_provenance():
    residuals = mine_policy_reaction_residuals(
        _calibration_benchmark(),
        min_magnitude=0.10,
    )
    matches = retrieve_semantic_factors(
        residuals,
        default_semantic_factor_catalog(),
        top_k=1,
    )
    patches = compile_semantic_matches_to_parameter_patches(
        matches,
        default_semantic_factor_catalog(),
    )
    search = run_constrained_parameter_beam_search(patches, beam_width=2)

    candidate = build_s2pc_candidate_artifact(
        candidate_id="policy-reaction-s2pc-candidate-test",
        calibration_benchmark=_calibration_benchmark(),
        residual_artifact=residuals,
        semantic_matches=matches,
        parameter_patches=patches,
        search_result=search,
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["candidate_id"] == "policy-reaction-s2pc-candidate-test"
    assert candidate["generator"] == "s2pc_l0_deterministic_catalog_beam_search"
    assert candidate["source_split_contract"]["residual_mining"] == "calibration"
    assert candidate["best_candidate"]["parameter_patches"]
    assert candidate["candidate_prompt_components"]["calibration_anchor"]
    json.dumps(candidate, allow_nan=False)


def test_build_s2pc_l1_candidate_set_keeps_multiple_runtime_candidates():
    residuals = mine_policy_reaction_residuals(
        _calibration_benchmark(),
        min_magnitude=0.05,
    )
    matches = retrieve_semantic_factors(
        residuals,
        default_semantic_factor_catalog(),
        top_k=2,
    )
    patches = compile_semantic_matches_to_parameter_patches(
        matches,
        default_semantic_factor_catalog(),
    )
    search = run_constrained_parameter_beam_search(patches, beam_width=3)

    candidate_set = build_s2pc_l1_candidate_set_artifact(
        candidate_set_id="policy-reaction-s2pc-l1-candidate-set-test",
        calibration_benchmark=_calibration_benchmark(),
        residual_artifact=residuals,
        semantic_matches=matches,
        parameter_patches=patches,
        search_result=search,
    )

    assert candidate_set["schema_version"] == S2PC_L1_CANDIDATE_SET_SCHEMA_VERSION
    assert candidate_set["candidate_set_id"] == (
        "policy-reaction-s2pc-l1-candidate-set-test"
    )
    assert candidate_set["generator"] == "s2pc_l1_multi_candidate_runtime_search"
    assert candidate_set["candidate_count"] == 3
    assert candidate_set["candidates"][0]["candidate_prompt_components"][
        "calibration_anchor"
    ]
    assert candidate_set["source_split_contract"]["candidate_acceptance"] == (
        "heldout_required"
    )
    json.dumps(candidate_set, allow_nan=False)


def test_extract_s2pc_candidate_from_l1_set_is_product_runtime_compatible():
    candidate_set = _build_l1_candidate_set_fixture()
    selected_id = candidate_set["candidates"][1]["candidate_id"]

    candidate = extract_s2pc_candidate_from_l1_set(
        candidate_set,
        candidate_id=selected_id,
    )

    assert candidate["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert candidate["candidate_id"] == selected_id
    assert candidate["generator"] == "s2pc_l1_multi_candidate_runtime_search"
    assert candidate["candidate_prompt_components"]
    assert candidate["source_split_contract"]["candidate_acceptance"] == (
        "heldout_required"
    )
    json.dumps(candidate, allow_nan=False)


def test_policy_reaction_s2pc_gate_accepts_improved_heldout_candidate(tmp_path):
    candidate = build_policy_reaction_s2pc_candidate(
        _calibration_benchmark(),
        candidate_id="policy-reaction-s2pc-candidate-test",
        min_residual_magnitude=0.10,
        top_k=1,
        beam_width=2,
    )

    gate = build_policy_reaction_s2pc_gate(
        candidate,
        initial_heldout_benchmark=_heldout_benchmark("initial-heldout", loss=0.159),
        candidate_heldout_benchmark=_heldout_benchmark(
            "candidate-heldout",
            loss=0.011,
        ),
        artifact_id="policy-reaction-s2pc-gate-test",
    )

    assert gate["schema_version"] == "policy-reaction-s2pc-gate-v1"
    assert gate["overall_status"] == "accepted"
    assert gate["initial_loss"] == 0.159
    assert gate["best_loss"] == 0.011
    assert gate["final_loss"] == 0.011
    assert gate["candidate_accepted_count"] == 1
    assert gate["candidate_rejected_count"] == 0
    assert gate["source_split_contract"]["candidate_acceptance"] == "heldout"
    json.dumps(gate, allow_nan=False)


def test_policy_reaction_s2pc_gate_rejects_regressed_candidate():
    candidate = build_policy_reaction_s2pc_candidate(
        _calibration_benchmark(),
        candidate_id="policy-reaction-s2pc-candidate-test",
        min_residual_magnitude=0.10,
        top_k=1,
        beam_width=2,
    )

    gate = build_policy_reaction_s2pc_gate(
        candidate,
        initial_heldout_benchmark=_heldout_benchmark("initial-heldout", loss=0.011),
        candidate_heldout_benchmark=_heldout_benchmark(
            "candidate-heldout",
            loss=0.020,
        ),
        artifact_id="policy-reaction-s2pc-gate-test",
    )

    assert gate["overall_status"] == "rejected"
    assert gate["best_loss"] == 0.011
    assert gate["final_loss"] == 0.011
    assert gate["candidate_accepted_count"] == 0
    assert gate["candidate_rejected_count"] == 1


def test_write_policy_reaction_s2pc_gate_writes_candidate_and_gate(tmp_path):
    candidate_output = tmp_path / "candidate.json"
    gate_output = tmp_path / "gate.json"
    calibration_path = tmp_path / "calibration.json"
    initial_path = tmp_path / "initial.json"
    candidate_heldout_path = tmp_path / "candidate-heldout.json"
    calibration_path.write_text(json.dumps(_calibration_benchmark()))
    initial_path.write_text(
        json.dumps(_heldout_benchmark("initial-heldout", loss=0.159))
    )
    candidate_heldout_path.write_text(
        json.dumps(_heldout_benchmark("candidate-heldout", loss=0.011))
    )

    written = write_policy_reaction_s2pc_gate(
        gate_output,
        candidate_output_path=candidate_output,
        calibration_benchmark_path=calibration_path,
        initial_heldout_benchmark_path=initial_path,
        candidate_heldout_benchmark_path=candidate_heldout_path,
        candidate_id="policy-reaction-s2pc-candidate-test",
        artifact_id="policy-reaction-s2pc-gate-test",
        min_residual_magnitude=0.10,
        top_k=1,
        beam_width=2,
    )

    assert written == gate_output
    assert (
        json.loads(candidate_output.read_text())["candidate_id"]
        == "policy-reaction-s2pc-candidate-test"
    )
    assert json.loads(gate_output.read_text())["overall_status"] == "accepted"


def test_write_policy_reaction_s2pc_l1_candidate_set(tmp_path):
    calibration_path = tmp_path / "calibration.json"
    output = tmp_path / "candidate-set.json"
    calibration_path.write_text(json.dumps(_calibration_benchmark()))

    written = write_policy_reaction_s2pc_l1_candidate_set(
        output,
        calibration_benchmark_path=calibration_path,
        candidate_set_id="policy-reaction-s2pc-l1-candidate-set-test",
        min_residual_magnitude=0.05,
        top_k=2,
        beam_width=3,
    )

    assert written == output
    persisted = json.loads(output.read_text())
    assert persisted["schema_version"] == "policy-reaction-s2pc-l1-candidate-set-v1"
    assert persisted["candidate_count"] == 3
    assert persisted["candidates"][0]["candidate_prompt_components"]


def test_write_policy_reaction_s2pc_candidate_from_l1_set(tmp_path):
    candidate_set_path = tmp_path / "candidate-set.json"
    output = tmp_path / "candidate.json"
    candidate_set_path.write_text(json.dumps(_build_l1_candidate_set_fixture()))
    candidate_id = (
        "policy-reaction-s2pc-l1-candidate-set-test-c02"
    )

    written = write_policy_reaction_s2pc_candidate_from_l1_set(
        output,
        candidate_set_path=candidate_set_path,
        candidate_id=candidate_id,
    )

    assert written == output
    persisted = json.loads(output.read_text())
    assert persisted["schema_version"] == "policy-reaction-s2pc-candidate-v1"
    assert persisted["candidate_id"] == candidate_id
    assert persisted["generator"] == "s2pc_l1_multi_candidate_runtime_search"
    assert persisted["candidate_prompt_components"]


def _calibration_benchmark() -> dict:
    return {
        "schema_version": "policy-reaction-official-segment-benchmark-v1",
        "artifact_id": "policy-reaction-calibration-benchmark-test",
        "source_ingestion_artifact_id": "policy-reaction-htops-calibration-ingestion",
        "prediction_artifact_id": "policy-reaction-initial-predictions-test",
        "overall_status": "passed",
        "benchmark_metrics": {"weighted_choice_distribution_jsd": 0.20},
        "segment_coverage": {"coverage_rate": 1.0},
        "segment_metrics": {
            "low_income_food_insecure": {
                "official_distribution": {
                    "baseline_no_new_support": 0.20,
                    "cash_cost_of_living_rebate": 0.25,
                    "food_subsidy_expansion": 0.55,
                },
                "predicted_distribution": {
                    "baseline_no_new_support": 0.05,
                    "cash_cost_of_living_rebate": 0.35,
                    "food_subsidy_expansion": 0.60,
                },
            },
            "general_population_cost_pressure": {
                "official_distribution": {
                    "baseline_no_new_support": 0.55,
                    "cash_cost_of_living_rebate": 0.27,
                    "food_subsidy_expansion": 0.18,
                },
                "predicted_distribution": {
                    "baseline_no_new_support": 0.10,
                    "cash_cost_of_living_rebate": 0.34,
                    "food_subsidy_expansion": 0.56,
                },
            },
        },
    }


def _heldout_benchmark(artifact_id: str, *, loss: float) -> dict:
    return {
        "schema_version": "policy-reaction-official-segment-benchmark-v1",
        "artifact_id": artifact_id,
        "source_ingestion_artifact_id": "policy-reaction-htops-evaluation-ingestion",
        "prediction_artifact_id": f"{artifact_id}-predictions",
        "prediction_model": "deepseek-v4-flash",
        "overall_status": "passed",
        "benchmark_metrics": {
            "weighted_choice_distribution_jsd": loss,
            "segment_rank_correlation": 0.75,
        },
        "segment_coverage": {"coverage_rate": 1.0},
        "segment_metrics": {},
    }


def _build_l1_candidate_set_fixture() -> dict:
    residuals = mine_policy_reaction_residuals(
        _calibration_benchmark(),
        min_magnitude=0.05,
    )
    matches = retrieve_semantic_factors(
        residuals,
        default_semantic_factor_catalog(),
        top_k=2,
    )
    patches = compile_semantic_matches_to_parameter_patches(
        matches,
        default_semantic_factor_catalog(),
    )
    search = run_constrained_parameter_beam_search(patches, beam_width=3)
    return build_s2pc_l1_candidate_set_artifact(
        candidate_set_id="policy-reaction-s2pc-l1-candidate-set-test",
        calibration_benchmark=_calibration_benchmark(),
        residual_artifact=residuals,
        semantic_matches=matches,
        parameter_patches=patches,
        search_result=search,
    )
