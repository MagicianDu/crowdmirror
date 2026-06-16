import json
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.r6_product_outcome_review import build_r6_product_outcome_review


def test_r6_product_outcome_review_keeps_learning_bounded():
    review = build_r6_product_outcome_review(
        artifact_id="r6-product-outcome-review-test",
        run_id="r6-product-first-run",
        observed_outcome={
            "outcome_id": "airline-fee-outcome-001",
            "measurement_window": "post_release_30d",
            "observed_signal": "churn_risk_higher_than_static_prior",
            "source_level": "field_proxy",
        },
    )

    assert review["schema_version"] == "r6-product-outcome-review-v1"
    assert review["status"] == "outcome_review_ready_update_blocked"
    assert review["review_outputs"] == [
        "static_prior_error",
        "interaction_error",
        "risk_signal_classification",
        "error_attribution",
        "candidate_update",
        "update_gate",
    ]
    assert review["update_gate"]["candidate_update_generated"] is True
    assert review["update_gate"]["runtime_default_allowed"] is False
    assert review["update_gate"]["requires_holdout_before_default"] is True
    assert "same_outcome_review_not_global_validation" in review["risk_flags"]
    json.dumps(review, allow_nan=False)


def test_r6_product_outcome_review_uses_default_only_when_outcome_is_none():
    review = build_r6_product_outcome_review(
        artifact_id="r6-product-outcome-review-test",
        run_id="r6-product-first-run",
    )

    assert review["observed_outcome"] == {
        "outcome_id": "generic-outcome-review-001",
        "measurement_window": "post_release_30d",
        "observed_signal": "risk_signal_requires_review",
        "source_level": "field_proxy",
    }
    assert review["source_refs"] == ["generic-outcome-review-001"]


@pytest.mark.parametrize("observed_outcome", [[], ""])
def test_r6_product_outcome_review_rejects_bad_observed_outcome_type(
    observed_outcome,
):
    with pytest.raises(ValueError, match="observed_outcome must be an object"):
        build_r6_product_outcome_review(
            artifact_id="r6-product-outcome-review-test",
            run_id="r6-product-first-run",
            observed_outcome=observed_outcome,
        )


def test_r6_product_outcome_review_rejects_empty_observed_outcome_object():
    with pytest.raises(ValueError, match="observed_outcome.outcome_id"):
        build_r6_product_outcome_review(
            artifact_id="r6-product-outcome-review-test",
            run_id="r6-product-first-run",
            observed_outcome={},
        )


@pytest.mark.parametrize(
    "field",
    ["outcome_id", "measurement_window", "observed_signal", "source_level"],
)
def test_r6_product_outcome_review_rejects_blank_outcome_field(field):
    observed_outcome = {
        "outcome_id": "airline-fee-outcome-001",
        "measurement_window": "post_release_30d",
        "observed_signal": "churn_risk_higher_than_static_prior",
        "source_level": "field_proxy",
    }
    observed_outcome[field] = " "

    with pytest.raises(ValueError, match=f"observed_outcome.{field}"):
        build_r6_product_outcome_review(
            artifact_id="r6-product-outcome-review-test",
            run_id="r6-product-first-run",
            observed_outcome=observed_outcome,
        )


@pytest.mark.parametrize(
    ("artifact_id", "run_id", "error_field"),
    [
        (" ", "r6-product-first-run", "artifact_id"),
        ("r6-product-outcome-review-test", " ", "run_id"),
    ],
)
def test_r6_product_outcome_review_rejects_blank_required_ids(
    artifact_id,
    run_id,
    error_field,
):
    with pytest.raises(ValueError, match=error_field):
        build_r6_product_outcome_review(
            artifact_id=artifact_id,
            run_id=run_id,
            observed_outcome={
                "outcome_id": "airline-fee-outcome-001",
                "measurement_window": "post_release_30d",
                "observed_signal": "churn_risk_higher_than_static_prior",
                "source_level": "field_proxy",
            },
        )


def test_r6_product_outcome_review_cli_writes_artifact_and_stdout_json(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    output = tmp_path / "outcome-review.json"

    completed = subprocess.run(
        [
            sys.executable,
            "experiments/r6_product_outcome_review.py",
            "--artifact-id",
            "r6-product-outcome-review-cli-test",
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
        "artifact_id": "r6-product-outcome-review-cli-test",
        "output": str(output),
        "status": "outcome_review_ready_update_blocked",
    }
    assert artifact["artifact_id"] == "r6-product-outcome-review-cli-test"
    assert artifact["run_id"] == "r6-product-cli-run"
    assert artifact["update_gate"]["runtime_default_allowed"] is False
    assert "field_or_proxy_source_requires_audit" in artifact["risk_flags"]
    json.dumps(artifact, allow_nan=False)
