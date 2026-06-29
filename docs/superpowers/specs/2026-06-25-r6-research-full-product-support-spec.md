# R6 Research 全面支撑 Product Spec

## 1. 背景

R6 的 Product 定位已经从“精准预测系统”修正为：

> 人群反应趋势与风险区间模拟器。

这意味着 Product 不承诺精确预测单点结果，而是面向发布前决策，提供趋势方向、可信区间、风险分布、异常群体、机制解释和 outcome 回流后的复盘更新。

当前 Research 已经建立了可审计 artifact chain，并完成了 trend / interval / risk / segment / mechanism / feedback 的初步指标化。但最新证据仍显示 Research 只是 partial support，尚未全面支撑 Product 的核心价值：

- `r6_research_product_value_support` 状态为 `product_value_support_partial`。
- 6 个 Product 价值项中，`supported_value_count=0`，`partial_value_count=2`，`diagnostic_value_count=3`，`blocked_value_count=1`。
- `trend_direction_accuracy=0.667`，`interval_coverage=0.667`，`risk_ranking_quality=0.333`，`false_alarm_rate=0.667`。
- `field_outcome_validated=false`，`runtime_default_allowed=false`。
- Product 客户报告可以 guarded 展示，但不能宣称 field validated、runtime default ready 或 accuracy superiority。

本 spec 的目标是定义 Research 后续必须完成的工作，使 Research 能从“可审计诊断层”推进到“可验证 Product 支撑层”。

## 2. 总目标

Research 的总目标是支撑 Product 稳健说出以下能力边界：

> 系统基于静态人口或客户先验、场景冲击、虚拟人群反应和交互传播，给出趋势方向、风险区间、风险分布、异常群体和机制解释；真实 outcome 回来后，系统能做误差归因，并生成受约束、可审计、可阻断的方法更新。

Research 不以“点预测 beat 静态先验”作为唯一目标。静态先验是仿真底座，不是必须被击败的对手。Research 要证明的是：

1. 静态先验很强时，交互仿真是否能发现静态平均值掩盖的风险。
2. 交互仿真是否能改善趋势方向、区间校准、风险排序和异常群体识别。
3. 交互仿真产生误报时，系统是否能识别、解释和阻断过度 claim。
4. outcome 回流后，系统是否能把错误转化为可审计学习资产。

## 3. Product 需要 Research 支撑的核心承诺

Research 必须逐项支撑以下 Product 能力：

| Product 能力 | 客户看到的输出 | Research 必须提供的证据 |
| --- | --- | --- |
| 趋势方向 | 风险上升、下降、分化、扩散、收敛或不确定 | 趋势方向与 outcome / proxy 的一致性 |
| 风险区间 | 可信数值区间和不确定性说明 | 区间覆盖率、区间宽度和校准来源 |
| 风险分布 | 高风险群体、地区、身份或关系网络分布 | segment ranking、risk concentration、false alarm control |
| 异常群体 | 静态平均值掩盖的敏感群体、反向群体和传播放大群体 | segment-level label、precision / recall、证据来源 |
| 机制解释 | 哪些先验、场景冲击、交互传播或反馈路径导致风险变化 | mechanism trace、operator ablation、传播路径证据 |
| outcome 回流 | 发布后复盘、误差归因、候选更新和阻断原因 | outcome review protocol、bounded update candidate、runtime guard |

只有当对应 Research artifact 通过验收 gate 时，Product 才能把该能力标记为 `validated`。否则只能标记为 `guarded`、`diagnostic` 或 `blocked`。

## 4. 当前根因判断

Research 仍未全面支撑 Product 的底层原因不是“完全没有研究结果”，而是以下断点尚未补齐：

1. 缺少独立 outcome / field outcome，导致很多证据只能作为 proxy diagnostic。
2. 趋势和区间指标已可计算，但稳定性不足，当前 3 个 case 的 accuracy / coverage 都只有 0.667。
3. 风险排序质量偏低，当前 `risk_ranking_quality=0.333`，还不足以支撑客户优先级决策。
4. 交互信号有价值，但容易放大风险，当前 false alarm 偏高。
5. 异常群体 recall 有正向信号，但 label 仍来自 proxy-aligned audit fixture，不是 field segment label。
6. behavioral update operator 没有通过 holdout non-regression，不能作为 runtime default。
7. outcome feedback 能生成学习信号，但还不能通过 static prior guard 和 runtime update guard。

因此，后续 Research 的关键不是继续堆算法名称，而是补齐可验证的支撑闭环。

## 5. 范围

### 5.1 本阶段包含

本阶段 Research 包含以下工作：

