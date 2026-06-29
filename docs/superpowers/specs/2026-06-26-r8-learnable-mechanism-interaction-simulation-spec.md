# R8 可学习机制交互仿真 Spec

## 1. 背景判断

当前 Product 已明确定位为：

> 人群反应趋势与风险区间模拟器。

这意味着系统不承诺精准预测单点结果，而是提供趋势方向、可信区间、风险分布、异常群体、机制解释和 outcome 回流后的复盘更新。

R6 已经建立 Product guard、证据链、claim boundary、false-alarm gate 和 outcome review。R7 已经把方法从后处理分数推进到机制状态、交互图、rollout distribution 和策略沙盘。最新 R7 v2 在当前 public proxy 上出现 guarded positive signal：

- `interval_coverage=1.0`
- `false_alarm_rate=0.0`
- `static_prior_miss_recovery_rate=1.0`
- `mean_absolute_error=0.04`

但 R7 v2 仍不能作为稳定支撑 Product 的核心方法，原因是：

1. 当前正向信号主要来自固定场景修正项和区间 floor。
2. 修正项不是从数据中学习出来的可迁移 operator。
3. 当前验证只有 3 个 public proxy case，缺少独立 field/customer outcome。
4. 没有证明机制参数、传播边或群体更新规则能在 holdout 上迁移。
5. 不能把当前结果升级为 `field_outcome_validated=true` 或 `runtime_default_allowed=true`。

因此 R8 不再做 R7 v3 式局部调参，而是切换到新的主方法：

> 可学习机制因果图 + 交互传播算子 + outcome 反馈更新。

R8 的目标是把“交互仿真为什么有效、什么时候失效、真实结果回来后如何自动改进”变成可计算、可审计、可测试的系统能力。

## 2. R8 总目标

R8 的总目标是让 Research 能更扎实地支撑 Product 的核心价值：

> 在强静态先验存在的情况下，通过机制激活、群体交互传播和不确定性建模，发现静态先验无法表达的二阶风险；在真实或 proxy outcome 回来后，把误差归因到具体机制、传播边或区间校准，并生成受约束的自动更新候选。

R8 不追求“每个 case 点预测都 beat 静态先验”。R8 要验证的是：

1. 趋势方向是否稳定。
2. 区间是否校准且不过宽。
3. 高风险和异常群体排序是否有决策价值。
4. 交互层是否能恢复静态先验漏报。
5. false alarm 是否可识别、可解释、可阻断。
6. outcome 反馈是否能自动生成机制级更新，而不是人工改 prompt 或规则。
7. 更新候选是否能在 holdout 或扰动验证中保持 non-regression。

## 3. 方法边界

### 3.1 R8 不是

R8 不做以下事情：

1. 不把 Product 改回精准预测系统。
2. 不把 R7 v2 的固定修正项包装成通用算法。
3. 不继续依赖人工补 `boost`、`buffer` 或区间 floor 作为主方法。
4. 不把 TextGrad、DSPy、prompt/persona patch 作为 Research 主线。
5. 不在没有 holdout 或 field/customer outcome 时开启 runtime default。
6. 不用过宽区间换取 coverage 指标。

### 3.2 R8 保留

R8 保留并复用以下资产：

1. R6 的 Product guard、claim boundary、evidence card 和 failure diagnosis。
2. R6 的 strong static prior / no-interaction control。
3. R6 的 public proxy、holdout、robustness、ablation 结果。
4. R7 的机制状态、交互图、rollout distribution、策略沙盘和 Product support report。
5. R7 v2 作为固定规则 baseline，而不是最终方法。

## 4. 核心假设

R8 建立在三个假设上。

### 4.1 静态先验是底座

静态先验不是对手，而是仿真起点。交互仿真只有在以下情况下才有额外价值：

1. 发现静态平均值掩盖的高风险群体。
2. 发现交互传播带来的风险放大、缓和、扩散或反转。
3. 给出比静态先验更有决策价值的区间和风险排序。
4. 在 outcome 回流后形成可审计学习资产。

