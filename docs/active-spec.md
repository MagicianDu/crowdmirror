# Active Spec

## 当前唯一事实源

当前 Research / Product 双线的 active spec 由一个主控 spec 和一个当前阶段 addendum 组成：

- `docs/superpowers/specs/2026-06-05-r6-outcome-feedback-prior-anchored-interaction-simulation-spec.md`
- `docs/superpowers/specs/2026-06-06-r6-method-gates-transfer-protocol-spec.md`
- `docs/superpowers/specs/2026-06-11-r6-risk-discovery-method-spec.md`
- `docs/superpowers/specs/2026-06-16-r6-mechanism-driven-interaction-learning-design.md`
- `docs/superpowers/specs/2026-06-16-r6-product-first-solid-value-spec.md`
- `docs/superpowers/specs/2026-06-19-r6-trend-interval-risk-positioning.md`
- `docs/superpowers/specs/2026-06-25-r6-learning-counterfactual-method-upgrade.md`
- `docs/superpowers/specs/2026-06-25-r7-mechanism-generative-risk-simulation-spec.md`
- `docs/superpowers/specs/2026-06-26-r8-learnable-mechanism-interaction-simulation-spec.md`
- `docs/superpowers/specs/2026-06-26-r9-evidence-constrained-interaction-world-model-spec.md`
- `docs/superpowers/specs/2026-06-26-r11-learnable-interaction-risk-discoverer-spec.md`
- `docs/superpowers/specs/2026-06-26-r12-outcome-supervised-causal-interaction-operator-spec.md`

工作名：

- 中文：R12 Outcome 监督因果交互算子
- English: Outcome-Supervised Causal Interaction Operator

其中：

- `2026-06-05-r6-outcome-feedback-prior-anchored-interaction-simulation-spec.md` 定义 R6 的总体问题、方法边界和 foundation artifact chain。
- `2026-06-06-r6-method-gates-transfer-protocol-spec.md` 定义当前阶段的 evidence levels、acceptance gates、cross-case transfer protocol 和止损边界。
- `2026-06-11-r6-risk-discovery-method-spec.md` 定义 R6 下一阶段的风险发现目标、decision-value 指标和 holdout validation 协议。
- `2026-06-16-r6-mechanism-driven-interaction-learning-design.md` 定义当前 scoring candidate 止损后的方法升级方向：机制驱动交互传播、结构化 behavioral update operator、outcome-feedback learning，以及 Product guard 保留边界。
- `2026-06-16-r6-product-first-solid-value-spec.md` 定义当前降级后的真实目标：不再默认冲 CCF-A 主贡献，而是把 Research 变成有理论和学术价值的产品可信度支撑，把 Product 作为主交付目标。
- `2026-06-19-r6-trend-interval-risk-positioning.md` 定义最新目标修正：产品定位为“人群反应趋势与风险区间模拟器”，Research 不再以点预测 beat 静态先验为唯一目标，而是验证趋势判断、区间校准、风险排序、异常群体识别和决策价值。
- `2026-06-25-r6-learning-counterfactual-method-upgrade.md` 定义当前方法升级方向：用 outcome residual 学习机制层权重，并把交互仿真推进为可比较的反事实策略沙盘。
- `2026-06-25-r7-mechanism-generative-risk-simulation-spec.md` 定义新的 Research 主方法：停止把 R6 局部校准 patch 当作核心方法，转向机制状态、交互传播、分布式 rollout、策略沙盘和 outcome feedback learning。
- `2026-06-26-r8-learnable-mechanism-interaction-simulation-spec.md` 定义可学习机制因果图、交互传播算子和 outcome feedback 更新候选，并把 R7 v2 降为固定规则 baseline。
- `2026-06-26-r9-evidence-constrained-interaction-world-model-spec.md` 定义当前 Research 方法探索框架：外部证据、机制学习、多主体交互 rollout、结果反馈校准和 Product guard 的组合比较。
- `2026-06-26-r11-learnable-interaction-risk-discoverer-spec.md` 定义上一阶段 Research 主方法候选：停止继续把 R10 的 external evidence overlay 和 interval guard 包装成核心算法，转向可学习机制权重、群体敏感度、交互传播和区间不确定性的风险发现算子。
- `2026-06-26-r12-outcome-supervised-causal-interaction-operator-spec.md` 定义当前新的 Research 主方法候选：停止继续堆叠 guard、overlay 和 outcome ledger，转向 outcome 监督的因果交互算子，用 train / holdout split 验证结构化更新是否具备可迁移增益。

后续实现若与历史 R2-R11、旧 prompt/persona 优化、单一 proxy 扩张路线冲突，以 R12 当前阶段 spec 和 `docs/CURRENT_STATE.md` 为准。

## 当前目标

项目当前目标不是继续证明某个 prompt、persona、TextGrad、LCDU、R4 interaction 或 R5 mechanism-state 变体在单一静态数据集上更准，也不是把人群模拟包装成“精准预测系统”。

当前目标是：

> 基于真实人口、客户或群体先验，构建一个可审计的交互仿真沙盘，用于在政策、规则、价格、权益、服务变更发布前输出人群反应趋势方向、可信数值区间、风险分布、异常群体和机制解释，并在真实结果回流后持续校正方法。

Product 对外定位是：

> 人群反应趋势与风险区间模拟器。

当前优先级调整为 Product-first：

> Research 要扎实，但不再以 CCF-A 主贡献为默认验收目标；Research 的职责是提供清晰理论定义、证据边界、误差归因和方法护栏。Product 是当前主交付目标，必须形成有价值、好用、可审计、能说服客户的发布前风险评估与发布后复盘产品。

因此后续工作排序是：

1. 先补完整 Product 工作流：输入场景、选择人群、运行静态先验与交互仿真、展示趋势方向、风险区间、风险分布、异常群体、机制解释、证据卡，并导出决策报告。
2. 再补 Product 可信度：所有结论必须绑定 artifact、source refs、claim boundary、blocked claims 和 remaining gaps。
3. Research 继续作为技术壁垒支撑：强先验、交互传播、趋势判断、区间校准、风险排序、异常群体识别、结果反馈学习、误差归因、失败边界和可审计 gate。
4. 不再为了追逐 CCF-A 指标而牺牲产品可用性、解释性和客户工作流闭环。

本阶段宣传和验收 scope 调整为公开数据验证：

1. 当前阶段不把真实客户 field validation 作为必须完成项；客户 field slice / customer holdout 能力保留为后续企业试运行扩展。
2. 当前阶段允许的对外说法是“已在公开数据上测试并显示有效”，且必须绑定 public-data artifact、指标和 claim boundary。
3. “有效”只覆盖 guarded public-data hindcast / replay 证据中的趋势、区间、风险排序、静态先验漏报恢复、误报控制和决策价值改善；不得扩张为精准单点预测、客户 field validated 或 runtime default。
4. Product gate 必须显式暴露 `public_data_effectiveness_claim_allowed`、`customer_field_validation_required_for_current_stage=false` 和 `runtime_default_allowed=false`。
5. R13 新增规模化仿真实现边界：LLM 负责生成 segment/persona 行为规则，结构化 rollout 负责按静态先验和规则扩展到 1 万+ synthetic individuals；LLM 不按个体调用，R13 artifact 只能证明 guarded 架构链路和可审计规模化能力，不能替代 public-data validation、客户 field validation 或 runtime default 授权。