1. 建立 outcome / holdout validation 层。
2. 强化趋势方向与区间校准。
3. 强化风险排序与异常群体识别。
4. 建立 false alarm control。
5. 定义并验证 mechanism-driven behavioral update operator。
6. 建立 outcome feedback learning protocol。
7. 固化 Research -> Product evidence contract。

### 5.2 本阶段不包含

本阶段不做以下事情：

1. 不把 Product 包装为精准预测系统。
2. 不宣称交互仿真稳定比静态先验更准。
3. 不宣称 field validation 已完成。
4. 不默认开启 runtime update。
5. 不继续把 TextGrad、DSPy、prompt patch 或 persona patch 作为单独主线。
6. 不为追求论文指标牺牲 Product 证据边界。

## 6. Research 工作包

### WP1：Outcome / Holdout Validation 层

**目标**

建立独立于当前 proxy fixture 的验证层，使 Research 能判断趋势、区间、风险排序和异常群体是否在不同数据源上成立。

**输入**

- 现有 `r6_outcome_holdout_registry`。
- 现有 ANES / HPS / HTOPS proxy。
- 后续新增公开数据或准真实 customer pilot outcome。

**输出 artifact**

- `r6_outcome_holdout_registry_v2`
- `r6_external_outcome_dataset_manifest`
- `r6_holdout_validation_summary`

**必须包含字段**

- `dataset_id`
- `domain`
- `source_type`
- `field_outcome_available`
- `proxy_outcome_available`
- `static_prior_fields`
- `scenario_shock_fields`
- `segment_label_fields`
- `allowed_claim_level`
- `known_limitations`

**验收标准**

- 至少包含 2 个不同领域的数据源或公开 proxy。
- 每个数据源明确 claim level：`validation`、`proxy_diagnostic` 或 `blocked`。
- 所有 Research 指标都能追溯到 source artifact。
- 没有 field outcome 时，不允许设置 `field_outcome_validated=true`。

### WP2：Trend / Interval Calibration 层

**目标**

让 Product 的“趋势方向 + 可信区间”有可计算、可复验、不过度扩宽的 Research 支撑。

**输入**

- 静态先验结果。
- 交互仿真结果。
- outcome / proxy outcome。
- scenario shock 描述。

**输出 artifact**

- `r6_trend_interval_calibration_report`

**核心指标**

- `trend_direction_accuracy`
- `interval_coverage`
- `mean_interval_width`
- `interval_efficiency`
- `uncertainty_source_breakdown`
- `indeterminate_rate`

**方法要求**

趋势方向至少支持：

- `risk_up`
- `risk_down`
- `risk_divergent`
- `risk_diffusion`
- `risk_convergent`
- `uncertain`

区间必须区分三类不确定性：

- 静态先验不确定性。
- 交互传播不确定性。
- outcome / proxy 观测不确定性。

**验收标准**

- holdout 上 `trend_direction_accuracy >= 0.75`。
- holdout 上 `interval_coverage >= 0.75`。
- `mean_interval_width` 必须低于预设上限，不能用过宽区间换覆盖率。
- Product 可以展示区间可信等级：`high`、`medium`、`low`、`diagnostic_only`。

### WP3：Risk Ranking 与异常群体识别层

**目标**

支撑 Product 回答“客户现在最该担心谁、为什么担心、证据是什么”。

**输入**

- segment 静态先验。
- segment 交互后风险偏移。
- segment outcome / audit label。
- mechanism trace。

**输出 artifact**

- `r6_segment_risk_ranking_report`
- `r6_abnormal_segment_validation_report`

**核心指标**

- `risk_ranking_quality`
- `top_k_segment_precision`
- `segment_recall`
- `segment_precision`
- `static_prior_miss_recovery_rate`
- `interaction_only_risk_discovery_count`

**segment 类型**

每个高风险 segment 必须归类为：

- `static_prior_high_risk`
- `interaction_amplified_risk`
- `static_prior_missed_risk`
- `reverse_response_segment`
- `false_alarm_candidate`

**验收标准**

- holdout 上 `risk_ranking_quality >= 0.60`。
- `top_k_segment_precision >= 0.60`。
- `segment_recall >= 0.75`。
- 每个异常群体都有 source artifact、risk reason 和 uncertainty level。
- Product 不展示没有 source 的异常群体。

### WP4：False Alarm Control 层

**目标**

解决交互仿真容易制造虚假风险的问题，使 Product 能可信地区分“值得升级的风险”和“只能诊断展示的风险”。

**输入**

- risk ranking report。
- trend / interval calibration report。
- outcome / proxy outcome。
- mechanism trace。

**输出 artifact**

- `r6_false_alarm_control_report`
- `r6_claim_escalation_gate_report`

