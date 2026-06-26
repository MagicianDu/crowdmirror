# R12 Outcome-Supervised Causal Interaction Operator Spec

## 一句话目标

R12 的目标是把 R11 的 guarded shadow evidence 推进为一个更强的 Research 方法候选：在静态人口先验很强的前提下，用真实或准真实 outcome 反馈监督交互传播算子，使系统能够学习可迁移的机制权重、群体敏感度、传播边权和区间不确定性更新。

R12 不承诺精确单点预测，也不以简单 beat 静态先验为目标。R12 要证明的是：

> 当真实结果回流后，交互仿真层能从误差中学习出可迁移的机制更新，并在新的 holdout case 上改善趋势判断、风险排序、区间校准、异常群体识别或决策价值。

## 背景判断

R6-R11 已经建立了比较完整的 artifact、guard、Product report、API manifest 和 outcome review 基础设施，但 Research 方法本身仍不够强。

当前主要问题不是缺少更多报告，而是缺少一个可以通过 outcome 监督持续变强的算法闭环：

1. R10 的真实 HPS public-use 数据带来了 source-backed 风险排序信号，但主要是 evidence overlay 和 interval guard。
2. R11 的可学习交互风险发现器在 HPS proxy holdout 上有 guarded 正向信号，但 L3 outcome feedback update 仍是 public proxy replay 下的 bounded ledger。
3. R11 L3 能把 residual 转成 accepted / rejected / diagnostic_only 候选，但没有证明这些候选能跨 case 迁移。
4. Product 需要的是发布前风险评估和发布后复盘闭环；只有 ledger 不足以形成核心技术壁垒。

因此 R12 必须从“记录反馈”升级为“用反馈监督交互算子学习”。

## 非目标

R12 第一阶段不做以下事情：

- 不把 prompt/persona 文案更新包装成自动校准方法。
- 不宣称 `field_outcome_validated=true`。
- 不开启 `runtime_default_allowed=true`。
- 不把 public proxy replay 直接等同于客户 field outcome。
- 不再继续优化 R10 overlay patch 或 R11 ledger 本身。
- 不承诺单点精确预测。
- 不为了单一数据集指标提升而破坏 Product 的 claim boundary。

## 方法定义

R12 主方法定义为：

> Outcome-supervised causal interaction operator，简称 OSCIO。

OSCIO 由三层组成：

1. 因果交互表示层
2. outcome 监督更新层
3. 迁移验证与 Product guard 层

### 1. 因果交互表示层

R12 不直接让 LLM 或 prompt 预测人群结果，而是把每个场景表示为结构化因果交互状态：

- `scenario_shock`：政策、价格、规则、权益或服务变更。
- `static_population_prior`：无交互的强人口先验。
- `mechanism_nodes`：价格压力、权益损失、信任下降、替代选择、社交放大、服务摩擦等机制。
- `segment_nodes`：低敏感群体轴，例如地域、城市化程度、收入压力代理、出行依赖代理。
- `interaction_edges`：群体之间、机制之间、场景冲击到机制之间的传播边。
- `outcome_proxy`：真实 outcome、准真实 public-use proxy 或客户 field feedback。
- `uncertainty_state`：区间宽度、尾部风险、不确定性来源。

这一层的关键要求是所有可学习对象必须是结构化参数，而不是自然语言 prompt：

- 机制权重
- 群体敏感度
- 传播边权
- 区间不确定性
- 机制激活阈值
- 更新置信度

### 2. Outcome 监督更新层

R12 使用 outcome residual 来监督更新。

对每个已观察 case，先计算：

- 静态先验预测 `prior_prediction`
- 交互预测 `interaction_prediction`
- outcome 或 proxy `observed_outcome`
- residual `observed_outcome - interaction_prediction`
- 静态先验漏报标记
- false alarm 标记
- interval miss 标记
- segment-level error attribution

然后把 residual 归因到四类参数：

1. `mechanism_weight_update`
   - 解释机制方向和机制强度是否错了。
   - 例如价格压力机制低估导致高风险群体反应不足。

2. `segment_sensitivity_update`
   - 解释某些群体是否对同一机制反应更强或更弱。
   - 例如城市化程度、区域、收入压力代理群体的敏感度差异。

