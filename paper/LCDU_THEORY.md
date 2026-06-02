# LCDU 理论定义草案

## 1. 目标

LCDU 的目标是把 LLM 人群模拟校准从“自由文本 prompt 调整”形式化为：

> 带有语义因素、数值约束、segment guard 和 split-gated acceptance 的分布更新问题。

当前 `LCDU L3` 是该框架的第一个稳定实例，但论文层面的对象应是通用的
`Latent-Constraint Distribution Update`。

## 2. 基本对象

给定一个政策反应任务：

- `s in S`: 人群 segment，例如收入、价格压力、家庭结构、食品安全状态。
- `p in P`: 政策选项，例如现金补贴、食品补贴、不新增支持。
- `x`: scenario，上下文包括政策描述、persona profile、segment prompt、response contract。
- `q_theta(y | x, s)`: 当前 LLM simulator 在参数状态 `theta` 下输出的政策选择分布。
- `p_star(y | s)`: public-data target distribution。
- `A`: 可接受的更新动作空间，包括 prompt component、calibration anchor、latent factor、constraint program。

政策反应校准的核心目标是让：

```text
q_theta(y | x, s) -> p_star(y | s)
```

但更新不能直接覆盖整段 prompt，也不能使用 evaluation/test target 泄漏生成候选。

## 3. 损失函数

当前主损失是 segment-level weighted JSD：

```text
L(theta; D) = sum_s w_s JSD(q_theta(. | x, s), p_star(. | s))
```

为了避免平均损失掩盖少数 segment 的恶化，论文主实验还必须报告：

1. `weighted_choice_distribution_jsd`
2. `segment_rank_correlation`
3. `worst_segment_loss`
4. `axis_level_loss`
5. `accepted/rejected candidate count`
6. `stability_improvement_rate`

## 4. Residual 与语义因素

LCDU 不直接对 prompt 做自由文本梯度，而是先把 residual 映射为可解释因素：

```text
r_s = p_star(. | s) - q_theta(. | x, s)
f = FactorExtractor(r_s, segment_schema, policy_schema)
```

`f` 可以包括：

1. 经济压力因素：`price_stress_level`
2. 收入约束因素：`income_band`
3. 制度信任因素：`institutional_trust`
4. 福利可及性因素：`benefit_accessibility`
5. 政策显著性因素：`benefit_salience`

关键点：语义因素不是解释性标签，而是候选生成和约束构造的输入。

## 5. Constraint Program

给定语义因素 `f`，LCDU 构造 soft constraint program：

```text
c = ConstraintBuilder(f, residual_signature)
```

典型约束包括：

1. `max_probability(policy_id, segment, value)`
2. `min_probability(policy_id, segment, value)`
3. `rank_preservation(segment, preferred_order)`
4. `shape_guard(segment, max_jsd_drift)`
5. `axis_guard(axis, affected_segments)`

LCDU L3 的核心机制是对 `working_family_price_stressed` 施加同步约束，使
segment prompt 与 calibration anchor 同时表达同一个 guard program。

## 6. Update Candidate

一个 LCDU candidate 定义为：

```text
u = (F, C, G, H)
```

其中：

- `F`: latent/semantic factors
- `C`: numeric constraint program
- `G`: segment guard
- `H`: synchronized prompt-anchor realization

在 artifact 中应至少映射到：

1. `candidate_id`
2. `source_split_contract`
3. `best_candidate.parameter_patches`
4. `candidate_prompt_components.segment_prompt`
5. `candidate_prompt_components.calibration_anchor`
6. `candidate_prompt_components.response_contract`
7. `claim_boundary`

## 7. Split-Gated Acceptance

LCDU 必须满足：

```text
candidate_generation_split != candidate_acceptance_split
```

当前默认 contract：

```json
{
  "candidate_generation": "calibration",
  "candidate_acceptance": "heldout",
  "final_claim_check": "test_required_for_ccf_a"
}
```

接受规则：

```text
Accept u_i iff
  L(theta + u_i; D_heldout) < L(theta; D_heldout) - epsilon
  and coverage(theta + u_i; D_heldout) = 1
  and no forbidden worst-segment regression occurs
```

如果多个候选改善，只接受 held-out loss 最低且通过边界检查的候选；其它候选记录为 rejected。

## 8. LCDU 与普通 Prompt Tuning 的差异

LCDU 不等价于 prompt tuning，原因是：

