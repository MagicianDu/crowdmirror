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

## Contribution-to-Evidence

| Contribution | Notation/equation | Algorithm/protocol | Baseline/ablation | Main table/figure | Allowed claim | Forbidden claim |
| --- | --- | --- | --- | --- | --- | --- |
| Formal joint causal-emergence calibration problem | `S_theta(x) -> (a_hat, z_hat)` and `L_joint(theta,m)=w_c L_choice + w_e L_emerge` under the hard constraint `L_manifest(m)=0` | Definition of scenario, choice outcome, emergence trace, simulator state, and evidence manifest | Compare problem coverage against prompt-only persona generation, discrete choice calibration, and ABM-only emergence references | Figure 1: problem graph from scenario to micro choice, macro trajectory, and manifest | CIRCE formalizes simultaneous micro-choice fit and macro-emergence distortion reporting for LLM social simulation | The formalism alone establishes external behavioral validity |
| CIRCE calibration method | Accepted update `theta_{t+1}` must satisfy `Delta L_joint <= -epsilon` and per-lane constraints for choice, emergence, and manifest validity | Closed-loop joint calibration protocol: propose prompt/model update, run lane, compute losses, write manifest, accept or reject | Causal-only, emergence-only, joint, and manifest-disabled variants | Algorithm 1 and Table 2: accepted updates and loss decomposition | CIRCE evaluates whether a prompt/model update reduces the recorded joint objective for the tested lane and mode | A dry-run or single model run generalizes to all customers, providers, or domains |
| Benchmark suite | Domain index `D={semi_synthetic_choice, transport_choice, abm_emergence}` with metric vector `(choice_fit, causal_loss, emergence_distortion, manifest_completeness)` | Fixed configs, seeds, commands, result artifacts, and manifest index per benchmark lane | Prompt-only persona, discrete choice calibration, ABM reference, causal-only CIRCE, emergence-only CIRCE, joint CIRCE | Table 1: lane coverage; Table 3: benchmark metrics; Figure 2: ablation deltas | The benchmark tests whether joint calibration changes both micro and macro metrics under recorded configs | The benchmark is a production demand forecast or customer predictive-validity certificate |
| Executable audit and claim protocol | Claim predicate `claim_allowed(c, m)` over manifest fields `mode`, `status`, `metrics`, `artifacts`, `boundary`, and `config_hash` | Audit script rejects claims without matching manifest class: dry-run, local, live, or archived paper artifact | Protocol-on versus protocol-off claim review; dry-run-only versus manifest-backed local/live claims | Table 4: claim audit results; Appendix manifest examples | The protocol blocks unsupported manuscript and product claims before release | The protocol substitutes for model validation or field evidence |

## Joint Objective Details

- Variables:
  - `x`: scenario, intervention, and choice context.
  - `a`: observed, semi-synthetic, or benchmark choice outcome.
  - `z`: macro-emergence trajectory or endpoint statistic.
  - `theta`: simulator prompt, model configuration, parser, and calibration state.
  - `m`: evidence manifest containing mode, status, command, config, metrics, artifact paths, model/provider, seed, and claim boundary.
- Loss terms:
  - `L_choice(theta; x, a)`: micro-choice fit or causal-choice mismatch.
  - `L_emerge(theta; x, z)`: macro-emergence distortion against ABM, semi-synthetic, or archived reference dynamics.
  - `L_manifest(m)`: hard acceptance predicate that is zero only when required manifest fields are complete and inspectable; it is not an additive soft penalty.
- Weights and constraints:
  - `w_c` and `w_e` are declared per benchmark lane before running the experiment; they cannot be tuned after reading results.
  - `L_manifest(m)=0` is a hard acceptance constraint for any paper or Product-facing claim.
  - Local/live evidence cannot be mixed with dry-run plumbing evidence in the same main-result row.
- Acceptance rule:
  - A candidate update is accepted only when the relevant lane objective decreases by at least `epsilon`, manifest validation passes, and no protected claim boundary is violated.
  - Dry-run acceptance only validates orchestration, parser, persistence, and manifest shape; it does not enter model-quality tables.
- Discrimination experiments:
  - Causal-only: optimize/report `L_choice` while holding the emergence calibration lane inactive.
  - Emergence-only: optimize/report `L_emerge` while holding the choice calibration lane inactive.
  - Joint: optimize/report both `L_choice` and `L_emerge` under the manifest completeness constraint.
  - Reviewer-facing discrimination criterion: joint calibration must be reported separately from causal-only and emergence-only variants so the paper can show whether simultaneous micro-choice fit and macro-emergence distortion reporting changes the conclusion.