## 当前方法边界

当前 R6-R11 方法资产必须同时满足：

1. 强先验作为无交互基础状态和 no-interaction control。
2. 交互仿真用于发现静态先验无法覆盖的风险偏移。
3. 未接入真实 outcome 前，不宣称交互仿真一定更准。
4. 真实 outcome 回来后，必须生成误差归因和受约束的方法更新候选。
5. 垂直场景只能作为 case template，不能把方法过拟合到单一行业。

关键修正：

- 静态先验不是 R6 要击败的“对手”，而是大规模仿真的底座。
- 候选更新如果要进入 runtime default，必须通过不伤害静态先验的护栏。
- Research/Product 的主价值 gate 不是单一 aggregate accuracy race，也不是单点预测误差竞赛，而是：交互层是否改善趋势判断、区间校准、风险排序、异常群体识别和决策价值；是否发现静态先验看不到的风险；是否能形成可审计证据链；真实 outcome 回来后是否能学习失败边界并更新方法。

## 当前实现范围

已完成并作为 R7 基础保留的 R6 foundation：

1. `r6_prior_manifest`
2. `r6_scenario_manifest`
3. `r6_interaction_trace`
4. `r6_risk_shift_report`
5. `r6_outcome_manifest`
6. `r6_learning_report`
7. `r6_update_registry`

R6 随后已扩展到方法验收层，并形成以下 guard / baseline / Product evidence 资产。这些资产继续保留，但不再作为 Research 主方法继续 patch：

1. `cross-case transfer protocol artifact`
2. `in-condition holdout 搜索标准`
3. `Product evidence card contract`
4. `decision-value metrics`
5. `risk-discovery holdout validation`
6. `risk-discovery threshold sweep / false-alarm discriminator diagnosis`
7. `Interaction Signal Validity Score / holdout validation`
8. `mechanism-driven interaction propagation / behavioral update operator`
9. `Product API manifest / source registry contract`
10. `trend / interval / risk metrics`
11. `Research -> Product value support matrix`
12. `Product customer value report`
13. `Product frontend demo / source-backed customer report UI`
14. `Research -> Product support gap ledger / next research task contract`
15. `Research next task execution artifact`
16. `Learning counterfactual mechanism simulator / policy comparison artifact`

当前 R7 第一阶段已完成并保留为 R9 baseline：

1. `r7_mechanism_state_manifest`
2. `r7_interaction_graph_manifest`
3. `r7_rollout_distribution`
4. `r7_risk_interval_report`
5. `r7_segment_anomaly_report`
6. `r7_counterfactual_policy_sandbox`
7. `r7_outcome_feedback_update_candidate`
8. `r7_product_support_report`

不再把“继续增加 public proxy 数量”作为默认目标；只有当新增数据能触发 acceptance gate，才进入数据接入。

当前 R9 已完成：

1. `r9_world_model_manifest`
2. `r9_route_outputs`
3. `r9_combination_matrix`
4. `r9_product_support_gate`
5. `r9_combination_comparison`
6. `r9_synthetic_mechanism_lab`
7. `r9_false_alarm_gate_redesign`
8. `r9_holdout_guard`
9. `r9_method_support` Product ingestion
10. `r6_product_r9_diagnostic_workflow`

R9 当前结论是 guarded diagnostic candidate：`A+B+C` 有 current fixture 与 synthetic lab 正向信号，但 `field_outcome_validated=false`、`runtime_default_allowed=false`，不能声明 Product core method 已成立。

当前 R10 L0 已完成：

1. `r10_external_evidence_registry`

R10 L0 只建立外部官方公开数据源候选 registry，覆盖 Census HPS、BTS O&D/DB1B 和 DOT Air Travel Consumer Reports。它的作用是为后续路线 B 语义先例检索、路线 A 证据约束机制算子和路线 C 交互 rollout 提供 source-backed 输入；它没有完成真实 public data ingestion，不能声明 field outcome validation 或 Product core method 支撑。

当前 R10 L1 已完成：

1. `r10_hps_policy_reaction_ingestion`

R10 L1 已读取 Census 官方 HTOPS/HPS March 2026 PUF CSV zip，形成真实 public-use survey outcome proxy artifact。该 artifact 可以作为 R10 路线 B 语义先例检索和路线 A 机制算子的外部证据输入，但它仍不是 field outcome validation，也没有完成方法效果比较。

当前 R10 L2 已完成：

1. `r10_hps_precedent_retrieval`

R10 L2 已把 HPS ingestion artifact 转成 route B semantic precedent retrieval 输入，包括 source-backed precedent case、低敏感 segment risk ranking 和 trend/interval/ranking metric candidates。它证明外部证据可以进入方法链路，但尚未证明该证据能提升 R9/R10 combination 的效果。

当前 R10 L3 已完成：

1. `r10_hps_combination_comparison`

R10 L3 已把 HPS route-B evidence input 接入组合比较 overlay。当前只出现 source-backed risk-ranking candidate gain，且 interval non-regression 失败，因此它不能升级 Product core method；下一步必须针对 interval regression 做 holdout/outcome mapping 或区间校准。

当前 R10 L4 已完成：

1. `r10_hps_interval_guard`

R10 L4 已把 L3 暴露的 interval regression 转成显式 guard：保留 HPS source-backed risk-ranking gain，同时用 R9 interval floor 阻断区间覆盖退化。该结果只能说明 guard 可用，不能说明 HPS route-B 已完成 field/outcome validation。

当前 R11 L0 已完成：

1. `r11_interaction_risk_discoverer`

R11 L0 已把 Research 主线从 R10 的 external evidence overlay / interval guard 切换到可学习交互风险发现器。当前 artifact `r11-interaction-risk-discoverer-current-001` 在 controlled proxy lab 中显示相对 R10 guarded overlay 的 `risk_ranking_quality_delta=0.25`、`decision_value_delta=0.08`，同时 `interval_coverage_delta=0.0`、`false_alarm_rate_delta=0.0`。这说明 R11 是一个值得继续做外部 holdout 和 Product shadow trial 的方法候选；但该结果仍是 `controlled_proxy_lab_only`，`product_core_method_ready=false`、`field_outcome_validated=false`、`runtime_default_allowed=false`。

当前 R11 L1 已完成：

1. `r11_external_holdout_validation`

