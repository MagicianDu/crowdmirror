import json
import subprocess
import sys
from pathlib import Path

from experiments.r12_customer_trial_launch_packet_export import (
    R12_CUSTOMER_TRIAL_LAUNCH_PACKET_EXPORT_SCHEMA_VERSION,
    build_r12_customer_trial_launch_packet_export,
    write_r12_customer_trial_launch_packet_export,
)


def test_r12_customer_trial_launch_packet_export_writes_customer_readable_markdown(
    tmp_path,
):
    markdown_output = tmp_path / "customer-trial-launch-packet.md"

    export = build_r12_customer_trial_launch_packet_export(
        artifact_id="r12-customer-trial-launch-packet-export-test",
        run_id="r12-l31-test",
        exported_at="2026-06-28T14:20:00Z",
        r12_customer_trial_launch_handoff_package=_load_current_l30(),
        markdown_output_path=markdown_output,
    )

    assert export["schema_version"] == (
        R12_CUSTOMER_TRIAL_LAUNCH_PACKET_EXPORT_SCHEMA_VERSION
    )
    assert export["status"] == (
        "r12_customer_trial_launch_packet_export_ready_source_pending"
    )
    assert export["claim_level"] == "customer_trial_packet_export_no_validation_claim"
    assert export["export_summary"] == {
        "exported_at": "2026-06-28T14:20:00Z",
        "launch_handoff_artifact_id": (
            "r12-customer-trial-launch-handoff-package-current-001"
        ),
        "current_stage": "source_arrival_pending",
        "launch_handoff_ready": True,
        "markdown_output_path": str(markdown_output),
        "markdown_export_written": True,
        "customer_field_slice_present": False,
        "field_outcome_validated": False,
    }
    assert export["packet_sections"] == [
        "客户试运行数据回流请求",
        "字段模板",
        "审批与隐私边界",
        "提交后操作步骤",
        "阻断声明",
    ]
    assert export["acceptance_gates"] == {
        "launch_packet_export_ready": True,
        "launch_handoff_package_ready": True,
        "markdown_export_written": True,
        "customer_field_slice_present": False,
        "field_outcome_validated": False,
        "product_default_allowed": False,
        "runtime_default_allowed": False,
    }
    assert {
        "artifact_id": f"customer_trial_launch_packet_markdown:{markdown_output}",
        "path": str(markdown_output),
    } in export["source_registry"]
    markdown = markdown_output.read_text()
    assert "# 客户试运行数据回流请求" in markdown
    assert "r12_customer_field_slice_submission_request" in markdown
    assert "case_id, segment_id, scenario_id" in markdown
    assert "field validation 尚未完成" in markdown
    assert "runtime_default_allowed=true" in export["blocked_claims"]
    json.dumps(export, allow_nan=False)


def test_r12_customer_trial_launch_packet_export_writer_and_cli(tmp_path):
    launch_path = tmp_path / "l30.json"
    launch_path.write_text(json.dumps(_load_current_l30(), allow_nan=False))
    markdown_output = tmp_path / "packet-cli.md"
    artifact_output = tmp_path / "packet-export.json"

    output_path = write_r12_customer_trial_launch_packet_export(
        output=artifact_output,
        artifact_id="r12-customer-trial-launch-packet-export-test",
        run_id="r12-l31-test",
        exported_at="2026-06-28T14:20:00Z",
        r12_customer_trial_launch_handoff_package=_load_current_l30(),
        markdown_output_path=markdown_output,
    )

    assert output_path == artifact_output
    assert markdown_output.exists()
    assert json.loads(artifact_output.read_text())["acceptance_gates"][
        "launch_packet_export_ready"
    ] is True

    cli_markdown = tmp_path / "packet-cli-output.md"
    cli_output = tmp_path / "packet-export-cli.json"
    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r12_customer_trial_launch_packet_export.py",
            "--artifact-id",
            "r12-customer-trial-launch-packet-export-cli",
            "--run-id",
            "r12-l31-cli-test",
            "--exported-at",
            "2026-06-28T14:20:00Z",
            "--r12-customer-trial-launch-handoff-package-path",
            str(launch_path),
            "--markdown-output-path",
            str(cli_markdown),
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
        "r12-customer-trial-launch-packet-export-v1"
    )
    assert json.loads(completed.stdout) == {
        "artifact_id": "r12-customer-trial-launch-packet-export-cli",
        "markdown_export_written": True,
        "output": str(cli_output),
        "status": "r12_customer_trial_launch_packet_export_ready_source_pending",
    }


def _load_current_l30():
    return _load_result(
        "r12_customer_trial_launch_handoff_package/"
        "r12-customer-trial-launch-handoff-package-current-001.json"
    )


def _load_result(relative_path: str) -> dict:
    return json.loads((_repo_root() / "experiments/results" / relative_path).read_text())


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
