import json
from pathlib import Path

from experiments.trust_chain_validation import run_validation


def test_trust_chain_validation_writes_expected_sections(tmp_path):
    output_path = tmp_path / "trust_chain_validation.json"
    report = run_validation(output_path=output_path)
    assert output_path.exists()
    saved = json.loads(output_path.read_text())
    assert saved == report
    assert set(report) == {"ece", "probability_contract", "emergence"}
    assert report["ece"]["zero_probability_true_event"] == 1.0
    assert report["probability_contract"]["has_all_alternatives"] is True
    assert report["emergence"]["edm_score"] >= 0.0
