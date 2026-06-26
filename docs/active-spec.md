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

R12 不再把 R11 L3 的 bounded update ledger 继续包装成方法突破，而是把下一阶段 Research 目标改为 outcome-supervised causal interaction operator：用 train split outcome residual 监督机制权重、群体敏感度、传播边权和区间不确定性更新，再用 validation / holdout split 验证更新是否可迁移。R12 的关键指标是 `update_transfer_gain`，并继续要求 `interval_coverage_delta >= 0`、`false_alarm_rate_delta <= 0`、`runtime_default_allowed=false`。如果只产生 same-case improvement，必须判定为 `r12_update_transfer_blocked_same_case_only`。

当前 R12 L0-L4 已完成：

1. `r12_outcome_case_registry`
2. `r12_causal_interaction_operator`
3. `r12_outcome_supervised_update`
4. `r12_transfer_validation`
5. `r12_product_support_gate`

R12 L0 已把 R11 HPS public-use proxy holdout 的 6 个 cases 固定拆分为 train / validation / holdout，并输出 `r12-outcome-case-registry-current-001`。L0 的核心 guard 是 `outcome_leakage_blocked=true`：validation / holdout outcome 不允许进入训练。

R12 L1 已定义 causal interaction operator contract，并输出 `r12-causal-interaction-operator-current-001`。L1 定义了 `mechanism_weights`、`segment_sensitivities`、`interaction_edge_weights`、`uncertainty_parameters`、`prior_shrinkage_rules` 和 `update_bounds`，但不执行 outcome-supervised update。

R12 L2 已输出 `r12-outcome-supervised-update-current-001`：只使用 train split outcome residual，生成 accepted shadow-only `price_pressure` mechanism update，同时保留 segment diagnostic、edge rejected 和 uncertainty diagnostic 分支。它证明 R12 更新对象已从 prompt/persona 转为结构化参数，但不允许 runtime default。

R12 L3 已输出 `r12-transfer-validation-current-001`：当前 HPS public-use proxy split 上 validation MAE 从 `0.009743` 降至 `0.009312`，holdout MAE 从 `0.005104` 降至 `0.004248`，`update_transfer_gain=0.001287`，且 `interval_coverage_delta=0.0`、`false_alarm_rate_delta=0.0`。当前状态为 `r12_transfer_validation_positive_guarded`，说明 R12 有最小可迁移正向信号；但这仍不是 field/customer outcome validation，也不允许 `runtime_default_allowed=true`。

R12 L3+ 已在同一 artifact 中补齐 Product 扩展指标：risk ranking 和 decision value 在 validation / holdout 上没有回归，但 static-prior miss recovery 与 abnormal segment recall 的 holdout eligible case count 都为 `0`。因此当前扩展支持等级为 `guarded_mae_positive_extended_metric_coverage_gap`：R12 有 MAE 层正向迁移，但还没有覆盖 Product 最关键的静态漏报恢复和异常群体验证。

R12 L4 已输出 `r12-product-support-gate-current-001`，并接入 `r6-product-customer-value-report-current-001`、`r6-product-api-manifest-current-001` 和 `/demo/`。Product 现在可以展示 `r12_transfer_evidence` section、`/r6/product/r12-transfer-evidence` endpoint 和“R12 迁移验证”面板，并展示 L3+ 扩展指标覆盖 gap。但 R12 输出角色被固定为 `secondary_transfer_evidence_card_only`，`r12_can_override_primary_decision=false`，主决策仍来自 guarded baseline。

R12 L5 已输出 `r12-high-risk-holdout-registry-current-001`，并刷新 `r12-product-support-gate-current-001` 与 `r6-product-customer-value-report-current-001`。L5 从当前 HPS public-use artifact 中找到了 29 个 source-backed research-only 高风险 holdout 候选，其中 12 个可用于验证 R12 update 是否恢复静态先验漏报；但 Product 默认可用的低敏感高风险 holdout 候选为 0。因此当前边界更新为：Research 可以继续做 high-risk replay / transfer validation，Product 只能展示该边界，不能宣称 `R12 Product default high-risk recovery validated`，也不能开启 runtime default。

R12 L6 已输出 `r12-high-risk-holdout-transfer-replay-current-001`，并刷新 Product gate、customer value report 和 demo。L6 在 29 个 research-only high-risk 候选上回放 R12 update：MAE 从 `0.087818` 降至 `0.084134`，但 static-prior miss recovery 与 abnormal segment recall 均未提升，false alarm 因候选集全是 observed high-risk 而不可评估。当前边界更新为：Research 有 high-risk replay 的小幅误差正向信号，但还没有证明高风险漏报恢复能力提升，Product default 继续阻断。

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