3. `interaction_edge_update`
   - 解释是否存在社交放大、替代路径或跨群体传播。
   - 只有反馈中包含直接或间接传播证据时才允许更新。

4. `uncertainty_update`
   - 解释区间是否过窄、过宽或尾部风险不足。
   - 用于保护 Product 的可信区间输出。

R12 不允许同 case 自我修补直接升级。每个更新都必须生成：

- `update_candidate`
- `evidence_level`
- `source_refs`
- `acceptance_reason`
- `rejection_reason`
- `transfer_scope`
- `holdout_requirement`
- `runtime_default_allowed=false`

### 3. 贝叶斯收缩与先验保护

R12 必须承认静态人口先验很强，因此更新不能无约束覆盖 prior。

第一阶段采用保守的层级收缩思想：

- 静态先验是基础分布。
- 交互层只能产生 bounded risk shift。
- outcome feedback 只能更新交互层参数，不直接重写人口先验。
- 小样本 update 必须向全局机制均值或强 prior 收缩。
- 当 evidence weak 或 source family 不匹配时，更新降级为 diagnostic_only。

这层的目的不是复杂建模，而是防止 Research 为了短期指标提升牺牲 Product 可信度。

## 三条路线的关系

R12 不是单一路线，而是把三条正交方法融合成一个算法空间。

### 路线 A：事件级因果反馈算子

核心：从 `shock -> mechanism -> segment -> interaction edge -> outcome` 的路径上归因 residual。

优势：

- 最贴近 Product 的机制解释。
- 能回答为什么某些群体是异常风险群体。
- 有机会形成真正的技术壁垒。

风险：

- 因果假设强。
- 如果没有 outcome 或传播证据，边权更新容易变成臆测。

### 路线 B：层级区间校准算子

核心：把静态先验作为强 prior，交互仿真作为 bounded update，用层级收缩保护区间。

优势：

- 更适合 Product 的趋势和风险区间定位。
- 对小样本更稳健。
- 能减少 false alarm 和过度更新。

风险：

- 方法创新可能偏保守。
- 如果只做校准，不足以体现交互仿真的机制价值。

### 路线 C：案例记忆与机制检索

核心：检索相似历史政策、价格或服务变更案例，提供机制候选、参数先验和解释来源。

优势：

- 有助于连接公开数据和客户解释。
- Product 报告更容易说服客户。
- 可作为 LLM 的安全使用位置：抽取机制、归纳案例，不直接输出预测。

风险：

- 容易退化成 retrieval overlay。
- 必须证明检索结果改变了结构化参数并通过 holdout，而不是只改变叙事。

R12 推荐主线是 A+B，C 作为 evidence layer：

- A 负责机制与交互创新。
- B 负责稳健性和区间可信度。
- C 负责外部案例证据、解释和参数候选来源。

## 输入 artifact

R12 第一阶段复用以下现有资产：

- `r11-interaction-risk-discoverer-current-001`
- `r11-external-holdout-validation-current-001`
- `r11-product-shadow-trial-current-001`
- `r11-outcome-feedback-update-current-001`
- `r10-hps-policy-reaction-ingestion-current-001`
- `r10-hps-precedent-retrieval-current-001`
- `r10-hps-interval-guard-current-001`
- `r9-combination-comparison-current-001`
- `r9-holdout-guard-current-001`
- `r6-product-customer-value-report-current-001`

R12 第一阶段不要求新增外部数据源，但必须把 HPS public-use proxy 从“验证材料”变成“训练/验证 split 的 outcome-supervised learning material”。

## 输出 artifact

R12 第一阶段应新增四类 artifact。

### 1. `r12_outcome_case_registry`

作用：把可用于 outcome-supervised learning 的 case 统一登记。

必须包含：

- case id
- scenario shock
- static prior prediction
- interaction prediction
- observed outcome 或 proxy
- segment labels
- mechanism labels
- source refs
- evidence level
- train / validation / holdout split
- blocked claims

### 2. `r12_causal_interaction_operator`

作用：定义可学习参数、当前参数值和参数约束。

必须包含：

