import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_trial_launch_bundle_verification import (
    R12_CUSTOMER_TRIAL_LAUNCH_BUNDLE_VERIFICATION_SCHEMA_VERSION,
    build_r12_customer_trial_launch_bundle_verification,
    write_r12_customer_trial_launch_bundle_verification,
)


def test_r12_customer_trial_launch_bundle_verification_checks_required_files():
    verification = build_r12_customer_trial_launch_bundle_verification(
        artifact_id="r12-customer-trial-launch-bundle-verification-test",
        run_id="r12-l32-test",
        verified_at="2026-06-28T15:10:00Z",
        r12_customer_trial_launch_packet_export=_load_current_l31(),
        r12_customer_trial_launch_packet_export_path=_current_l31_path(),
        repo_root=_repo_root(),
    )

    assert verification["schema_version"] == (
        R12_CUSTOMER_TRIAL_LAUNCH_BUNDLE_VERIFICATION_SCHEMA_VERSION
    )
    assert verification["status"] == (
        "r12_customer_trial_launch_bundle_verification_ready_source_pending"
    )
    assert verification["claim_level"] == (
        "customer_trial_launch_bundle_verified_no_validation_claim"
    )
    assert verification["bundle_summary"] == {
        "verified_at": "2026-06-28T15:10:00Z",
        "packet_export_artifact_id": (
            "r12-customer-trial-launch-packet-export-current-001"
        ),
        "current_stage": "source_arrival_pending",
        "required_item_count": 4,
        "resolved_required_item_count": 4,
        "missing_required_item_ids": [],
        "field_outcome_validated": False,
    }
    assert verification["acceptance_gates"] == {
        "launch_bundle_verified": True,
        "packet_export_json_resolvable": True,
        "markdown_packet_resolvable": True,
        "launch_handoff_json_resolvable": True,
        "field_slice_template_resolvable": True,
        "all_required_bundle_items_resolvable": True,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    required_ids = {
        item["bundle_item_id"]
        for item in verification["bundle_items"]
        if item["required_for_customer_launch"]
    }
    assert required_ids == {
        "packet_export_json",
        "customer_launch_packet_markdown",
        "launch_handoff_json",
        "field_slice_template_csv",
    }
    for item in verification["bundle_items"]:
        assert item["path_resolvable"] is True
        assert item["size_bytes"] > 0
        assert len(item["sha256"]) == 64
    assert "field validation 已完成" in verification["blocked_claims"]
    assert "runtime_default_allowed=true" in verification["blocked_claims"]
    json.dumps(verification, allow_nan=False)


def test_r12_customer_trial_launch_bundle_verification_fails_closed_when_packet_missing(
    tmp_path,
):
    packet = _load_current_l31()
    missing_markdown = tmp_path / "missing-packet.md"
    packet["export_summary"]["markdown_output_path"] = str(missing_markdown)
    for entry in packet["source_registry"]:
        if entry["artifact_id"].startswith("customer_trial_launch_packet_markdown:"):
            entry["path"] = str(missing_markdown)
            entry["artifact_id"] = f"customer_trial_launch_packet_markdown:{missing_markdown}"

    verification = build_r12_customer_trial_launch_bundle_verification(
        artifact_id="r12-customer-trial-launch-bundle-verification-missing-test",
        run_id="r12-l32-missing-test",
        verified_at="2026-06-28T15:10:00Z",
        r12_customer_trial_launch_packet_export=packet,
        r12_customer_trial_launch_packet_export_path=_current_l31_path(),
        repo_root=_repo_root(),
    )

    assert verification["status"] == (
        "r12_customer_trial_launch_bundle_verification_blocked_missing_bundle_item"
    )
    assert verification["bundle_summary"]["missing_required_item_ids"] == [
        "customer_launch_packet_markdown"
    ]
    assert verification["acceptance_gates"]["launch_bundle_verified"] is False
    assert verification["acceptance_gates"]["markdown_packet_resolvable"] is False
    assert verification["acceptance_gates"]["product_default_allowed"] is False
    assert verification["acceptance_gates"]["runtime_default_allowed"] is False


def test_r12_customer_trial_launch_bundle_verification_writer_and_cli(tmp_path):
    packet_path = tmp_path / "l31.json"
    packet_path.write_text(json.dumps(_load_current_l31(), allow_nan=False))
    artifact_output = tmp_path / "bundle-verification.json"

    output_path = write_r12_customer_trial_launch_bundle_verification(
        output=artifact_output,
        artifact_id="r12-customer-trial-launch-bundle-verification-test",
        run_id="r12-l32-test",
        verified_at="2026-06-28T15:10:00Z",
        r12_customer_trial_launch_packet_export=_load_current_l31(),
        r12_customer_trial_launch_packet_export_path=_current_l31_path(),
        repo_root=_repo_root(),
    )

    assert output_path == artifact_output
    assert json.loads(artifact_output.read_text())["acceptance_gates"][
        "launch_bundle_verified"
    ] is True

    cli_output = tmp_path / "bundle-verification-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_trial_launch_bundle_verification.py",
            "--artifact-id",
            "r12-customer-trial-launch-bundle-verification-cli",
            "--run-id",
            "r12-l32-cli-test",
            "--verified-at",
            "2026-06-28T15:10:00Z",
            "--r12-customer-trial-launch-packet-export-path",
            str(packet_path),
            "--repo-root",
            str(_repo_root()),
            "--output",
            str(cli_output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    artifact = json.loads(cli_output.read_text())
    assert artifact["schema_version"] == (
        "r12-customer-trial-launch-bundle-verification-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-customer-trial-launch-bundle-verification-cli",
        "launch_bundle_verified": True,
        "output": str(cli_output),
        "status": "r12_customer_trial_launch_bundle_verification_ready_source_pending",
    }


def _load_current_l31():
    return json.loads(_current_l31_path().read_text())


def _current_l31_path() -> Path:
    return (
        _repo_root()
        / "experiments/results/r12_customer_trial_launch_packet_export/"
        "r12-customer-trial-launch-packet-export-current-001.json"
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