## Product Transfer Paths

| Contribution | Product transfer path | Product-facing surface |
| --- | --- | --- |
| Formal joint causal-emergence calibration problem | Trust explanation | Explain why CrowdMirror is not a prompt-only synthetic persona tool: every recommendation names both micro-choice fit and macro-emergence risk. |
| CIRCE calibration under auditable evidence manifests | Report evidence card | Surface model, mode, command, metric, artifact path, and claim boundary in customer reports. |
| Benchmark suite across choice and emergence domains | Customer proof point | Compare against survey-only, generic LLM persona, static dashboard, and notebook-based simulation alternatives using reproducible benchmark lanes. |
| Claim-boundary protocol | Sensitivity language | State when a recommendation is stable, when evidence is dry-run plumbing only, and when human review or additional local/live evidence is required. |

## Product Moat Crosswalk

| Research artifact | Product surface/API/report field | Customer proof sentence | Moat claim | Evidence gate | Forbidden claim |
| --- | --- | --- | --- | --- | --- |
| Evidence manifest | Report evidence card fields: `model`, `provider`, `mode`, `status`, `command`, `config_hash`, `seed`, `metrics`, `artifacts`, `claim_boundary`, `notes` | "This recommendation is tied to a reproducible run record with model, mode, command, metrics, artifacts, and explicit boundary." | Auditability is built into the simulation workflow, not added after the result is written. | Manifest validates against schema and artifact paths are inspectable. | The report is accurate because a manifest exists. |
| Joint objective run | API/report fields: `choice_fit_metric`, `emergence_distortion_metric`, `joint_objective`, `accepted_update`, `lane` | "The run checks both individual choice fit and macro-emergence distortion before presenting a recommendation." | Differentiates from prompt-only persona demos that expose only generated text or aggregate counts. | Non-dry-run manifest or archived benchmark artifact records initial and final metrics. | This establishes real customer demand or field conversion. |
| Causal-only/emergence-only/joint ablation | Report sensitivity section: `ablation_lane`, `metric_delta`, `stability_label`, `review_required` | "The recommendation is stable only if causal-only and emergence-only lanes do not contradict the joint result." | Product can explain sensitivity rather than hiding disagreement between lanes. | All compared lanes share fixed config, seed policy, and manifest schema. | A stable ablation replaces human decision review. |
| Benchmark matrix | Sales proof appendix/API export: `domain`, `baseline`, `ablation`, `mode`, `metric_table`, `artifact_index` | "The method has been compared against declared baseline families on recorded benchmark lanes." | Creates a reproducible comparison surface against survey-only, static dashboard, generic LLM persona, and notebook simulation alternatives. | Benchmark run is backed by committed manifests or archived artifacts; dry-run rows are labeled plumbing only. | Benchmark evidence is customer predictive validity or production ROI evidence. |
| Claim audit protocol | Release gate/API status: `claim_allowed`, `claim_blocked_reason`, `evidence_class`, `required_manifest` | "Claims are blocked when evidence class, mode, metrics, or artifact paths do not support the wording." | Trust surface includes negative and blocked claims, not only favorable examples. | Audit script or checklist maps every claim to a manifest class. | Audit status means model behavior is validated in the field. |
| Dry-run plumbing evidence | Internal QA/report footnote only: `mode=dry-run`, `boundary=dry-run plumbing evidence only` | "This run checked orchestration and artifact wiring; it is not model-quality evidence." | Makes engineering readiness visible without overstating model validity. | Dry-run manifest records command, config, child runs, metrics shape, and artifacts. | Dry-run results support product recommendation quality, live performance, or customer proof. |

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
  - Simulator parameters `theta`, scenario `x`, choice outcome `a`, emergence trace `z`, and manifest `m`
  - Joint objective: weighted choice loss, weighted emergence loss, and hard manifest-completeness constraint
- 4.2 Calibration Loop
  - Causal calibration lane for semi-synthetic and transport choice
  - Emergence calibration lane for ABM-controlled dynamics
  - Joint acceptance rule recorded with metrics, artifacts, lane label, mode label, and boundary text
  - Causal-only, emergence-only, and joint variants are first-class discrimination experiments, not informal appendix checks
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
