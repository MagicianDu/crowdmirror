# Current State

## 当前状态

截至 2026-06-19，项目已从 R4/R5 的静态 heldout accuracy race 转向 R6：

> 结果反馈约束的先验锚定交互仿真框架。

已提交的 R6 spec：

- commit: `2d57ad7 docs: add R6 outcome feedback simulation spec`
- file: `docs/superpowers/specs/2026-06-05-r6-outcome-feedback-prior-anchored-interaction-simulation-spec.md`

已提交的 R6 foundation：

- commit: `26edc7d feat: add R6 foundation artifact chain`
- 覆盖 `prior -> scenario -> interaction -> risk shift -> outcome -> learning -> update registry`

当前新增的 R6 第二阶段最小单元：

- `experiments/r6_case_templates.py`：3 个行业无关 fixture。
- `experiments/r6_case_matrix.py`：跨 case 跑通完整 R6 chain。
- `experiments/r6_product_report.py`：生成 Product 可消费的发布前风险和发布后复盘报告。
- `experiments/results/r6_case_matrix/r6-case-matrix-current-001.json`
- `experiments/results/r6_product_report/r6-product-report-current-001.json`

当前新增的 R6 证据升级单元：

- `experiments/r6_public_outcome_proxy.py`：将 HTOPS/HPS public-use ingestion artifact 转成 R6 public outcome proxy。
- `experiments/r6_ablation_report.py`：比较 no-interaction prior、random noise、uncalibrated interaction、prior-anchored interaction 和 same-case outcome feedback update。
- `experiments/r6_evidence_report.py`：回答当前 R6 是继续推进还是触发止损。
- `experiments/results/r6_public_outcome_proxy/r6-public-outcome-proxy-current-001.json`
- `experiments/results/r6_ablation_report/r6-ablation-report-current-001.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-001.json`

当前新增的 R6 双 proxy 证据单元：

- `experiments/results/r6_public_outcome_proxy/r6-public-outcome-proxy-anes-health-current-001.json`
- `experiments/results/r6_ablation_report/r6-ablation-report-anes-health-current-001.json`
- `experiments/results/r6_case_matrix/r6-case-matrix-current-002.json`
- `experiments/results/r6_product_report/r6-product-report-current-002.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-002.json`

当前新增的 R6 诊断收束单元：

- `experiments/r6_proxy_mapping_review.py`
- `experiments/r6_failure_boundary_report.py`
- `experiments/results/r6_proxy_mapping_review/r6-proxy-mapping-review-current-001.json`
- `experiments/results/r6_failure_boundary_report/r6-failure-boundary-report-anes-health-current-001.json`

当前新增的 R6 mechanism cap ablation 单元：

- `experiments/r6_mechanism_cap_ablation.py`
- `experiments/results/r6_mechanism_cap_ablation/r6-mechanism-cap-ablation-current-001.json`

当前新增的 R6 Product 证据链接入单元：

- `experiments/r6_product_report.py` 支持 `mechanism_cap_ablation` ingestion。
- `experiments/r6_evidence_report.py` 将 Product ingestion 纳入 acceptance gate。
- `experiments/results/r6_product_report/r6-product-report-current-003.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-003.json`

当前新增的 R6 follow-up / holdout 验证单元：

- `experiments/r6_followup_holdout_validation.py`
- `experiments/r6_evidence_report.py` 将 follow-up / holdout validation 纳入 acceptance gate。
- `experiments/results/r6_followup_holdout_validation/r6-followup-holdout-validation-current-001.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-004.json`

当前新增的 R6 第三个 public proxy 单元：

- `experiments/r6_public_outcome_proxy.py` 支持 `anes_climate_heldout`。
- `experiments/results/r6_public_outcome_proxy/r6-public-outcome-proxy-anes-climate-current-001.json`
- `experiments/results/r6_ablation_report/r6-ablation-report-anes-climate-current-001.json`
- `experiments/results/r6_followup_holdout_validation/r6-followup-holdout-validation-current-002.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-005.json`

当前新增的 R6 方法验收与迁移协议 addendum：

- `docs/superpowers/specs/2026-06-06-r6-method-gates-transfer-protocol-spec.md`
- 当前路线已从“继续补 public proxy / artifact 细节”切换到“方法定义、acceptance gates、cross-case transfer protocol 和 Product evidence card contract”。
- 后续不再把泛泛增加 proxy 数量作为推进目标；新增数据必须服务于明确 gate，例如 in-condition same-family holdout 或 outcome feedback cross-case transfer。

当前新增的 R6 方法验收实现单元：