- mechanism weights
- segment sensitivities
- interaction edge weights
- uncertainty parameters
- prior shrinkage rules
- update bounds
- no-prompt-persona-update guard

### 3. `r12_outcome_supervised_update`

作用：用 train split outcome residual 生成结构化更新候选。

必须包含：

- residual summary
- error attribution
- update candidates
- accepted / rejected / diagnostic_only ledger
- posterior parameter state
- transfer scope
- holdout requirement

### 4. `r12_transfer_validation`

作用：在 validation / holdout split 上验证更新是否可迁移。

必须包含：

- before / after metrics
- trend direction delta
- interval coverage delta
- risk ranking delta
- false alarm delta
- static prior miss recovery delta
- abnormal segment recall delta
- decision value delta
- update transfer gain
- stop-loss decision

## 核心指标

R12 不使用单一 accuracy 作为主指标。必须同时报告：

1. `trend_direction_accuracy`
2. `interval_coverage`
3. `risk_ranking_quality`
4. `false_alarm_rate`
5. `static_prior_miss_recovery_rate`
6. `abnormal_segment_recall`
7. `decision_value_score`
8. `update_transfer_gain`
9. `mechanism_trace_consistency`
10. `posterior_shrinkage_strength`

其中 `update_transfer_gain` 是 R12 的关键新指标。

定义：

> update_transfer_gain = 更新后 holdout 指标改善数量和改善幅度的综合分，且不能以 interval coverage 或 false alarm regression 为代价。

第一阶段可以用规则化 scoring 实现，但必须显式拆分：

- same-case improvement
- same-family holdout improvement
- cross-family holdout improvement
- negative transfer

## 第一阶段验收标准

R12 L0/L1 只能进入下一阶段，不能进入 runtime default。

最低通过条件：

1. case registry 能把 HPS proxy cases 分成 train / validation / holdout。
2. update 只能从 train split 读取 observed outcome。
3. validation / holdout 不允许泄漏 outcome 到训练。
4. 至少一个结构化参数类型出现 accepted shadow-only update。
5. accepted update 在 holdout 上带来正向 `update_transfer_gain`。
6. `interval_coverage_delta >= 0`。
7. `false_alarm_rate_delta <= 0`。
8. `risk_ranking_quality_delta > 0` 或 `static_prior_miss_recovery_rate_delta > 0` 至少一项成立。
9. 所有 Product-facing artifact 继续保持 `field_outcome_validated=false`。
10. 所有 Product-facing artifact 继续保持 `runtime_default_allowed=false`。

如果只能 same-case improvement，而 holdout 无提升，则必须判定为：

`r12_update_transfer_blocked_same_case_only`

## 止损标准

R12 必须比 R11 更严格。出现以下任一情况，应止损或降级：

1. 更新只改善 train case，不改善 holdout case。
2. 更新改善 risk ranking 但显著伤害 interval coverage。
3. 更新减少静态漏报但引入更多 false alarm。
4. accepted update 依赖 source family 标签泄漏。
5. 机制归因无法稳定复现。
6. interaction edge update 没有传播证据支持。
7. Product report 只能展示更复杂的解释，但没有更强的决策价值指标。

止损后 R12 保留为：

- failure diagnosis
- outcome review learning ledger
- Product evidence boundary
- 后续真实 field outcome 接入的准备资产

## Product 支撑边界

R12 如果第一阶段通过，只能支撑以下 Product claim：

- 系统能够把发布后 outcome feedback 转成结构化、可审计、可验证的交互参数更新候选。
- 系统能够区分 same-case improvement 和可迁移 improvement。
- 系统能够在 holdout 上报告更新是否带来趋势、区间、风险排序或异常群体识别增益。
- 系统不会把未验证更新直接进入 runtime default。

R12 第一阶段不能支撑以下 Product claim：

- 系统已经精准预测大众反应。
- 系统已经 field validated。
- 系统默认优于静态人口先验。
- 系统可以自动改 prompt/persona 完成校准。
- 系统可以无人工审查自动更新 runtime。

## LLM 的位置

R12 可以使用 LLM，但 LLM 不作为主预测器。

允许：

