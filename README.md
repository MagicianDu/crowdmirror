# 人群反应趋势与风险区间模拟器

这是一个面向企业试用的公开数据验证版原型，用于在政策、价格、权益或服务规则变更发布前，模拟人群反应趋势、可信数值区间、风险分布、异常群体和机制解释。

项目当前不定位为精准预测系统，而是定位为：

> 基于静态人口先验、公开数据验证、虚拟人群反应和交互传播的发布前风险评估工具。

## 当前能力

- 公开数据测试：当前 R12 gate 已允许 `public_data_effectiveness_claim_allowed=true`，表示可对外做“公开数据测试有效”的受限声明。
- 趋势与区间：输出趋势方向、风险区间、风险排序、静态先验漏报恢复、误报控制和决策价值指标。
- 离线校准闭环：支持 outcome 反馈后的结构化更新候选、shadow replay、holdout review 和人工确认流程。
- 证据边界：所有 Product 展示绑定 artifact、source refs、blocked claims 和 runtime guard。
- 企业试用路径：可先用公开数据版演示价值，再决定是否进入企业 field validation。

## 不能承诺

- 不承诺精确单点预测。
- 不宣称客户 field validation 已完成。
- 不把校准更新默认自动上线。
- 不开启 runtime default；当前 `runtime_default_allowed=false`。

## 本地预览

```bash
python3 -m http.server 8088 --bind 127.0.0.1
```

- 宣传页：[http://127.0.0.1:8088/demo/promo.html](http://127.0.0.1:8088/demo/promo.html)
- 产品 demo：[http://127.0.0.1:8088/demo/](http://127.0.0.1:8088/demo/)

## 关键文档

- `docs/active-spec.md`
- `docs/CURRENT_STATE.md`
- `docs/superpowers/specs/2026-06-26-r12-outcome-supervised-causal-interaction-operator-spec.md`

## 关键证据 artifact

- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json`
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json`
- `experiments/results/r12_real_source_validation_execution_packet/r12-real-source-validation-execution-packet-current-001.json`

## 验证

```bash
.venv/bin/python -m pytest -q
node --check demo/app.js
node --check demo/promo.js
```

## Historical Background

# Research Worktree — Calibrated Generative Agents for CSS

**学科定位**：计算社会科学 / 社会计算

**核心命题**：把生成式智能体从"看起来像人"提升到"统计上像人群"

## 目标 Venue

- CS 顶会：WWW / KDD / NeurIPS / AAAI / CSCW / ICWSM
- 社科顶刊：Nature Human Behaviour / PNAS / Science Advances

## 核心贡献

1. **结构化生成式智能体架构**：Persona→Utility→Choice 三层分离
2. **验收门校准框架**：TextGrad、residual rule、参数搜索共同生成候选 patch，
   由 held-out loss gate 自动接受或拒绝
3. **PopulationBench**：首个跨 domain 群体行为模拟基准（消费/道德/政策/健康）
4. **范式贡献**：推进 CSS 从 ABM 到 GBM 的范式转移

## 文档

- [ROADMAP.md](ROADMAP.md) — 9 月研究路线图
- [paper/OUTLINE.md](paper/OUTLINE.md) — 论文章节大纲

## 代码结构

```
src/
├── simulator/      # 三层生成式智能体（schema, persona, utility, choice）
├── calibration/    # 多候选 prompt/persona patch + acceptance gate 校准
└── evaluation/     # 指标与违例检测器
experiments/        # 实验脚本（按 domain 组织）
data/               # 数据加载与预处理（multi-domain adapters）
paper/              # LaTeX 源、图表、bib
```
