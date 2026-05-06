# Paper Outline

## Title
Calibrated LLM Traveler Simulator: Structured Behavior Priors with Textual-Gradient Prompt Optimization

## Abstract (~250 words)
- Problem: 动态定价/推荐系统上线前需要仿真测试，但真实用户行为数据稀缺且异质
- Gap: 直接用 LLM 模拟用户行为存在概率失准、结构违例、不可控等问题
- Method: 三层结构化模拟器 + 双层校准（TextGrad 结构纠偏 + post-hoc 概率校准）
- Results: 在 X 数据集上，违例率降低 Y%，ECE 降低 Z%，同时保持拟合精度
- Contribution: 架构 + 校准框架 + 评测协议

## 1. Introduction (1.5 pages)
- 动机：旅客行为模拟对定价/推荐系统的价值
- 现有方法局限：传统 choice model 需大量数据；直接 LLM 模拟不可控
- 本文方案概述
- 贡献列表

## 2. Related Work (1.5 pages)
- 2.1 Discrete Choice Models (MNL, Mixed Logit, DNN-based)
- 2.2 LLM as Simulator / Synthetic User
- 2.3 Prompt Optimization (TextGrad, ProTeGi, DSPy, PromptBreeder)
- 2.4 Calibration (post-hoc, temperature scaling, Platt, isotonic)

## 3. Method (3 pages)
- 3.1 Problem Formulation & Protocol (ScenarioSpec → BehaviorTrace)
- 3.2 Three-Layer Simulator Architecture
  - 3.2.1 Persona/State Generation (prior sampling + LLM completion)
  - 3.2.2 Utility/Preference Extraction (LLM → β weights, thresholds)
  - 3.2.3 Choice Model (MNL/Nested Logit with outside option)
- 3.3 Dual-Layer Calibration
  - 3.3.1 Loss Function Design (L_fit + L_cal + L_con + L_stab)
  - 3.3.2 Structural Calibration via TextGrad
  - 3.3.3 Probabilistic Calibration via Post-hoc Methods
- 3.4 Implementation Details (LLM choice, JSON contracts, seed control)

## 4. Experimental Setup (1.5 pages)
- 4.1 Datasets & Task Formulation
- 4.2 Baselines & Ablations
- 4.3 Metrics & Evaluation Protocol
- 4.4 Hyperparameters & Reproducibility

## 5. Results (2.5 pages)
- 5.1 Main Results (Table: all methods × all metrics)
- 5.2 Ablation Study
- 5.3 Calibration Analysis (reliability diagrams, per-segment ECE)
- 5.4 Structural Consistency Analysis (violation rates breakdown)
- 5.5 Robustness Under Distribution Shift

## 6. Analysis & Discussion (1 page)
- TextGrad 收敛行为分析
- Prompt 编辑轨迹可视化
- 失败案例分析
- 计算成本对比

## 7. Conclusion & Future Work (0.5 page)

## Appendix
- A. Full JSON Schema (ScenarioSpec, BehaviorTrace)
- B. Prompt Templates (P1, P2, P3 initial versions)
- C. TextGrad Optimization Traces
- D. Additional Experimental Results