R11 L1 已把 L0 controlled proxy lab 推进到 HPS public-use proxy holdout：使用 `PRICECONCERN` 作为外部信号、`PRICESTRESS` 作为 held-out outcome proxy，在 `REGION` 与 `METRO_STATUS` 两个低敏感 segment 轴上计算趋势、区间、风险排序、误报、静态先验漏报恢复和异常群体召回。当前 artifact `r11-external-holdout-validation-current-001` 为 `r11_external_holdout_validation_passed_guarded`，`trend_direction_accuracy=0.833`、`interval_coverage=1.0`、`risk_ranking_quality=1.0`、`false_alarm_rate=0.0`、`static_prior_miss_recovery_rate=1.0`、`abnormal_segment_recall=1.0`。这是一条 source-backed proxy holdout 正向信号，但仍不是客户 field outcome；`product_core_method_ready=false`、`field_outcome_validated=false`、`runtime_default_allowed=false`。

当前 R11 L2 已完成：

1. `r11_product_shadow_trial`
2. `r11_shadow_trial` Product customer report section
3. `/r6/product/r11-shadow-trial` Product API endpoint

R11 L2 已把 L1 的 public-use proxy holdout 结果接入 Product shadow trial。当前 artifact `r11-product-shadow-trial-current-001` 为 `r11_product_shadow_trial_ready_guarded`，Product customer value report 新增 `r11_shadow_trial` section，API manifest 新增 `/r6/product/r11-shadow-trial` endpoint。该能力允许 Product 展示 R11 的 shadow-only evidence card，并把后续真实 outcome 回流到 outcome review；但客户可见主结论仍由 guarded baseline 输出，`r11_can_override_primary_decision=false`、`product_core_method_ready=false`、`field_outcome_validated=false`、`runtime_default_allowed=false`。

当前 R11 L3 已完成第一版：

1. `r11_outcome_feedback_update`

R11 L3 已把 shadow trial 的 outcome review handoff 转成可计算的 bounded update ledger。当前 artifact `r11-outcome-feedback-update-current-001` 为 `r11_outcome_feedback_update_ready_guarded`，使用 `public_proxy_replay` 作为 current feedback source，生成 `mechanism_weight`、`segment_sensitivity`、`propagation_edge`、`interval_uncertainty` 四类更新候选，并覆盖 `accepted`、`rejected`、`diagnostic_only` 三类状态。当前只有 `segment_sensitivity` 候选被 accepted for shadow-only replay；`mechanism_weight` 与 `interval_uncertainty` 仍是 diagnostic-only，`propagation_edge` 因缺少直接传播证据被 rejected。该结果证明更新机制可审计，但不是客户 field outcome，也不是足以支撑 Product core method 的方法效果突破；`prompt_or_persona_manual_patch_allowed=false`、`runtime_default_allowed=false`。

当前 R12 设计已确立：

1. `r12_outcome_case_registry`
2. `r12_causal_interaction_operator`
3. `r12_outcome_supervised_update`
4. `r12_transfer_validation`
5. `r12_product_support_gate`
6. `r12_high_risk_holdout_registry`
7. `r12_high_risk_holdout_transfer_replay`
8. `r12_recall_oriented_update`
9. `r12_recall_update_false_alarm_stress_test`
10. `r12_recall_false_alarm_mitigation_candidate`
11. `r12_recall_mitigation_holdout_validation`
12. `r12_recall_mitigation_independent_holdout_data`
13. `r12_recall_mitigation_external_holdout_ingestion_or_customer_slice`
14. `r12_external_or_customer_holdout_raw_slice`
15. `r12_recall_mitigation_external_holdout_revalidation`
16. `r12_pre_outcome_or_independent_prediction_packet`

17. `r12_independent_hindcast_revalidation`
18. `r12_pre_outcome_prediction_trial_or_customer_field_revalidation`
19. `r12_pre_outcome_or_customer_field_outcome_ingestion`
20. `r12_pre_outcome_or_customer_field_outcome_revalidation`
21. `r12_target_outcome_or_customer_field_slice_arrival`
22. `r12_customer_field_slice_handoff_package`
23. `r12_customer_field_slice_intake_validation`
24. `r12_customer_field_slice_revalidation`
25. `r12_customer_field_outcome_feedback_update`
26. `r12_customer_feedback_update_shadow_replay`
27. `r12_customer_feedback_shadow_replay_holdout_review`
28. `r12_customer_validation_workflow_status`
29. `r12_customer_trial_readiness_package`
30. `r12_customer_trial_operational_check`
31. `r12_customer_trial_launch_handoff_package`
32. `r12_customer_trial_launch_packet_export`
33. `r12_customer_trial_launch_bundle_verification`

当前 R13 已完成第一版 guarded 规模化 rollout：

1. `r13_llm_rule_structured_rollout`

R13 把 LLM 的位置收束为 segment/persona 行为规则生成，把规模扩展交给结构化 rollout。当前 artifact `r13-llm-rule-structured-rollout-current-001` 已覆盖 10,000 个 synthetic individuals、3 个 segment、趋势方向、风险区间、风险分布、异常群体、机制摘要、LLM 调用次数和 runtime guard。current artifact 使用 `offline_fixture_llm_shape` 规则源验证链路，真实 provider 运行需通过 operator 显式 `--execute-llm`；`field_outcome_validated=false`、`runtime_default_allowed=false` 边界继续保留。

R12 不再把 R11 L3 的 bounded update ledger 继续包装成方法突破，而是把下一阶段 Research 目标改为 outcome-supervised causal interaction operator：用 train split outcome residual 监督机制权重、群体敏感度、传播边权和区间不确定性更新，再用 validation / holdout split 验证更新是否可迁移。R12 的关键指标是 `update_transfer_gain`，并继续要求 `interval_coverage_delta >= 0`、`false_alarm_rate_delta <= 0`、`runtime_default_allowed=false`。如果只产生 same-case improvement，必须判定为 `r12_update_transfer_blocked_same_case_only`。

当前 R12 L0-L32 已完成：

1. `r12_outcome_case_registry`
2. `r12_causal_interaction_operator`
3. `r12_outcome_supervised_update`
4. `r12_transfer_validation`
5. `r12_product_support_gate`
6. `r12_high_risk_holdout_registry`
7. `r12_high_risk_holdout_transfer_replay`
8. `r12_recall_oriented_update`
9. `r12_recall_update_false_alarm_stress_test`
10. `r12_recall_false_alarm_mitigation_candidate`
11. `r12_recall_mitigation_holdout_validation`
12. `r12_recall_mitigation_independent_holdout_data`
13. `r12_recall_mitigation_external_holdout_ingestion_or_customer_slice`
14. `r12_external_or_customer_holdout_raw_slice`
15. `r12_recall_mitigation_external_holdout_revalidation`
16. `r12_pre_outcome_or_independent_prediction_packet`
17. `r12_independent_hindcast_revalidation`
18. `r12_pre_outcome_prediction_trial_or_customer_field_revalidation`
19. `r12_pre_outcome_or_customer_field_outcome_ingestion`
20. `r12_pre_outcome_or_customer_field_outcome_revalidation`
21. `r12_target_outcome_or_customer_field_slice_arrival`
22. `r12_customer_field_slice_handoff_package`
23. `r12_customer_field_slice_intake_validation`
24. `r12_customer_field_slice_revalidation`
25. `r12_customer_field_outcome_feedback_update`
26. `r12_customer_feedback_update_shadow_replay`
27. `r12_customer_feedback_shadow_replay_holdout_review`
28. `r12_customer_validation_workflow_status`
29. `r12_customer_trial_readiness_package`
30. `r12_customer_trial_operational_check`
31. `r12_customer_trial_launch_handoff_package`
32. `r12_customer_trial_launch_packet_export`
33. `r12_customer_trial_launch_bundle_verification`

