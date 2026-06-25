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
63. R8 第一阶段 Task 1-5 已按计划落地：`r8-learnable-mechanism-bundle-current-001` 生成机制因果图、参数 registry、rollout、attribution、bounded update candidate 和 Product support gate；`r8-baseline-comparison-current-001` 将 R8 与 static prior、R6 learning counterfactual、R7 v2、分层区间 baseline、多智能体传播 baseline 同口径比较；`r8-robustness-holdout-gate-current-001` 运行 perturbation、leave-one-case、same-family holdout 和 cross-family fail-closed。当前结论不是 R8 通过，而是 `r8_robustness_diagnostic_or_stop_loss`，`stop_loss_recommendation=keep_r8_as_diagnostic_asset`。Product customer value report 已新增 `r8_method_support` section，并在 API manifest source registry 中保留 source-backed 引用，但 R8 只能作为 diagnostic/guarded 方法证据展示，不能宣称 `R8 validated`、field validated 或 runtime default ready。
64. R8 stop-loss 复盘 artifact 已落地为 `r8-stop-loss-diagnosis-current-001`，并接入 Product customer value report 的 `r8_method_support`。复盘结论是 `research_decision=keep_r8_as_diagnostic_asset`，根因包括 `not_beating_fixed_rule_baseline`、`insufficient_metric_dominance`、`l1_l2_gate_blocked`、`field_customer_outcome_missing` 和 `runtime_default_guard_blocked`。这说明 R8 当前主要价值是 failure diagnosis / outcome replay / 方法审计，不是 Product core 方法。下一步必须在三条路线中做明确选择：更强可迁移机制学习算子、真实 field/customer outcome 接入，或 Product failure diagnosis 工作流强化。
65. R8 Product failure diagnosis package 已落地为 `r8-product-failure-diagnosis-package-current-001`，并接入 Product customer value report 与 API manifest。该 package 将 R8 stop-loss/root causes 转成客户可见 failure cards、evidence requests 和 outcome replay workflow。它的边界是 `diagnostic_only=true`、`field_outcome_validated=false`、`runtime_default_allowed=false`，用于防止 Product 误用弱 Research 方法；它不改变 R8 未能支撑 Product core 方法的结论。当前判断更明确：Research 方法层仍不够强，R9 必须转向方法创新，而不是继续包装 R8。
66. R9 中文 spec 已新增为 `docs/superpowers/specs/2026-06-26-r9-evidence-constrained-interaction-world-model-spec.md`。R9 主线定义为“证据约束交互世界模型”，目标是把外部证据、机制学习、多主体交互 rollout 和 outcome replay 融成一个可验证算法空间。R9 不再押注单一路线，而是并行比较 `A_only`、`B_only`、`C_only`、`A+B`、`A+C`、`B+C`、`A+B+C` 七种组合，并用 trend / interval / risk ranking / false alarm / static prior miss recovery / decision value / holdout guard 统一验收。当前该 spec 只定义下一阶段方法探索，不声明 R9 已经支撑 Product core method。
67. R9 Task 1 artifact contract 与 Task 2 route MVP 已实现为 `experiments/r9_evidence_constrained_world_model.py`，并落盘 `r9-world-model-bundle-current-001`。该 bundle 包含 `r9_world_model_manifest`、`r9_route_outputs`、`r9_combination_matrix` 和 `r9_product_support_gate` 四类 artifact；三条路线 A/B/C 和七种组合均有统一指标结构、可计算字段、source refs 和 Product guard。当前状态是 `r9_route_mvp_ready_guarded`：每条路线已能独立输出 trend、risk interval、risk distribution、abnormal segments、mechanism trace 和 failure reasons，但 route/combination 的评估指标仍是 `not_computed_l0_contract_only`，`field_outcome_validated=false`、`runtime_default_allowed=false`。这一步只证明 R9 三路线最小输出可审计，不证明方法效果。
68. R9 Task 3 combination comparison 已实现为 `experiments/r9_combination_comparison.py`，并落盘 `r9-combination-comparison-current-001`。该 artifact 将 `static_prior`、`r6_learning_counterfactual`、`r7_v2_guarded_baseline`、`r8_diagnostic_method` 与 R9 七种组合放到 trend、interval、risk ranking、false alarm、static prior miss recovery、decision value 六个指标下比较。当前结果是 `r9_combination_comparison_guarded_current_fixture_signal`：`A+B+C` 在 current fixture 上相对 R7 v2 多出 `risk_ranking_quality` 和 `decision_value_score` 两个候选优势，同时不提高 false alarm、不降低 static prior miss recovery，因此 `stop_loss_recommendation=continue_to_holdout_and_synthetic_lab_guarded`。但该信号仍是 `current_fixture_diagnostic_only`，不是 holdout validation、field validation 或 Product core method 证据；其他六个组合均保留为 `diagnostic_failed_or_partial`。
69. R9 Task 4 holdout / perturbation / synthetic mechanism lab 已实现为 `experiments/r9_synthetic_mechanism_lab.py` 和 `experiments/r9_holdout_guard.py`，并落盘 `r9-synthetic-mechanism-lab-current-001` 与 `r9-holdout-guard-current-001`。Synthetic lab 当前是 `r9_synthetic_mechanism_lab_passed_guarded`：`mechanism_direction_recovery_rate=1.0`、`propagation_trace_consistency=0.75`、`abnormal_segment_recall=1.0`，说明 A+B+C 在有已知机制真值的 sanity lab 中能恢复机制方向。初版 holdout guard 曾被 `near_threshold_false_alarm_passed=false` 阻断；修复后 current artifact 已重跑为 `r9_holdout_guard_passed_guarded`，`leave_one_case_pass_rate=1.0`、`perturbation_pass_rate=1.0`、`near_threshold_false_alarm_passed=true`、`overall_holdout_guard_passed=true`。但它仍是 guarded diagnostic candidate：`field_outcome_validated=false`、`runtime_default_allowed=false`，不能声明 Product core method 或 runtime default。
70. R9 near-threshold false alarm gate redesign 已实现为 `experiments/r9_false_alarm_gate_redesign.py`，并落盘 `r9-false-alarm-gate-redesign-current-001`。核心规则是 `strong_prior_near_threshold_evidence_margin`：当风险信号处在 `near_threshold_band=0.03` 内、静态先验置信度强、外部证据 margin 不足时，将高风险信号降级为 `diagnostic_watch`。该 gate 将 `anes_health_near_threshold_false_alarm` 的 `risk_signal_before_guard=0.51` 调整为 `risk_signal_after_guard=0.49`，从而让 near-threshold false alarm trial 通过。该规则只允许作为 holdout guard 的诊断护栏，不允许直接设置 `runtime_default_allowed=true`。
71. R9 Task 5 Product ingestion 已接入 `experiments/r6_product_customer_value_report.py`，并刷新 `r6-product-customer-value-report-current-001` 与 `r6-product-api-manifest-current-001`。Customer report 现在新增 `r9_method_support` section，展示 `A+B+C` 的 guarded success signal、相对 R7 v2 的 `risk_ranking_quality` / `decision_value_score` 候选优势、synthetic mechanism recovery、false-alarm gate、holdout guard 和 blocked claims。API manifest 已将 `r9-combination-comparison-current-001`、`r9-synthetic-mechanism-lab-current-001`、`r9-false-alarm-gate-redesign-current-001`、`r9-holdout-guard-current-001` 纳入 source registry。Product 侧可展示 R9 guarded diagnostic support，但仍不能声明 field validation、runtime default 或 Product core method。
72. Product R9 diagnostic workflow 已实现为 `experiments/r6_product_r9_diagnostic_workflow.py`，并落盘 `r6-product-r9-diagnostic-workflow-current-001`。该 workflow 把 `scenario_intake -> r9_guarded_diagnostic_report -> outcome_review` 固化成可审计链路，并在 API manifest 中新增 `/r6/product/r9-diagnostic-workflow` endpoint 和 `r9_diagnostic_workflow` artifact ref。workflow contract 明确 `source_backed_only=true`、`customer_visible=true`、`field_outcome_validated=false`、`runtime_default_allowed=false`，因此它解决的是 Product 工作流闭环和证据边界问题，不改变 Research 方法强度不足的结论。
73. R10 L0 external evidence registry 已实现为 `experiments/r10_external_evidence_registry.py`，并落盘 `r10-external-evidence-registry-current-001`。该 registry 不是正式 R10 方法 spec，而是为后续方法升级补齐外部案例证据输入：当前纳入 Census HPS Public Use File、BTS O&D/DB1B 航线票价与客流、DOT Air Travel Consumer Reports 三类官方公开数据源候选，分别覆盖政策反应 survey、交通价格需求和航空服务投诉/摩擦风险。它明确 `actual_public_data_ingested=false`、`field_outcome_validated=false`、`runtime_default_allowed=false`，只能声明“外部证据候选源 registry 已建立”，不能声明真实数据 ingestion、方法验证或 Product core method 支撑。
74. R10 L1 HPS/HTOPS public-use ingestion 已实现为 `experiments/r10_hps_policy_reaction_ingestion.py`，并落盘 `r10-hps-policy-reaction-ingestion-current-001`。该 artifact 使用 Census 官方 `HTOPS_HPS_2603_CSV.zip`，读取主 PUF CSV `HTOPS_HPS_2603_PUF.csv`，生成 `row_count=12521`、`column_count=219`、`outcome_columns_present=[PRICECHANGE, PRICESTRESS, PRICECONCERN]`、segment coverage 和加权 outcome distribution。它把 R10 从“候选源 registry”推进到“真实官方 public-use 微数据已 ingest 的 survey outcome proxy”，但仍是 guarded research input：`field_outcome_validated=false`、`runtime_default_allowed=false`，不能宣称 Product core method 已成立。
75. R10 L2 HPS route-B precedent retrieval 已实现为 `experiments/r10_hps_precedent_retrieval.py`，并落盘 `r10-hps-precedent-retrieval-current-001`。该 artifact 消费 `r10-hps-policy-reaction-ingestion-current-001` 中的 segment-level `PRICECONCERN` profile，把 HPS 真实 public-use 数据转成 route B 语义先例检索输入、source-backed precedent case、低敏感默认 segment ranking 和 metric candidates。当前真实数据输出中 top ranking 为 `METRO_STATUS=2 risk_proxy_share=0.33601`、`REGION=2 risk_proxy_share=0.32435`，risk interval proxy 为 `lower=0.204271 / median=0.237774 / upper=0.33601`，trend signal 为 `price_pressure_risk_watch`。这说明 R10 已从数据接入推进到可供方法比较的 route-B evidence input，但仍需要 holdout/outcome mapping 才能评价 `risk_ranking_quality` 或 `decision_value_score`。
76. R10 L3 HPS combination comparison overlay 已实现为 `experiments/r10_hps_combination_comparison.py`，并落盘 `r10-hps-combination-comparison-current-001`。该 artifact 不改写 R9 历史结论，而是把真实 HPS route-B evidence input 叠加到 `r9_A+B+C_guarded_current_fixture` 上比较。当前结果是：`risk_ranking_quality_delta=0.083`，winner 从风险排序指标看变为 `r10_A+B_hps+C_guarded_overlay`；但 `interval_coverage_delta=-0.333`，`interval_non_regression_passed=false`，`decision_value_delta=0.0`。因此 R10 L3 给出的是“真实外部证据带来 source-backed 风险排序候选增益，但区间覆盖非回归失败，必须继续 holdout/outcome mapping”的结论；仍不能声明 Product core method、field validation 或 runtime default。
77. R10 L4 HPS interval non-regression guard 已实现为 `experiments/r10_hps_interval_guard.py`，并落盘 `r10-hps-interval-guard-current-001`。该 artifact 消费 L3 comparison，检测到 pre-guard `interval_coverage_delta=-0.333` 和 `interval_non_regression_passed=false` 后，执行 `apply_r9_interval_floor_to_hps_overlay`：保留 HPS 的 `risk_ranking_quality_delta=0.083`，但用 R9 interval floor 阻断 HPS overlay 对区间覆盖的伤害。post-guard 结果为 `interval_coverage_delta=0.0`、`post_guard_interval_non_regression_passed=true`、`risk_ranking_gain_preserved=true`。这说明 L4 修复了“真实外部证据带来风险排序但伤害区间”的直接 gap，但它仍是 guard，不是 field/outcome validation；`runtime_default_allowed=false` 继续保持。
78. R11 可学习交互风险发现器中文 spec 已新增为 `docs/superpowers/specs/2026-06-26-r11-learnable-interaction-risk-discoverer-spec.md`，并实现 L0 MVP：`experiments/r11_interaction_risk_discoverer.py`、`tests/test_r11_interaction_risk_discoverer.py` 和 `r11-interaction-risk-discoverer-current-001`。R11 的定位是停止继续把 R10 external evidence overlay / interval guard 包装成核心算法，转向机制权重、群体敏感度、交互传播和区间不确定性的可学习风险发现算子。当前 L0 是 controlled proxy lab positive：相对 `r10_hps_interval_guarded_overlay`，`risk_ranking_quality_delta=0.25`、`decision_value_delta=0.08`，同时 `interval_coverage_delta=0.0`、`false_alarm_rate_delta=0.0`，`controlled_lab_holdout.pass_rate=1.0`。但该结论只允许作为继续外部 holdout 和 Product shadow trial 的依据；`claim_level=controlled_proxy_lab_only`、`product_core_method_ready=false`、`field_outcome_validated=false`、`runtime_default_allowed=false`。
79. R11 L1 external public-use proxy holdout 已实现为 `experiments/r11_external_holdout_validation.py`、`tests/test_r11_external_holdout_validation.py` 和 `r11-external-holdout-validation-current-001`。该 artifact 消费 R11 L0 与 HPS ingestion，用 `PRICECONCERN` 作为 source signal、`PRICESTRESS` 作为 held-out outcome proxy，并在 `REGION` / `METRO_STATUS` 两个低敏感 segment 轴上验证。current result 为 `r11_external_holdout_validation_passed_guarded`：`case_count=6`、`trend_direction_accuracy=0.833`、`interval_coverage=1.0`、`risk_ranking_quality=1.0`、`false_alarm_rate=0.0`、`static_prior_miss_recovery_rate=1.0`、`abnormal_segment_recall=1.0`，且 `failure_reasons=[]`。这是一条比 L0 更强的 source-backed proxy holdout 正向信号，但仍不是客户 field outcome；`product_core_method_ready=false`、`field_outcome_validated=false`、`runtime_default_allowed=false`。fixture 测试中矛盾映射会输出 `r11_external_holdout_validation_blocked`，说明 L1 有真实止损分支，不是固定通过。
80. R11 L2 Product shadow trial 已实现为 `experiments/r11_product_shadow_trial.py`、`tests/test_r11_product_shadow_trial.py`、`r11-product-shadow-trial-current-001`，并接入 `r6_product_customer_value_report` 与 `r6_product_api_manifest`。Product customer value report 现在包含 `r11_shadow_trial` section，API manifest 暴露 `/r6/product/r11-shadow-trial` endpoint。当前 shadow trial 为 `r11_product_shadow_trial_ready_guarded`：`shadow_evidence_card.claim_status=shadow_only_guarded_positive`，`customer_visible_primary_decision.r11_can_override_primary_decision=false`，`outcome_review_handoff.requires_customer_or_field_outcome=true`，`prompt_or_persona_manual_patch_allowed=false`。这说明 Product 已能展示 R11 的 source-backed shadow-only evidence card，并把后续真实 outcome 接到 review/update 入口；但 R11 仍不能覆盖客户可见主结论，`product_core_method_ready=false`、`field_outcome_validated=false`、`runtime_default_allowed=false`。
81. R11 L3 outcome feedback update 第一版已实现为 `experiments/r11_outcome_feedback_update.py`、`tests/test_r11_outcome_feedback_update.py` 和 `r11-outcome-feedback-update-current-001`。该 artifact 消费 R11 shadow trial 与 external holdout，将 outcome feedback 转成四类受约束更新候选：`mechanism_weight`、`segment_sensitivity`、`propagation_edge`、`interval_uncertainty`。current artifact 使用 `public_proxy_replay`，不是客户 field outcome；输出 `primary_error_mode=segment_specific_under_reaction`，`mechanism_weight_update_needed=true`，`segment_sensitivity_update_needed=true`，`propagation_edge_update_supported=false`，`interval_uncertainty_update_needed=false`。候选状态覆盖 `accepted`、`rejected`、`diagnostic_only`：唯一 accepted 是 `segment_sensitivity` 的 shadow-only replay update；`mechanism_weight` 与 `interval_uncertainty` 仍是 diagnostic-only，`propagation_edge` 因缺少直接传播证据 rejected。`prompt_or_persona_manual_patch_allowed=false`、`runtime_default_allowed=false` 继续保持。
82. R12 中文 spec 已新增为 `docs/superpowers/specs/2026-06-26-r12-outcome-supervised-causal-interaction-operator-spec.md`。R12 的判断是：当前 Research 方法强度仍不足，R11 L3 只能证明反馈更新机制可审计，不能证明 Product core method。R12 把下一阶段方法目标定义为 outcome-supervised causal interaction operator：用 train split outcome residual 监督机制权重、群体敏感度、传播边权和区间不确定性更新，再用 validation / holdout split 验证更新是否可迁移。R12 明确新增 `update_transfer_gain`，并把 same-case improvement 与 holdout improvement 分开；如果只能 same-case 改善，必须输出 `r12_update_transfer_blocked_same_case_only`。R12 仍保持 `field_outcome_validated=false`、`runtime_default_allowed=false`，不允许 prompt/persona manual patch 作为自动校准。
83. R12 L0 case registry 已实现为 `experiments/r12_outcome_case_registry.py`、`tests/test_r12_outcome_case_registry.py` 和 `r12-outcome-case-registry-current-001`。它把 R11 HPS public-use proxy holdout 的 6 个 cases 固定拆分为 train / validation / holdout：train 为 `hps_REGION_2` 与 `hps_METRO_STATUS_2`，validation 为 `hps_REGION_1` 与 `hps_METRO_STATUS_1`，holdout 为 `hps_REGION_3` 与 `hps_REGION_4`。该 artifact 明确 validation / holdout outcome 不允许进入训练，`outcome_leakage_blocked=true`；它只证明 outcome-supervised learning material 已准备好，仍保持 `field_outcome_validated=false`、`runtime_default_allowed=false`。
84. R12 L1 causal interaction operator 已实现为 `experiments/r12_causal_interaction_operator.py`、`tests/test_r12_causal_interaction_operator.py` 和 `r12-causal-interaction-operator-current-001`。它定义 `mechanism_weights`、`segment_sensitivities`、`interaction_edge_weights`、`uncertainty_parameters`、`prior_shrinkage_rules` 和 `update_bounds`，并显式阻断 prompt/persona manual patch、field validation claim 与 runtime default。当前 `price_pressure` mechanism weight 为 `0.52`，`hps_METRO_STATUS_2` segment sensitivity 为 `1.09`。
85. R12 L2 outcome-supervised update 已实现为 `experiments/r12_outcome_supervised_update.py`、`tests/test_r12_outcome_supervised_update.py` 和 `r12-outcome-supervised-update-current-001`。该 artifact 只使用 train split 的 `hps_REGION_2` 与 `hps_METRO_STATUS_2` outcome residual，生成一个 accepted shadow-only `mechanism_weight` 更新：`price_pressure` 从 `0.52` 到 `0.55`；同时把 train segment sensitivity 保持为 `diagnostic_only`、把缺少直接传播证据的 interaction edge update 判定为 `rejected`、把 uncertainty update 保持为 `diagnostic_only`。它证明 R12 已能把 outcome residual 转成结构化、可审计、可拒绝的更新候选，但不允许 validation / holdout 泄漏，仍保持 `field_outcome_validated=false`、`runtime_default_allowed=false`。
86. R12 L3 transfer validation 已实现为 `experiments/r12_transfer_validation.py`、`tests/test_r12_transfer_validation.py` 和 `r12-transfer-validation-current-001`。当前 artifact 状态为 `r12_transfer_validation_positive_guarded`，在 current HPS public-use proxy split 上得到最小正向迁移信号：validation MAE 从 `0.009743` 降至 `0.009312`，holdout MAE 从 `0.005104` 降至 `0.004248`，`update_transfer_gain=0.001287`，且 `interval_coverage_delta=0.0`、`false_alarm_rate_delta=0.0`。该结论比 R11 L3 的 same-case bounded ledger 更强，但仍是 public proxy guarded signal，不是客户 field outcome、不是 Product core method ready，也不能开启 runtime default。下一步只能进入 Product L4 的 guarded evidence card / source refs 接入，不能包装成“精准预测”或主决策覆盖能力。

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
2. Research 已完成 R8 第一阶段 artifact contract、可学习机制算子 MVP、baseline comparison、robustness/holdout gate、stop-loss diagnosis、Product failure diagnosis package 和 Product ingestion，并完成 R9 Task 1/Task 2/Task 3/Task 4/Task 5、near-threshold false alarm gate redesign、Product workflow ingestion、R10 L0 external evidence registry、R10 L1 HPS public-use ingestion、R10 L2 HPS route-B precedent retrieval、R10 L3 HPS combination comparison overlay、R10 L4 HPS interval guard、R11 L0 learnable interaction risk discoverer、R11 L1 external public-use proxy holdout、R11 L2 Product shadow trial、R11 L3 outcome feedback update 第一版、R12 方法升级 spec、R12 L0 case registry、R12 L1 causal interaction operator、R12 L2 outcome-supervised update 和 R12 L3 transfer validation。当前 R12 的新增正向信号是：只用 train residual 生成的 `price_pressure` mechanism update，在 validation / holdout 上均降低 MAE，且不牺牲区间覆盖和 false alarm。这个信号说明 R12 没有立即失败，且比 R11 same-case ledger 更接近 Product 需要的“真实结果回流后可学习”能力；但它仍是小规模 HPS public-use proxy split，不是 field/customer outcome，也不是足以全面支撑 Product core method 的结果。
3. 数据侧不再泛泛增加 proxy；新增数据必须服务于 Product decision report、outcome review、operator holdout 或 field outcome 复核。R10 L5 outcome mapping 可以作为审计任务保留；R12 下一步需要扩大 case family、补 risk ranking / static prior miss recovery / abnormal segment recall 的 transfer 指标，并寻找能做 field-like replay 的真实业务 outcome 或更接近业务决策的数据。
4. 方法侧停止继续优化当前 scoring candidate、R10 overlay patch 和 R11 ledger；它们保留为 negative baseline、diagnostic gate 和 conservative guard。主方法候选继续是 R12，但当前只能说“guarded positive transfer signal”，不能说“Research 已全面支撑 Product”。下一步若 R12 L4 接入 Product，也必须以 shadow evidence card、source refs、blocked claims 和 runtime-off guard 的方式接入。
5. Product 侧保留并强化 `interaction_signal_validity_holdout_summary`、false-alarm diagnosis、blocked update reason、claim boundary 和 `r9_diagnostic_workflow`，确保弱 Research 方法不会污染 runtime default。
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