- `experiments/r6_cross_case_transfer_protocol.py`
- `experiments/r6_in_condition_holdout_ledger.py`
- `experiments/r6_product_evidence_cards.py`
- `experiments/r6_ccfa_readiness_report.py`
- `experiments/r6_risk_discovery_value_report.py`
- `experiments/results/r6_cross_case_transfer_protocol/r6-cross-case-transfer-protocol-current-001.json`
- `experiments/results/r6_cross_case_transfer_protocol/r6-cross-case-transfer-protocol-current-002.json`
- `experiments/results/r6_in_condition_holdout_ledger/r6-in-condition-holdout-ledger-current-001.json`
- `experiments/results/r6_product_evidence_cards/r6-product-evidence-cards-current-001.json`
- `experiments/results/r6_ccfa_readiness_report/r6-ccfa-readiness-report-current-001.json`
- `experiments/results/r6_ccfa_readiness_report/r6-ccfa-readiness-report-current-002.json`
- `experiments/results/r6_risk_discovery_value_report/r6-risk-discovery-value-report-current-001.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-006.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-007.json`

当前新增的 R6 目标修正单元：

- `experiments/r6_risk_discovery_value_report.py`：把 R6 从“全局击败静态先验”修正为“静态先验底座 + 交互风险发现 + 受护栏约束的结果反馈学习”。
- 静态先验相关 gate 被拆分为两类：Research/Product 价值 gate 看风险发现、决策价值和可审计学习；runtime update gate 才要求候选更新不能伤害静态先验。

当前新增的 R6 风险发现验证单元：

- `experiments/r6_decision_value_metrics.py`
- `experiments/r6_risk_discovery_holdout_validation.py`
- `experiments/r6_risk_discovery_threshold_sweep.py`
- `experiments/r6_false_alarm_discriminator.py`
- `experiments/r6_interaction_signal_validity.py`
- `experiments/r6_interaction_signal_validity_holdout_validation.py`
- `docs/superpowers/specs/2026-06-11-r6-risk-discovery-method-spec.md`
- `docs/superpowers/specs/2026-06-16-r6-mechanism-driven-interaction-learning-design.md`
- `experiments/results/r6_decision_value_metrics/r6-decision-value-metrics-current-001.json`
- `experiments/results/r6_risk_discovery_holdout_validation/r6-risk-discovery-holdout-validation-current-001.json`
- `experiments/results/r6_risk_discovery_threshold_sweep/r6-risk-discovery-threshold-sweep-current-001.json`
- `experiments/results/r6_false_alarm_discriminator/r6-false-alarm-discriminator-current-001.json`
- `experiments/results/r6_interaction_signal_validity/r6-interaction-signal-validity-current-001.json`
- `experiments/results/r6_interaction_signal_validity_holdout_validation/r6-interaction-signal-validity-holdout-validation-current-001.json`
- `experiments/results/r6_risk_discovery_value_report/r6-risk-discovery-value-report-current-002.json`
- `experiments/results/r6_risk_discovery_value_report/r6-risk-discovery-value-report-current-003.json`
- `experiments/results/r6_risk_discovery_value_report/r6-risk-discovery-value-report-current-004.json`
- `experiments/results/r6_risk_discovery_value_report/r6-risk-discovery-value-report-current-005.json`
- `experiments/results/r6_risk_discovery_value_report/r6-risk-discovery-value-report-current-006.json`
- `experiments/results/r6_ccfa_readiness_report/r6-ccfa-readiness-report-current-003.json`
- `experiments/results/r6_ccfa_readiness_report/r6-ccfa-readiness-report-current-004.json`
- `experiments/results/r6_ccfa_readiness_report/r6-ccfa-readiness-report-current-005.json`
- `experiments/results/r6_ccfa_readiness_report/r6-ccfa-readiness-report-current-006.json`
- `experiments/results/r6_ccfa_readiness_report/r6-ccfa-readiness-report-current-007.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-008.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-009.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-010.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-011.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-012.json`

当前新增的 R6 mechanism-driven MVP 和 Product guard 集成单元：

- `experiments/r6_mechanism_propagation_trace.py`
- `experiments/r6_behavioral_update_operator.py`
- `experiments/r6_mechanism_ablation_report.py`
- `experiments/r6_operator_holdout_validation.py`
- `experiments/r6_mechanism_research_readiness_report.py`
- `experiments/r6_product_evidence_cards.py` 支持 mechanism readiness 输入并扩展 Product guard cards。
- `experiments/r6_evidence_report.py` 将 mechanism research readiness 纳入 summary、acceptance gates 和 remaining gaps。
- `experiments/results/r6_mechanism_propagation_trace/r6-mechanism-propagation-trace-current-001.json`
- `experiments/results/r6_behavioral_update_operator/r6-behavioral-update-operator-current-001.json`
- `experiments/results/r6_mechanism_ablation_report/r6-mechanism-ablation-report-current-001.json`
- `experiments/results/r6_operator_holdout_validation/r6-operator-holdout-validation-current-001.json`
- `experiments/results/r6_mechanism_research_readiness_report/r6-mechanism-research-readiness-report-current-001.json`
- `experiments/results/r6_product_evidence_cards/r6-product-evidence-cards-current-002.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-013.json`