R12 L0 已把 R11 HPS public-use proxy holdout 的 6 个 cases 固定拆分为 train / validation / holdout，并输出 `r12-outcome-case-registry-current-001`。L0 的核心 guard 是 `outcome_leakage_blocked=true`：validation / holdout outcome 不允许进入训练。

R12 L1 已定义 causal interaction operator contract，并输出 `r12-causal-interaction-operator-current-001`。L1 定义了 `mechanism_weights`、`segment_sensitivities`、`interaction_edge_weights`、`uncertainty_parameters`、`prior_shrinkage_rules` 和 `update_bounds`，但不执行 outcome-supervised update。

R12 L2 已输出 `r12-outcome-supervised-update-current-001`：只使用 train split outcome residual，生成 accepted shadow-only `price_pressure` mechanism update，同时保留 segment diagnostic、edge rejected 和 uncertainty diagnostic 分支。它证明 R12 更新对象已从 prompt/persona 转为结构化参数，但不允许 runtime default。

R12 L3 已输出 `r12-transfer-validation-current-001`：当前 HPS public-use proxy split 上 validation MAE 从 `0.009743` 降至 `0.009312`，holdout MAE 从 `0.005104` 降至 `0.004248`，`update_transfer_gain=0.001287`，且 `interval_coverage_delta=0.0`、`false_alarm_rate_delta=0.0`。当前状态为 `r12_transfer_validation_positive_guarded`，说明 R12 有最小可迁移正向信号；但这仍不是 field/customer outcome validation，也不允许 `runtime_default_allowed=true`。

R12 L3+ 已在同一 artifact 中补齐 Product 扩展指标：risk ranking 和 decision value 在 validation / holdout 上没有回归，但 static-prior miss recovery 与 abnormal segment recall 的 holdout eligible case count 都为 `0`。因此当前扩展支持等级为 `guarded_mae_positive_extended_metric_coverage_gap`：R12 有 MAE 层正向迁移，但还没有覆盖 Product 最关键的静态漏报恢复和异常群体验证。

R12 L4 已输出 `r12-product-support-gate-current-001`，并接入 `r6-product-customer-value-report-current-001`、`r6-product-api-manifest-current-001` 和 `/demo/`。Product 现在可以展示 `r12_transfer_evidence` section、`/r6/product/r12-transfer-evidence` endpoint 和“R12 迁移验证”面板，并展示 L3+ 扩展指标覆盖 gap。但 R12 输出角色被固定为 `secondary_transfer_evidence_card_only`，`r12_can_override_primary_decision=false`，主决策仍来自 guarded baseline。

R12 L5 已输出 `r12-high-risk-holdout-registry-current-001`，并刷新 `r12-product-support-gate-current-001` 与 `r6-product-customer-value-report-current-001`。L5 从当前 HPS public-use artifact 中找到了 29 个 source-backed research-only 高风险 holdout 候选，其中 12 个可用于验证 R12 update 是否恢复静态先验漏报；但 Product 默认可用的低敏感高风险 holdout 候选为 0。因此当前边界更新为：Research 可以继续做 high-risk replay / transfer validation，Product 只能展示该边界，不能宣称 `R12 Product default high-risk recovery validated`，也不能开启 runtime default。

R12 L6 已输出 `r12-high-risk-holdout-transfer-replay-current-001`，并刷新 Product gate、customer value report 和 demo。L6 在 29 个 research-only high-risk 候选上回放 R12 update：MAE 从 `0.087818` 降至 `0.084134`，但 static-prior miss recovery 与 abnormal segment recall 均未提升，false alarm 因候选集全是 observed high-risk 而不可评估。当前边界更新为：Research 有 high-risk replay 的小幅误差正向信号，但还没有证明高风险漏报恢复能力提升，Product default 继续阻断。

R12 L7 已输出 `r12-recall-oriented-update-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L7 不继续优化全局 MAE，而是把 high-risk activation margin 从 `0.03` 调整为 `0.01`，选择规则是“在 research false-alarm delta 上限 `0.08` 内最大化召回”。当前 source-backed public proxy replay 结果是：static-prior miss recovery 与 abnormal segment recall 从 `0.413793` 提升到 `0.62069`，`delta=0.206897`；false alarm rate 从 `0.097561` 升至 `0.170732`，`delta=0.073171`；precision 从 `0.75` 降至 `0.72`；interval coverage 保持 `0.8`。因此 L7 是 `research_only_recall_positive_false_alarm_tradeoff`：证明存在能提升静态先验漏报恢复的结构化阈值候选，但它没有通过 false-alarm non-regression 和 precision non-regression，仍不得进入 Product runtime default。

R12 L8 已输出 `r12-recall-update-false-alarm-stress-test-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L8 对 L7 的 activation margin 候选做 false-alarm stress：评估 70 个 HPS segment cases，其中 low-sensitive cases 为 4、protected 或高治理 cases 为 66。结论是 `r12_recall_update_false_alarm_stress_blocked_product_default`：L7 的 recall gain `+0.206897` 被保留，但 global false alarm rate `+0.073171`、precision `-0.03`；低敏感轴 false alarm 没有退化但没有 observed high-risk，因此 `low_sensitive_recall_evaluable=false`；新增 3 个 false alarm 全部集中在 `TAGE` 年龄轴，protected-sensitive false alarm delta 为 `+0.096774`。因此 Product default 继续阻断，下一步必须做 `r12_recall_false_alarm_mitigation_candidate`，而不是扩大 L7 claim。

R12 L9 已输出 `r12-recall-false-alarm-mitigation-candidate-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L9 比较多类 mitigation 候选，按“在 false alarm 与 precision 非回归条件下最大化召回保留”选择 `TAGE 58-62 activation guard`：默认 margin 仍为 `0.01`，但对 `TAGE` 的 `58-62` 年龄带回退到 guarded margin `0.03`。当前结果是 `r12_recall_false_alarm_mitigation_ready_research_guarded`：相对 baseline，mitigated recall delta 为 `+0.172414`，保留 L7 召回增益的 `0.833333`；false alarm delta 回到 `0.0`，移除 L7 新增的 3 个 false alarm；precision delta 为 `+0.059524`。代价是丢失 `hps_TAGE_60` 这个 L7 recovered case，且候选明显由当前 false-alarm band 推导，`overfit_risk=high_current_false_alarm_band_derived`。因此 L9 是 Research guarded positive mitigation，不是 Product default；其泛化验证已由 L10 执行。

R12 L10 已输出 `r12-recall-mitigation-holdout-validation-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L10 用 leave-one false-alarm band pseudo-holdout 验证 L9 的 `TAGE 58-62` guard 是否稳定：3 个 trial 中只有 1 个通过，`pass_rate=0.333333`，低于要求的 `0.666667`；两个端点 holdout `hps_TAGE_58` 与 `hps_TAGE_62` 失败，说明当前 band guard 对端点依赖明显。保守的 `TAGE family cap` 虽然稳定且 false alarm delta 为 `0.0`，但只保留 L7 召回增益的 `0.333333`，低于可接受门槛。因此 L10 结论是 `r12_recall_mitigation_holdout_validation_blocked_overfit`：L9 候选只能保留为 failure diagnosis candidate，不能作为 Product default 或 runtime default。独立 holdout / 低敏感切片 / 客户授权 outcome 的数据审计已由 L11 执行。

