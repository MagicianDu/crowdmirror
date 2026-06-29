import csv
import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_field_slice_handoff_package import (
    R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION,
    build_r12_customer_field_slice_handoff_package,
    write_r12_customer_field_slice_handoff_package,
)


def test_r12_customer_field_slice_handoff_package_defines_machine_checkable_customer_template():
    report = build_r12_customer_field_slice_handoff_package(
        artifact_id="r12-customer-field-slice-handoff-package-test",
        run_id="r12-l21-test",
        r12_target_outcome_or_customer_field_slice_arrival=_load_current_l20(),
        generated_at="2026-06-27T15:45:00Z",
        template_output_path=(
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-template-current-001.csv"
        ),
    )

    assert report["schema_version"] == (
        R12_CUSTOMER_FIELD_SLICE_HANDOFF_PACKAGE_SCHEMA_VERSION
    )
    assert report["status"] == (
        "r12_customer_field_slice_handoff_package_ready_guarded"
    )
    assert report["claim_level"] == (
        "customer_field_slice_handoff_ready_no_validation_claim"
    )
    assert report["handoff_summary"] == {
        "source_arrival_artifact_id": (
            "r12-target-outcome-or-customer-field-slice-arrival-current-001"
        ),
        "target_outcome_period": "May 2026",
        "prediction_case_count": 14,
        "minimum_case_count": 10,
        "generated_at": "2026-06-27T15:45:00Z",
        "template_output_path": (
            "experiments/results/r12_customer_field_slice_handoff_package/"
            "r12-customer-field-slice-template-current-001.csv"
        ),
    }
    assert report["field_slice_contract"]["required_fields"] == [
        "case_id",
        "segment_id",
        "scenario_id",
        "prediction_share_or_score",
        "observed_outcome",
        "outcome_timestamp",
        "customer_approval_reference",
    ]
    assert report["field_slice_contract"]["accepted_formats"] == [
        "csv",
        "jsonl",
    ]
    assert report["privacy_and_approval_contract"] == {
        "customer_approval_reference_required": True,
        "direct_personal_identifiers_allowed": False,
        "aggregation_or_pseudonymous_case_id_required": True,
        "manual_prompt_or_persona_patch_allowed": False,
    }
    assert report["template_preview"]["header_only_template"] is True
    assert report["template_preview"]["columns"] == report[
        "field_slice_contract"
    ]["required_fields"]
    assert report["template_preview"]["example_row"]["case_id"] == (
        "customer_case_001"
    )
    assert report["acceptance_gates"] == {
        "source_arrival_gate_ready": True,
        "customer_field_slice_template_generated": True,
        "customer_field_slice_contract_machine_checkable": True,
        "customer_data_request_ready": True,
        "outcome_source_arrived": False,
        "metrics_computed": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
        "direct_personal_identifiers_allowed": False,
        "manual_prompt_or_persona_patch_allowed": False,
    }
    assert report["next_required_artifact"] == (
        "r12_target_outcome_or_customer_field_slice_arrival_with_customer_slice"
    )
    assert "metrics_computed=true" in report["blocked_claims"]
    assert "direct personal identifiers in customer slice" in report[
        "blocked_claims"
    ]
    json.dumps(report, allow_nan=False)


def test_r12_customer_field_slice_handoff_package_writer_outputs_json_and_csv_template(
    tmp_path,
):
    output = tmp_path / "handoff.json"
    template = tmp_path / "template.csv"

    output_path = write_r12_customer_field_slice_handoff_package(
        output=output,
        artifact_id="r12-customer-field-slice-handoff-package-test",
        run_id="r12-l21-test",
        r12_target_outcome_or_customer_field_slice_arrival=_load_current_l20(),
        generated_at="2026-06-27T15:45:00Z",
        template_output_path=template,
    )

    assert output_path == output
    report = json.loads(output.read_text())
    assert report["template_preview"]["template_output_path"] == str(template)
    with template.open(newline="") as fh:
        rows = list(csv.reader(fh))
    assert rows == [
        [
            "case_id",
            "segment_id",
            "scenario_id",
            "prediction_share_or_score",
            "observed_outcome",
            "outcome_timestamp",
            "customer_approval_reference",
        ]
    ]


def test_r12_customer_field_slice_handoff_package_cli_writes_artifacts(tmp_path):
    arrival_path = tmp_path / "r12-l20.json"
    output = tmp_path / "handoff.json"
    template = tmp_path / "template.csv"
    arrival_path.write_text(json.dumps(_load_current_l20(), allow_nan=False))

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_field_slice_handoff_package.py",
            "--artifact-id",
            "r12-customer-field-slice-handoff-package-cli",
            "--run-id",
            "r12-l21-test",
            "--r12-target-outcome-or-customer-field-slice-arrival-path",
            str(arrival_path),
            "--generated-at",
            "2026-06-27T15:45:00Z",
            "--template-output",
            str(template),
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(output.read_text())
    assert artifact["schema_version"] == (
        "r12-customer-field-slice-handoff-package-v1"
    )
    assert template.exists()
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-customer-field-slice-handoff-package-cli",
        "output": str(output),
        "status": "r12_customer_field_slice_handoff_package_ready_guarded",
        "template_output": str(template),
    }


def _load_current_l20():
    repo_root = Path(__file__).resolve().parents[1]
    return json.loads(
        (
            repo_root
            / "experiments/results/"
            "r12_target_outcome_or_customer_field_slice_arrival/"
            "r12-target-outcome-or-customer-field-slice-arrival-current-001.json"
        ).read_text()
    )
