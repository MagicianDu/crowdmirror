from pathlib import Path


def test_theory_artifact_contains_required_sections():
    theory = Path("paper/THEORY.md")
    assert theory.exists()
    text = theory.read_text()
    for heading in [
        "## Definitions",
        "## Joint Calibration Objective",
        "## Assumptions",
        "## Proposition 1",
        "## Proof Sketch",
        "## Limits",
    ]:
        assert heading in text


def test_theory_proposition_is_conditional_not_convergence_claim():
    text = Path("paper/THEORY.md").read_text()

    assert "does not guarantee that the update operator can always find another accepted candidate" in text
    assert "does not guarantee optimizer convergence or objective reachability" in text
    assert "must reach the threshold" not in text
