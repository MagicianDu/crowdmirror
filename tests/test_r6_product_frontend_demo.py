import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"


def test_r6_product_frontend_assets_exist_and_bind_current_artifacts():
    html = (DEMO / "index.html").read_text()
    js = (DEMO / "app.js").read_text()

    assert 'id="app"' in html
    assert "styles.css" in html
    assert "app.js" in html

    expected_artifact_paths = [
        (
            "/experiments/results/r6_product_customer_value_report/"
            "r6-product-customer-value-report-current-001.json"
        ),
        (
            "/experiments/results/r6_research_product_value_support/"
            "r6-research-product-value-support-current-001.json"
        ),
        (
            "/experiments/results/r6_product_readiness_index/"
            "r6-product-readiness-index-current-001.json"
        ),
        (
            "/experiments/results/r6_product_api_manifest/"
            "r6-product-api-manifest-current-001.json"
        ),
    ]
    for path in expected_artifact_paths:
        assert path in js

    expected_sections = [
        "趋势方向",
        "风险区间",
        "风险分布",
        "异常群体",
        "机制解释",
        "研究支撑",
        "R12 迁移验证",
        "证据边界",
        "阻断声明",
        "数据来源",
    ]
    for section in expected_sections:
        assert section in js


def test_r6_product_frontend_is_source_backed_and_fail_closed():
    html = (DEMO / "index.html").read_text()
    js = (DEMO / "app.js").read_text()

    assert "static_narrative_fallback_allowed" in js
    assert "renderLoadError" in js
    assert "不展示静态兜底结论" in js
    assert "sourceRefs" in js
    assert "blockedClaims" in js
    assert "supportGapLedger" in js
    assert "researchNextTasks" in js
    assert "r12_transfer_evidence" in js
    assert "update_transfer_gain" in js
    assert "secondary_transfer_evidence_card_only" in js
    assert "/r6/product/r12-transfer-evidence" in js

    assert "精准预测系统" not in html
    assert "系统可以精确预测单点结果" not in html
    assert "field validation 已完成" not in html
    assert "runtime default 可以开启" not in html


def test_r6_product_frontend_css_is_responsive_and_stable():
    css = (DEMO / "styles.css").read_text()

    assert "@media (max-width:" in css
    assert "grid-template-columns" in css
    assert "minmax(" in css
    assert re.search(r"border-radius:\s*(6|8)px", css)
    assert not re.search(r"font-size:\s*[^;]*vw", css)
    assert not re.search(r"letter-spacing:\s*-\d", css)