R12 L11 已输出 `r12-recall-mitigation-independent-holdout-data-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L11 不是方法效果验证，而是数据可用性审计：当前 HPS 同源 public proxy 中，排除 `TAGE 58-62` derivation band 后仍有 65 个 segment cases 和 5 个同源召回诊断候选，但这些不是独立数据集；低敏感切片有 4 个 cases，但 observed high-risk 为 0，不能验证低敏感召回；R10 external registry 中有 3 个官方公开候选源，但 ingestion status 都是 `candidate_source_not_ingested`；客户授权 holdout 为 0。因此 L11 状态为 `r12_recall_mitigation_independent_holdout_data_blocked_needs_external_or_customer_slice`，Product default 继续阻断。下一步是 `r12_recall_mitigation_external_holdout_ingestion_or_customer_slice`。

R12 L12 已输出 `r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L12 不是外部验证通过，而是把下一步变成可执行的数据合同：优先外部公开 holdout，客户授权切片作为 fallback。当前首选外部源是 `dot_air_travel_consumer_report_complaint_candidate`，用于服务变更 complaint-risk holdout；第二优先是 `bts_db1b_route_price_demand_candidate`，用于价格变更 revealed-demand holdout；第三优先是 `census_hps_policy_reaction_public_use_candidate`，用于政策反应 survey holdout。客户切片合同已定义 `csv/jsonl`、最少 10 个 cases、必需字段、可选字段、必须包含低敏感或客户授权轴、不得只用 L9 derivation band 作为证明。当前 `raw_external_or_customer_slice_present=false`，因此 Product default 继续阻断。下一步是 `r12_external_or_customer_holdout_raw_slice`。

R12 L13 已输出 `r12-external-or-customer-holdout-raw-slice-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L13 使用 DOT June 2026 Air Travel Consumer Report 的 April 2026 Table 3，形成 14 条 U.S. airline complaint raw holdout cases，总 observed complaint cases 为 `4839`；Hawaiian Airlines 的 38 条按 DOT 脚注作为 `source_excluded_records`，避免与 Alaska Airlines 双计。当前 `actual_public_data_ingested=true`、`raw_external_or_customer_slice_present=true`，但 `prediction_fields_present=false`、`external_holdout_revalidation_ready=false`，因此 Product default 和 runtime default 仍阻断。下一步是 `r12_recall_mitigation_external_holdout_revalidation`。

R12 L14 已输出 `r12-recall-mitigation-external-holdout-revalidation-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L14 在 DOT ATCR raw slice 上生成可计算的 proxy revalidation：静态先验为 `uniform_carrier_share_control`，interaction 预测为 `same_table_mechanism_composition_proxy`。结果显示 interaction 相对静态先验有诊断性正向信号：MAE delta `-0.004329`、interval coverage delta `+0.071429`、risk ranking quality delta `+0.25`、static-prior miss recovery delta `+0.8`；但 false alarm rate delta 为 `+0.428571`，且 `prediction_source_independent_of_observed_outcome=false`、`same_table_prediction_leakage_risk=true`。因此当前状态是 `r12_recall_mitigation_external_holdout_revalidation_blocked_prediction_proxy_only`：可以作为 Product failure diagnosis / evidence boundary 展示，不能宣称 independent external holdout validation passed、Product default、field outcome validated 或 runtime default。下一步是 `r12_pre_outcome_or_independent_prediction_packet`。

R12 L15 已输出 `r12-pre-outcome-or-independent-prediction-packet-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L15 使用 DOT May 2026 Air Travel Consumer Report 的 March 2026 Table 3 作为 April 2026 target outcome 的前一月官方独立特征源，生成 14 个 carrier-level complaint share predictions：`prediction_source_independent_of_target_outcome=true`、`target_outcome_used_for_prediction_generation=false`、`same_table_prediction_leakage_risk=false`、`matched_case_count=14`。但该 packet 是 post-hoc hindcast，不是 outcome 发生前锁定的 prediction packet：`prediction_lock_timestamp_pre_target_outcome=false`、`pre_outcome_revalidation_ready=false`。因此当前状态是 `r12_pre_outcome_or_independent_prediction_packet_ready_independent_hindcast_not_pre_registered`：可以进入 independent hindcast revalidation，但仍不能宣称 Product default、field outcome validated 或 runtime default。下一步是 `r12_independent_hindcast_revalidation`。

R12 L16 已输出 `r12-independent-hindcast-revalidation-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L16 使用 L15 的 March 2026 官方前一月独立预测包，对 L13 的 April 2026 DOT target outcome 做 independent-feature hindcast revalidation。当前结果相对静态均匀先验有明确正向诊断信号：MAE delta `-0.062951`、interval coverage delta `+0.714286`、risk ranking quality delta `+1.0`、static-prior miss recovery delta `+1.0`、false alarm delta `0.0`、decision value delta `+0.714286`。但它仍是 post-hoc hindcast，不是 outcome 发生前锁定的真实预测：`prediction_lock_timestamp_pre_target_outcome=false`、`pre_outcome_revalidation_ready=false`、`product_default_allowed=false`。因此当前状态是 `r12_independent_hindcast_revalidation_passed_guarded_not_pre_outcome`：可以作为 Product 次级证据展示“独立特征 hindcast 比静态先验更有风险发现价值”，但不能宣称 field validation、Product default 或 runtime default。下一步是 `r12_pre_outcome_prediction_trial_or_customer_field_revalidation`。