### 4.2 交互价值来自机制传播

交互仿真的价值不应来自事后调数，而应来自可解释机制：

```text
场景冲击
  -> 机制激活
  -> 群体状态变化
  -> 交互传播
  -> 分布式风险结果
```

如果某个方法不能说明风险来自哪个机制、哪类群体、哪条传播路径，它只能作为 diagnostic baseline，不能作为 Product 核心方法。

### 4.3 学习必须发生在机制层

outcome 回流后，系统不能只更新一个全局 residual。R8 必须把误差拆成：

1. 机制激活错误。
2. 机制方向错误。
3. 机制强度错误。
4. 传播边权错误。
5. 群体敏感度错误。
6. 区间不确定性错误。
7. 静态先验缺失或偏差。

只有这种拆解能支撑 Product 的“为什么、怎么办、下次如何改进”。

## 5. 方法框架

### 5.1 输入

R8 的最小输入包括：

1. `static_prior_state`：群体静态先验，包括基线风险、敏感度、不确定性。
2. `scenario_shock`：政策、产品、价格、规则或服务变化。
3. `segment_profile`：群体属性、角色、行为约束和可能反应机制。
4. `interaction_graph`：群体之间的影响、相似、信任、替代和传播关系。
5. `mechanism_catalog`：可激活机制集合。
6. `outcome_manifest`：真实 outcome 或 public proxy outcome。
7. `guard_context`：Product claim boundary、false-alarm gate、runtime update gate。

### 5.2 状态表示

每个群体节点 `s` 维护以下状态：

```text
z_s = {
  prior_risk,
  prior_uncertainty,
  mechanism_activation_vector,
  exposure_level,
  behavioral_sensitivity,
  interaction_susceptibility,
  propagated_influence,
  current_risk_distribution
}
```

其中 `mechanism_activation_vector` 至少包含：

1. 价格敏感。
2. 信任损失。
3. 公平感知。
4. 替代选项。
5. 身份或价值一致性。
6. 服务可达性。
7. 损失规避。
8. 社交扩散敏感度。

### 5.3 机制因果图

R8 引入 `mechanism_causal_graph`，用于表示机制之间的因果和约束关系：

```text
scenario_shock -> mechanism_activation -> segment_response -> interaction_propagation -> risk_distribution
```

图中每条边必须包含：

1. `source_node`
2. `target_node`
3. `effect_direction`
4. `effect_strength`
5. `uncertainty`
6. `evidence_source`
7. `learnable`
8. `guard_constraints`

`evidence_source` 可以是静态先验、公开数据、历史 outcome、LLM judge、人工 domain config 或实验 fixture。客户可见结论必须能追溯 source。

### 5.4 可学习交互算子

R8 的核心算子是：

```text
F_theta(prior_state, scenario_shock, mechanism_graph, interaction_graph)
  -> rollout_distribution
```

其中 `theta` 包含：

1. 机制激活权重。
2. 机制方向约束。
3. 群体敏感度参数。
4. 传播边权。
5. 传播衰减参数。
6. 不确定性膨胀/收缩参数。
7. false-alarm penalty。
8. non-regression guard 参数。

R8 的学习目标不是直接拟合 observed outcome 单点，而是优化以下多目标：

```text
L = trend_loss
  + interval_miscalibration_loss
  + false_alarm_loss
  + missed_risk_loss
  + ranking_loss
  + over_width_penalty
  + update_complexity_penalty
  + guard_violation_penalty
```

### 5.5 outcome 反馈更新

真实或 proxy outcome 回来后，R8 生成 `outcome_attribution_report`：

1. 哪些机制解释了正确方向。
2. 哪些机制导致 false alarm。
3. 哪些静态先验漏报被交互恢复。
4. 哪些传播边导致过度放大。
5. 哪些区间太窄或太宽。
6. 哪些更新候选应被接受、拒绝或等待 holdout。

然后生成 `operator_update_candidate`：

