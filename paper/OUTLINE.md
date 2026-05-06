# Paper Outline

## Title
**Calibrated Generative Agents: From Personas to Populations**

*Subtitle (alt)*: Structured Behavior Simulation at Scale with Textual-Gradient Calibration

## Abstract (~250 words)
- **Problem**: 计算社会科学正经历从 ABM 到生成式智能体（GBM）的范式转移；
  现有 LLM-based simulation 让智能体"看起来像人"，但缺乏可校准性——
  它们生成的群体分布是否真的对应现实人群？
- **Gap**: 直接用 LLM 模拟存在概率失准、结构违例、分群异质失真、不可审计等问题；
  现有 prompt 优化工作（TextGrad/ProTeGi）面向单点任务，未涉及群体校准。
- **Method**: 三层结构化生成式智能体（Persona→Utility→Choice） + 双层校准
  （TextGrad 结构纠偏 + post-hoc 概率校准），并提出多 domain 评测基准 PopulationBench。
- **Results**: 在 N 个 domain（消费决策、道德判断、公共政策）上，
  违例率降低 X%，ECE 降低 Y%，分群异质拟合提升 Z%，与传统 DCM 在 data-scarce 场景下打成平手。
- **Contribution**: 架构 + 校准框架 + 跨 domain 基准 + CSS 范式贡献。

## 1. Introduction (1.5-2 pages)
- 计算社会科学的范式转移：rule-based ABM → generative agents (GBM)
- 关键问题：当前生成式智能体"逼真但不可信"——分布对齐缺失
- 我们的核心问题：如何让 LLM 群体模拟从"像人"升级到"像人群"？
- 方案概述：结构化架构 + 双层校准 + 跨 domain 验证
- 贡献列表（4 点）

## 2. Related Work (1.5-2 pages)
- 2.1 Computational Social Science & ABM
- 2.2 Generative Agents & LLM-based Social Simulation (Park et al., AgentSociety, ...)
- 2.3 Discrete Choice Models (MNL, Nested/Mixed Logit, DNN-based)
- 2.4 Prompt Optimization (TextGrad, ProTeGi, DSPy, PromptBreeder)
- 2.5 Calibration of Probabilistic Predictors (temperature, isotonic, Platt)
- 2.6 LLM Alignment to Human Distributions (silicone samples, persona steering)

## 3. Problem Formulation (1 page)
- 3.1 Population Behavior Simulation as a Formal Problem
  - ScenarioSpec → BehaviorTrace 抽象
  - Domain-agnostic 形式化（choice set, context, info set, controls）
- 3.2 Calibration Targets
  - 边际分布对齐 vs. 条件分布对齐 vs. 结构一致性
- 3.3 Why Pure LLM Fails: Failure Modes
  - 概率失准、结构违例、分群同质化、prompt 漂移

## 4. Method (3 pages)
- 4.1 Three-Layer Generative Agent Architecture
  - 4.1.1 Persona/State (prior sampling + LLM completion, demographic anchoring)
  - 4.1.2 Utility/Preference (LLM → β, thresholds, reference points)
  - 4.1.3 Choice Model (MNL/Nested/Mixed Logit, outside option)
- 4.2 Dual-Layer Calibration
  - 4.2.1 Loss Design (L_fit + L_cal + L_con + L_stab + L_hetero)
  - 4.2.2 Structural Calibration via TextGrad (multi-module prompt graph)
  - 4.2.3 Probabilistic Calibration via Per-Segment Post-hoc Methods
- 4.3 Implementation
  - JSON 合约、版本与种子控制、prompt hash 审计

## 5. PopulationBench: A Multi-Domain Benchmark (1.5 pages)
- 5.1 设计原则（domain coverage, structural diversity, data accessibility）
- 5.2 包含的 domains
  - 消费决策（Swissmetro, ModeChoice）
  - 道德判断（Moral Machine）
  - 公共政策（GSS/ANES subsets）
  - 健康行为（HINTS）（可选）
  - 半合成（已知真值）
- 5.3 Metrics（fit / calibration / structure / heterogeneity / stability / robustness）
- 5.4 Reproducibility Protocol

## 6. Experimental Setup (1 page)
- Baselines (B1-B6 incl. Generative Agents 复现 & traditional DCM)
- Ablations
- Hyperparameters & Compute

## 7. Results (2.5 pages)
- 7.1 Main Results across PopulationBench
- 7.2 Ablation Study
- 7.3 Calibration Analysis（reliability diagrams, per-segment ECE）
- 7.4 Structural Consistency Analysis
- 7.5 Heterogeneity & Intersectional Fairness
- 7.6 Robustness Under Distribution Shift
- 7.7 Cross-Domain Transfer

## 8. Analysis & Discussion (1 page)
- TextGrad 收敛行为与 prompt 编辑轨迹
- 失败案例剖析（哪些 domain/segment 仍难校准）
- 计算成本对比与可扩展性
- 与传统 DCM、Generative Agents 的能力边界对比

## 9. Implications for Computational Social Science (0.5 page)
- 从 ABM 到 GBM 的范式转移意义
- 可校准生成式智能体作为 CSS 的新基础设施
- 伦理考量（隐私、stereotyping、误用风险）

## 10. Conclusion & Future Work (0.5 page)
- 多智能体交互、纵向行为、政策反事实仿真

## Appendix
- A. Full JSON Schema (ScenarioSpec, BehaviorTrace)
- B. Prompt Templates (P1, P2, P3 initial versions)
- C. TextGrad Optimization Traces
- D. Per-Domain Detailed Results
- E. PopulationBench Documentation & Leaderboard
- F. Ethical Considerations & Data Statements