R12 L17 已输出 `r12-pre-outcome-prediction-trial-or-customer-field-revalidation-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L17 使用 L13 的 April 2026 DOT official raw slice 作为 May 2026 target outcome 的前一月特征源，在 `2026-06-27T14:45:00Z` 锁定 14 个 carrier-level prediction shares，并同时定义客户 field slice revalidation 合同。当前 `prediction_lock_timestamp_pre_target_outcome=true`、`target_outcome_used_for_prediction_generation=false`、`customer_field_slice_contract_ready=true`，但 `target_outcome_artifact_present=false`、`pre_outcome_revalidation_ready=false`、`field_outcome_validated=false`、`product_default_allowed=false`。因此当前状态是 `r12_pre_outcome_prediction_trial_locked_outcome_pending_guarded`：R12 已从 post-hoc hindcast 推进到真正 pre-outcome trial lock，但仍必须等待 May 2026 outcome 或客户 field slice 回流后才能验证。下一步是 `r12_pre_outcome_or_customer_field_outcome_ingestion`。

R12 L18 已输出 `r12-pre-outcome-or-customer-field-outcome-ingestion-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L18 对 May 2026 target outcome 做 ingestion audit：当前官方最新可用报告仍是 `June 2026 Air Travel Consumer Report (April 2026 Data)`，预期的 `July 2026 Air Travel Consumer Report (May 2026 Data)` 尚未接入；客户 field slice 也尚未提供。当前 `pre_outcome_trial_locked=true`、`prediction_lock_timestamp_pre_target_outcome=true`、`customer_field_slice_contract_ready=true`，但 `target_public_outcome_available=false`、`target_outcome_artifact_present=false`、`customer_field_slice_present=false`、`field_or_pre_outcome_revalidation_ready=false`、`product_default_allowed=false`。因此当前状态是 `r12_pre_outcome_or_customer_field_outcome_ingestion_pending_no_target_outcome`：Product 可以展示 outcome 等待状态和客户 field 数据入口，不能宣称 pre-outcome validation passed 或 runtime default。下一步是 `r12_pre_outcome_or_customer_field_outcome_revalidation`，前提是 May 2026 DOT target outcome 或客户授权 field slice 回流。

R12 L19 已输出 `r12-pre-outcome-or-customer-field-outcome-revalidation-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L19 消费 L18 ingestion artifact，执行 fail-closed revalidation harness：当 May 2026 DOT target outcome 和客户授权 field slice 均未回流时，不计算 MAE、区间覆盖、风险排序、静态先验漏报恢复、false alarm 或 decision value，也不允许 Product default / runtime default。当前 `metrics_computed=false`、`field_or_pre_outcome_revalidation_ready=false`、`field_or_pre_outcome_revalidation_passed=false`、`target_outcome_artifact_present=false`、`customer_field_slice_present=false`、`product_default_allowed=false`。因此当前状态是 `r12_pre_outcome_or_customer_field_outcome_revalidation_blocked_no_outcome`：Product 可以展示复核器已就绪和验收指标计划，但不能宣称 pre-outcome/customer field validation passed。下一步是 `r12_target_outcome_or_customer_field_slice_arrival`。

R12 L20 已输出 `r12-target-outcome-or-customer-field-slice-arrival-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L20 把 L19 的下一步变成可执行 arrival gate：当前官方 May 2026 target outcome 尚未回流，客户 field slice 也未提供，因此 current artifact 状态是 `r12_target_outcome_or_customer_field_slice_arrival_pending_no_source`。同时 L20 已支持客户授权 `csv/jsonl` field slice 校验：只要字段齐全、至少 10 个 cases 且 `customer_approval_reference` 完整，就可以把 `field_or_pre_outcome_revalidation_ready` 打开，但仍保持 `metrics_computed=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。下一步是继续等待 target outcome 或客户 field slice；source 到达后运行真实 revalidation，而不是修改 Product claim。

R12 L21 已输出 `r12-customer-field-slice-handoff-package-current-001` 和客户 field slice 模板 `r12-customer-field-slice-template-current-001.csv`，并刷新 Product gate、customer value report、API manifest 和 demo。L21 不计算验证指标，而是把客户 outcome/field slice 回流变成可交付、可审计的 Product handoff package：要求伪匿名 case、至少 10 个 cases、必需字段齐全、`customer_approval_reference` 完整、禁止直接个人标识、禁止 manual prompt/persona patch。当前 `customer_data_request_ready=true`、`customer_field_slice_template_generated=true`，但 `metrics_computed=false`、`field_outcome_validated=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。下一步不是继续包装 claim，而是等待真实客户 field slice 或 May 2026 DOT target outcome 到达后执行 L19/L20/L21 串联复核。

R12 L22 已输出 `r12-customer-field-slice-intake-validation-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L22 是客户 field slice 到达后的 intake validator：校验必需字段、最少 10 个 cases、审批引用、直接 PII 列/值、数值字段、时间戳和重复 `case_id`，通过后只允许进入 revalidation，不允许打开 Product default。当前没有真实客户 field slice，因此 current artifact 状态为 `r12_customer_field_slice_intake_validation_pending_no_slice`，`ready_for_revalidation=false`、`metrics_computed=false`、`field_outcome_validated=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。下一步仍是等待客户授权 field slice 或 May 2026 DOT target outcome；source 到达后先过 L22 intake，再运行真实 revalidation。

R12 L23 已输出 `r12-customer-field-slice-revalidation-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L23 是通过 L22 intake 后的 customer field revalidation 计算器：如果 intake 通过，则读取客户 slice 并计算 `mean_absolute_error`、`mean_signed_error`、`risk_ranking_quality` 和 `top_quintile_overlap`；如果 intake 未通过或无 slice，则 fail-closed。当前没有 validated intake，因此 current artifact 状态为 `r12_customer_field_slice_revalidation_blocked_no_validated_intake`，`metrics_computed=false`、`field_outcome_validated=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。即使未来 field metrics 通过，Product default 仍需独立 review，不会自动打开。

R12 L24 已输出 `r12-customer-field-outcome-feedback-update-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L24 是 validated customer field outcome 之后的结构化 feedback update 候选生成器，不做人工 prompt/persona patch。当前没有 validated field outcome，因此状态为 `r12_customer_field_outcome_feedback_update_blocked_no_field_validation`，`metrics_consumed=false`、`candidate_updates_generated=false`、`candidate_count=0`、`product_default_allowed=false`、`runtime_default_allowed=false`。

R12 L25 已输出 `r12-customer-feedback-update-shadow-replay-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L25 是 L24 候选之后的 shadow replay gate：有候选时计算保守 replay 指标并区分 accepted/rejected candidate；当前没有 L24 候选，因此状态为 `r12_customer_feedback_update_shadow_replay_blocked_no_candidates`，`shadow_replay_executed=false`、`accepted_candidate_count=0`、`product_default_allowed=false`、`runtime_default_allowed=false`。

