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
