import json
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.r6_product_decision_report import build_r6_product_decision_report


def test_r6_product_decision_report_exports_customer_readable_guarded_report():
    report = build_r6_product_decision_report(
        artifact_id="r6-product-decision-report-test",
        run_id="r6-product-first-run",
    )

    assert report["schema_version"] == "r6-product-decision-report-v1"
    assert report["status"] == "decision_report_ready_guarded"
    assert report["customer_sections"] == [
        "what_changed",
        "who_is_at_risk",
        "why_risk_moved",
        "what_is_supported_by_evidence",
        "what_is_blocked",
        "what_to_measure_next",
    ]
    assert report["report_contract"]["source_backed_only"] is True
    assert report["report_contract"]["static_narrative_fallback_allowed"] is False
    assert "field validation 已完成" in report["blocked_claims"]
    assert "runtime default 可以开启" in report["blocked_claims"]
    assert report["next_measurement_plan"]
    assert "r6-product-story-package-current-001" in report["source_refs"]
    assert len(report["source_refs"]) > 1
    _assert_report_sources_resolvable(report)
    json.dumps(report, allow_nan=False)


def test_r6_product_decision_report_accepts_valid_story_package_and_extends_source_refs():
    story_package = _valid_story_package()

    report = build_r6_product_decision_report(
        artifact_id="r6-product-decision-report-test",
        run_id="r6-product-first-run",
        story_package=story_package,
    )

    assert report["blocked_claims"] == story_package["blocked_claims"]
    assert report["next_measurement_plan"] == {
        "source_artifact_ids": ["r6-evidence-report", "r6-gap-closure-report"],
        "required_gate_paths": [
            "acceptance_gates.field_outcome_validated",
            "acceptance_gates.global_update_accepted",
        ],
    }
    assert report["source_refs"] == [
        "r6-product-decision-report-test-story-package",
        "r6-story-source-1",
        "r6-story-source-2",
    ]
    assert report["source_registry"] == [
        *story_package["source_registry"],
        {
            "artifact_id": "r6-product-decision-report-test-story-package",
            "path": "direct_input:story_package",
        },
    ]


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        ({"schema_version": "bad-schema"}, "story_package.schema_version"),
        ({"status": "bad-status"}, "story_package.status"),
    ],
)
def test_r6_product_decision_report_rejects_bad_story_schema_or_status(
    mutation,
    match,
):
    story_package = {**_valid_story_package(), **mutation}

    with pytest.raises(ValueError, match=match):
        build_r6_product_decision_report(
            artifact_id="r6-product-decision-report-test",
            run_id="r6-product-first-run",
            story_package=story_package,
        )


def test_r6_product_decision_report_rejects_mismatched_story_artifact_id():
    story_package = {
        **_valid_story_package(),
        "artifact_id": "r6-product-decision-report-wrong-story-package",
    }

    with pytest.raises(ValueError, match="story_package.artifact_id"):
        build_r6_product_decision_report(
            artifact_id="r6-product-decision-report-test",
            run_id="r6-product-first-run",
            story_package=story_package,
        )


def test_r6_product_decision_report_rejects_string_blocked_claims():
    story_package = {
        **_valid_story_package(),
        "blocked_claims": "runtime default 可以开启",
    }

    with pytest.raises(ValueError, match="story_package.blocked_claims"):
        build_r6_product_decision_report(
            artifact_id="r6-product-decision-report-test",
            run_id="r6-product-first-run",
            story_package=story_package,
        )


@pytest.mark.parametrize(
    "next_measurement_plan",
    [
        [],
        {"source_artifact_ids": ["r6-source"]},
        {"source_artifact_ids": [], "required_gate_paths": ["gate"]},
        {"source_artifact_ids": ["r6-source"], "required_gate_paths": []},
    ],
)
def test_r6_product_decision_report_rejects_bad_next_measurement_plan(
    next_measurement_plan,
):
    story_package = {
        **_valid_story_package(),
        "next_measurement_plan": next_measurement_plan,
    }

    with pytest.raises(ValueError, match="story_package.next_measurement_plan"):
        build_r6_product_decision_report(
            artifact_id="r6-product-decision-report-test",
            run_id="r6-product-first-run",
            story_package=story_package,
        )