R12 L26 已输出 `r12-customer-feedback-shadow-replay-holdout-review-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L26 是 accepted shadow replay candidate 之后的独立 holdout review gate：只有存在 accepted shadow candidate 且有独立或客户批准 holdout source 时，才会执行 review；当前没有 accepted shadow candidate，因此状态为 `r12_customer_feedback_shadow_replay_holdout_review_blocked_no_shadow_candidates`，`holdout_review_executed=false`、`holdout_review_passed=false`、`independent_holdout_case_count=0`、`product_default_allowed=false`、`runtime_default_allowed=false`。

R12 L27 已输出 `r12-customer-validation-workflow-status-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L27 不验证效果，而是把 L20-L26 串成客户验证工作流状态包：展示当前 stage、next action、blocking artifact、source refs 和 operator runbook。当前 stage 为 `source_arrival_pending`，下一步是 `collect_customer_field_slice_or_wait_for_target_outcome`；因此 `field_outcome_validated=false`、`feedback_candidates_present=false`、`shadow_replay_executed=false`、`holdout_review_executed=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。Product 现在可以展示“客户数据/公开 outcome 到达后如何执行验证”的可操作闭环，但仍不能宣称 validation passed。

R12 L28 已输出 `r12-customer-trial-readiness-package-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L28 不新增验证结果，而是把 L21 的客户 field slice handoff package 和 L27 的 workflow status 打包成试运行准备包：明确当前 stage、下一步、最少 10 个 cases、7 个必需字段、2 个手工审批点、模板路径和 operator runbook。当前状态为 `r12_customer_trial_readiness_package_ready_guarded_source_pending`，`field_outcome_validated=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。Product 现在可以展示“客户试运行已经准备到可发起数据回流请求”的证据链，但仍不能宣称客户验证已通过。

R12 L29 已输出 `r12-customer-trial-operational-check-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L29 不新增验证结果，而是对 L28 试运行准备包做 operational check：确认模板路径可解析、模板必需字段齐全、source registry 全部可解析、operator runbook 命令已声明。当前状态为 `r12_customer_trial_operational_check_ready_source_pending`，`customer_trial_request_operationally_ready=true`，但 `field_outcome_validated=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。Product 现在可以展示“客户试运行包不是纸面文档，而是已通过本地可操作性检查”的证据链；真实效果仍等待客户 field slice 或 public target outcome 回流。

R12 L30 已输出 `r12-customer-trial-launch-handoff-package-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L30 不新增验证结果，而是把 L28/L29 组合成客户试运行 launch handoff package：包含数据请求、字段模板、审批清单、提交说明、operator runbook 和 claim boundary。当前状态为 `r12_customer_trial_launch_handoff_package_ready_source_pending`，`launch_handoff_ready=true`，但 `field_outcome_validated=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。Product 现在可以展示“可向客户发起 field slice 回流请求”的交付包；真实效果仍等待客户 field slice 或 public target outcome 回流。

R12 L31 已输出 `r12-customer-trial-launch-packet-export-current-001` 和客户可读 Markdown `r12-customer-trial-launch-packet-current-001.md`，并刷新 Product gate、customer value report、API manifest 和 demo。L31 不新增验证结果，而是把 L30 launch handoff package 导出成可审计的 JSON/Markdown launch packet：包含客户数据回流请求、字段模板摘要、提交说明、operator runbook、claim boundary 和验收门禁。当前状态为 `r12_customer_trial_launch_packet_export_ready_source_pending`，`launch_packet_export_ready=true`、`markdown_export_written=true`，但 `field_outcome_validated=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。Product 现在可以展示“客户试运行交付包已导出且可发送”，并在 `/demo/` 通过 source-backed `markdown_output_path` 提供打开 Markdown packet 的入口；但仍不能宣称 field validation passed。

R12 L32 已输出 `r12-customer-trial-launch-bundle-verification-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L32 不新增验证结果，而是对 L31 launch packet、L30 handoff JSON 和客户 field slice 模板做 bundle-level 文件存在性、大小和 SHA-256 校验，证明客户试运行交付物不是散落文件。当前状态为 `r12_customer_trial_launch_bundle_verification_ready_source_pending`，`launch_bundle_verified=true`、`resolved_required_item_count=4/4`、`missing_required_item_ids=[]`，但 `field_outcome_validated=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。Product 现在可以展示“客户试运行交付包完整且可审计”，并在 `/demo/` 通过客户试运行行动面板展示 current stage、客户下一步、packet 入口和 bundle verification；但仍不能宣称 field validation passed。

R12 L33 已实现 `experiments/r12_public_target_outcome_availability_refresh.py` 和 `tests/test_r12_public_target_outcome_availability_refresh.py`。L33 不新增方法效果、不宣称 target outcome 到达；它只消费 DOT 官方页面快照，刷新 `July 2026 Air Travel Consumer Report (May 2026 Data)` 是否出现，并在 target found / not found 两种情况下都保持 `target_outcome_artifact_present=false`、`field_or_pre_outcome_revalidation_ready=false`、`field_outcome_validated=false`、`product_default_allowed=false`、`runtime_default_allowed=false`，直到 raw target outcome slice 单独接入。L33 还会拒绝 `Access Denied` 或非 ATCR 页面，防止把本地抓取失败误判成 target outcome 未发布；当前本地 `curl` DOT 页面仍返回 Akamai `Access Denied`，因此没有可信 current availability artifact。

R12 L34 已输出 `r12-customer-field-slice-operator-rehearsal-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L34 不新增方法效果、不宣称客户 field validation passed；它生成合规 synthetic rehearsal field slice，调用真实 L22 intake validator，证明 `/demo/` 给出的 operator command shape 可执行。当前 `operator_command_rehearsed=true`、`sample_slice_ready_for_revalidation=true`，但 `real_customer_field_slice_submitted=false`、`metrics_computed=false`、`field_outcome_validated=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。Product 现在可以展示“operator 入口已演练”，但真实效果仍等待客户 field slice 或 public target outcome 回流。

R12 L35 已输出 `r12-customer-feedback-loop-operator-rehearsal-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L35 不新增方法效果、不宣称客户 field validation passed；它用 synthetic field slice 连续执行 L22 intake、L23 field metrics、L24 feedback update candidate generation、L25 shadow replay 和 L26 synthetic holdout review。当前 `l22_intake_validator_executed=true`、`l23_field_revalidation_executed=true`、`l24_feedback_candidates_generated=true`、`l25_shadow_replay_executed=true`、`l26_synthetic_holdout_review_executed=true`，但 `real_customer_field_slice_submitted=false`、`real_independent_holdout_present=false`、`metrics_computed_on_real_customer_slice=false`、`field_outcome_validated=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。Product 现在可以展示“真实数据到达后的完整 operator 闭环已演练”，但真实效果仍等待客户 field slice 或 public target outcome 回流。

