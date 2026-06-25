# Research Worktree — Active Direction

> **当前主线已切换到 R7。**
>
> 后续开发以 `docs/active-spec.md` 和 `docs/CURRENT_STATE.md` 为准。
> 本 README 下方原有内容保留为历史背景，不再作为当前实现依据。

当前 active spec：

- `docs/superpowers/specs/2026-06-05-r6-outcome-feedback-prior-anchored-interaction-simulation-spec.md`
- `docs/superpowers/specs/2026-06-25-r7-mechanism-generative-risk-simulation-spec.md`

当前目标：

> R7 机制生成式交互风险仿真：用强静态先验建立可信底座，用机制状态和交互传播发现静态数据盲区，用分布式 rollout 生成趋势区间和风险排序，并用真实 outcome 回流持续校正方法。

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
