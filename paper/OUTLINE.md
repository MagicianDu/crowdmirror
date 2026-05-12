# Paper Outline

## Title
**CIRCE: Joint Causal-Emergence Calibration for Auditable LLM Social Simulation**

*Subtitle (alt)*: From Prompt-Only Personas to Manifest-Backed Social Simulation

## Abstract (~250 words)
- **Problem**: 计算社会科学正在从 rule-based ABM 走向 LLM social simulation,
  但 prompt-only persona simulation 通常只优化表面可读性，缺少同时约束微观选择拟合
  与宏观涌现失真的方法。
- **Gap**: 现有 LLM persona、prompt optimization、ABM 和离散选择校准各自覆盖了
  语言生成、规则涌现或选择概率的一部分，却很少把 causal calibration、
  emergence calibration 和 evidence manifest 作为同一个审计对象。
- **Method**: CIRCE 将 LLM social simulation 写成 joint causal-emergence calibration
  problem, 在同一校准目标中记录 micro-level choice fit、macro-level emergence
  distortion、prompt/update command、model/mode 和 claim boundary。
- **Results**: 论文结果只在对应 manifest 或 archived benchmark artifact 可审计后写入；
  dry-run 只支持 orchestration 和 data-contract 结论，local/live 结果只支持其记录配置下的
  有界 model-quality 结论。
- **Contribution**: formal problem + CIRCE calibration method + benchmark suite +
  claim-boundary protocol, with every research output mapped to a Product trust surface.

## Target Contributions

1. A formal joint causal-emergence calibration problem for LLM social simulation.
2. CIRCE, a calibration method that optimizes micro-level choice fit and macro-level emergence distortion under auditable evidence manifests.
3. A benchmark suite covering semi-synthetic choice, transport choice, and agent-based emergence dynamics.
4. A claim-boundary protocol that prevents dry-run, local-model, and live-model evidence from being overclaimed.

## Product Transfer Paths

| Contribution | Product transfer path | Product-facing surface |
| --- | --- | --- |
| Formal joint causal-emergence calibration problem | Trust explanation | Explain why CrowdMirror is not a prompt-only synthetic persona tool: every recommendation names both micro-choice fit and macro-emergence risk. |
| CIRCE calibration under auditable evidence manifests | Report evidence card | Surface model, mode, command, metric, artifact path, and claim boundary in customer reports. |
| Benchmark suite across choice and emergence domains | Customer proof point | Compare against survey-only, generic LLM persona, static dashboard, and notebook-based simulation alternatives using reproducible benchmark lanes. |
| Claim-boundary protocol | Sensitivity language | State when a recommendation is stable, when evidence is dry-run plumbing only, and when human review or additional local/live evidence is required. |

## 1. Introduction (1.5-2 pages)
- 计算社会科学的范式转移：rule-based ABM -> LLM social simulation
- 关键问题：当前生成式智能体 often looks plausible but is not calibrated
  against both causal choice behavior and macro emergence.
- 核心问题：How can LLM social simulation be calibrated so that micro-level
  choice fit and macro-level emergence distortion are evaluated together?
- 方案概述：CIRCE joint objective + auditable evidence manifests + benchmark
  lanes spanning semi-synthetic choice, transport choice, and ABM emergence.
- Target Contributions 四点必须逐字对应上文，并在 introduction 末尾点明 Product
  transfer path: trust explanation, report evidence card, customer proof point,
  and sensitivity language.

## 2. Related Work (1.5-2 pages)
- 2.1 LLM persona simulation and prompt-only synthetic users
- 2.2 Computational Social Science & ABM
- 2.3 Discrete Choice Calibration (MNL, Nested/Mixed Logit, transport-choice models)
- 2.4 Prompt Optimization (TextGrad, ProTeGi, DSPy, PromptBreeder)
- 2.5 Computational Social Science Simulation and policy experiments
- 2.6 Positioning summary: cite `paper/RELATED_WORK_MATRIX.md` to show what each
  line explains, what it misses, and where CIRCE draws a claim boundary.