- 从政策文本或客户场景中抽取 mechanism candidates。
- 从历史案例中生成机制解释草稿。
- 帮助归纳 failure diagnosis。
- 辅助生成 Product 报告叙事。

不允许：

- 直接用 LLM 输出最终风险数值作为主算法结果。
- 用 LLM 自由改写 persona/prompt 作为校准。
- 用不可审计的 LLM reasoning 替代结构化 update candidate。
- 把模型输出包装成 field validation。

## 实施阶段划分

### R12 L0：Case registry 与 split contract

目标：把 HPS proxy cases 和 R11 artifacts 转成 outcome-supervised learning case registry。

当前实现：

- `experiments/r12_outcome_case_registry.py`
- `tests/test_r12_outcome_case_registry.py`
- `experiments/results/r12_outcome_case_registry/r12-outcome-case-registry-current-001.json`

当前状态为 `r12_outcome_case_registry_ready_guarded`。该 artifact 使用固定 HPS segment split：train 为 `hps_REGION_2` 与 `hps_METRO_STATUS_2`，validation 为 `hps_REGION_1` 与 `hps_METRO_STATUS_1`，holdout 为 `hps_REGION_3` 与 `hps_REGION_4`。它只证明 outcome-supervised learning material 已准备好，不证明 update transfer gain。

验收：

- split 明确。
- outcome 泄漏被阻断。
- source refs 完整。
- Product guard 仍关闭。

### R12 L1：Causal interaction operator contract

目标：定义可学习参数和 prior shrinkage 规则。

当前实现：

- `experiments/r12_causal_interaction_operator.py`
- `tests/test_r12_causal_interaction_operator.py`
- `experiments/results/r12_causal_interaction_operator/r12-causal-interaction-operator-current-001.json`

当前状态为 `r12_causal_interaction_operator_ready_guarded`。该 artifact 定义 mechanism weights、segment sensitivities、interaction edge weights、uncertainty parameters、prior shrinkage rules 和 update bounds，并阻断 prompt/persona manual patch、field validation claim 和 runtime default。它不执行 outcome-supervised update。

验收：

- 参数类型完整。
- 更新边界明确。
- prompt/persona 更新被阻断。
- interaction edge update 需要传播证据。

### R12 L2：Outcome-supervised update

目标：只用 train split residual 生成结构化更新。

当前实现：

- `experiments/r12_outcome_supervised_update.py`
- `tests/test_r12_outcome_supervised_update.py`
- `experiments/results/r12_outcome_supervised_update/r12-outcome-supervised-update-current-001.json`

当前状态为 `r12_outcome_supervised_update_ready_guarded`。该 artifact 只使用 train split 的 `hps_REGION_2` 与 `hps_METRO_STATUS_2` outcome residual，训练残差均值为 `0.041323`，生成一个 accepted shadow-only `mechanism_weight` 候选：`price_pressure` 从 `0.52` 调整到 `0.55`。同时它保留三类非升级分支：train segment sensitivity 为 `diagnostic_only`，缺少直接传播证据的 interaction edge update 为 `rejected`，interval uncertainty 为 `diagnostic_only`。

验收：

- 至少生成 mechanism 或 segment 的 accepted shadow-only update：已满足。
- rejected / diagnostic_only 分支真实存在：已满足。
- update 不写入 runtime default：已满足，`runtime_default_allowed=false`。
- validation / holdout outcome 不参与训练：已满足，`outcome_leakage_blocked=true`。

### R12 L3：Transfer validation

目标：用 validation / holdout split 验证更新是否可迁移。

当前实现：

- `experiments/r12_transfer_validation.py`
- `tests/test_r12_transfer_validation.py`
- `experiments/results/r12_transfer_validation/r12-transfer-validation-current-001.json`

当前状态为 `r12_transfer_validation_positive_guarded`。在 current HPS public-use proxy split 上，L2 的 `price_pressure=0.55` 更新得到以下 before / after 结果：

- train MAE：`0.041323 -> 0.035285`，但 train metrics 不用于 transfer decision。
- validation MAE：`0.009743 -> 0.009312`，`mean_absolute_error_delta=-0.000431`。
- holdout MAE：`0.005104 -> 0.004248`，`mean_absolute_error_delta=-0.000856`。
- `update_transfer_gain=0.001287`。
- `interval_coverage_delta=0.0`。
- `false_alarm_rate_delta=0.0`。