**核心指标**

- `false_alarm_rate`
- `controlled_false_alarm_rate`
- `missed_risk_rate`
- `risk_escalation_precision`
- `risk_escalation_recall`
- `blocked_risk_count`

**gate 规则**

风险升级为 Product 正式结论前，必须同时满足：

1. 趋势方向不是 `uncertain`。
2. 区间可信等级不是 `diagnostic_only`。
3. segment risk ranking 通过最低门槛。
4. false alarm discriminator 未标记为 high-risk false alarm。
5. claim level 不超过数据源允许边界。

**验收标准**

- holdout 上 `controlled_false_alarm_rate <= 0.30`。
- false alarm 降低不能让 `missed_risk_rate` 超过 0.30。
- 被阻断的风险必须给出可读原因。
- Product 报告必须展示 blocked / diagnostic risk，而不是静默删除。

### WP5：Mechanism-Driven Behavioral Update Operator

**目标**

把交互仿真从“后验解释”推进为“有机制约束、可消融、可阻断的行为更新算子”。

**输入**

- 静态先验。
- 场景冲击。
- 人群 segment。
- 交互关系或传播假设。
- historical / proxy outcome。

**输出 artifact**

- `r6_behavioral_update_operator_v3`
- `r6_mechanism_operator_ablation_report`
- `r6_operator_holdout_non_regression_report`

**operator 必须支持的机制**

- 利益受损传播。
- 信任下降传播。
- 服务依赖传播。
- 规则敏感传播。
- 同伴影响传播。
- 反向抵抗或逆反应。

**核心指标**

- `operator_holdout_pass_rate`
- `operator_non_regression_rate`
- `mechanism_ablation_delta`
- `static_prior_guard_passed`
- `runtime_default_allowed`

**验收标准**

- holdout 上 `operator_non_regression_rate >= 0.80`。
- 至少一个机制 ablation 能解释风险变化来源。
- 没有通过 static prior guard 时，`runtime_default_allowed=false`。
- operator 不能只靠自然语言解释，必须输出结构化 risk delta。

### WP6：Outcome Feedback Learning Protocol

**目标**

支撑 Product 的发布后复盘和持续学习能力，把错误变成可审计、可比较、可阻断的学习资产。

**输入**

- Product 发布前报告。
- 真实 outcome 或 proxy outcome。
- 静态先验预测。
- 交互仿真预测。
- 用户或 analyst review。

**输出 artifact**

- `r6_outcome_feedback_review`
- `r6_bounded_update_candidate`
- `r6_feedback_transfer_validation`

**必须包含字段**

- `initial_loss`
- `candidate_loss`
- `final_loss`
- `candidate_accepted`
- `candidate_rejected_reason`
- `updated_components`
- `guard_results`
- `rollback_policy`

**更新类型**

- segment 权重更新。
- mechanism 强度更新。
- scenario similarity 更新。
- interval calibration 更新。
- false alarm discriminator 更新。
- blocked claim policy 更新。

**验收标准**

- 每次 outcome 回流都能生成 review artifact。
- 每个 update candidate 都有 accepted / rejected 决策。
- candidate 必须通过 holdout guard 才能进入 runtime default。
- Product 能展示“系统学到了什么”和“什么被阻断”。

### WP7：Research -> Product Evidence Contract

**目标**

让 Product 每个客户可见结论都绑定 Research artifact，并明确 claim status。

**输入**

- WP1-WP6 所有 Research artifact。
- Product story package。
- Product decision report。
- Product customer value report。
- Product API manifest。

**输出 artifact**

- `r6_research_product_value_support_v2`
- `r6_product_claim_evidence_registry`

**claim status**

每个 Product claim 必须是以下状态之一：

- `validated`
- `guarded`
- `diagnostic`
- `blocked`

**映射要求**

| Product section | Research artifact |
| --- | --- |
| 趋势方向 | `r6_trend_interval_calibration_report` |
| 风险区间 | `r6_trend_interval_calibration_report` |
| 风险分布 | `r6_segment_risk_ranking_report` |
| 异常群体 | `r6_abnormal_segment_validation_report` |
| 机制解释 | `r6_mechanism_operator_ablation_report` |
| 误报控制 | `r6_false_alarm_control_report` |
| outcome 回流 | `r6_outcome_feedback_review` |
| 更新候选 | `r6_bounded_update_candidate` |

**验收标准**

- `supported_value_count > 0`。
- `diagnostic_value_count` 和 `blocked_value_count` 都有明确原因。
- 所有 Product-visible claim 都有 source artifact。
- 没有 source 的 claim 不允许进入客户报告。
- `overall_product_core_value_supported=true` 前，Product 必须继续显示 guarded boundary。

