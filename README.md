# Research Worktree — Calibrated LLM Traveler Simulator

CCF-A 论文目标：WWW / KDD / NeurIPS / AAAI

## 核心贡献

1. **结构化 LLM 模拟器**：Persona→Utility→Choice 三层分离
2. **双层校准框架**：TextGrad prompt 优化 + post-hoc 概率校准
3. **模拟器评测协议**：拟合/校准/结构一致性/稳定性/漂移鲁棒性

## 文档

- [ROADMAP.md](ROADMAP.md) — 6 月研究路线图
- [paper/OUTLINE.md](paper/OUTLINE.md) — 论文章节大纲

## 代码结构

```
src/
├── simulator/      # 三层模拟器（schema, persona, utility, choice）
├── calibration/    # TextGrad + post-hoc 校准
└── evaluation/     # 指标与违例检测器
experiments/        # 实验脚本（按数据集组织）
data/               # 数据加载与预处理
paper/              # LaTeX 源、图表、bib
```