L3+ 已新增 Product 扩展指标：

- risk ranking quality：train / validation / holdout 均为 `1.0 -> 1.0`，未回归。
- decision value score：train / validation / holdout 均为 `1.0 -> 1.0`，未回归。
- static-prior miss recovery：train eligible case count 为 `2`，但 validation / holdout eligible case count 为 `0`。
- abnormal segment recall：train eligible case count 为 `2`，但 validation / holdout eligible case count 为 `0`。
- 当前扩展支持等级为 `guarded_mae_positive_extended_metric_coverage_gap`。

解释边界：

- 这是 R12 当前最小正向信号，说明 outcome-supervised 结构化更新没有停留在 same-case 修补。
- 正向信号主要来自 MAE 小幅改善和非回归；还没有覆盖 Product 最关键的静态漏报恢复与异常群体 holdout 验证。
- 这是 public proxy split，不是客户 field outcome。
- 样本仍很小，不能宣称 Product core method fully supported。
- `runtime_default_allowed=false` 必须继续保持。

验收：

- 报告 before / after metrics：已满足。
- 报告 same-case 和 holdout 的差别：已满足。
- 明确 positive transfer、negative transfer 或 blocked same-case only：当前为 `r12_update_transfer_positive_guarded`。
- 明确 train metrics 不作为 transfer proof：已满足。
- 报告 risk ranking、static-prior miss recovery、abnormal segment recall 和 decision value：已满足，但其中 static-prior miss recovery 与 abnormal segment recall 暴露 holdout 覆盖 gap。

### R12 L4：Product support gate

目标：把 R12 的结论接入 Product evidence，但不污染主决策。

当前实现：

- `experiments/r12_product_support_gate.py`
- `tests/test_r12_product_support_gate.py`
- `tests/test_r12_product_integration.py`
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json`
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json`
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json`
- `demo/app.js`

当前状态为 `r12_product_support_gate_ready_guarded`。Product L4 将 R12 L3 的 transfer validation 包装成 `r12_transfer_validation_evidence_card`，并接入三个 Product surface：

- customer value report 新增 `r12_transfer_evidence` section。
- API manifest 新增 `/r6/product/r12-transfer-evidence` endpoint。
- `/demo/` 新增“R12 迁移验证”面板，展示 `update_transfer_gain`、validation / holdout MAE delta、区间覆盖变化和误报变化。
- `/demo/` 同步展示 L3+ 的扩展指标覆盖 gap，避免把 MAE 小幅正向误读为 Product core method ready。

边界：

- R12 evidence 只能作为 `secondary_transfer_evidence_card_only`。
- `r12_can_override_primary_decision=false`。
- `field_outcome_validated=false`。
- `runtime_default_allowed=false`。
- blocked claims 包含 `R12 supports Product core method by default`、`R12 can override guarded baseline primary decision` 和“精准预测系统”。

验收：

- Product report 能展示 R12 transfer validation card：已满足。
- API manifest 能暴露 R12 source refs：已满足。
- `/demo/` 能展示 R12 迁移验证面板：已满足。
- blocked claims 完整：已满足。
- `runtime_default_allowed=false`：已满足。

### R12 L5：High-risk holdout registry

目标：把 L3+ 暴露的两个 Product 关键 gap 转成可审计的数据与治理边界：当前 holdout 缺少 observed high-risk case，因此无法验证 static-prior miss recovery 和 abnormal segment recall。L5 的任务不是直接证明 Product core method ready，而是寻找 source-backed high-risk holdout case family，并区分 Research 可验证材料与 Product 默认可用材料。

当前已实现：

- `experiments/r12_high_risk_holdout_registry.py`
- `tests/test_r12_high_risk_holdout_registry.py`
- `experiments/results/r12_high_risk_holdout_registry/r12-high-risk-holdout-registry-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L5 registry。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L5 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。

