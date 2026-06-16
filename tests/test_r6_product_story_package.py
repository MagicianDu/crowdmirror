import json
import subprocess
import sys
from pathlib import Path

import pytest

from experiments import r6_product_story_package as story_package
from experiments.r6_gap_closure_report import build_r6_gap_closure_report
from experiments.r6_product_evidence_cards import build_r6_product_evidence_cards
from experiments.r6_product_scenario_intake import build_r6_product_scenario_intake
from experiments.r6_product_story_package import (
    R6_PRODUCT_STORY_CANONICAL_SOURCE_REGISTRY,
    build_r6_product_story_package,
)


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
    for entry in R6_PRODUCT_STORY_CANONICAL_SOURCE_REGISTRY:
        assert entry in package["source_registry"]
    _assert_package_sources_resolvable(package)
    json.dumps(package, allow_nan=False)


def test_r6_product_story_package_rejects_dangerous_card_claim_status(monkeypatch):
    _patch_cards(
        monkeypatch,
        card_mutation={"claim_status": "accuracy_superiority_established"},
    )

    with pytest.raises(ValueError, match="claim_status"):
        build_r6_product_story_package(
            artifact_id="r6-product-story-package-bad-claim-status",
            run_id="r6-product-first-run",
        )


def test_r6_product_story_package_rejects_string_allowed_claims(monkeypatch):
    _patch_cards(
        monkeypatch,
        card_mutation={"allowed_claims": "交互仿真已经更准"},
    )

    with pytest.raises(ValueError, match="allowed_claims"):
        build_r6_product_story_package(
            artifact_id="r6-product-story-package-bad-allowed-claims",
            run_id="r6-product-first-run",
        )


def test_r6_product_story_package_rejects_dangerous_allowed_claim(monkeypatch):
    _patch_cards(
        monkeypatch,
        card_mutation={"allowed_claims": ["field validation 已完成"]},
    )

    with pytest.raises(ValueError, match="allowed_claims"):
        build_r6_product_story_package(
            artifact_id="r6-product-story-package-dangerous-allowed-claim",
            run_id="r6-product-first-run",
        )


@pytest.mark.parametrize(
    "dangerous_allowed_claim",
    [
        "field_validated",
        "runtime_default_ready",
        "ccf_a_ready",
        "accuracy superiority established",
    ],
)
def test_r6_product_story_package_rejects_dangerous_allowed_claim_variants(
    monkeypatch,
    dangerous_allowed_claim,
):
    _patch_cards(
        monkeypatch,
        card_mutation={"allowed_claims": [dangerous_allowed_claim]},
    )

    with pytest.raises(ValueError, match="allowed_claims"):
        build_r6_product_story_package(
            artifact_id="r6-product-story-package-dangerous-allowed-claim",
            run_id="r6-product-first-run",
        )


def test_r6_product_story_package_rejects_unregistered_card_source(monkeypatch):
    _patch_cards(
        monkeypatch,
        card_mutation={"source_artifact_ids": ["missing-source-artifact"]},
    )

    with pytest.raises(ValueError, match="source_artifact_ids"):
        build_r6_product_story_package(
            artifact_id="r6-product-story-package-missing-source",
            run_id="r6-product-first-run",
        )


def test_r6_product_story_package_rejects_missing_required_card(monkeypatch):
    def fake_product_evidence_cards(
        *,
        artifact_id,
        run_id,
        gap_closure_report,
        **kwargs,
    ):
        report = build_r6_product_evidence_cards(
            artifact_id=artifact_id,
            run_id=run_id,
            gap_closure_report=gap_closure_report,
            **kwargs,
        )
        cards = [
            card
            for card in report["cards"]
            if card["card_id"] != "static-prior-control"
        ]
        return {**report, "cards": cards}

    monkeypatch.setattr(
        story_package,
        "build_r6_product_evidence_cards",
        fake_product_evidence_cards,
    )

    with pytest.raises(ValueError, match="static-prior-control"):
        build_r6_product_story_package(
            artifact_id="r6-product-story-package-missing-required-card",
            run_id="r6-product-first-run",
        )


def test_r6_product_story_package_rejects_empty_blocked_claims(monkeypatch):
    _patch_cards(monkeypatch, card_mutation={"blocked_claims": []})

    with pytest.raises(ValueError, match="blocked_claims"):
        build_r6_product_story_package(
            artifact_id="r6-product-story-package-empty-blocked-claims",
            run_id="r6-product-first-run",
        )