1. 更新对象是结构化 candidate，不是整段 prompt。
2. 候选来源必须记录 residual/factor/constraint provenance。
3. prompt 与 numeric anchor 必须同步。
4. 更新是否进入 accepted state 由 held-out/test gate 决定。
5. 失败候选和负结果是方法证据的一部分。

## 9. 命题草案

### Proposition 1: Acceptance-Gated Monotonicity

若每个 accepted update 都满足固定 held-out loss 改善阈值 `epsilon > 0`，且 loss 有下界，则 accepted update 序列在达到阈值前有限。

这不是优化器收敛证明，只是说明 acceptance gate 防止无限接受无效更新。

### Proposition 2: Boundary-Preserving Update

若 LCDU candidate 通过 worst-segment regression guard，则平均 loss 改善不能以已声明关键 segment 的系统性恶化为代价。

这需要在实验中用 worst-segment loss 和 axis-level loss 验证。

### Proposition 3: Synchronized Constraint Advantage

若 prompt-only 与 anchor-only 更新分别只能影响语义解释或数值输出边界，则 synchronized prompt-anchor program 能在同一 residual factor 上同时约束解释和输出形状。

该命题目前只能作为经验命题，需要 ablation 支持，不能写成已证明定理。

## 10. Artifact Schema Contract

| 理论对象 | 当前 artifact 字段 |
| --- | --- |
| `theta` | Product cohort manifest 的 prompt/profile/calibration context |
| `S` | `segment_predictions`、`segment_metrics` |
| `P` | policy probability keys |
| `p_star` | official public-data distribution |
| `q_theta` | Product LLM output / segment prediction artifact |
| `L(theta)` | benchmark `weighted_choice_distribution_jsd` |
| `u` | `policy-reaction-s2pc-candidate-v1` candidate |
| `F` | parameter patch provenance / latent factor ids |
| `C` | constraint program fields and calibration anchors |
| `G` | segment guard text and selector |
| acceptance | runtime effect / stability / method summary artifacts |
| boundary | `claim_boundary`, `claim_boundaries`, `risk_flags` |

## 11. 当前未闭合理论缺口

1. 还没有证明 semantic factor extractor 的一致性。
2. 还没有证明 constraint builder 的可迁移性。
3. 还没有建立跨任务 generalization bound。
4. 还没有把 LLM 输出随机性纳入正式不确定性分析。
5. 还没有把 Product runtime latency/cost 纳入优化目标。

## 12. Theory Contract Artifact

当前理论对象已经落成可测试 contract：

`experiments/results/lcdu_theory/lcdu-theory-contract-current-001.json`

该 artifact 覆盖 8 个 formal objects：

1. `simulator_state_theta`
2. `segment_space_s`
3. `policy_option_space_p`
4. `target_distribution_p_star`
5. `simulator_distribution_q_theta`
6. `residual_signature_r`
7. `lcdu_update_candidate_u`
8. `split_gated_acceptance`

它关闭的是执行层子门控 `complete_lcdu_theory_contract`，但不关闭 CCF-A 层面的
`theoretical_identification_needs_formalization`。后者仍需要进一步证明 semantic
factor extraction、constraint building 与 cross-task transfer 的理论条件。

## 13. Bounded Identification Proof

当前已经新增 bounded theoretical identification proof：

`experiments/results/lcdu_theory/lcdu-theoretical-identification-proof-current-001.json`

该 proof 不是完整 generalization theorem，而是对 `LCDU-hybrid` 的当前可证部分做形式化：

1. `split_isolation`：calibration-derived anchor 和 heldout-selected method choice 在读取 test loss 前固定；test split 只用于最终 claim check。
2. `anchor_copy_identification`：若 LLM strict-copy distribution 在 tolerance 内等于 calibration segment anchor，则 LCDU-hybrid 的 numeric prediction 可识别为 deterministic anchor program。
3. `non_superiority_boundary`：由于 LCDU-hybrid 的 numeric component 复用 deterministic anchor，因此它只能主张 numeric parity 与 audit decomposition，不能主张相对 deterministic anchor 的 accuracy superiority。

当前 proof 关闭的子门控：

```json
["theoretical_identification_proof_ready"]
```

仍未闭合的理论风险：

1. external validity bound missing；
2. finer schema identifiability unproven；
3. narrative utility metric missing；
4. customer field validation missing。

因此，Research 主张应从 `LCDU-soft beats strong baselines` 改为：

```text
LCDU-hybrid identifies the numeric simulator distribution with calibrated
segment anchors under a split-gated contract, while delegating explanation,
auditability, and counterfactual reporting to the LLM layer.
```