```text
delta_theta = constrained_update(
  residual,
  mechanism_trace,
  propagation_trace,
  guard_context
)
```

更新候选必须包含：

1. 更新对象。
2. 更新方向。
3. 更新幅度。
4. 触发证据。
5. 预期改善指标。
6. 可能伤害的指标。
7. rollback 条件。
8. 是否允许 runtime default。

默认规则：

> 没有通过 holdout、robustness 和 Product guard 时，`runtime_default_allowed=false`。

## 6. 三条并行验证线

R8 主方法和两个 baseline 必须并行推进，避免单点算法自我确认。

### 6.1 主线 A：机制因果图 + 可学习交互算子

目标：验证机制参数和传播边能否从 outcome 反馈中学习，并迁移到 holdout。

优势：

1. 最贴合 Product 的机制解释和更新闭环。
2. 能把错误归因到机制和传播路径。
3. 有机会形成真正的技术壁垒。

劣势：

1. 数据需求更高。
2. 参数容易过拟合小样本 proxy。
3. 需要严格 guard，避免把当前 proxy 记忆当成算法。

### 6.2 基线 B：分层区间校准

目标：验证不引入复杂交互学习时，仅通过分层不确定性和 conformal-style 区间校准，能达到什么效果。

作用：

1. 给 R8 主方法提供区间校准下限。
2. 证明 R8 的提升不是只靠扩大区间。
3. 作为 Product 的保守 fallback。

限制：

1. 机制解释弱。
2. 对异常群体和传播路径支撑不足。
3. 不能单独构成 Product 核心仿真壁垒。

### 6.3 基线 C：多智能体传播仿真

目标：验证更显式的人群交互和传播过程是否能提高风险发现和策略沙盘价值。

作用：

1. 增强 Product 对“交互过程”的展示和解释。
2. 检查 R8 主方法是否过度抽象，忽略过程动态。
3. 提供策略沙盘的行为路径 baseline。

限制：

1. 如果没有 outcome 学习，容易变成更复杂的 demo。
2. 大规模仿真成本更高。
3. 需要和 R8 主方法共享 guard，不能单独宣称 field validation。

## 7. LLM 的角色边界

R8 可以使用 LLM，但 LLM 不是最终判定器，也不能绕过 Research/Product gate。

### 7.1 LLM 可以做什么

LLM 可以作为以下模块的辅助能力：

1. 从 scenario 文本中抽取候选机制。
2. 为 segment 生成候选反应路径。
3. 为机制因果图补充可解释的边和约束。
4. 判断某个机制是否与场景冲击语义匹配。
5. 生成 outcome attribution 的自然语言解释草稿。
6. 为 Product report 生成可读叙事，但必须引用 source artifact。

### 7.2 LLM 不能做什么

LLM 不允许直接决定：

1. `field_outcome_validated`。
2. `runtime_default_allowed`。
3. update candidate 是否 accepted。
4. 是否可以宣称 Product validated。
5. 是否可以跳过 holdout 或 robustness gate。

### 7.3 LLM 输出必须结构化

LLM 输出必须落到结构化字段：

1. `candidate_mechanisms`
2. `candidate_edges`
3. `mechanism_rationale`
4. `evidence_source`
5. `uncertainty_level`
6. `requires_human_review`

如果 LLM 输出无法结构化，或者缺少 source refs，则只能进入 draft，不得进入客户可见 report。

## 8. Artifact 合同

R8 必须新增以下 artifacts。

### 8.1 `r8_mechanism_causal_graph_manifest`

用途：描述机制因果图和证据来源。

必须包含：

1. `graph_nodes`
2. `graph_edges`
3. `mechanism_catalog`
4. `evidence_sources`
5. `learnable_parameters`
6. `non_learnable_constraints`
7. `claim_boundary`

### 8.2 `r8_operator_parameter_registry`

用途：记录当前 operator 参数、更新历史和 guard 状态。

必须包含：

