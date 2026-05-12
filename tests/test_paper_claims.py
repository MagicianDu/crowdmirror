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