## 已确认结论

1. 强人口/客户/群体先验不是研究对手，而是仿真底座。
2. 交互仿真的第一价值是发现静态先验盲区和二阶风险。
3. 没有真实 outcome 前，不能宣称交互仿真一定比静态先验更准。
4. 真实 outcome 回来后，系统必须能做误差归因和方法更新。
5. 垂直场景只能作为验证 case，不能成为方法定义。
6. 当前 public proxy evidence 支持继续 R6，但只能作为诊断证据，不能作为 field validation 或跨域准确性结论。
7. same-case outcome feedback update 即使降低误差，也必须保持 `blocked_same_case_only`，不能进入全局默认参数。
8. 双 proxy 结果是 mixed evidence：HTOPS public proxy 上 prior-anchored interaction 优于 no-interaction prior；ANES health heldout proxy 上 prior-anchored interaction 劣于 no-interaction prior。
9. 当前结论不是“R6 稳定正效应成立”，而是“R6 已能发现正向信号和失败边界，值得继续但必须做跨 proxy/holdout 约束”。
10. HTOPS 与 ANES 的 proxy mapping 已形成审计记录，二者都只能作为 bounded reject proxy，不能当作 field outcome 或直接态度真值。
11. ANES health 失败边界已定位为 `interaction_over_amplifies_rejection_risk`：当静态先验已经接近 public proxy 时，rights/rule interaction profile 的 rejection amplification 会过冲。
12. mechanism cap ablation 形成一个诊断候选：当 `static_prior_error <= 0.03` 且目标属于 rights/rule change 时，将 aggregate reject delta 限制到 `0.02`，可以把 ANES heldout proxy 的 prior-anchored error 从 `0.05` 降到 `0.00`，同时不影响 HTOPS proxy 上的正向信号。
13. 上述 cap 仍是 `diagnostic_only`，`global_update_status=blocked_until_follow_up_holdout`；它证明 R6 能做失败归因和候选修复，但还不能宣称机制更新已通过全局验收。
14. Product report 已能展示完整证据链：`pre_release_risk_shift -> public_proxy_failure_boundary -> mechanism_cap_candidate`；其中 mechanism cap 的 `claim_status=diagnostic_candidate_not_runtime_default`，`default_runtime_enabled=false`。
15. Evidence report 已将 Product ingestion 纳入 gate：`product_report_ingests_mechanism_cap=true`；旧的 `needs_product_demo_report_ingestion` 与 `needs_public_proxy_mapping_review` gap 不再保留。
16. follow-up / holdout validation 的当前结论是 `holdout_validation_partial`：mechanism cap 在 ANES source case 上修复失败，并在 HTOPS cross-proxy holdout 上不回归，但缺少同 family 的 rights/rule holdout，因此 `global_update_accepted=false`。
17. outcome feedback update 在两个 public proxy 上都降低了 same-case error，但仍是 `blocked_same_case_only`；当前没有 cross-case transfer protocol，不能进入全局更新。
18. 第三个 public proxy `anes_climate_heldout` 已接入：它是同 ANES public-use、不同政策域的 climate-energy regulation heldout，映射到 `generic-rights-rule-change` 的 bounded reject proxy，`observed_reject_proxy=0.25`。
19. 第三个 proxy 让 holdout 结论更精确：当前不是“没有同 family holdout”，而是“同 family holdout 可用，但不覆盖 cap 触发条件”。在 climate holdout 上 static prior error 为 `0.06`，高于 cap 条件阈值 `0.03`，因此 `mechanism_cap_same_family_cap_condition_covered=false`、`global_update_accepted=false`。
20. 三个 public proxy 的整体证据仍是 mixed evidence：HTOPS 上 prior-anchored interaction 为正向，ANES health 与 ANES climate 上都是 regression；因此 R6 只能继续作为有约束风险发现框架推进，不能宣称稳定预测准确性。
21. 当前工作没有偏离 R6 主线，但已到达细节扩张边界；继续堆 proxy 或 JSON 变体收益不足，必须转向方法验收层。
22. 当前 R6 最强主张是：它已经形成能连接强先验、交互风险偏移、结果反馈、失败边界和受约束更新的可审计框架；静态先验是仿真底座，交互层负责发现静态先验看不到的发布前风险和二阶影响。
23. mechanism cap 当前处于 `L3 partial`：source case 修复成立，部分 holdout 不回归，但缺少覆盖 cap 触发条件的独立同 family holdout，不能进入 runtime default。
24. outcome feedback 当前处于 `L2 same-case improvement`：两个 public proxy 上 same-case error 均下降，但缺少 cross-case transfer protocol，不能宣称可迁移优化。
25. cross-case transfer protocol 已实现：mechanism cap 的 ANES health -> HTOPS 是 `non_regression_only`，ANES health -> ANES climate 是 `condition_not_covered`；因此 mechanism cap 仍不是 L4。
26. outcome feedback residual transfer 已实现：ANES health -> ANES climate 和 ANES climate -> ANES health 都能降低 prior-interaction error，但未通过 runtime update guard，因此不能升级为全局自动校准方法；这不等于 R6 风险发现主线失败。
27. in-condition holdout ledger 已实现：当前 `in_condition_holdout_count=0`，ANES health 是 source case，ANES climate 是 same-family 但 out-of-condition，HTOPS 是 out-of-family。
28. Product evidence card contract 已实现：当前 7 张卡包含原有 5 张 base cards 和 2 张 mechanism guard cards，均含 `claim_status`、`allowed_claims`、`blocked_claims`、`source_artifact_ids`，并明确 `static_narrative_fallback_allowed=false`。
29. CCF-A readiness report 已实现，当前结论是 `ccf_a_main_contribution_ready=false`；R6 还没有达到 CCF-A 级主贡献算法水准，核心缺口改为形式化问题与理论、风险发现 holdout validation、decision-value 指标、generalized interaction signal validity、signal holdout validation、field outcome validation。
30. risk-discovery value report 已实现，当前结论是 `risk_discovery_value_partial_decision_metric_failed_holdout`；R6 值得继续作为先验锚定风险发现框架推进，但 runtime default update 仍被阻断。
31. decision-value metrics 已实现，当前结论是 `decision_value_partial_high_false_alarm`：`static_prior_miss_recovery_rate=1.0`，说明 HTOPS 上存在一个静态先验漏报被交互层恢复；但 `top_k_risk_hit_rate=0.333`、`false_alarm_rate=0.667`，说明 ANES health / climate 暴露明显 false alarm。
32. risk-discovery holdout validation 已实现，当前结论是 `risk_discovery_holdout_failed_current_public_proxies`：same-family ANES health -> climate 与 climate -> health 两个 trial 都没有通过，`passed_trial_count=0`。
33. R6 当前不是失败，但也不是方法通过；更准确是“已从指标缺失推进到指标可计算，且当前指标显示 partial positive + high false alarm + holdout failed”。
34. risk-discovery threshold sweep 已实现，当前结论是 `threshold_sweep_no_separating_rule`：HTOPS 真风险和 ANES false alarm 的 `interaction_delta_vs_static` 都是 `0.07`，所以单纯调 `interaction_delta_threshold` 不能降低误报同时保留静态先验漏报恢复；后续已转向非阈值 Interaction Signal Validity 评分与 holdout/field 验证。
35. false-alarm discriminator diagnosis 已实现，当前结论是 `false_alarm_discriminator_diagnostic_only`：target case family、source family、post-outcome static error 三类候选都能在当前 3 个 public proxy 上把 1 个 HTOPS true positive 和 2 个 ANES false alarm 分开，但 `accepted_candidate_count=0`、`generalizable_discriminator_found=false`。原因是当前可分离规则本质上是 case/source family 记忆，缺少 in-family positive signal 或外部 holdout，不能作为 runtime gate 或 CCF-A 主贡献证据。
36. Interaction Signal Validity Score 已实现，当前结论是 `interaction_signal_validity_diagnostic_only`：评分特征显式排除 `source_key`、`target_case_id`、`target_case_type`，改用 `segment_pattern_score`、`mechanism_alignment_score`、`counterfactual_sensitivity_score`、`prior_uncertainty_score`、`holdout_consistency_score`。当前 HTOPS 得到 `validity_score=0.93` 且 `diagnostic_only`，ANES health / climate 得到 `validity_score=0.68` 且 `reject_as_likely_false_alarm`；这说明它比 case/source family gate 更通用，并产生了一个 current-proxy-supported 正向信号，但 `accepted_count=0`、`interaction_signal_validity_generalized=false`，仍不能宣称 R6 通过。
37. Interaction Signal Validity holdout validation 已实现，当前结论是 `interaction_signal_validity_holdout_failed_current_public_proxies`：`source_supported_count=1`、`eligible_independent_holdout_count=2`、`passed_holdout_count=0`、`contradicted_holdout_count=2`。这说明 HTOPS 上的正向交互信号目前只是 source-supported diagnostic signal，尚未在独立 public proxy holdout 上泛化；当前新增的 gate 会把该信号阻断在 CCF-A 主贡献和 runtime default 之外，直到出现独立 supported holdout 或 field outcome 支持。
38. 当前 scoring candidate 已止损为 Research 负结果和诊断基线；后续 Research 不再围绕 post-hoc score、阈值、prompt/persona patch 小修小补推进，而是转向机制驱动交互传播、结构化 behavioral update operator 和 outcome-feedback learning。
39. Product 侧的 failure diagnosis、false-alarm gate、claim boundary、evidence cards 必须保留，作为所有新 Research 方法的外层 guard；Research 方法未过 gate 时，Product 只能展示 diagnostic / blocked，不允许展示 runtime default 或 field validated 声明。
40. R6 mechanism-driven MVP 第一轮已实现，当前结论是 `mechanism_research_diagnostic_only`：机制传播 trace 能展示区别于静态先验的动态路径，但 mechanism ablation 仍是 1 个 positive、2 个 regression，behavioral update operator 被 holdout gate 阻断，不能作为 CCF-A 主贡献或 runtime default。
41. Product guard 已保留并扩展：Product evidence cards 能展示 mechanism propagation path 和 behavioral update guard，但 blocked claims 继续禁止 field validation、accuracy superiority、automatic runtime update。
42. R6.2 gap closure 第一阶段已接入 Product/evidence 链路：theory/data/method/product gap 已被结构化管理；但 `field_outcome_validated=false`、`runtime_default_allowed=false`、`ccf_a_main_contribution_ready=false`，仍不能声明 field validation 完成、runtime default 可开启或 R6 已达到 CCF-A 主贡献。
43. 项目目标已调整为 Product-first：Research 不再默认冲 CCF-A 主贡献，而是作为理论、证据边界、误差归因和方法护栏；Product 是主交付目标，后续必须补齐 scenario intake、story package、decision report 和 outcome review 闭环。
44. Product 下一阶段验收不是 demo 文案，而是 source-backed artifact/API contract：所有客户可见 claim 必须绑定 source artifact，`static_narrative_fallback_allowed=false` 继续保持。
45. Product-first 第一阶段五个合同/证据 artifacts 已落盘：readiness index、scenario intake、story package、decision report、outcome review；其中 readiness 仍是 partial，scenario/story/decision 是 guarded ready，outcome review 是 update blocked。
46. 当前可对 Product 侧声明的是“可审计决策链路已搭起”，不是“方法已 field validated”或“runtime default 可开启”；真实 outcome 回流只能生成 bounded candidate update，仍需 holdout/复核后才能默认启用。
47. Product contract readiness 已更新为 scenario/story/decision/outcome 合同就绪，但 overall readiness 仍是 `product_first_readiness_partial`；story package 和 decision report 的 source refs 已从合成 ID 修正为 canonical source registry，UI/API 可解析到已落盘 source artifact，仍不能声明 field validated 或 runtime default。
48. Product API manifest 已实现并落盘为 `r6-product-api-manifest-current-001`：它聚合 readiness、scenario intake、story package、decision report、outcome review 五个 current artifacts，暴露 endpoint contract、source registry 和 source-backed display contract；readiness 中 `needs_product_ui_or_api_contract` 已关闭。当时仍保留 `needs_customer_facing_ui_integration`、`needs_field_outcome_validation` 和 `needs_runtime_default_holdout_review`，本轮前端集成后的更新见第 51 条。
49. 产品/研究目标已进一步修正：人群模拟不再定位为“精准预测系统”，Product 对外定位改为“人群反应趋势与风险区间模拟器”；Research 不再以“点预测 beat 静态先验”为唯一目标，而是验证交互仿真是否在强静态先验基础上改善趋势判断、区间校准、风险排序、异常群体识别和决策价值。对应 active addendum 为 `docs/superpowers/specs/2026-06-19-r6-trend-interval-risk-positioning.md`。
50. Research/Product 双线补强第一轮已完成并落盘：`r6-trend-interval-risk-metrics-current-001` 显示 `trend_direction_accuracy=0.667`、`interval_coverage=0.667`、`risk_ranking_quality=0.333`、`false_alarm_rate=0.667`，因此 Research 对 Product 核心价值的支撑状态是 `product_value_support_partial`，不是 fully supported。Product 已新增 `r6-product-customer-value-report-current-001` 和 customer value report API endpoint，可展示趋势、区间、风险分布、异常群体和机制解释，但必须保留 guarded/blocked claims，不能声明精准预测、field validation 或 runtime default。
51. Product 客户可见前端第一版已实现为 `/demo/` source-backed report UI：页面从 `r6-product-customer-value-report-current-001`、`r6-research-product-value-support-current-001`、`r6-product-readiness-index-current-001` 和 `r6-product-api-manifest-current-001` 读取数据，展示趋势方向、风险区间、风险分布、异常群体、机制解释、证据边界、阻断声明和来源。`customer_facing_ui_demo_ready=true` 已写入 readiness/API/customer report artifacts；旧 gap `needs_customer_facing_ui_integration` 已收窄为 `needs_customer_workflow_runtime_integration`，仍保留 `needs_field_outcome_validation` 和 `needs_runtime_default_holdout_review`。
52. Research -> Product 支撑补齐第一步已实现为可审计 gap ledger：`r6-research-product-value-support-current-001` 现在包含 `support_coverage`、`support_gap_ledger`、`research_next_tasks`、`product_claim_support_summary` 和 `acceptance_gates`。当前结论仍是 `overall_product_core_value_supported=false`，但每个 Product value 已绑定当前指标、目标阈值、差距、阻断原因、下一步任务和验收标准。Customer value report 与 `/demo/` 前端已消费该 ledger，展示“研究支撑”面板。当前可说的是“Research 支撑合同已补齐”，不是“Research 已全面支撑 Product”。
53. 五个 `research_next_tasks` 已全部执行并落盘为 `r6-research-next-task-execution-current-001`：`all_five_tasks_executed=true`、`task_count=5`、`accepted_for_guarded_reporting_count=1`、`blocked_or_failed_count=4`。具体结论是：trend/interval holdout 在当前 public proxy 上未过阈值；false-alarm control 在 current proxy 上可把误报降到 0 但缺 holdout validation；segment outcome labels 已有 proxy-aligned audit fixture，可计算 precision/recall，但不是 field segment labels；mechanism holdout validation 仍失败；outcome feedback transfer 可改善 prior-interaction error，但未过 runtime update guard。测试通过只证明五项任务链路已执行，不代表 Research 已全面支撑 Product。
54. 由于 R6 证据链已搭好但方法本身仍偏弱，当前 Research 主线新增 `2026-06-25-r6-learning-counterfactual-method-upgrade.md`：不再继续包装旧 scoring candidate，而是转向“学习型反事实机制仿真器”。新增 `experiments/r6_learning_counterfactual_simulator.py` 用 outcome residual 学习机制层权重，并输出 counterfactual policy ranking；当前 MVP 在 public proxy fixture 上显示 `raw_interaction_false_alarm_rate=0.667` 降到 `learned_operator_false_alarm_rate=0.0`，同时保留 `static_prior_miss_recovery_rate=1.0`。该结果只能作为 current-proxy guarded positive signal，仍不是 field validation、跨域泛化或 runtime default。
55. 学习型反事实机制仿真器已补充 leave-one-case holdout 和 Product ingestion：`r6-learning-counterfactual-holdout-validation-current-001` 当前是 `learning_counterfactual_holdout_passed_guarded`。第一版 holdout 暴露的问题是 HTOPS heldout 的高风险机制在 ANES 训练集中完全未见，导致 unseen mechanisms 被置零，`static_prior_miss_recovery_rate=0.0`。随后加入 `unseen_mechanism_transfer_floor=0.65` 恢复风险发现，再加入 `risk_preserving_calibration_target=raw_interaction_prediction` 作为非回归护栏；当前结果为 `non_regression_rate=1.0`、`false_alarm_reduction_rate=1.0`、`static_prior_miss_recovery_rate=1.0`、`independent_holdout_passed=true`。这说明 current proxy leave-one-case 层面已同时保留风险发现、降低 false alarm、满足相对 raw interaction 的 non-regression；但它仍不是 field/customer outcome validation，因此 `runtime_default_allowed=false`。Product 侧已新增 `counterfactual_policy_comparison` section，并在 customer report / API manifest source registry 中绑定 simulator 与 holdout artifacts；该能力只能以 guarded / diagnostic 方式展示。
56. 学习型反事实机制仿真器已补充 calibration ablation / stress grid：`r6-counterfactual-calibration-ablation-current-001` 显示 `learned_weights_only` 只能降低 false alarm，但 `static_prior_miss_recovery_rate=0.0`；`unseen_floor_only` 能恢复 `static_prior_miss_recovery_rate=1.0`，但 `non_regression_rate=0.667`；只有 `floor_plus_non_regression_calibration` 同时达到 `non_regression_rate=1.0`、`false_alarm_reduction_rate=1.0`、`static_prior_miss_recovery_rate=1.0`。stress grid 中 8 个配置只有 2 个通过 current-proxy holdout gate，且都需要 risk-preserving calibration。因此当前正向结论应归因于“unseen mechanism floor + non-regression calibration”的受约束组合，而不是 learned mechanism weights 单独成立。
57. 学习型反事实机制仿真器已补充 local proxy robustness validation：`r6-counterfactual-robustness-validation-current-001` 当前是 `counterfactual_robustness_diagnostic_blocked`。在 9 个 observed/proxy outcome 小幅扰动场景中，8 个通过，`robustness_pass_rate=0.889`；失败场景是 `anes_health_heldout:+0.03`，此时 near-threshold false alarm 同时暴露 `non_regression_rate=0.667`、`false_alarm_reduction_rate=0.5`。这说明 current-proxy leave-one-case gate 虽已通过，但近阈值 false alarm 校准仍不稳，不能宣称 robustness 通过。
58. 由于 R6 已经暴露“证据链完整但方法强度不足”的边界，当前 Research 主线新增 `2026-06-25-r7-mechanism-generative-risk-simulation-spec.md`。R7 不继续把 near-threshold calibration patch、floor 调参或 post-hoc scoring 当作主方法，而是转向机制状态、交互传播、分布式 rollout、风险区间、异常群体、策略沙盘和 outcome feedback learning。R6 保留为 Product guard、diagnostic baseline 和 failure replay harness；R7 才是下一阶段 Research 主方法候选。当前还没有 R7 runtime 代码，下一步必须先实现 R7 artifact contract 和最小机制生成式仿真链路。
59. R7 contract-first MVP 已实现为 `experiments/r7_mechanism_generative_simulation.py`，并落盘 `r7-mechanism-generative-bundle-current-001`。该 bundle 同时包含 `r7_mechanism_state_manifest`、`r7_interaction_graph_manifest`、`r7_rollout_distribution`、`r7_risk_interval_report`、`r7_segment_anomaly_report`、`r7_counterfactual_policy_sandbox`、`r7_outcome_feedback_update_candidate` 和 `r7_product_support_report` 八个 artifact。当前结果显示 `rollout_count=50`、`no_interaction_median=0.3432`、`interaction_median=0.3657`、风险区间 `p10=0.3625 / median=0.3657 / p90=0.3682`，top policy `targeted_compensation` 将 median 降到 `0.3317`。这证明 R7 已从 R6 的后处理校准推进到可回放的机制状态 + 交互图 + rollout distribution + 策略沙盘链路，但仍只是 `r7_contract_first_mvp_ready_guarded`：`field_outcome_validated=false`、`runtime_default_allowed=false`，尚未证明真实效果优于 R6 或 fully support Product。
60. R7 effect validation 已实现为 `experiments/r7_effect_validation.py`，并落盘 `r7-effect-validation-current-001`。它用同一组 current R6 public proxy case 对比 static prior、R6 raw interaction、R6 learning counterfactual 和 R7 mechanism-generative rollout。当前结论是 `r7_effect_validation_diagnostic_blocked`：R7 的 `trend_direction_accuracy=0.667` 与 R6 raw 持平，但 `interval_coverage=0.0`、`false_alarm_rate=1.0`、`static_prior_miss_recovery_rate=0.0`、`mean_absolute_error=0.1056`，均未达到 Product 支撑要求，且弱于 R6 learning counterfactual 的 `mean_absolute_error=0.049`。具体失败边界是：HTOPS 高风险 case 中 R7 未恢复静态先验漏报；ANES health / climate 上 R7 都触发高风险，其中 health / climate 都是 false alarm；R7 区间过窄，三个 case 均未覆盖 observed/proxy outcome。因此 R7 目前只证明“机制生成式链路可审计”，尚未证明“机制生成式方法效果更强”。
61. R7 v2 guarded mechanism calibration 已接入 `experiments/r7_effect_validation.py`，并落盘 `r7-effect-validation-v2-current-001`。v2 不改写 v1 历史结论，而是在 effect validation 中加入 outcome-agnostic 的三项候选调整：`access_constraint_recovery_boost`、`rights_rule_grandfathering_buffer`、`uncertainty_interval_floor`。当前 v2 结果是 `r7_v2_effect_validation_guarded_positive_signal`：`trend_direction_accuracy=0.667` 与 R6 raw 持平，`interval_coverage=1.0`，`false_alarm_rate=0.0`，`static_prior_miss_recovery_rate=1.0`，`mean_absolute_error=0.04`，优于 R6 learning counterfactual 的 `0.049`。它恢复了 HTOPS 高风险漏报，并抑制了 ANES health / climate 的高风险误报。但该结论仍只是在 current public proxy 上成立，`field_outcome_validated=false`、`runtime_default_allowed=false`，下一步必须做 holdout/扰动/跨场景验证，防止 v2 只是对当前三例 proxy 的机制规则过拟合。
62. 由于 R7 v2 的正向信号仍主要来自固定机制修正项和区间 floor，当前 Research 主线新增 `2026-06-26-r8-learnable-mechanism-interaction-simulation-spec.md`。R8 不再把 R7 v2 继续包装成主算法，而是将其降为固定规则 baseline；新的主方法候选是“可学习机制因果图 + 交互传播算子 + outcome 反馈更新”。R8 的目标是让 outcome 回流后自动归因到机制激活、机制方向、传播边权、群体敏感度或区间不确定性，并生成受约束的 update candidate。R8 同时要求并行比较分层区间校准 baseline 和多智能体传播仿真 baseline；未通过 holdout、robustness 和 Product guard 时，`field_outcome_validated=false`、`runtime_default_allowed=false` 继续保持。