1. `parameter_id`
2. `parameter_family`
3. `current_value`
4. `allowed_range`
5. `evidence_level`
6. `last_update_source`
7. `runtime_default_allowed`
8. `rollback_policy`

### 8.3 `r8_rollout_distribution`

用途：输出 no-interaction、interaction-on 和 candidate-update 三类 rollout 分布。

必须包含：

1. `rollout_count`
2. `seed_policy`
3. `no_interaction_distribution`
4. `interaction_distribution`
5. `candidate_update_distribution`
6. `uncertainty_breakdown`
7. `interval_width`
8. `over_width_penalty`

### 8.4 `r8_risk_interval_calibration_report`

用途：评估区间是否可信。

必须包含：

1. `trend_direction_accuracy`
2. `interval_coverage`
3. `mean_interval_width`
4. `interval_efficiency`
5. `coverage_by_case_family`
6. `indeterminate_rate`
7. `over_width_blocked`

### 8.5 `r8_risk_ranking_report`

用途：评估风险排序和异常群体识别。

必须包含：

1. `top_k_hit_rate`
2. `risk_ranking_quality`
3. `static_prior_miss_recovery_rate`
4. `false_alarm_rate`
5. `segment_precision`
6. `segment_recall`
7. `static_hidden_risk_segments`
8. `interaction_amplified_segments`

### 8.6 `r8_outcome_attribution_report`

用途：把 outcome error 归因到机制、传播、先验和区间。

必须包含：

1. `outcome_residual`
2. `attribution_by_mechanism`
3. `attribution_by_edge`
4. `attribution_by_segment`
5. `interval_error_type`
6. `false_alarm_sources`
7. `missed_risk_sources`
8. `unexplained_error`

### 8.7 `r8_operator_update_candidate`

用途：生成可审计、可阻断的更新候选。

必须包含：

1. `candidate_id`
2. `updated_parameters`
3. `expected_metric_delta`
4. `guard_checks`
5. `holdout_results`
6. `robustness_results`
7. `accepted`
8. `rejected_reason`
9. `runtime_default_allowed`

### 8.8 `r8_product_support_gate`

用途：决定 Product 能展示哪些 claim。

必须包含：

1. `trend_supported`
2. `interval_supported`
3. `risk_ranking_supported`
4. `abnormal_segment_supported`
5. `mechanism_explanation_supported`
6. `outcome_learning_supported`
7. `field_outcome_validated`
8. `runtime_default_allowed`
9. `blocked_claims`
10. `allowed_claims`

### 8.9 `r8_baseline_comparison_report`

用途：把 R8 主方法和 static prior、R6、R7 v2、基线 B、基线 C 统一比较。

必须包含：

1. `static_prior_metrics`
2. `r6_learning_counterfactual_metrics`
3. `r7_v2_metrics`
4. `r8_main_metrics`
5. `interval_baseline_metrics`
6. `agent_propagation_baseline_metrics`
7. `winner_by_metric`
8. `claim_level_by_metric`
9. `stop_loss_recommendation`

## 9. 验收标准

R8 分三层验收。

### 9.1 L0 合同验收

L0 只证明链路可运行，不证明方法有效。

必须满足：

1. 所有 R8 artifacts 可生成。
2. 所有 artifacts 通过 strict JSON 检查。
3. 所有客户可见字段有 source refs。
4. `field_outcome_validated=false`。
5. `runtime_default_allowed=false`。
6. Product guard 能消费 R8 support gate。

通过后状态：

> `r8_contract_ready_guarded`

### 9.2 L1 当前 proxy 正向信号

L1 证明当前 proxy 上有方法信号，但仍不能默认启用。

必须满足：

1. 趋势方向不低于 R7 v2。
2. 区间覆盖不低于 R7 v2，且 mean interval width 不超过 R7 v2 的 1.2 倍。
3. false alarm rate 不高于 R7 v2。
4. static prior miss recovery 不低于 R7 v2。
5. risk ranking quality 高于 R6/R7 当前 baseline。
6. outcome attribution 中 `unexplained_error` 比例可报告且不被隐藏。
7. 至少一个 update candidate 被 guard 正确拒绝或保留为 pending，不允许默认接受。