def test_r6_product_decision_report_does_not_forward_measurement_narrative():
    story_package = _valid_story_package()
    story_package["next_measurement_plan"] = {
        **story_package["next_measurement_plan"],
        "narrative": "runtime default 可以开启",
    }

    report = build_r6_product_decision_report(
        artifact_id="r6-product-decision-report-test",
        run_id="r6-product-first-run",
        story_package=story_package,
    )

    assert "narrative" not in report["next_measurement_plan"]


def test_r6_product_decision_report_does_not_forward_string_current_gate_values():
    story_package = _valid_story_package()
    story_package["next_measurement_plan"] = {
        **story_package["next_measurement_plan"],
        "current_gate_values": "runtime default 可以开启",
    }

    report = build_r6_product_decision_report(
        artifact_id="r6-product-decision-report-test",
        run_id="r6-product-first-run",
        story_package=story_package,
    )

    assert "current_gate_values" not in report["next_measurement_plan"]


def test_r6_product_decision_report_rejects_static_narrative_fallback_enabled():
    story_package = _valid_story_package()
    story_package["ui_contract"] = {
        **story_package["ui_contract"],
        "static_narrative_fallback_allowed": True,
    }

    with pytest.raises(
        ValueError,
        match="story_package.ui_contract.static_narrative_fallback_allowed",
    ):
        build_r6_product_decision_report(
            artifact_id="r6-product-decision-report-test",
            run_id="r6-product-first-run",
            story_package=story_package,
        )


def test_r6_product_decision_report_cli_writes_artifact_and_stdout_json(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    output = tmp_path / "decision-report.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_product_decision_report.py",
            "--artifact-id",
            "r6-product-decision-report-cli-test",
            "--run-id",
            "r6-product-cli-run",
            "--output",
            str(output),
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    stdout = json.loads(completed.stdout)
    artifact = json.loads(output.read_text())
    assert stdout == {
        "artifact_id": "r6-product-decision-report-cli-test",
        "output": str(output),
        "status": "decision_report_ready_guarded",
    }
    assert artifact["artifact_id"] == "r6-product-decision-report-cli-test"
    assert artifact["report_contract"]["source_backed_only"] is True
    assert artifact["report_contract"]["static_narrative_fallback_allowed"] is False
    assert "r6-product-story-package-current-001" in artifact["source_refs"]
    assert len(artifact["source_refs"]) > 1
    _assert_report_sources_resolvable(artifact)
    json.dumps(artifact, allow_nan=False)


def _valid_story_package():
    return {
        "schema_version": "r6-product-story-package-v1",
        "artifact_id": "r6-product-decision-report-test-story-package",
        "status": "product_story_package_ready_guarded",
        "ui_contract": {
            "static_narrative_fallback_allowed": False,
            "all_customer_visible_claims_require_source_artifact": True,
        },
        "blocked_claims": [
            "field validation 已完成",
            "runtime default 可以开启",
        ],
        "next_measurement_plan": {
            "source_artifact_ids": ["r6-evidence-report", "r6-gap-closure-report"],
            "required_gate_paths": [
                "acceptance_gates.field_outcome_validated",
                "acceptance_gates.global_update_accepted",
            ],
            "current_gate_values": {
                "field_outcome_validated": False,
                "global_update_accepted": False,
            },
        },
        "source_refs": ["r6-story-source-1", "r6-story-source-2"],
        "source_registry": [
            {
                "artifact_id": "r6-story-source-1",
                "path": "experiments/results/story-source-1.json",
            },
            {
                "artifact_id": "r6-story-source-2",
                "path": "experiments/results/story-source-2.json",
            },
        ],
    }


def _assert_report_sources_resolvable(report):
    registry_ids = {entry["artifact_id"] for entry in report["source_registry"]}
    direct_ids = {report["artifact_id"]}
    unresolved = {
        source_ref
        for source_ref in report["source_refs"]
        if source_ref not in registry_ids and source_ref not in direct_ids
    }
    assert unresolved == set()