## 可复用资产

- `MCR-Gate` 的 accepted/rejected ledger 和 failure diagnosis。
- `R4` 的 task / population / environment / interaction / gate artifact chain。
- `R5` 的 mechanism state、frame shock、mechanism gate 和 Product audit 经验。
- LCDU / shrinkage prior 作为 no-interaction strong prior 参考。
- Product report contract 中的 claim boundary 和 failure diagnosis 思路。

## 不再作为主线的内容

- DCL-PRS 作为 CCF-A 主算法。
- LCDU/LCDU-LCR-SG 作为唯一主研究路线。
- TextGrad/prompt/persona patch 作为核心优化路径。
- R4/R5 当前 interaction 或 mechanism-state 作为准确性主贡献。
- 单一垂直行业 demo 作为方法本体。
- “精准预测系统”或“单点结果精确预测”作为产品承诺。
- “点预测 beat 静态先验”作为 Research 唯一验收目标。

## 当前工作区风险

旧路线未提交文件已于 2026-06-05 移出 active worktree 并归档到 repo 外部：

- `/Users/dm/Documents/cc-社会计算器-worktrees/_archives/research-r2-r5-pre-r6-cleanup-20260605-115514`

当前仍需注意三类风险：

1. 旧 README、ROADMAP、paper 草案仍可能把开发目标拉回 persona / TextGrad / LCDU。
2. `experiments/results` 被 `.gitignore` 的 `results/` 规则忽略，新 R6/R7 证据 JSON 需要显式 `git add -f`。
3. 当前 3 个 case 仍是 fixture-level evidence，不是真实跨域验证。
4. 旧 CCF-A readiness 文档只能作为边界和历史评估，不再作为默认目标；后续优先做 Product 可用性、证据链、报告和 outcome review。
5. 旧文档中如果出现“精准预测”“accuracy superiority”或“点预测 beat 静态先验”叙事，必须按当前 active spec 降权为 blocked claim 或 runtime update guard。

