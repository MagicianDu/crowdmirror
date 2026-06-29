from pathlib import Path


def test_product_transfer_artifact_contains_required_sections():
    text = Path("paper/PRODUCT_TRANSFER.md").read_text()
    for heading in [
        "## Transfer Principle",
        "## Evidence Classes",
        "## Product Surfaces",
        "## Current Local Gemma Canary",
        "## No-Go Claims",
    ]:
        assert heading in text


def test_product_transfer_preserves_claim_boundaries():
    text = Path("paper/PRODUCT_TRANSFER.md").read_text()
    assert "local-gemma-w3w4-canary-001" in text
    assert "not cross-provider evidence" in text
    assert "not customer-specific forecast accuracy" in text
    assert "must remain `missing`" in text