通过后状态：

> `r8_current_proxy_positive_guarded`

### 9.3 L2 稳健性和 holdout 验收

L2 证明 R8 不是当前 3 个 proxy 过拟合。

必须满足：

1. observed/proxy outcome 扰动下，关键指标不出现大幅反转。
2. leave-one-case 验证下，至少保持 non-regression。
3. 同 family holdout 中 false alarm 不恶化。
4. 不同 family holdout 中能 fail closed，不产生过度 claim。
5. update candidate 至少在一个独立 holdout 上通过 guard。
6. Product support gate 对未通过能力保持 guarded 或 diagnostic。

通过后状态：

> `r8_holdout_positive_guarded`

### 9.4 L3 field/customer outcome 验收

L3 才能支撑更强 Product claim。

必须满足：

1. 至少一个真实 customer pilot 或 field outcome 接入。
2. field outcome 与 scenario、segment、机制 trace 可对齐。
3. R8 在 field outcome 上通过趋势、区间、风险排序、false alarm control 的最小 gate。
4. outcome feedback 能生成 update candidate。
5. update candidate 通过 holdout 或复核后才允许 runtime default。

通过后状态：

> `r8_field_validated_guarded`

即使 L3 通过，也只能声明“field outcome 支持的 guarded capability”，不能宣称所有场景精准预测。

## 10. 指标门槛

第一阶段建议门槛如下。

| 指标 | L1 当前 proxy | L2 holdout | L3 field/customer |
| --- | --- | --- | --- |
| 趋势方向 | 不低于 R7 v2 | `>= 0.75` 或 non-regression | `>= 0.75` |
| 区间覆盖 | 不低于 R7 v2 | `>= 0.75` | `>= 0.75` |
| 区间宽度 | 不超过 R7 v2 的 1.2 倍 | 不超过预设上限 | 不超过预设上限 |
| false alarm | 不高于 R7 v2 | `<= 0.30` 或 non-regression | `<= 0.30` |
| static miss recovery | 不低于 R7 v2 | non-regression | non-regression |
| risk ranking quality | 高于当前 baseline | `>= 0.60` | `>= 0.60` |
| update guard | 默认阻断 | 至少一个候选通过 holdout | field 后可复核启用 |

如果数据规模过小，指标必须同时报告置信等级，不能只报平均值。

## 11. 测试方案

### 11.1 合同测试

覆盖：

1. 所有 R8 artifact schema。
2. `artifact_id`、`run_id`、`schema_version`、`source_refs`、`claim_boundary`。
3. Product support gate 的 allowed/blocked claims。
4. 缺少 source refs 时 fail closed。

### 11.2 算子单元测试

覆盖：

1. 机制激活方向约束。
2. 传播边权范围。
3. 不确定性分解。
4. no-interaction control 不被污染。
5. update candidate 不允许越过 guard。

### 11.3 仿真测试

覆盖：

1. deterministic seed 可复现。
2. rollout_count 足够。
3. interaction-on 与 no-interaction 有可解释差异。
4. 区间宽度和 coverage 同时报。
5. 策略沙盘不改变 source refs。

### 11.4 验证测试

覆盖：

1. static prior、R6、R7 v2、R8 主方法、基线 B、基线 C 的同口径比较。
2. current proxy。
3. outcome perturbation。
4. leave-one-case。
5. same-family holdout。
6. cross-family fail-closed。

### 11.5 Product guard 测试

覆盖：

1. 未过 L2 时 `runtime_default_allowed=false`。
2. 未接 field outcome 时 `field_outcome_validated=false`。
3. false alarm 过高时 Product 只能展示 diagnostic。
4. 区间过宽时 Product 必须降级可信等级。
5. update candidate 未过 guard 时不能进入默认参数。

## 12. 止损条件

R8 必须设置明确止损线。

### 12.1 方法止损