R12 L36 已输出 `r12-customer-trial-evidence-ledger-current-001`，并刷新 Product gate、customer value report、API manifest 和 demo。L36 不新增方法效果、不宣称客户 field validation passed；它把 L32 launch bundle verification、L34 operator rehearsal 和 L35 feedback-loop rehearsal 聚合成客户试运行证据账本。当前 `customer_trial_evidence_ledger_ready=true`、`launch_bundle_verified=true`、`operator_rehearsal_executed=true`、`feedback_loop_rehearsed_l22_to_l26=true`，并显式记录 `customer_visible_readiness_evidence_count=1`、`operator_only_rehearsal_evidence_count=2`、`blocking_gap_count=3`。但 `real_customer_field_slice_submitted=false`、`metrics_computed_on_real_customer_slice=false`、`field_outcome_validated=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。Product 现在可以展示“客户试运行准备度、operator 演练和反馈闭环演练已有可审计账本”，但真实效果仍等待客户 field slice 或 public target outcome 回流。

Product `/demo/` 已新增 source-backed 试运行工作台，把客户路径拆成 `场景输入 -> 群体与先验 -> 运行闸门 -> 报告导出 -> outcome review`。工作台只读取 `apiManifest`、R12 evidence summary、launch packet/bundle gates 和 outcome revalidation readiness；它当前显示 runtime default 仍被阻断，真实 outcome/customer field slice 回流前不宣称 validation passed。

Product `/demo/` 已新增客户 field slice 本地 intake preview：客户选择 `.csv/.jsonl` 后，前端按 L22 同源规则校验字段、case 数、审批引用、PII、数值、时间戳和重复 case。校验通过只生成 `ready_for_operator_review` revalidation handoff 清单和 operator command 模板，不上传服务器、不生成 metrics、不宣称 field validation；校验失败显示错误码并保持 fail-closed。该面板现在也展示 L34 `operator_rehearsal_status` / `operator_command_rehearsed`、L35 `feedback_loop_rehearsal_status` / `l26_synthetic_holdout_review_executed` 和 L36 `customer_trial_evidence_ledger_boundary` / `blocking_gap_count`，用于说明本地 operator 链路与试运行证据账本已演练，但没有真实客户数据。

## 降权历史材料

以下材料只作为历史经验或基础设施参考，不再作为当前主线：

- LCDU / LCDU-hybrid / LCDU-LCR-SG：静态强先验、历史校准和 gate 参考。
- DCL-PRS：历史反例和诊断资产，不作为主算法。
- MCR-Gate：accepted/rejected ledger 与 failure diagnosis 基础设施。
- R4：population / environment / interaction / memory / gate artifact chain 参考。
- R5：机制解释和 Product audit 参考。
- TextGrad / DSPy / GA / prompt-persona patch：可选候选生成工具，不是主算法本体。

## 继续开发闸门

继续开发 R7 或修改 R6 guard 前必须满足：

- R7 主方法新代码和测试文件使用 `r7_` 前缀；仅在维护 R6 guard / baseline 时继续使用 `r6_` 前缀。
- R7 主方法测试优先运行 `tests/test_r7_*.py`；维护 R6 guard 时补充运行相关 `tests/test_r6_*.py`。
- 不运行或修改旧路线测试来证明 R6 成立，除非明确是在复用基础设施。
- 新增 Product 能力必须先定义 artifact/API contract 和验收测试，不能只做 demo 文案。
- Product 界面或报告不得出现无来源的静态叙事 fallback；所有客户可见结论必须来自可审计 artifact。
- Product 优先交付顺序高于继续扩展 CCF-A readiness、LCDU、TextGrad 或 prompt/persona 优化路线。
- Product 报告必须保留 claim boundary，不能展示未验证准确性宣称。
- Product 报告不得承诺精确预测单点结果；客户可见输出必须优先展示趋势方向、可信数值区间、风险分布、异常群体和机制解释。
- Product 前端必须从 current artifacts/API manifest 读取数据，缺 artifact 时 fail closed，不允许静态文案兜底。
- Research 若不能全面支撑 Product，必须输出每个 Product value 对应的当前证据、差距、下一步 research task 和验收标准；不得只给粗粒度 `partial` 结论。
- Research next task 被执行后必须落为 source-backed execution artifact，报告 task-level acceptance decision；测试通过只证明任务链路完成，不自动证明 Product core value fully supported。
- 候选更新必须通过当前阶段 addendum 定义的 evidence level 和 acceptance gate，才能从 diagnostic 升级。
- same-case outcome feedback improvement 不得直接包装成可迁移更新。
- `beat static prior` 只作为 runtime update guard 使用，不作为 R6 整体研究目标。
- `decision-value metric` 已实现不等于 R6 通过；必须同时报告 hit rate、false alarm、regret reduction 和 holdout validation。
- `interaction_delta_threshold` 调参不足以解释当前 false alarm；该历史结论已进入 R6 diagnostic baseline，R7 不再以阈值调参作为主方法。
- `false-alarm discriminator` 已实现不等于 R6 通过；当前 case/source family 候选只算 diagnostic-only，不能作为核心规则。
- `Interaction Signal Validity Score` 是当前非阈值主 gate；它必须显式排除 source/family 标签，并通过独立 holdout 或 field outcome 复核后才能从 diagnostic 升级。
- `Interaction Signal Validity holdout validation` 已实现不等于 R6 通过；当前结论是 `source_supported_count=1`、`eligible_independent_holdout_count=2`、`passed_holdout_count=0`、`contradicted_holdout_count=2`，因此正向信号仍停留在 diagnostic。
- 当前 scoring candidate 不再作为 Research 主贡献继续优化；R7 必须转向机制状态、交互传播 trace、分布式 rollout 和 outcome-feedback learning。
- 当前 behavioral update operator v3 只能作为 guarded static-fallback baseline；R6 learning counterfactual mechanism simulator 保留为 guarded diagnostic baseline，不再通过 near-threshold calibration patch 扩大 claim。
- 当前 Research 主方法候选已转向 R11 可学习交互风险发现器：R7/R8/R9/R10 保留为 baseline、failure diagnosis、external evidence input 和 conservative guard；R11 的下一步必须证明可学习交互算子能在外部 holdout 或 Product shadow trial 中产生比 guarded diagnostic 更硬的跨案例信号。
- R10 L0 external evidence registry 只能作为数据接入入口；R10 L1 必须把至少一个官方公开候选源转成可复现 ingestion artifact，报告样本量、时间窗、outcome label、segment coverage、缺失字段和 blocked claims，才允许进入方法效果比较。
- R10 L1 HPS ingestion 通过后，下一步不能停留在“数据已接入”；必须进入 route B precedent retrieval / route A evidence-constrained operator 的效果比较，继续报告 `field_outcome_validated=false` 和 `runtime_default_allowed=false`，直到有独立 holdout 或客户/field outcome。
- R10 L2 route-B precedent retrieval 通过后，下一步必须进入组合比较：将 HPS route-B evidence input 接入 R9/R10 trend、interval、risk ranking 和 decision value 候选指标；若没有 holdout/outcome mapping，仍不得升级 Product core method。
- R10 L3 combination overlay 若出现 risk-ranking gain 但 interval non-regression 失败，只能作为诊断正向信号；R10 L4 必须修复 interval regression 或明确止损为风险排序诊断资产。
- R10 L4 interval guard 通过后，下一步必须做 holdout/outcome mapping；没有独立 outcome 映射前，HPS route-B 只能作为风险排序诊断和保守区间 guard，不得成为 Product runtime default。
- R11 L3 outcome feedback update 第一版通过后，不能把 public_proxy_replay 的 bounded update 直接升级为 Product core method 或 runtime default；当前 Research 主线已切换到 R12，用 train / validation / holdout split 验证 outcome-supervised update 是否有可迁移增益。
- R11 的方法更新对象必须是机制权重、群体敏感度、传播边权或区间不确定性；不得把人工 prompt/persona 文案修改包装成自动校准。
- R12 的方法更新必须报告 same-case improvement、same-family holdout improvement、cross-family holdout improvement 和 negative transfer；如果没有 holdout gain，只能进入 diagnostic / stop-loss。
- Product 的 failure diagnosis、false-alarm gate、claim boundary、evidence cards 是新方法外层 guard，不能因为 Research 换方法而降级或移除。