当前状态为 `r12_high_risk_holdout_registry_ready_research_only`。L5 从当前 Census HPS public-use ingestion artifact 中扫描 `PRICESTRESS` 高风险 segment，使用 `PRICECONCERN` 作为 source signal，并排除已用于 R12 train split 的 `hps_REGION_2` 与 `hps_METRO_STATUS_2`。结果如下：

- scanned segment columns：6。
- scanned segment cases：84。
- research eligible high-risk holdout candidates：29。
- research recoverable static-prior miss candidates：12。
- product default eligible low-sensitive high-risk holdout candidates：0。
- current R12 holdout high-risk cases：0。

这给出一个明确结论：

- Research 侧：L5 找到了可以继续做 high-risk replay / transfer validation 的 source-backed public proxy 材料，R12 没有卡死在“无高风险 holdout 可测”的状态。
- Product 侧：这些新增候选主要来自收入、年龄、种族/族裔、性别等敏感或高治理 segment 轴，只能作为 research-only 或明确授权的审计材料，不能默认进入客户可见主决策。

因此 L5 后的 Product gate 仍保持：

- `product_core_method_ready=false`
- `field_outcome_validated=false`
- `runtime_default_allowed=false`
- `r12_can_override_primary_decision=false`
- blocked claim 新增或保留：`R12 Product default high-risk recovery validated`

L5 的下一步是 `r12_high_risk_holdout_transfer_replay`：在这 29 个 research-only 高风险候选上复核 R12 update 对 static-prior miss recovery、abnormal segment recall、false alarm 和 interval coverage 的影响，并继续报告敏感 segment 治理边界。

### R12 L6：High-risk holdout transfer replay

目标：不再停留在 L5 registry 的“有候选”，而是在 29 个 research-only high-risk 候选上实际回放 R12 L2 的 `price_pressure=0.55` update，判断它是否改善高风险漏报恢复、异常群体召回、区间覆盖和误报边界。

当前已实现：

- `experiments/r12_high_risk_holdout_transfer_replay.py`
- `tests/test_r12_high_risk_holdout_transfer_replay.py`
- `experiments/results/r12_high_risk_holdout_transfer_replay/r12-high-risk-holdout-transfer-replay-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L6 replay。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L6 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `demo/app.js` 已展示 replay MAE、漏报恢复变化、异常召回变化和 replay decision。

当前状态为 `r12_high_risk_holdout_transfer_replay_partial_research_positive`。指标如下：

- high-risk candidate count：29。
- MAE：`0.087818 -> 0.084134`，`delta=-0.003684`。
- static-prior miss recovery：`0.413793 -> 0.413793`，`delta=0.0`。
- abnormal segment recall：`0.413793 -> 0.413793`，`delta=0.0`。
- interval coverage：`0.62069 -> 0.62069`，`delta=0.0`。
- risk ranking quality：`0.662562 -> 0.662562`，`delta=0.0`。
- false alarm：不可评估，因为 replay 候选集全是 observed high-risk。
- Product default eligible high-risk holdout：0。

这给出一个更严格的结论：

- R12 update 在 high-risk research-only replay 上确实继续降低误差幅度。
- 但它没有提升静态先验漏报恢复率，也没有提升异常群体召回。
- 因此 L6 只能支撑 `research_only_mae_positive_recall_and_product_default_gap`，不能升级为 Product core method。

L6 后的下一步不应继续包装 MAE 正向，而应优先解决两个问题：

1. 找到低敏感或客户授权的 high-risk holdout，以便 Product 可默认展示。
2. 设计能改变 high-risk recall 的结构化 update，例如 segment sensitivity、threshold/activation 或 uncertainty-tail update，而不是只调整全局 `price_pressure` mechanism weight。

### R12 L7：Recall-oriented update

目标：针对 L6 暴露的“MAE 小幅改善但 high-risk recall 没有提升”问题，验证是否存在一个结构化、可审计、非 prompt/persona 的召回导向更新候选。L7 选择 activation threshold / margin，而不是继续调全局 mechanism weight。

当前已实现：

- `experiments/r12_recall_oriented_update.py`
- `tests/test_r12_recall_oriented_update.py`
- `experiments/results/r12_recall_oriented_update/r12-recall-oriented-update-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L7 recall update。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L7 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示召回更新 margin、漏报恢复、误报代价、精度代价、默认启用状态和下一验收产物。