出现任一情况，R8 主方法不得继续包装为 Product core：

1. L1 当前 proxy 不优于 R7 v2。
2. L2 holdout 大幅回归。
3. false alarm control 只能靠 case family 记忆。
4. 区间 coverage 只能靠过宽区间实现。
5. outcome attribution 中 `unexplained_error` 长期过高。
6. update candidate 不能通过任何独立 holdout。
7. 主方法效果不如基线 B 或基线 C，且没有额外解释价值。

### 12.2 Product 降级

触发止损后，Product 仍可保留：

1. source-backed report。
2. static prior baseline。
3. R6/R7/R8 对比。
4. failure diagnosis。
5. risk review workflow。
6. outcome replay。

但不得展示：

1. R8 validated。
2. runtime default ready。
3. field validated。
4. accuracy superiority。

## 13. 第一阶段实施顺序

第一阶段不直接追求完整大模型人群仿真，而是先完成可学习机制框架的最小闭环。

### Task 1：R8 artifact contract

目标：定义并生成 L0 最小 artifacts。

验收：

1. `r8_mechanism_causal_graph_manifest` 可生成。
2. `r8_operator_parameter_registry` 可生成。
3. `r8_product_support_gate` 可生成。
4. strict JSON 通过。
5. Product guard 默认阻断 runtime default。

### Task 2：R8 可学习算子 MVP

目标：实现机制参数、传播边权和区间参数的 bounded update candidate。

验收：

1. 可从 outcome residual 生成机制级 attribution。
2. 可生成 `operator_update_candidate`。
3. update candidate 默认需要 holdout。
4. no-interaction control 不受更新污染。

### Task 3：R8 baseline comparison

目标：同口径比较 static prior、R6、R7 v2、R8 主方法、基线 B、基线 C。

验收：

1. 输出 `r8_baseline_comparison_report`。
2. 每个指标有 winner 和 claim level。
3. 如果 R8 不优于 baseline，报告 stop-loss recommendation。

### Task 4：R8 robustness / holdout gate

目标：验证 R8 是否只是 current proxy 过拟合。

验收：

1. observed/proxy perturbation 可运行。
2. leave-one-case 可运行。
3. same-family holdout 可运行。
4. cross-family fail-closed 可运行。
5. 输出 L1/L2 状态。

### Task 5：Product support ingestion

目标：让 Product 使用 R8 结果，但严格保持 claim boundary。

验收：

1. customer value report 能读取 R8 support gate。
2. 前端或 API 能展示 R8 的支持等级。
3. 未过 gate 的能力显示 guarded/diagnostic/blocked。
4. blocked claims 不被覆盖。

## 14. 预期结论类型

R8 第一阶段只能产生三类结论之一。

### 14.1 成功信号

如果 R8 达到 L1 或 L2：

> R8 在当前 proxy 或 holdout 上显示可学习机制交互算子的正向信号，能够在保持 Product guard 的前提下继续推进。

### 14.2 诊断价值

如果 R8 主方法不稳定，但 attribution、guard 和 baseline comparison 有价值：

> R8 不足以作为 Product core，但可作为 failure diagnosis、outcome replay 和方法审计资产。

### 14.3 止损

如果 R8 不优于 R7 v2，也不能提供额外解释价值：

> R8 主方法止损。Product 保留 R6/R7 guard 和报告链路，Research 转向数据获取、客户 pilot outcome 或更具体的垂直场景验证。

## 15. 当前最重要的判断

R8 的真正目标不是“把当前 3 个 proxy 跑好”，而是回答：

> 在强静态先验已经存在的情况下，交互仿真能否通过可学习机制传播，稳定地产生趋势、区间、风险排序、异常群体和 outcome learning 的增量价值？

如果能，R8 才能成为 Product 的技术壁垒。

如果不能，Product 仍有价值，但价值会降级为：

> source-backed 静态先验 + 风险诊断 + 发布后复盘工具。

这两种结论都可接受。不可接受的是把 current proxy 上的规则修补包装成稳定方法。