## 3. Problem Formulation (1 page)
- 3.1 LLM Social Simulation as a Joint Calibration Problem
  - ScenarioSpec -> micro choices and macro trajectories
  - Choice set, context, intervention/control fields, and emergence trace
- 3.2 Calibration Targets
  - Micro-level causal or choice mismatch
  - Macro-level emergence distortion
  - Evidence completeness as a first-class audit target
- 3.3 Why Prompt-Only LLM Simulation Fails
  - Persona plausibility without causal fit
  - Macro emergence without ground-truth or semi-synthetic reference
  - Prompt drift and uninspectable result claims

## 4. Method (3 pages)
- 4.1 CIRCE Calibration Object
  - Simulator parameters, prompt/update state, choice outputs, emergence trace
  - Joint objective: causal loss + emergence distortion
- 4.2 Calibration Loop
  - Causal calibration lane for semi-synthetic and transport choice
  - Emergence calibration lane for ABM-controlled dynamics
  - Joint acceptance rule recorded with metrics and artifacts
- 4.3 Implementation
  - JSON evidence manifest contract
  - Mode labels: dry-run, local, live
  - Command, config, seed, model/provider, metric, artifact, and claim-boundary fields
  - Product transfer: the same manifest fields populate report evidence cards.

## 5. Benchmark Suite (1.5 pages)
- 5.1 设计原则
  - Covers choice and emergence, not only language plausibility
  - Uses fixed configs and manifests before any paper-claim evidence is written
- 5.2 Domains
  - Semi-synthetic choice
  - Transport choice
  - Agent-based emergence dynamics
- 5.3 Baselines and ablations
  - Prompt-only persona simulation
  - Discrete choice calibration
  - ABM-controlled emergence references
  - Causal-only, emergence-only, and joint CIRCE variants
- 5.4 Metrics
  - Choice fit, causal calibration, emergence distortion, stability, and artifact completeness
- 5.5 Product transfer
  - Benchmark outputs become customer proof points only when backed by committed
    manifests or archived benchmark artifacts.

## 6. Experimental Setup (1 page)
- Baselines: prompt-only synthetic personas, discrete-choice calibration, ABM reference,
  and prompt-optimization-only variants where applicable.
- Ablations: causal-only, emergence-only, joint objective, manifest boundary enabled.
- Evidence classes: deterministic contract, dry-run plumbing, local model, live model,
  and paper-claim evidence.
- Hyperparameters, compute, seeds, commands, and artifacts are recorded in manifests.

## 7. Results (2.5 pages)
- 7.1 Deterministic contract evidence
- 7.2 Dry-run plumbing evidence
- 7.3 Local-model evidence, if manifest-backed
- 7.4 Live-model evidence, if manifest-backed
- 7.5 Benchmark comparison across semi-synthetic choice, transport choice, and ABM emergence
- 7.6 Ablation study isolating causal calibration, emergence calibration, and joint calibration
- 7.7 Sensitivity and claim-boundary language for Product recommendations

## 8. Analysis & Discussion (1 page)
- CIRCE update behavior and prompt/edit traces
- Failure cases where choice fit changes but emergence distortion does not, or the reverse
- Compute cost, reproducibility, and auditability tradeoffs
- Capability boundary against prompt-only personas, traditional DCM, ABM, and notebook-based simulation
- Product-facing interpretation: stable recommendation, sensitive recommendation, or evidence-limited recommendation

## 9. Implications for Computational Social Science (0.5 page)
- 从 ABM 到 LLM social simulation 的范式转移意义
- Calibrated and auditable generative agents as CSS infrastructure
- Ethical considerations: privacy, stereotyping, misuse risk, and visible limits

## 10. Conclusion & Future Work (0.5 page)
- Multi-agent interaction, longitudinal behavior, policy counterfactual simulation,
  and customer-facing evidence review workflows.

## Appendix
- A. Full JSON Schema (ScenarioSpec, BehaviorTrace)
- B. Prompt Templates (P1, P2, P3 initial versions)
- C. CIRCE Optimization Traces
- D. Per-Domain Detailed Results
- E. Benchmark Documentation and Manifest Index
- F. Ethical Considerations & Data Statements