当前状态为 `r12_recall_oriented_update_ready_research_guarded`。L7 在排除 R12 train cases 且要求 `valid_response_count >= 100` 后，评估 70 个 HPS segment cases，其中 observed high-risk 为 29 个，observed low-risk 为 41 个。候选选择规则为：

> 在 research false-alarm delta ceiling `0.08` 以内，选择 recall improvement 最大的 activation margin。

当前选择：

- current activation margin：`0.03`
- recommended activation margin：`0.01`
- update status：`accepted_for_research_replay`
- product default allowed：`false`

指标如下：

- static-prior miss recovery：`0.413793 -> 0.62069`，`delta=0.206897`。
- abnormal segment recall：`0.413793 -> 0.62069`，`delta=0.206897`。
- false alarm rate：`0.097561 -> 0.170732`，`delta=0.073171`。
- precision：`0.75 -> 0.72`，`delta=-0.03`。
- interval coverage：`0.8 -> 0.8`，`delta=0.0`。
- newly recovered cases：`hps_ESEX_1`、`hps_RRACETH_1`、`hps_TAGE_46`、`hps_TAGE_60`、`hps_TAGE_64`、`hps_TAGE_73`。
- new false alarm cases：`hps_TAGE_58`、`hps_TAGE_59`、`hps_TAGE_62`。

这给出一个更精确的结论：

- R12 已经找到能提升静态先验漏报恢复和异常群体召回的结构化阈值候选。
- 该候选没有破坏 interval coverage，并且 false-alarm delta 仍在 research ceiling 内。
- 但它没有通过 `false_alarm_non_regression`，也没有通过 `precision_non_regression`。
- 因此 L7 只能支撑 `research_only_recall_positive_false_alarm_tradeoff`，不能升级为 Product core method 或 runtime default。

L7 后的下一步不是扩大 claim，而是补 `r12_recall_update_holdout_false_alarm_stress_test`：

1. 检查 activation margin `0.01` 是否只在当前 HPS segment 切片上有效。
2. 做 low-sensitive / customer-approved high-risk holdout。
3. 对 false alarm 新增样本做 segment-level failure diagnosis。
4. 比较 segment sensitivity、uncertainty-tail update 与 activation margin 的组合，判断能否保留 recall gain 并降低 false alarm / precision 代价。

### R12 L8：Recall update false-alarm stress test

目标：对 L7 activation margin 候选做 false-alarm stress，不让“召回提升”直接升级为 Product default。L8 的核心问题是：召回增益是否在低敏感、可产品默认展示的压力条件下成立，且是否没有引入不可治理误报。

当前已实现：

