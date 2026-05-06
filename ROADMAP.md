# Research Roadmap: Calibrated LLM Traveler Simulator

## 目标会议/期刊（CCF-A）

优先级排序：
1. **WWW** (The Web Conference) — 用户行为建模 + 电商/旅游场景天然契合
2. **KDD** — Applied Data Science track，强调可校准、可评测
3. **NeurIPS** — Datasets & Benchmarks track（如果侧重评测协议与基准）
4. **AAAI** — AI + 行为模拟 + 优化

## 论文标题（候选）

- "Calibrated LLM Traveler Simulator: Structured Behavior Priors with Textual-Gradient Prompt Optimization"
- "TextGrad Meets Discrete Choice: Calibrating LLM-Based User Simulators via Textual Gradients"

## 核心贡献（3 点）

1. **结构化 LLM 模拟器架构**：Persona→Utility→Choice 三层分离，LLM 生成可计算偏好参数，
   显式 choice model 输出概率——兼具 LLM 的语义丰富性与传统模型的可校准性。

2. **双层校准框架**：TextGrad prompt 优化修复结构性偏差（单调性/替代一致性/约束违例），
   post-hoc 概率校准修复尺度偏差——两层职责分离，互补而非冗余。

3. **模拟器专用评测协议**：面向离散选择的多维指标体系（拟合/校准/结构一致性/稳定性/漂移鲁棒性），
   含公开数据基准与半合成验证。

## 方法概览

```
┌─────────────────────────────────────────────────────────┐
│                    ScenarioSpec (Input)                  │
│  context + offer_set + information_set + controls       │
└───────────────────────────┬─────────────────────────────┘
                            │
                ┌───────────▼───────────┐
                │   P1: Persona/State   │  ← LLM generates structured persona
                │   (JSON contract)     │
                └───────────┬───────────┘
                            │
                ┌───────────▼───────────┐
                │   P2: Utility/Pref    │  ← LLM outputs β weights, thresholds
                │   (JSON contract)     │
                └───────────┬───────────┘
                            │
                ┌───────────▼───────────┐
                │   P3: Choice Model    │  ← MNL/Nested Logit (deterministic)
                │   (explicit formula)  │
                └───────────┬───────────┘
                            │
                ┌───────────▼───────────┐
                │   BehaviorTrace (Out) │
                │   probs + action +    │
                │   audit trail         │
                └───────────────────────┘

        ╔═══════════════════════════════════════╗
        ║       Calibration Loop (Offline)      ║
        ║                                       ║
        ║  TextGrad/ProTeGi ──► Edit P1/P2     ║
        ║       ↑                    │          ║
        ║       │    L_fit + L_cal   │          ║
        ║       │  + L_con + L_stab  │          ║
        ║       │         ↓          ▼          ║
        ║  Loss ◄──── Evaluate on Dev Set      ║
        ║                                       ║
        ║  Post-hoc: temperature / isotonic     ║
        ╚═══════════════════════════════════════╝
```

## 实验设计

### 数据集
| Dataset | Type | Task | Purpose |
|---------|------|------|---------|
| Swissmetro | Public | 3-way mode choice | 主实验：校准+结构检查 |
| Statsmodels ModeChoice | Public | 4-way transport | 快速验证 |
| Semi-synthetic (MNL ground truth) | Generated | N-way offer choice | 消融：已知真值下的收敛性 |
| Expedia Hotels (optional) | Kaggle | Hotel ranking/click | 商业场景泛化 |

### Baselines
- **B1**: Direct LLM choice (no structure, just ask LLM to pick)
- **B2**: LLM + post-hoc calibration only (no TextGrad)
- **B3**: ProTeGi prompt optimization (text gradient baseline)
- **B4**: DSPy optimizer (module-level prompt compilation)
- **Ours**: Full pipeline (structured simulator + TextGrad + post-hoc)

### Ablations
- w/o Persona layer (uniform persona)
- w/o Utility layer (LLM directly outputs probs)
- w/o TextGrad (post-hoc only)
- w/o post-hoc (TextGrad only)
- w/o structural constraints in loss

### Metrics
| Category | Metrics |
|----------|---------|
| Fit | LogLoss, Brier Score, KL Divergence |
| Calibration | ECE, MCE, Reliability Diagram |
| Structure | Monotonicity violation rate, Substitution consistency, Constraint violation rate |
| Stability | Intra-seed variance, Cross-seed distribution shift |
| Robustness | Performance under distribution shift (population, offer, info) |

## Timeline (6 months)

| Month | Focus | Deliverable |
|-------|-------|-------------|
| M1 | Schema + metrics + violation detectors | Evaluation framework |
| M2 | Simulator prototype (3-layer) | Baseline results on Swissmetro |
| M3 | Post-hoc calibration + segment analysis | Calibration module |
| M4-5 | TextGrad integration + ablations | Core experiments |
| M6 | Paper writing + robustness experiments | Submission-ready draft |
