import json
import subprocess
import sys

from experiments.lcdu_public_task_cards import build_lcdu_public_task_card
from experiments.lcdu_public_task_ingestion_smoke import (
    build_lcdu_public_task_ingestion_smoke,
    build_lcdu_public_task_ingestion_smoke_index,
)


def test_public_health_ingestion_smoke_materializes_official_codebook_distribution():
    smoke = build_lcdu_public_task_ingestion_smoke(
        task_card=build_lcdu_public_task_card(
            task_id="public_health_medical_insurance_attitude_v1"
        )
    )

    assert smoke["schema_version"] == "lcdu-public-task-ingestion-smoke-v1"
    assert smoke["task_id"] == "public_health_medical_insurance_attitude_v1"
    assert smoke["overall_status"] == "target_distribution_skeleton_materialized"
    assert smoke["source_extract"]["source_extract_type"] == (
        "official_codebook_frequency_table"
    )
    assert smoke["source_extract"]["target_variable_id"] == "V241245"
    assert smoke["source_extract"]["valid_substantive_n"] == 4778
    assert smoke["target_distribution_skeleton"]["policy_probabilities"] == {
        "government_insurance_plan": 0.478861448305,
        "mixed_or_middle_position": 0.174340728338,
        "private_insurance_plan": 0.346797823357,
    }
    assert smoke["split_contract"]["final_claim_check"] == "test"
    assert "not_microdata_ingestion_completed" in smoke["risk_flags"]
    json.dumps(smoke, allow_nan=False)


def test_climate_energy_ingestion_smoke_uses_exact_environment_tradeoff_variable():
    smoke = build_lcdu_public_task_ingestion_smoke(
        task_card=build_lcdu_public_task_card(
            task_id="climate_energy_regulation_attitude_v1"
        )
    )

    assert smoke["task_id"] == "climate_energy_regulation_attitude_v1"
    assert smoke["source_extract"]["target_variable_id"] == "V241258"
    assert smoke["source_extract"]["valid_substantive_n"] == 4577
    assert smoke["target_distribution_skeleton"]["policy_probabilities"] == {
        "support_more_regulation_or_spending": 0.58335154031,
        "mixed_or_status_quo": 0.161240987546,
        "oppose_more_regulation_or_spending": 0.255407472143,
    }
    assert smoke["source_extract"]["source_url"].endswith("hcbk0012.htm")


def test_public_task_ingestion_smoke_index_keeps_cross_task_gate_open():
    index = build_lcdu_public_task_ingestion_smoke_index(
        artifact_id="lcdu-public-task-ingestion-smoke-index-test",
        task_cards=[
            build_lcdu_public_task_card(
                task_id="public_health_medical_insurance_attitude_v1"
            ),
            build_lcdu_public_task_card(
                task_id="climate_energy_regulation_attitude_v1"
            ),
        ],
    )

    assert index["schema_version"] == "lcdu-public-task-ingestion-smoke-index-v1"
    assert index["overall_status"] == "target_distribution_skeletons_ready"
    assert index["task_count"] == 2
    assert index["next_gate"] == "load_public_use_microdata_or_verified_sample_slice"
    assert "not_cross_task_validation_evidence" in index["risk_flags"]


def test_public_task_ingestion_smoke_script_writes_artifacts(tmp_path):
    task_dir = tmp_path / "task_cards"
    smoke_dir = tmp_path / "smoke"
    task_dir.mkdir()
    for task_id, file_name in (
        (
            "public_health_medical_insurance_attitude_v1",
            "public-health-medical-insurance-attitude-v1.json",
        ),
        (
            "climate_energy_regulation_attitude_v1",
            "climate-energy-regulation-attitude-v1.json",
        ),
    ):
        card = build_lcdu_public_task_card(task_id=task_id)
        (task_dir / file_name).write_text(json.dumps(card))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/lcdu_public_task_ingestion_smoke.py",
            "--task-card-dir",
            str(task_dir),
            "--output-dir",
            str(smoke_dir),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        "index": str(
            smoke_dir / "lcdu-public-task-ingestion-smoke-index-current-001.json"
        ),
        "task_count": 2,
    }
    assert (
        smoke_dir / "public-health-medical-insurance-attitude-v1-smoke.json"
    ).exists()
    assert (
        smoke_dir / "climate-energy-regulation-attitude-v1-smoke.json"
    ).exists()