## 7. 测试方案

### 7.1 单元测试

每个 WP 至少包含独立测试：

- artifact schema 是否完整。
- 指标是否可计算。
- claim boundary 是否 fail-closed。
- blocked claims 是否保留。
- 无 source 时是否拒绝生成 Product claim。

### 7.2 集成测试

集成测试必须覆盖：

1. Research artifact 生成。
2. Product value support 映射。
3. Product customer report 消费 Research artifact。
4. API manifest 暴露 source registry。
5. readiness index 正确反映 guarded / blocked 状态。

### 7.3 回归测试

每轮实现后必须运行：

```bash
python -m pytest tests/test_r6_* -q
node --check demo/app.js
git diff --check
```

若修改范围不涉及 demo，可以跳过 `node --check demo/app.js`，但需要在汇报中说明。

### 7.4 验收测试

最终验收必须回答：

1. Product 是否能展示趋势方向，并说明可信等级？
2. Product 是否能展示风险区间，并说明区间来源？
3. Product 是否能展示风险分布和异常群体？
4. Product 是否能解释交互机制导致的风险变化？
5. Product 是否能展示 false alarm diagnosis？
6. Product 是否能接收 outcome 回流并生成更新候选？
7. Product 是否能阻断未验证 claim？
8. Research 是否至少让部分 Product 价值项从 diagnostic / partial 推进到 supported？

## 8. 验收门槛

本阶段成功不要求所有能力都达到 field validated，但必须达到以下最低门槛：

1. `trend_direction_accuracy >= 0.75` 或明确降级为 `diagnostic_only`。
2. `interval_coverage >= 0.75` 且 `mean_interval_width` 不超过预设上限。
3. `risk_ranking_quality >= 0.60` 或风险排序不进入客户正式结论。
4. `controlled_false_alarm_rate <= 0.30`。
5. 至少一个 Product 价值项达到 `validated` 或 `supported`。
6. outcome feedback 能生成 accepted / rejected 明确的 bounded update candidate。
7. `runtime_default_allowed` 只有在 holdout guard 通过后才能为 true。

如果这些门槛没有达到，Research 仍可继续提供 Product 诊断价值，但 Product 不得宣称 Research 已全面支撑核心价值。

## 9. 用户或外部数据依赖

以下事项需要用户或外部条件配合：

1. 如果要达到 field validation，需要真实业务 outcome 或客户 pilot 数据。
2. 如果没有真实 outcome，需要至少引入更多公开 proxy 数据源，覆盖不同领域。
3. 如果要验证 segment-level label，需要 analyst audit 或公开数据中可构造的 segment outcome。
4. 如果 Product 要面向真实客户试用，需要明确客户能接受的 claim boundary 和报告格式。

没有这些外部输入时，Research 可以继续推进 proxy validation、false alarm control 和 evidence contract，但不能宣称 field validated。

## 10. 推荐实施顺序

### 第一轮：验证底座

完成 WP1、WP2、WP4。

目标是先建立 outcome / holdout、趋势区间校准和 false alarm control。没有这三项，其他机制解释容易变成内部自证。

### 第二轮：风险发现

完成 WP3、WP7。

目标是把风险排序、异常群体和 Product evidence contract 打通，让客户报告不只展示总体趋势，还能回答“谁最该被关注”。

### 第三轮：机制与学习闭环

完成 WP5、WP6。

目标是把交互机制和 outcome feedback 做成长期技术壁垒，但必须继续受 static prior guard 和 holdout guard 约束。

## 11. Blocked Claims

在验收门槛通过前，以下 claim 必须继续 blocked：

- `精准预测系统`
- `系统可以精确预测单点结果`
- `field_outcome_validated=true`
- `runtime_default_allowed=true`
- `accuracy_superiority_established=true`
- `交互仿真稳定比静态先验更准`
- `Research 已完整支撑 Product 全部核心价值`
- `outcome feedback 已经形成通用自动校准器`
- `候选更新已可自动上线`

## 12. 完成定义

本 spec 完成后的 Research 状态应从：

> 可审计诊断层。

推进到：

> 可验证 Product 支撑层。

判断标准不是“所有指标都好看”，而是：

1. 哪些 Product 价值项已经被 Research 支撑，证据明确。
2. 哪些 Product 价值项仍然 guarded / diagnostic / blocked，原因明确。
3. 交互仿真什么时候有增量价值，什么时候应该回退静态先验，边界明确。
4. outcome 回来后，系统知道如何复盘、归因、生成更新候选并阻断不可靠更新。

这才是 Research 全面支撑 Product 的最小扎实版本。