R7 开发或 R6 guard 维护时必须只 stage 本轮明确修改的文件。

## 下一步

1. Product 下一步在 `/demo/` source-backed report UI 基础上推进真实客户工作流：场景输入、群体/先验选择、运行入口、报告导出、outcome review 入口和用户可理解的 failure diagnosis；当前 demo 已关闭“完全没有客户可见 UI”的 gap，但还不是完整 SaaS 工作流。
2. Research 已完成 R7 contract-first 最小链路、第一轮 blocked 效果验证和 v2 guarded positive candidate；R7 v2 保留为固定规则 baseline，不再作为默认主算法继续包装。下一步转入 R8：先实现 artifact contract、可学习机制算子 MVP、baseline comparison、robustness/holdout gate 和 Product support ingestion。
3. 数据侧不再泛泛增加 proxy；新增数据必须服务于 Product decision report、outcome review、operator holdout 或 field outcome 复核。
4. 方法侧停止继续优化当前 scoring candidate；它保留为 negative baseline 和 diagnostic gate。
5. Product 侧保留并强化 `interaction_signal_validity_holdout_summary`、false-alarm diagnosis、blocked update reason 和 claim boundary，确保 R7 新方法不会污染 runtime default。
6. Research 方法侧不再优先推进 R6 learning counterfactual 的 patch 化增强；`behavioral_update_operator_v3` 和 learning counterfactual simulator 保留为 guarded static-fallback / diagnostic baseline。
7. learning counterfactual 已完成第一轮迁移失败归因和保守修复：unseen high-risk mechanism floor 能在不恢复 ANES false alarm 的前提下保留 HTOPS 类静态漏报信号，risk-preserving calibration 能把 HTOPS holdout 拉回 raw-interaction 非回归边界。但这一正向信号依赖当前 proxy 和 calibration 组合，不足以作为 Product 核心方法。
8. calibration ablation 已把组件贡献拆开；后续不能把 `floor_plus_non_regression_calibration` 包装成通用学习算法。它只能作为 R7 的 baseline、guard 或 failure replay case。
9. local robustness 已暴露 near-threshold false alarm 缺口；R7 v2 已在 current proxy 上减少 false alarm 与局部 patch 依赖，但仍不能进入 Product core claim。后续验证应在 R8 baseline comparison 中保留 v2 稳健性检查，同时重点判断可学习机制算子是否能超过固定规则修补。

## 验收边界

第一阶段验收只确认：

- artifact 合同成立；
- risk shift 相对 no-interaction 可解释；
- outcome 可回填；
- learning report 可做误差归因；
- update registry 阻断未验证更新。

第一阶段不宣称：

- 交互仿真已经比静态先验更准；
- 系统可以精确预测单点结果；
- 方法已经具备跨行业真实预测能力；
- LLM agent 交互等价于真实人群行为。
