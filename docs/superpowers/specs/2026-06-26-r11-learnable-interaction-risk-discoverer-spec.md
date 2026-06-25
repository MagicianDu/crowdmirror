# R11 可学习交互风险发现器 Spec

## 背景判断

当前 Research 已经不缺 artifact、guard 和报告链路，真正的短板是方法强度不足。

R9/R10 给出的价值是：

- R9 把外部证据、机制算子、多主体 rollout 和 outcome replay 放到统一比较框架里。
- R10 接入了 Census HPS/HTOPS 真实 public-use 数据，并证明外部证据能提供 source-backed 风险排序候选信号。
- R10 L4 已用 interval floor 阻断 HPS overlay 对区间覆盖的伤害。

但这些仍然主要是 overlay、guard、diagnostic 和 evidence-routing，不是足够强的主方法。当前不能把 R10 包装成 Product 核心算法，因为它还没有证明：

1. 交互传播本身能稳定发现强静态先验看不到的风险。
2. outcome 回流后，系统能自动更新机制权重、群体敏感度、传播边权和区间不确定性。
3. 该更新能跨场景 holdout，而不是只服务当前 fixture。
4. Product 可以在默认运行时安全启用该方法。

因此 R11 的目标不是继续修补 R10，而是建立一个新的方法候选：**可学习交互风险发现器**。

## 核心目标

R11 要回答的问题是：

> 在强静态先验已经可用的情况下，能否学习一个交互风险发现算子，使系统在不伤害区间和误报 guard 的前提下，更好地识别趋势方向、风险排序、异常群体和决策价值？

R11 不承诺精确单点预测。R11 的 Product 支撑目标是：

- 趋势方向：风险升高、降低或稳定。
- 可信区间：保守覆盖，不因新证据变窄而退化。
- 风险排序：哪些群体、场景或政策组合更值得关注。
- 异常群体：静态先验低估或无法识别的局部群体。
- 机制解释：风险来自价格压力、信任损伤、替代选择、社会扩散还是缓冲政策不足。
- 结果回流：真实 outcome 或 proxy outcome 回来后，更新方法而不是人工改 prompt。

## 方法定义

R11 方法由四个学习单元组成：

1. `mechanism_weight_learning`
   - 学习场景冲击如何映射到静态先验之外的风险偏移。
   - 例：价格压力、信任损伤、替代选择、补偿缓冲。

2. `segment_sensitivity_learning`
   - 学习同一冲击在不同群体上的放大或缓冲程度。
   - 例：低灵活性重复客户、价格敏感客户、高信任客户。

3. `interaction_propagation_learning`
   - 学习个体风险何时变成群体级传播、放大或极化。
   - 例：社交扩散、同质群体强化、替代选择扩散。

4. `uncertainty_interval_learning`
   - 学习保守区间策略，保证外部证据或交互信号不会伤害 interval coverage。

R11 的输入不是直接让 LLM 预测结果，而是结构化状态：

- 静态人口/客户先验。
- 场景冲击。
- 机制信号。
- 群体状态。
- 交互传播候选。
- outcome residual。
- Product guard。

LLM 可以辅助机制抽取、案例解释和 persona 文本生成，但 R11 的核心校准必须落在可计算的机制权重、群体敏感度、传播边权和区间不确定性上。

## 验收指标

R11 与 `static_prior` 和 `r10_hps_interval_guarded_overlay` 对比，至少报告：

- `trend_direction_accuracy`
- `interval_coverage`
- `risk_ranking_quality`
- `false_alarm_rate`
- `static_prior_miss_recovery_rate`
- `abnormal_segment_recall`
- `decision_value_score`

R11 允许进入下一阶段的最低条件：

1. `risk_ranking_quality` 高于 R10 guarded overlay。
2. `decision_value_score` 高于 R10 guarded overlay。
3. `interval_coverage` 不低于 R10 guarded overlay。
4. `false_alarm_rate` 不高于 R10 guarded overlay。
5. 有明确 holdout 协议。
6. 保留 `field_outcome_validated=false` 和 `runtime_default_allowed=false`。

R11 不能升级为 Product core method，除非后续同时满足：

- 独立外部 holdout 通过。
- Product runtime shadow trial 通过。
- 真实客户或 field outcome 回流后，更新候选通过 guard。
- 失败边界被记录并能被 Product failure diagnosis 消费。

## 当前 L0 MVP

当前 L0 MVP 已实现为：

- `experiments/r11_interaction_risk_discoverer.py`
- `experiments/results/r11_interaction_risk_discoverer/r11-interaction-risk-discoverer-current-001.json`
- `tests/test_r11_interaction_risk_discoverer.py`

L0 只做 controlled proxy lab，不做外部 holdout 或 field validation。

当前 L0 结果：

- `status=r11_interaction_risk_discoverer_controlled_lab_positive`
- `claim_level=controlled_proxy_lab_only`
- `risk_ranking_quality_delta=0.25`
- `decision_value_delta=0.08`
- `interval_coverage_delta=0.0`
- `false_alarm_rate_delta=0.0`
- `product_core_method_ready=false`
- `field_outcome_validated=false`
- `runtime_default_allowed=false`

这说明 R11 有一个比 R10 更接近 Product 目标的方法候选，但证据级别仍然很低。当前只能支持继续做外部 holdout 和 Product shadow trial，不能对外宣称 R11 已经支撑 Product core method。

