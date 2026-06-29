import json
import math

import pytest

from experiments.r6_contracts import (
    R6_CLAIM_BOUNDARY,
    R6_UPDATE_STATUSES,
    assert_strict_json,
    claim_boundaries,
    finite_number,
    non_empty_string,
    positive_integer,
    probability_distribution,
    risk_flags,
    source_refs,
    write_json_artifact,
    load_json_artifact,
)


def test_r6_contracts_validate_common_fields_and_strict_json(tmp_path):
    assert non_empty_string(" artifact-1 ", field="artifact_id") == "artifact-1"
    assert positive_integer(3, field="scale") == 3
    assert finite_number(0.25, field="delta") == 0.25
    assert source_refs(["survey", "crm"], field="source_refs") == ["survey", "crm"]
    assert claim_boundaries([R6_CLAIM_BOUNDARY]) == [R6_CLAIM_BOUNDARY]
    assert risk_flags(["not_accuracy_claim"]) == ["not_accuracy_claim"]
    assert R6_UPDATE_STATUSES == {
        "accepted",
        "case_local",
        "diagnostic_only",
        "rejected",
        "needs_more_outcomes",
    }

    distribution = probability_distribution(
        {"accept": 0.2, "neutral": 0.3, "reject": 0.5},
        options=["accept", "neutral", "reject"],
        field="static_response_prior",
    )

    assert distribution == {"accept": 0.2, "neutral": 0.3, "reject": 0.5}

    payload = {
        "schema_version": "r6-test-v1",
        "artifact_id": "artifact-1",
        "distribution": distribution,
    }
    assert_strict_json(payload)

    output = tmp_path / "artifact.json"
    written = write_json_artifact(output, payload)

    assert written == output
    assert output.read_text().endswith("\n")
    assert load_json_artifact(output) == payload
    json.dumps(payload, allow_nan=False)


def test_r6_contracts_reject_invalid_inputs():
    with pytest.raises(ValueError, match="artifact_id must be a non-empty string"):
        non_empty_string(" ", field="artifact_id")

    with pytest.raises(ValueError, match="scale must be a positive integer"):
        positive_integer(0, field="scale")

    with pytest.raises(ValueError, match="delta must be finite"):
        finite_number(math.nan, field="delta")

    with pytest.raises(ValueError, match="source_refs must contain at least one item"):
        source_refs([], field="source_refs")

    with pytest.raises(ValueError, match="claim_boundaries must contain"):
        claim_boundaries([])

    with pytest.raises(ValueError, match="risk_flags must contain at least one item"):
        risk_flags([])

    with pytest.raises(ValueError, match="must sum to 1.0"):
        probability_distribution(
            {"accept": 0.2, "neutral": 0.3, "reject": 0.6},
            options=["accept", "neutral", "reject"],
            field="static_response_prior",
        )

    with pytest.raises(ValueError, match="missing option"):
        probability_distribution(
            {"accept": 0.5, "reject": 0.5},
            options=["accept", "neutral", "reject"],
            field="static_response_prior",
        )

    with pytest.raises(ValueError, match="not JSON serializable"):
        assert_strict_json({"bad": math.nan})
