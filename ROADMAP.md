# Research Roadmap

> **历史路线图。当前主线已切换到 R6。**
>
> 后续开发以 `docs/active-spec.md`、`docs/CURRENT_STATE.md` 和
> `docs/superpowers/specs/2026-06-05-r6-outcome-feedback-prior-anchored-interaction-simulation-spec.md`
> 为准。本文下方内容仅作为早期研究背景，不再作为当前实现依据。

当前 R6 目标：

> 构建结果反馈约束的先验锚定交互仿真框架，用于发布前反应评估和发布后反馈学习。

## Historical Roadmap

# Research Roadmap: Calibrated Generative Agents for Computational Social Science

## 学科定位

本研究属于**计算社会科学（CSS）** 与**社会计算**交叉领域，推动一个范式转移：

> 从 ABM（基于规则的智能体建模）到 **GBM（基于生成式智能体的群体行为建模）**

对标研究线：*Generative Agents* (Park et al., UIST'23)、Stanford Smallville、Anthropic/DeepMind multi-agent simulation、AgentSociety。**关键空位**：现有工作让智能体"看起来像人"，但缺乏校准与评测——它们生成的群体分布是否真的对应现实人群？这是本研究的核心命题。

## 目标 Venue（双栖发表策略）

### CS 顶会（CCF-A 优先）
1. **WWW** (The Web Conference) — Web 与社会、用户行为建模
2. **KDD** — Applied Data Science、社会计算
3. **NeurIPS** — Datasets & Benchmarks（评测协议与基准）
4. **CSCW / ICWSM** — 计算社会科学专属会议（CCF-B 但 CSS 领域顶级）
5. **AAAI** — AI + 行为模拟

### 社科顶刊（CSS 范式贡献）
1. **Nature Human Behaviour** — CSS 旗舰期刊
2. **PNAS** — 跨学科顶刊
3. **Science Advances** — 跨学科顶刊
4. **Journal of Computational Social Science** — 领域期刊

**理想路径**：方法论文投 CS 顶会，扩展应用论文投社科顶刊，引用结构互相加固。

## 论文标题（候选）

**主论文**（方法学）:
- "Calibrated Generative Agents: From Personas to Populations"
- "Structured Behavior Simulation at Scale: Calibrating LLM Populations with Textual Gradients"
- "Beyond Believable: Calibrating LLM-Based Social Simulation"

**Benchmark 论文**：
- "PopulationBench: A Multi-Domain Benchmark for Calibrated LLM Social Simulation"

## 核心贡献（4 点）

1. **结构化生成式智能体架构**：Persona→Utility→Choice 三层分离，LLM 生成可计算的偏好结构与情境响应，
   显式行为模型输出可观测的概率分布——兼具 LLM 的语义丰富性与传统 CSS 模型（DCM、ABM）的可校准性。

2. **双层校准框架**：TextGrad/ProTeGi prompt 优化修复结构性偏差（单调性/替代一致性/约束违例/分群异质），
   post-hoc 概率校准修复尺度偏差——两层职责分离，互补而非冗余。

3. **跨 domain 评测协议与基准（PopulationBench）**：首个面向 LLM 群体行为模拟的多领域基准，
   覆盖消费决策、公共政策、健康行为、道德判断等场景，含拟合/校准/结构一致性/稳定性/漂移鲁棒性多维指标。

4. **范式贡献**：推进 CSS 从 ABM 到 GBM 的范式转移，提供**可复现、可审计、可校准**的生成式智能体方法论。

## 方法概览

```
┌─────────────────────────────────────────────────────────┐
│                    ScenarioSpec (Input)                  │
│  context + choice_set + information_set + controls      │
│  (domain-agnostic: products, policies, behaviors, ...)  │
└───────────────────────────┬─────────────────────────────┘
                            │
                ┌───────────▼───────────┐
                │   P1: Persona/State   │  ← LLM generates structured persona
                │   (JSON contract)     │     conditioned on demographic priors
                └───────────┬───────────┘
                            │
                ┌───────────▼───────────┐
                │   P2: Utility/Pref    │  ← LLM outputs β weights, thresholds,
                │   (JSON contract)     │     reference points, constraints
                └───────────┬───────────┘
                            │
                ┌───────────▼───────────┐
                │   P3: Choice Model    │  ← MNL/Nested/Mixed Logit
                │   (explicit formula)  │     (deterministic, calibratable)
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
        ║       │  + L_hetero        │          ║
        ║       │         ↓          ▼          ║
        ║  Loss ◄──── Evaluate on Dev Set      ║
        ║                                       ║
        ║  Post-hoc: temperature / isotonic     ║
        ║            (per-segment)              ║
        ╚═══════════════════════════════════════╝
```

## 实验设计

### PopulationBench 数据集（多 domain，至少 3 个）

| Domain | Dataset | Type | Choice Task |
|--------|---------|------|-------------|
| 消费/出行 | Swissmetro | Public | 3-way mode choice |
| 消费/出行 | Statsmodels ModeChoice | Public | 4-way transport |
| 道德判断 | Moral Machine | Public | Trolley-style binary choice |
| 公共政策 | GSS / ANES subsets | Public | 政策态度 / 行为意愿 |
| 健康 | HINTS subsets | Public | 健康信息搜索 / 就医决策 |
| 商业（可选） | Expedia Hotels | Kaggle | Ranking & click |
| 半合成 | MNL/Mixed Logit ground truth | Generated | 已知真值收敛性验证 |

### Baselines
- **B1**: Direct LLM choice（无结构，直接让 LLM 选）
- **B2**: LLM + post-hoc calibration only（无 TextGrad）
- **B3**: ProTeGi prompt optimization（文本梯度基线）
- **B4**: DSPy optimizer（模块级 prompt 编译）
- **B5**: Generative Agents (Park et al.) 复现版（CSS baseline）
- **B6**: Traditional DCM（MNL/Mixed Logit 直接拟合，data-rich 上限参考）
- **Ours**: Full pipeline（structured + TextGrad + post-hoc）

### Ablations
- w/o Persona layer（uniform persona）
- w/o Utility layer（LLM 直接输出概率）
- w/o TextGrad（仅 post-hoc）
- w/o post-hoc（仅 TextGrad）
- w/o structural constraints in loss
- w/o heterogeneity loss（分群一致性）

### Metrics
| Category | Metrics |
|----------|---------|
| Fit | LogLoss, Brier Score, KL Divergence (group-level) |
| Calibration | ECE, MCE, Reliability Diagram, per-segment ECE |
| Structure | Monotonicity violation, substitution consistency, constraint violation |
| Heterogeneity | Cross-segment divergence, intersectional fairness |
| Stability | Intra-seed variance, cross-seed distribution shift |
| Robustness | Performance under population/scenario/info shift |
| Cost | Tokens per scenario, latency, $/1K simulations |

## Timeline (9 months, extended for multi-domain)

| Month | Focus | Deliverable |
|-------|-------|-------------|
| M1 | Schema + metrics + violation detectors（domain-agnostic） | Evaluation framework |
| M2 | Simulator prototype (3-layer) + Swissmetro baseline | First domain results |
| M3 | Post-hoc calibration + segment analysis | Calibration module |
| M4 | TextGrad integration | Core method |
| M5 | Domain 2 (Moral Machine) + Domain 3 (GSS/ANES) | Multi-domain results |
| M6 | Ablations + baselines (Generative Agents, DCM) | Full ablation table |
| M7 | Robustness + cross-domain transfer experiments | Robustness analysis |
| M8 | PopulationBench release + leaderboard | Benchmark publication |
| M9 | Paper writing (CS venue) + extension draft (CSS venue) | Two submissions |

## 风险与对策

| 风险 | 对策 |
|------|------|
| Multi-domain 数据 schema 异构 | 统一到 ScenarioSpec 抽象，每 domain 写 adapter |
| 跨 domain 校准成本高 | 共享 prompt 骨架，domain-specific 仅替换变量集合 |
| CSS 领域审稿人对 ML/LLM 不熟 | 双栖论文策略：CS 版强调方法，CSS 版强调发现 |
| Generative Agents 复现成本高 | 用其论文 prompt + 同等 LLM 即可 |