## 当前 L1 外部 proxy holdout

当前 L1 已实现为：

- `experiments/r11_external_holdout_validation.py`
- `experiments/results/r11_external_holdout_validation/r11-external-holdout-validation-current-001.json`
- `tests/test_r11_external_holdout_validation.py`

L1 使用 HPS public-use ingestion artifact 中的两个不同 outcome proxy：

- source signal：`PRICECONCERN`
- holdout outcome proxy：`PRICESTRESS`

验证方式是把 R11 L0 学到的 `price_pressure` transfer rule 投射到 HPS segment-level public-use proxy holdout，并在 `REGION` 与 `METRO_STATUS` 两个低敏感 segment 轴上计算趋势、区间、风险排序、误报、静态先验漏报恢复和异常群体召回。

当前 L1 current result：

- `status=r11_external_holdout_validation_passed_guarded`
- `claim_level=public_use_proxy_holdout_only`
- `case_count=6`
- `trend_direction_accuracy=0.833`
- `interval_coverage=1.0`
- `risk_ranking_quality=1.0`
- `false_alarm_rate=0.0`
- `static_prior_miss_recovery_rate=1.0`
- `abnormal_segment_recall=1.0`
- `product_core_method_ready=false`
- `field_outcome_validated=false`
- `runtime_default_allowed=false`

这是一条比 L0 更强的正向信号：R11 不只是在 controlled proxy lab 中成立，也能在真实 public-use HPS proxy holdout 中保持风险排序、区间覆盖、误报和静态漏报恢复边界。但它仍不是客户 field outcome，也不能直接升级 Product core method。下一步应进入 Product shadow trial，让 Product 后台运行 R11，同时保持客户可见主结论由 guarded baseline 输出。

## 当前 L2 Product shadow trial

当前 L2 已实现为：

- `experiments/r11_product_shadow_trial.py`
- `experiments/results/r11_product_shadow_trial/r11-product-shadow-trial-current-001.json`
- `tests/test_r11_product_shadow_trial.py`
- `experiments/r6_product_customer_value_report.py` 的 `r11_shadow_trial` section
- `experiments/r6_product_api_manifest.py` 的 `/r6/product/r11-shadow-trial` endpoint

L2 的 Product 合同是：

- R11 后台运行，作为 shadow-only evidence card。
- 客户可见主结论仍由 guarded baseline customer value report 输出。
- R11 不允许覆盖 primary decision。
- R11 输出必须进入 outcome review handoff。
- 真实客户或 field outcome 回来前，不允许 runtime default。

当前 L2 current result：

- `status=r11_product_shadow_trial_ready_guarded`
- `claim_level=product_shadow_trial_only`
- `shadow_evidence_card.claim_status=shadow_only_guarded_positive`
- `customer_visible_primary_decision.r11_can_override_primary_decision=false`
- `outcome_review_handoff.requires_customer_or_field_outcome=true`
- `prompt_or_persona_manual_patch_allowed=false`
- `product_core_method_ready=false`
- `field_outcome_validated=false`
- `runtime_default_allowed=false`

Product customer value report 已新增 `r11_shadow_trial` section，API manifest 已新增 `/r6/product/r11-shadow-trial` endpoint。该能力使 Product 能展示 R11 的技术壁垒和证据进展，但仍不把 R11 包装成默认可用的核心预测方法。

## 下一阶段任务

### R11 L1：外部 holdout 映射

目标：把 R11 controlled proxy lab 转成至少一个真实 public-use 外部 holdout。

验收：

- 至少一个独立数据源或独立切片。
- 同时计算趋势、区间、风险排序、异常群体和误报。
- 不能只报告 aggregate accuracy。
- 如果 R11 未通过，必须输出 stop-loss reason。

### R11 L2：Product shadow trial

目标：让 Product 在不影响客户可见默认结论的前提下，后台同时运行 R11。

验收：

- Product report 中新增 shadow-only R11 evidence card。
- 客户可见主结论仍由 guarded baseline 输出。
- R11 输出必须绑定 artifact、source refs 和 blocked claims。
- shadow trial 记录人工复核入口和 outcome 回流入口。

当前状态：已完成。

### R11 L3：Outcome feedback update

目标：真实 outcome 或 proxy outcome 回来后，自动生成受约束的更新候选。

验收：

- 更新对象必须是机制权重、segment sensitivity、propagation edge 或 interval uncertainty。
- 不允许只更新 prompt 文案。
- 更新候选必须区分 accepted / rejected / diagnostic_only。
- 未通过 guard 时不得进入 runtime default。

### R11 L4：止损判定

目标：如果 R11 在外部 holdout 或 shadow trial 中无法稳定产生增益，应及时止损。

止损条件：

- 风险排序无法超过 R10 guarded overlay。
- false alarm 高于 R10。
- 区间覆盖退化。
- 异常群体召回不稳定。
- outcome feedback 只能 same-case 改善，不能迁移。

止损后 R11 保留为 failure diagnosis 和机制审计资产，不再作为主算法。

## Product 边界

Product 可以展示：

- R11 是新的 Research 方法候选。
- R11 在 controlled proxy lab 中有风险排序和决策价值正向信号。
- R11 的输出正在进入 shadow trial。

Product 不得展示：

- R11 已经验证。
- R11 默认支撑 Product core method。
- R11 可以精准预测单点结果。
- R11 已经 field validated。
- R11 可以直接 runtime default。
