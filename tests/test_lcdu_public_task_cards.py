import json
import subprocess
import sys

from experiments.lcdu_public_task_cards import (
    build_lcdu_public_task_card,
    build_lcdu_public_task_card_index,
)


def test_build_public_health_task_card_records_no_leakage_split_and_targets():
    card = build_lcdu_public_task_card(
        task_id="public_health_medical_insurance_attitude_v1"
    )

    assert card["schema_version"] == "lcdu-public-task-card-v1"
    assert card["task_id"] == "public_health_medical_insurance_attitude_v1"
    assert card["task_status"] == "task_card_smoke_passed"
    assert card["policy_domain"] == "public_health"
    assert card["primary_data_source"]["source_name"] == "ANES 2024 Time Series"
    assert card["target_distribution"]["target_type"] == "policy_attitude_scale"
    assert "V241245" in card["target_distribution"]["candidate_variables"]
    assert card["split_contract"] == {
        "candidate_generation": "calibration",
        "candidate_acceptance": "heldout",
        "final_claim_check": "test",
    }
    assert "public_opinion_alignment_not_field_validation" in card["risk_flags"]
    json.dumps(card, allow_nan=False)


def test_build_climate_energy_task_card_uses_independent_policy_domain():
    card = build_lcdu_public_task_card(
        task_id="climate_energy_regulation_attitude_v1"
    )

    assert card["policy_domain"] == "climate_energy"
    assert card["primary_data_source"]["source_name"] == "ANES 2024 Time Series"
    assert card["target_distribution"]["target_type"] == "policy_support_distribution"
    assert "V241258" in card["target_distribution"]["candidate_variables"]
    assert "party_or_ideology" in card["segment_schema"]["required_axes"]
    assert card["ingestion_smoke"]["status"] == "ready_for_microdata_variable_audit"


def test_build_task_card_index_requires_two_recommended_tasks():
    index = build_lcdu_public_task_card_index(
        artifact_id="lcdu-public-task-card-index-test",
        task_ids=[
            "public_health_medical_insurance_attitude_v1",
            "climate_energy_regulation_attitude_v1",
        ],
    )

    assert index["schema_version"] == "lcdu-public-task-card-index-v1"
    assert index["task_count"] == 2
    assert index["overall_status"] == "recommended_task_cards_ready"
    assert index["next_gate"] == "run_public_task_ingestion_smoke"
    assert index["task_ids"] == [
        "public_health_medical_insurance_attitude_v1",
        "climate_energy_regulation_attitude_v1",
    ]


def test_public_task_card_script_writes_cards_and_index(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_public_task_cards.py",
            "--output-dir",
            str(tmp_path),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(tmp_path / "lcdu-public-task-card-index-current-001.json"),
        "task_count": 2,
    }
    assert (tmp_path / "public-health-medical-insurance-attitude-v1.json").exists()
    assert (tmp_path / "climate-energy-regulation-attitude-v1.json").exists()