def test_r6_product_story_package_rejects_string_gap_closure_blocked_claims(
    monkeypatch,
):
    def fake_gap_closure_report(*, artifact_id, run_id):
        report = build_r6_gap_closure_report(
            artifact_id=artifact_id,
            run_id=run_id,
        )
        return {**report, "blocked_claims": "runtime_default_allowed"}

    monkeypatch.setattr(
        story_package,
        "build_r6_gap_closure_report",
        fake_gap_closure_report,
    )

    with pytest.raises(ValueError, match="gap_closure_report.blocked_claims"):
        build_r6_product_story_package(
            artifact_id="r6-product-story-package-bad-gap-blocked-claims",
            run_id="r6-product-first-run",
        )


def test_r6_product_story_package_cli_writes_artifact_and_stdout_json(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    output = tmp_path / "story-package.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_product_story_package.py",
            "--artifact-id",
            "r6-product-story-package-cli-test",
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
        "artifact_id": "r6-product-story-package-cli-test",
        "output": str(output),
        "status": "product_story_package_ready_guarded",
    }
    assert artifact["artifact_id"] == "r6-product-story-package-cli-test"
    assert artifact["ui_contract"]["static_narrative_fallback_allowed"] is False
    assert "r6-gap-closure-status" in artifact["evidence_card_ids"]
    _assert_package_sources_resolvable(artifact)
    json.dumps(artifact, allow_nan=False)


def test_r6_product_story_package_default_sources_use_canonical_registry():
    package = build_r6_product_story_package(
        artifact_id="r6-product-story-package-test",
        run_id="r6-product-first-run",
    )

    registry_ids = {entry["artifact_id"] for entry in package["source_registry"]}
    assert "r6-product-report-current-003" in registry_ids
    assert "r6-product-evidence-cards-current-003" in registry_ids
    assert "r6-evidence-report-current-014" in registry_ids
    assert "r6-product-story-package-test-evidence-cards-product-report" not in (
        package["source_refs"]
    )
    _assert_package_sources_resolvable(package)


def test_r6_product_current_story_and_decision_artifact_sources_are_resolvable():
    repo_root = Path(__file__).resolve().parents[1]
    story_artifact = json.loads(
        (
            repo_root
            / "experiments/results/r6_product_story_package/"
            / "r6-product-story-package-current-001.json"
        ).read_text()
    )
    decision_artifact = json.loads(
        (
            repo_root
            / "experiments/results/r6_product_decision_report/"
            / "r6-product-decision-report-current-001.json"
        ).read_text()
    )

    _assert_package_sources_resolvable(story_artifact)
    _assert_report_sources_resolvable(decision_artifact)


def _patch_cards(monkeypatch, *, card_mutation):
    def fake_product_evidence_cards(
        *,
        artifact_id,
        run_id,
        gap_closure_report,
        **kwargs,
    ):
        report = build_r6_product_evidence_cards(
            artifact_id=artifact_id,
            run_id=run_id,
            gap_closure_report=gap_closure_report,
            **kwargs,
        )
        cards = [dict(card) for card in report["cards"]]
        cards[0] = {**cards[0], **card_mutation}
        return {**report, "cards": cards}

    monkeypatch.setattr(
        story_package,
        "build_r6_product_evidence_cards",
        fake_product_evidence_cards,
    )


def _assert_package_sources_resolvable(package):
    registry_ids = {entry["artifact_id"] for entry in package["source_registry"]}
    repo_root = Path(__file__).resolve().parents[1]
    for entry in package["source_registry"]:
        if entry["path"].startswith("experiments/"):
            source_artifact = json.loads((repo_root / entry["path"]).read_text())
            assert source_artifact["artifact_id"] == entry["artifact_id"]
    direct_ids = {
        package["artifact_id"],
        *package["artifact_refs"].values(),
    }
    unresolved = set()
    for source_ref in package["source_refs"]:
        if source_ref not in registry_ids and source_ref not in direct_ids:
            unresolved.add(source_ref)
    for section in package["section_contracts"]:
        for source_ref in section["source_artifact_ids"]:
            if source_ref not in registry_ids and source_ref not in direct_ids:
                unresolved.add(source_ref)
    for card in package["customer_visible_claim_cards"]:
        for source_ref in card["source_artifact_ids"]:
            if source_ref not in registry_ids and source_ref not in direct_ids:
                unresolved.add(source_ref)
    assert unresolved == set()


def _assert_report_sources_resolvable(report):
    registry_ids = {entry["artifact_id"] for entry in report["source_registry"]}
    direct_ids = {report["artifact_id"]}
    unresolved = {
        source_ref
        for source_ref in report["source_refs"]
        if source_ref not in registry_ids and source_ref not in direct_ids
    }
    assert unresolved == set()