- `experiments/r12_recall_update_false_alarm_stress_test.py`
- `tests/test_r12_recall_update_false_alarm_stress_test.py`
- `experiments/results/r12_recall_update_false_alarm_stress_test/r12-recall-update-false-alarm-stress-test-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L8 stress artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L8 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示误报压力测试状态、global false alarm delta、protected-sensitive false alarm delta、low-sensitive recall evaluable 和 dominant false-alarm segment。

当前状态为 `r12_recall_update_false_alarm_stress_blocked_product_default`。L8 继续使用 HPS public-use proxy，并排除 R12 train cases，评估 70 个 segment cases：

- observed high-risk：29。
- observed low-risk：41。
- low-sensitive cases：4。
- protected 或高治理 cases：66。
- newly recovered：6。
- new false alarms：3。

关键指标：

- L7 recall gain 保留：`+0.206897`。
- global false alarm rate delta：`+0.073171`。
- precision delta：`-0.03`。
- interval coverage delta：`0.0`。
- low-sensitive false alarm delta：`0.0`。
- low-sensitive recall evaluable：`false`，因为低敏感切片没有 observed high-risk。
- protected-sensitive false alarm delta：`+0.096774`。
- worst segment family：`TAGE`，false alarm delta `+0.115385`。
- new false alarms：`hps_TAGE_58`、`hps_TAGE_59`、`hps_TAGE_62`，100% 集中在 protected-sensitive 年龄轴。

L8 结论：

- L7 的召回提升不是假信号，但它伴随明确误报和精度代价。
- 低敏感轴目前不能证明召回提升，因为没有 observed high-risk。
- 新增 false alarm 完全集中在 protected-sensitive 年龄轴，不能产品默认启用。
- 因此 L8 只能支撑 `reject_product_default_keep_research_guarded_candidate`。

L8 后的下一步是 `r12_recall_false_alarm_mitigation_candidate`：

1. 对 `TAGE` false alarm 做 failure diagnosis，区分接近阈值误报、source signal 过强、年龄轴机制敏感度过高还是 activation margin 过低。
2. 比较三类 mitigation：segment-specific activation margin、uncertainty-tail guard、protected-sensitive conservative cap。
3. 验收条件不是单纯降低 false alarm，而是保留一部分 recall gain，同时让 protected-sensitive false alarm delta 和 precision regression 进入可治理边界。

## 当前推荐推进顺序

1. R12 L0/L1 已完成：case registry 和 operator contract 已建立。
2. R12 L2 已完成：train residual 已生成可审计结构化更新。
3. R12 L3 已完成：当前 HPS public-use proxy split 上存在 guarded positive transfer signal。
4. R12 L4 已完成：只以 guarded evidence card / API manifest source refs / blocked claims 的方式接入 Product，不覆盖主决策，不开启 runtime default。
5. R12 L5 已完成：已找到 29 个 source-backed research-only 高风险 holdout 候选，其中 12 个可用于验证静态先验漏报恢复；但 Product 默认可用的低敏感高风险 holdout 仍为 0。
6. R12 L6 已完成：high-risk replay 有 MAE 小幅正向，但 static-prior miss recovery 和 abnormal segment recall 没有提升，false alarm 不可评估，Product default 仍阻断。
7. R12 L7 已完成：activation margin recall-oriented update 让 high-risk recall 相关指标提升 `0.206897`，但引入 false alarm 与 precision 代价，Product default 仍阻断。
8. R12 L8 已完成：false-alarm stress test 保留 L7 recall gain，但确认 Product default 被 global false alarm、precision regression、low-sensitive recall 不可验和 protected-sensitive 年龄轴误报集中共同阻断。
9. 下一步推进 `r12_recall_false_alarm_mitigation_candidate`：优先探索 segment-specific activation margin、uncertainty-tail guard 或 protected-sensitive conservative cap，目标是在保留部分 recall gain 的同时降低 false alarm / precision 代价。

## 成功信号

R12 的最小成功信号不是“指标全赢”，而是：

- 在 holdout case 上，结构化 outcome update 至少改善一个 Product-relevant 指标；
- 没有牺牲 interval coverage；
- 没有不可解释或不可治理地增加 false alarm；
- 能解释为什么 update 对某类机制或群体可迁移；
- 能明确阻断不该迁移的更新。

## 当前判断

R12 目前拿到了比 R11 更强的最低正向信号：R11 只能证明 feedback ledger 可审计，R12 L3 已证明一个 train-only 结构化 mechanism update 能在 validation / holdout 上产生小幅正向迁移，且没有牺牲区间覆盖和 false alarm；R12 L5/L6 进一步找到了 high-risk replay 材料，并证明当前 update 在 high-risk research-only replay 上有 MAE 小幅正向；R12 L7 则进一步证明 activation margin 这类结构化阈值候选可以提升 static-prior miss recovery 与 abnormal segment recall；R12 L8 又把该召回增益的 false-alarm 失败边界量化出来。

但这个结果仍不足以说 Research 已全面支撑 Product。当前最准确的表述是：

> R12 在 HPS public-use proxy split 上形成了 guarded positive transfer signal，在 research-only high-risk replay 上取得 MAE 小幅改善，并通过 activation margin 候选提升了 high-risk recall；但 L8 stress test 已证明该召回增益伴随 global false alarm、precision regression、low-sensitive recall 不可验和 protected-sensitive 年龄轴误报集中，因此它不是 field-validated、customer-validated、低敏感 Product-default-ready 或 runtime-default-ready 的 Product core method。
