from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_explains_how_a_non_developer_uses_the_product():
    readme = (ROOT / "README.md").read_text()

    required_sections = [
        "## 适合谁用",
        "## 5 分钟上手",
        "## 产品 demo 怎么看",
        "## 看懂核心指标",
        "## 一次企业试用需要准备什么",
        "## 什么时候需要 LLM key",
        "## 架构：LLM 驱动，但不是浏览器里跑 LLM",
        "## 本地运行",
        "## 常见问题",
    ]
    for section in required_sections:
        assert section in readme

    required_phrases = [
        "宣传页",
        "产品 demo",
        "趋势方向",
        "风险区间",
        "风险排序",
        "异常群体",
        "机制解释",
        "不上传客户数据",
        "OPENROUTER_API_KEY",
        "DEEPSEEK_API_KEY",
        "LM Studio",
        "真实运行新场景的人群模拟需要 LLM",
        "LLM 生成 segment/persona 行为规则",
        "1 万+ synthetic individuals",
        "r13-llm-rule-structured-rollout-current-001.json",
        "llm-crowd-simulation-architecture.png",
        "docs/USER_GUIDE.md",
        "https://magiciandu.github.io/crowdmirror/demo/promo.html",
        "https://magiciandu.github.io/crowdmirror/demo/",
    ]
    for phrase in required_phrases:
        assert phrase in readme


def test_user_guide_provides_step_by_step_trial_workflow_and_boundaries():
    guide = ROOT / "docs" / "USER_GUIDE.md"
    assert guide.exists()
    text = guide.read_text()

    required_sections = [
        "# 用户使用指南",
        "## 第一步：打开宣传页",
        "## 第二步：打开产品 demo",
        "## 第三步：读懂报告",
        "## 第四步：准备企业试用数据",
        "## LLM key 怎么配置",
        "## 人群模拟和 LLM 的关系",
        "## 第五步：验收一次试用",
        "## 当前边界",
    ]
    for section in required_sections:
        assert section in text

    required_phrases = [
        "趋势方向",
        "可信数值区间",
        "风险分布",
        "异常群体",
        "机制解释",
        "customer_approval_reference",
        "至少 10 个 cases",
        "不承诺精确单点预测",
        "runtime_default_allowed=false",
        "在线 demo 不需要配置 LLM key",
        "OPENROUTER_API_KEY",
        "DEEPSEEK_API_KEY",
        "LM Studio",
        "浏览器端不会读取",
        "真实运行新场景的人群模拟需要 LLM",
        "静态人口先验负责规模化底座",
        "LLM 只生成 segment/persona 层面的行为规则",
        "1 万+ synthetic individuals",
        "offline_fixture_llm_shape",
    ]
    for phrase in required_phrases:
        assert phrase in text
