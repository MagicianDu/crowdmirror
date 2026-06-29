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

### R12 L9：Recall false-alarm mitigation candidate

目标：在 L8 已经确认 Product default 被 false alarm / precision / low-sensitive recall gap 阻断后，进一步验证是否存在结构化 mitigation 候选，能保留部分 L7 recall gain，同时消除当前新增 false alarm。

当前已实现：

- `experiments/r12_recall_false_alarm_mitigation_candidate.py`
- `tests/test_r12_recall_false_alarm_mitigation_candidate.py`
- `experiments/results/r12_recall_false_alarm_mitigation_candidate/r12-recall-false-alarm-mitigation-candidate-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L9 mitigation artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L9 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 mitigation candidate、recall gain retained、mitigated false alarm delta、mitigated precision delta、overfit risk 和下一验收产物。

L9 比较的候选包括：

- `r12-tage-58-62-activation-guard-001`
- `r12-tage-family-conservative-cap-001`
- `r12-global-margin-0015-001`
- `r12-global-margin-002-001`
- `r12-protected-sensitive-conservative-cap-001`

选择规则：

> maximize recall retention subject to false-alarm and precision non-regression

当前选中的候选是 `r12-tage-58-62-activation-guard-001`。它的规则是：

- 默认 activation margin：`0.01`。
- 对 `TAGE` 的 `58-62` 年龄带使用 guarded activation margin：`0.03`。
- 该候选只允许 `accepted_for_research_mitigation_replay`。
- `product_default_allowed=false`。
- `overfit_risk=high_current_false_alarm_band_derived`。

关键指标：

- static-prior miss recovery：baseline `0.413793`，L7 `0.62069`，mitigated `0.586207`。
- mitigated recall delta：`+0.172414`。
- L7 recall gain retained：`0.833333`。
- false alarm rate：baseline `0.097561`，L7 `0.170732`，mitigated `0.097561`。
- L7 false alarm delta removed：`0.073171`。
- precision：baseline `0.75`，L7 `0.72`，mitigated `0.809524`。
- precision delta：`+0.059524`。
- interval coverage delta：`0.0`。

case-level 结果：

- 保留 recovered cases：`hps_ESEX_1`、`hps_RRACETH_1`、`hps_TAGE_46`、`hps_TAGE_64`、`hps_TAGE_73`。
- 移除 L7 false alarms：`hps_TAGE_58`、`hps_TAGE_59`、`hps_TAGE_62`。
- 丢失 L7 recovered case：`hps_TAGE_60`。
- 新 false alarm：0。

L9 结论：

- 当前 false-alarm 代价不是不可缓解；存在一个 research-only mitigation candidate。
- 但该候选来自当前 false-alarm band，过拟合风险高。
- 低敏感召回仍不可验，field/customer outcome 仍缺失。
- 因此 L9 只能支撑 `accept_research_guarded_mitigation_reject_product_default`，不能升级 Product default。

L9 后已执行的验证是 `r12_recall_mitigation_holdout_validation`：

1. 用独立 holdout 或客户授权切片验证 `TAGE 58-62` guard 是否泛化。
2. 如果不能泛化，降级为 failure diagnosis rule，而不是 Product method。
3. 如果能泛化，再比较更稳健的机制解释：是否应该是 uncertainty-tail guard、age-axis conservative cap，还是 segment-value band guard。

### R12 L10：Recall mitigation holdout validation

目标：验证 L9 的 `TAGE 58-62 activation guard` 是否只是当前 false-alarm band 的过拟合，还是能在 pseudo-holdout / independent holdout 上稳定缓解误报并保留足够召回。

当前已实现：

- `experiments/r12_recall_mitigation_holdout_validation.py`
- `tests/test_r12_recall_mitigation_holdout_validation.py`
- `experiments/results/r12_recall_mitigation_holdout_validation/r12-recall-mitigation-holdout-validation-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L10 holdout validation artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L10 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 holdout validation 状态、leave-one pass rate、端点 holdout failure、独立 holdout 状态和下一验收产物。

验证设计：

- 使用 L7 新增 false alarm case：`hps_TAGE_58`、`hps_TAGE_59`、`hps_TAGE_62`。
- 每次 hold out 一个 false alarm，只用剩余 false alarm 推导 guarded band。
- 要求 holdout false alarm 被移除、false alarm rate 非回归、precision 非回归、recall delta 保持正向。
- 要求 leave-one pass rate 至少达到 `0.666667`。

当前结果：

- trial count：3。
- pass count：1。
- pass rate：`0.333333`。
- endpoint holdout failure count：2。
- `hps_TAGE_58` holdout 失败：由 `59-62` 推导的 band 无法移除 `58`。
- `hps_TAGE_59` holdout 通过：由 `58-62` 推导的 band 可以移除 `59`。
- `hps_TAGE_62` holdout 失败：由 `58-59` 推导的 band 无法移除 `62`。

稳定替代检查：

- `r12-tage-family-conservative-cap-001` 的 false alarm delta 为 `0.0`，new false alarm count 为 0。
- 但它只保留 L7 recall gain 的 `0.333333`，低于要求的 `0.5`。
- 因此它是稳定但过度保守的 failure diagnosis candidate，不是可直接替代的 Product method。

L10 结论：

- L9 的 `TAGE 58-62` guard 没有通过 holdout 稳定性验证。
- 当前 mitigation candidate 不能作为 Product default、runtime default 或 field-validated 方法。
- 该候选可以保留为 Product failure diagnosis：它能解释“当前召回提升为什么会集中引入年龄轴误报”，并帮助客户看到系统如何阻断不稳定更新。
- 独立 holdout、低敏感可召回切片或客户授权 outcome 的数据审计已由 L11 执行。

### R12 L11：Recall mitigation independent holdout data

目标：不再停留在“需要独立数据”的抽象说法，而是审计当前已经有的数据、同源 public proxy 的剩余候选、低敏感可召回切片、外部公开数据候选源和客户授权切片是否足以解除 L10 阻断。

当前已实现：

- `experiments/r12_recall_mitigation_independent_holdout_data.py`
- `tests/test_r12_recall_mitigation_independent_holdout_data.py`
- `experiments/results/r12_recall_mitigation_independent_holdout_data/r12-recall-mitigation-independent-holdout-data-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L11 data audit artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L11 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 independent holdout data audit 状态、同源诊断候选数、低敏感高风险样本数、外部候选源数、已接入独立数据数和下一步。

当前数据审计结果：

- 当前 HPS public proxy 已 ingest，可以继续作为 source-backed diagnostic material。
- L9 derivation band `TAGE 58-62` 覆盖 5 个 cases。
- 排除 derivation band 后，同源 HPS 仍有 65 个 segment cases。
- 同源非 derivation 召回诊断候选有 5 个：`hps_ESEX_1`、`hps_RRACETH_1`、`hps_TAGE_46`、`hps_TAGE_64`、`hps_TAGE_73`。
- 但这些仍来自同一 HPS public proxy dataset，不能当作独立 holdout。
- 低敏感 slice 只有 4 个 cases，observed high-risk count 为 0，因此 `low_sensitive_recall_evaluable=false`。
- R10 external registry 中有 3 个官方公开候选源：HPS、BTS DB1B、DOT Air Travel Consumer Reports；但当前 ingestion status 均为 `candidate_source_not_ingested`。
- 客户授权 holdout case count 为 0。

L11 结论：

- L11 没有解除 L10 的 Product default 阻断。
- 它把“缺独立数据”从口头 gap 变成可审计 artifact：同源数据可用于 failure diagnosis，不能用于 Product default；外部公开源存在，但必须先 ingest 或切片；客户授权 outcome 仍缺失。
- 下一步是 `r12_recall_mitigation_external_holdout_ingestion_or_customer_slice`：优先接入一个外部公开 holdout，或准备客户授权切片入口。

### R12 L12：External holdout ingestion or customer slice contract

目标：把 L11 的“需要外部 holdout 或客户授权切片”进一步转成可执行的数据合同，明确优先数据源、客户切片字段、验收门槛、revalidation 前置条件和 Product 阻断边界。

当前已实现：

- `experiments/r12_recall_mitigation_external_holdout_ingestion_or_customer_slice.py`
- `tests/test_r12_recall_mitigation_external_holdout_ingestion_or_customer_slice.py`
- `experiments/results/r12_recall_mitigation_external_holdout_ingestion_or_customer_slice/r12-recall-mitigation-external-holdout-ingestion-or-customer-slice-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L12 contract artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L12 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示外部/客户切片合同状态、首选外部源、raw slice 状态、客户授权状态和下一步。

当前 route selection：

- selected route：`external_public_holdout_first_customer_slice_compatible`。
- 首选外部源：`dot_air_travel_consumer_report_complaint_candidate`，用于服务变更 complaint-risk holdout。
- 第二优先：`bts_db1b_route_price_demand_candidate`，用于价格变更 revealed-demand holdout。
- 第三优先：`census_hps_policy_reaction_public_use_candidate`，用于政策反应 survey holdout。
- 客户授权切片作为 fallback。

客户切片合同：

- 支持 `csv` 与 `jsonl`。
- 最少 10 个 cases。
- 必需字段：`case_id`、`scenario_family`、`segment_column`、`segment_value`、`static_prior_prediction`、`interaction_prediction`、`observed_outcome`、`outcome_window_start`、`outcome_window_end`、`customer_approval_id`、`source_ref`。
- 可选字段：`complaint_count`、`exposure_count`、`price_change_pct`、`policy_change_label`、`mechanism_tags`、`segment_sensitivity_level`。
- 必须包含低敏感轴或客户授权轴。
- 不允许只用 L9 derivation band 作为证明。
- 不允许 manual prompt/persona patch。

L12 结论：

- L12 让外部 holdout / 客户授权切片从“下一步想法”变成可执行合同。
- 但当前 `raw_external_or_customer_slice_present=false`，`minimum_case_count_met=false`，`customer_approval_present=false`。
- 因此 L12 仍不能启动 revalidation，Product default 继续阻断。
- 下一步是 `r12_external_or_customer_holdout_raw_slice`。

### R12 L13：External/customer holdout raw slice

目标：把 L12 的合同推进为真实官方外部 raw outcome slice。L13 只解决“有没有 raw outcome 数据可供下一步 revalidation 使用”，不解决“R12 方法已经通过外部验证”。

当前已实现：

- `experiments/r12_external_or_customer_holdout_raw_slice.py`
- `tests/test_r12_external_or_customer_holdout_raw_slice.py`
- `experiments/results/r12_external_or_customer_holdout_raw_slice/r12-external-or-customer-holdout-raw-slice-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L13 raw slice artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L13 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 raw slice 状态、官方数据接入、case count、observed complaint total、预测字段状态和下一步。

当前 raw slice 来源：

- selected source：`dot_air_travel_consumer_report_complaint_candidate`。
- source route：`external_public_official_report_slice`。
- source owner：U.S. Department of Transportation。
- source document：June 2026 Air Travel Consumer Report，April 2026 data。
- source table：Table 3，Consumer Complaint Cases: U.S. Airlines。
- source URL：`https://www.transportation.gov/resources/individuals/aviation-consumer-protection/june-2026-air-travel-consumer-report-april-2026`。
- source PDF：`https://www.transportation.gov/sites/dot.gov/files/2026-06/June%202026%20ATCR.pdf`。

当前 raw slice 结果：

- `source_row_count=15`。
- `case_count=14`。
- `total_observed_complaint_cases=4839`。
- `minimum_case_count_met=true`。
- `actual_public_data_ingested=true`。
- `raw_external_or_customer_slice_present=true`。
- `prediction_fields_present=false`。
- `external_holdout_revalidation_ready=false`。
- `product_default_allowed=false`。

Hawaiian Airlines 处理：

- DOT PDF Table 3 的文本抽取中包含 Hawaiian Airlines `total=38`。
- 但 DOT 脚注说明 Hawaiian Airlines consumer complaint data 已合并并归因到 Alaska Airlines。
- 为避免双计，L13 将 Hawaiian Airlines 放入 `source_excluded_records`，不进入 `raw_records` 与 `normalized_holdout_cases`。
- 这样 analytic rows 的总数与 DOT 官方 `TOTAL April 2026 = 4839` 对齐。

L13 结论：

- L13 已解除 L12 的“raw external/customer slice 缺失”阻断。
- 但 L13 还没有为 DOT raw cases 生成 `static_prior_prediction` 与 `interaction_prediction`。
- 因此 L13 不能启动 Product default，也不能声明 external holdout revalidation completed。
- 下一步是 `r12_recall_mitigation_external_holdout_revalidation`：为 DOT raw slice 生成对齐预测字段，并验证 R12 update 是否在官方外部投诉 outcome 上改善 trend/risk ranking/interval/false alarm/recall 或给出失败结论。

### R12 L14：External holdout proxy revalidation

目标：把 L13 的 DOT official raw outcome slice 转成可计算 revalidation artifact，同时明确区分 proxy diagnostic 和 independent validation。L14 只解决“能否在真实外部 raw outcome 上计算 Product-relevant 指标并暴露失败边界”，不解决“独立预结果预测已经通过”。

当前已实现：

- `experiments/r12_recall_mitigation_external_holdout_revalidation.py`
- `tests/test_r12_recall_mitigation_external_holdout_revalidation.py`
- `experiments/results/r12_recall_mitigation_external_holdout_revalidation/r12-recall-mitigation-external-holdout-revalidation-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L14 revalidation artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L14 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L14 revalidation 状态、passed gate、同表泄漏风险、MAE/risk ranking/static-prior miss recovery/false alarm 变化和下一步 artifact。

当前 L14 预测定义：

- static prior：`uniform_carrier_share_control`，即 14 个 airline cases 的均匀份额。
- interaction prediction：`same_table_mechanism_composition_proxy`，用 DOT 同表 complaint category 构成生成机制压力分数，再归一化为 interaction proxy share。
- 因为 interaction prediction 使用同一张 outcome table 的 category 构成，必须标注 `prediction_source_independent_of_observed_outcome=false` 和 `same_table_prediction_leakage_risk=true`。

当前 L14 指标：

- `case_count=14`。
- `observed_total=4839`。
- `mean_absolute_error.delta=-0.004329`。
- `interval_coverage.delta=+0.071429`。
- `risk_ranking_quality.delta=+0.25`。
- `static_prior_miss_recovery.delta=+0.8`。
- `false_alarm_rate.delta=+0.428571`。
- `precision.delta=+0.571429`。

L14 结论：

- 这是一个有用的 failure diagnosis / evidence boundary artifact：它说明机制构成 proxy 能恢复一部分静态先验漏报，并改善 MAE、区间覆盖和 top-k 风险排序。
- 但 false alarm 明显上升，且预测并非 outcome-independent。
- 因此状态为 `r12_recall_mitigation_external_holdout_revalidation_blocked_prediction_proxy_only`。
- Product 可展示该 diagnostic boundary，但不能声明 `external_holdout_revalidation_passed`、Product default、field outcome validated 或 runtime default。
- 下一步是 `r12_pre_outcome_or_independent_prediction_packet`：需要在 outcome 产生前或使用独立 source 生成预测，再回来对照 DOT/customer/field outcome。

### R12 L15：Pre-outcome or independent prediction packet

目标：把 L14 的 proxy-only 阻断推进为可审计的独立预测包。L15 不做 revalidation 结论，只确认是否存在不使用 April target outcome 的预测输入和 locked predictions，从而为下一步 independent hindcast revalidation 提供输入。

当前已实现：

- `experiments/r12_pre_outcome_or_independent_prediction_packet.py`
- `tests/test_r12_pre_outcome_or_independent_prediction_packet.py`
- `experiments/results/r12_pre_outcome_or_independent_prediction_packet/r12-pre-outcome-or-independent-prediction-packet-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L15 prediction packet。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L15 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L15 prediction packet 状态、独立特征源、事前锁定状态、hindcast ready、pre-outcome ready、prediction case count 和下一步 artifact。

当前 L15 数据源：

- source：DOT May 2026 Air Travel Consumer Report，March 2026 data。
- source table：Table 3，Consumer Complaint Cases: U.S. Airlines。
- source route：`external_public_official_prior_month_report`。
- prediction route：`prior_month_complaint_share_hindcast`。
- feature period：March 2026。
- target period：April 2026。
- prior month complaint total：`6024`。
- matched carrier cases：`14`。

当前 L15 gate：

- `prediction_source_independent_of_target_outcome=true`。
- `target_outcome_used_for_prediction_generation=false`。
- `same_table_prediction_leakage_risk=false`。
- `hindcast_independent_revalidation_ready=true`。
- `prediction_lock_timestamp_pre_target_outcome=false`。
- `pre_outcome_revalidation_ready=false`。
- `product_default_allowed=false`。
- `field_outcome_validated=false`。
- `runtime_default_allowed=false`。

L15 结论：

- L15 比 L14 更强：它不再用 April target outcome table 的 category mix 生成 prediction，而是用 March prior-month official source 生成 prediction shares。
- 但 L15 仍是 post-hoc hindcast packet，不是 target outcome 发生前锁定的预测包。
- 因此 Product 可展示它作为“独立特征 hindcast revalidation 输入已就绪”，但不能展示为 pre-outcome validation、Product default 或 runtime default。
- 下一步是 `r12_independent_hindcast_revalidation`：使用 L15 locked predictions 对 L13 April target outcome 计算 MAE、interval、risk ranking、static-prior miss recovery、false alarm 和 decision-value，并与 L14 proxy-only revalidation 做边界比较。

### R12 L16：Independent hindcast revalidation

目标：把 L15 的独立预测包推进为可计算的 independent-feature hindcast revalidation。L16 不宣称事前预测成功，只验证“在不使用 April target outcome 的前一月官方特征源下，interaction-style prediction 是否比静态均匀先验更能发现风险、覆盖区间、恢复静态先验漏报，并保持误报不退化”。

当前已实现：

- `experiments/r12_independent_hindcast_revalidation.py`
- `tests/test_r12_independent_hindcast_revalidation.py`
- `experiments/results/r12_independent_hindcast_revalidation/r12-independent-hindcast-revalidation-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L16 independent hindcast revalidation。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L16 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L16 hindcast 状态、passed gate、MAE/区间/风险排序/漏报恢复/误报/决策价值变化和下一步 artifact。

当前 L16 指标：

- `case_count=14`。
- `prediction_source_independent_of_target_outcome=true`。
- `target_outcome_used_for_prediction_generation=false`。
- `mean_absolute_error.delta=-0.062951`。
- `interval_coverage.delta=+0.714286`。
- `risk_ranking_quality.delta=+1.0`。
- `static_prior_miss_recovery.delta=+1.0`。
- `false_alarm_rate.delta=0.0`。
- `decision_value.delta=+0.714286`。

当前 L16 gate：

- `hindcast_independent_revalidation_executed=true`。
- `hindcast_independent_revalidation_passed=true`。
- `prediction_lock_timestamp_pre_target_outcome=false`。
- `pre_outcome_revalidation_ready=false`。
- `product_default_allowed=false`。
- `field_outcome_validated=false`。
- `runtime_default_allowed=false`。

L16 结论：

- L16 比 L14/L15 更强：它不再只是准备预测包，也不使用同表 target outcome 生成 proxy prediction，而是用独立 prior-month feature 对 target outcome 做完整指标复核。
- 当前结果支持一个 guarded positive claim：独立特征 hindcast 在 DOT airline complaint slice 上比静态均匀先验更能发现风险，并且误报不退化。
- 但 L16 仍是 post-hoc hindcast，不是 outcome 发生前锁定的预测，也不是客户 field outcome validation。
- 因此 Product 可展示它作为“R12 有风险发现价值的次级证据”，但不能作为 Product default、runtime default 或 field-validated claim。
- 下一步是 `r12_pre_outcome_prediction_trial_or_customer_field_revalidation`：要么建立真正事前锁定 prediction packet 后等待 outcome，要么用客户授权 field slice 做 outcome review 和参数更新闭环。

### R12 L17：Pre-outcome prediction trial or customer field revalidation

目标：把 L16 的 post-hoc hindcast 正向信号推进为真正的 pre-outcome trial lock。L17 不验证 outcome，也不宣称事前预测成功；它只完成两件事：第一，在 target outcome 回流前锁定下一期 prediction packet；第二，定义客户 field slice revalidation 合同，保证未来真实 outcome 回流后能按同一套指标复核。

当前已实现：

- `experiments/r12_pre_outcome_prediction_trial_or_customer_field_revalidation.py`
- `tests/test_r12_pre_outcome_prediction_trial_or_customer_field_revalidation.py`
- `experiments/results/r12_pre_outcome_prediction_trial_or_customer_field_revalidation/r12-pre-outcome-prediction-trial-or-customer-field-revalidation-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L17 pre-outcome trial artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L17 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L17 trial 状态、锁定时间、target period、target outcome 接入状态、客户 field 合同状态和下一步 artifact。

当前 L17 trial：

- selected route：`pre_outcome_public_dot_trial`。
- feature period：April 2026。
- target outcome period：May 2026。
- prediction lock timestamp：`2026-06-27T14:45:00Z`。
- prediction case count：`14`。
- prediction source：April 2026 DOT official complaint share。
- customer field fallback：enabled。
- customer field slice contract：ready。

当前 L17 gate：

- `pre_outcome_prediction_trial_created=true`。
- `prediction_packet_locked=true`。
- `prediction_lock_timestamp_pre_target_outcome=true`。
- `prediction_source_independent_of_target_outcome=true`。
- `target_outcome_used_for_prediction_generation=false`。
- `target_outcome_artifact_present=false`。
- `pre_outcome_revalidation_ready=false`。
- `customer_field_slice_contract_ready=true`。
- `customer_field_slice_present=false`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L17 结论：

- L17 比 L16 更进一步：它不再只是 post-hoc hindcast，而是锁定了下一期 target outcome 的 prediction packet。
- 当前 Product 可展示“R12 已进入事前预测试验，等待 outcome 回流验证”，这比只展示历史回测更有客户说服力。
- 但 L17 仍没有 target outcome 或客户 field slice，因此不能宣称 pre-outcome validation passed、field outcome validated、Product default 或 runtime default。
- 下一步是 `r12_pre_outcome_or_customer_field_outcome_ingestion`：接入 May 2026 DOT target outcome 或客户授权 field slice，然后复核 L17 locked predictions 的 MAE、区间覆盖、风险排序、静态先验漏报恢复、false alarm 和 decision value。

### R12 L18：Pre-outcome or customer field outcome ingestion

目标：把 L17 的“等待 outcome”变成可审计的 ingestion 状态，而不是让 Product 页面停留在空泛下一步。L18 不伪造 outcome，不计算 validation 指标；它只确认当前公开 target outcome 与客户 field slice 是否可用，并把缺口、来源和下一步 revalidation 入口写入 artifact。

当前已实现：

- `experiments/r12_pre_outcome_or_customer_field_outcome_ingestion.py`
- `tests/test_r12_pre_outcome_or_customer_field_outcome_ingestion.py`
- `experiments/results/r12_pre_outcome_or_customer_field_outcome_ingestion/r12-pre-outcome-or-customer-field-outcome-ingestion-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L18 outcome ingestion artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L18 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L18 outcome ingestion 状态、availability checked 时间、latest report、target outcome 接入状态、field slice contract 和下一步 artifact。

当前 L18 ingestion 状态：

- target outcome period：May 2026。
- availability checked at：`2026-06-27T14:55:00Z`。
- latest available report：`June 2026 Air Travel Consumer Report (April 2026 Data)`。
- expected target report：`July 2026 Air Travel Consumer Report (May 2026 Data)`。
- target public outcome available：`false`。
- target outcome artifact present：`false`。
- customer field slice contract ready：`true`。
- customer field slice present：`false`。

当前 L18 gate：

- `pre_outcome_trial_locked=true`。
- `prediction_lock_timestamp_pre_target_outcome=true`。
- `target_outcome_used_for_prediction_generation=false`。
- `target_public_outcome_available=false`。
- `target_outcome_artifact_present=false`。
- `customer_field_slice_contract_ready=true`。
- `customer_field_slice_present=false`。
- `field_or_pre_outcome_revalidation_ready=false`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L18 结论：

- L18 把“没有 target outcome”从口头说明变成 Product 可展示、source-backed、fail-closed 的 artifact。
- 当前 Product 可展示：R12 已锁定事前 trial，且已确认公开 target 尚未可用；客户 field slice 入口已定义。
- 但 L18 不包含 outcome，因此不能宣称 pre-outcome/customer field validation passed，也不能开启 Product default 或 runtime default。
- 下一步是 `r12_pre_outcome_or_customer_field_outcome_revalidation`，只有在 May 2026 DOT target outcome 或客户授权 field slice 回流后才可执行。

### R12 L19：Pre-outcome or customer field outcome revalidation

目标：把 L18 的 revalidation 入口做成可运行的 fail-closed harness。L19 不等待口头汇报，不伪造 outcome；它在 target outcome 或客户 field slice 缺失时明确拒绝计算验证指标，并把未来指标计划、缺失输入和 blocked claims 写入 Product 可展示证据链。

当前已实现：

- `experiments/r12_pre_outcome_or_customer_field_outcome_revalidation.py`
- `tests/test_r12_pre_outcome_or_customer_field_outcome_revalidation.py`
- `experiments/results/r12_pre_outcome_or_customer_field_outcome_revalidation/r12-pre-outcome-or-customer-field-outcome-revalidation-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L19 outcome revalidation artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L19 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L19 revalidation 状态、`metrics_computed`、`field_or_pre_outcome_revalidation_passed` 和下一步 artifact。

当前 L19 revalidation 状态：

- target outcome period：May 2026。
- prediction lock timestamp：`2026-06-27T14:45:00Z`。
- revalidation requested at：`2026-06-27T15:05:00Z`。
- target outcome artifact present：`false`。
- customer field slice present：`false`。
- field or pre-outcome revalidation ready：`false`。
- metrics computed：`false`。

当前 L19 gate：

- `pre_outcome_trial_locked=true`。
- `prediction_lock_timestamp_pre_target_outcome=true`。
- `target_outcome_artifact_present=false`。
- `customer_field_slice_present=false`。
- `field_or_pre_outcome_revalidation_ready=false`。
- `metrics_computed=false`。
- `field_or_pre_outcome_revalidation_passed=false`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L19 结论：

- L19 让 Product 能展示“复核器已就绪、指标计划明确、等待 outcome 回流”，而不是只说下一步未做。
- L19 的正确结果是 blocked：没有 May 2026 DOT target outcome 或客户授权 field slice，就不能计算真实 validation 指标。
- 因此 L19 不能证明 R12 已 field-validated 或 customer-validated；它只能证明当前证据链在缺 outcome 时会 fail-closed。
- 下一步是 `r12_target_outcome_or_customer_field_slice_arrival`，即接入 May 2026 DOT target outcome 或客户授权 field slice 后再运行真实 revalidation。

### R12 L20：Target outcome or customer field slice arrival

目标：把 L19 的“等待 outcome/source 到达”变成可运行的 source-arrival gate。L20 不计算验证指标；它只判断 May 2026 DOT target outcome 或客户授权 field slice 是否已经到达，并在客户 field slice 到达时做机器可校验的合同检查。

当前已实现：

- `experiments/r12_target_outcome_or_customer_field_slice_arrival.py`
- `tests/test_r12_target_outcome_or_customer_field_slice_arrival.py`
- `experiments/results/r12_target_outcome_or_customer_field_slice_arrival/r12-target-outcome-or-customer-field-slice-arrival-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L20 arrival artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L20 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L20 arrival 状态、`outcome_source_arrived`、`field_or_pre_outcome_revalidation_ready` 和下一步 artifact。

当前 L20 状态：

- target outcome period：May 2026。
- latest available public report：`June 2026 Air Travel Consumer Report (April 2026 Data)`。
- expected public report：`July 2026 Air Travel Consumer Report (May 2026 Data)`。
- target report found：`false`。
- customer field slice present：`false`。
- outcome source arrived：`false`。
- field or pre-outcome revalidation ready：`false`。
- metrics computed：`false`。

客户 field slice 合同：

- accepted formats：`csv`、`jsonl`。
- minimum case count：10。
- required fields：`case_id`、`segment_id`、`scenario_id`、`prediction_share_or_score`、`observed_outcome`、`outcome_timestamp`、`customer_approval_reference`。
- 若字段齐全、case 数达标且 customer approval 完整，L20 可把 `field_or_pre_outcome_revalidation_ready` 置为 `true`，但仍保持 `metrics_computed=false`、`product_default_allowed=false`、`runtime_default_allowed=false`。

L20 结论：

- L20 让 Product 能展示“source-arrival gate 已就绪”，并把客户 field slice 的最低可验收格式合同化。
- 当前 current artifact 仍是 pending：没有 May 2026 DOT target outcome，也没有客户授权 field slice。
- 因此 L20 不能证明 R12 已 field-validated 或 customer-validated；它只能证明 outcome/source 到达时已有 fail-closed 接入入口。

### R12 L21：Customer field slice handoff package

目标：把 L20 的客户 field slice 接入入口进一步产品化为可交付的 handoff package。L21 不计算验证指标；它只把客户数据请求、字段模板、隐私边界、审批引用和后续复核路径固化为机器可校验 artifact，避免 Product 在没有 outcome 的情况下提前扩大 claim。

当前已实现：

- `experiments/r12_customer_field_slice_handoff_package.py`
- `tests/test_r12_customer_field_slice_handoff_package.py`
- `experiments/results/r12_customer_field_slice_handoff_package/r12-customer-field-slice-handoff-package-current-001.json`
- `experiments/results/r12_customer_field_slice_handoff_package/r12-customer-field-slice-template-current-001.csv`
- `experiments/r12_product_support_gate.py` 已支持消费 L21 handoff artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L21 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L21 handoff 状态、客户数据请求、模板文件、最少 case 数和下一步 artifact。

当前 L21 handoff contract：

- accepted formats：`csv`、`jsonl`。
- minimum case count：10。
- required fields：`case_id`、`segment_id`、`scenario_id`、`prediction_share_or_score`、`observed_outcome`、`outcome_timestamp`、`customer_approval_reference`。
- 模板文件：`r12-customer-field-slice-template-current-001.csv`。
- 必须使用伪匿名 case，不允许直接个人标识。
- 不允许 manual prompt/persona patch。
- 不允许 Product default 或 runtime default 因 handoff package 生成而打开。

当前 L21 gates：

- `source_arrival_gate_ready=true`。
- `customer_field_slice_template_generated=true`。
- `customer_field_slice_contract_machine_checkable=true`。
- `customer_data_request_ready=true`。
- `outcome_source_arrived=false`。
- `metrics_computed=false`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L21 结论：

- L21 让 Product 能把客户 field outcome 回流作为正式、可审计、可复用的数据交付工作流，而不是停留在“等客户给数据”的口头状态。
- 但 L21 仍不是 validation artifact；它没有真实 outcome/customer field slice，也不计算 MAE、区间覆盖、风险排序、漏报恢复、false alarm 或 decision value。
- 因此 L21 不能证明 R12 已 field-validated、customer-validated 或 runtime-default-ready；它只能证明客户数据回流入口已经可交付。

### R12 L22：Customer field slice intake validation

目标：把 L21 的客户 handoff package 推进为真实数据到达后的 intake validator。L22 不计算效果指标；它只检查客户 field slice 是否满足合同、安全、隐私和质量要求，避免 PII、坏数值、坏时间戳或重复 case 进入 revalidation。

当前已实现：

- `experiments/r12_customer_field_slice_intake_validation.py`
- `tests/test_r12_customer_field_slice_intake_validation.py`
- `experiments/results/r12_customer_field_slice_intake_validation/r12-customer-field-slice-intake-validation-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L22 intake artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L22 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L22 intake 状态、`ready_for_revalidation`、privacy/numeric/timestamp/duplicate gates、case count 和下一步 artifact。

当前 L22 intake checks：

- required fields present：`case_id`、`segment_id`、`scenario_id`、`prediction_share_or_score`、`observed_outcome`、`outcome_timestamp`、`customer_approval_reference`。
- minimum case count：10。
- customer approval reference non-empty。
- direct PII columns blocked：`email`、`phone`、`name`、`full_name`、`address`、`ssn`、`id_card`、`passport`。
- direct PII values blocked：当前至少检查 email pattern。
- numeric fields parseable：`prediction_share_or_score`、`observed_outcome`。
- timestamp parseable：`outcome_timestamp`。
- duplicate `case_id` blocked。

当前 L22 gates：

- `customer_field_slice_submitted=false`。
- `ready_for_revalidation=false`。
- `metrics_computed=false`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L22 结论：

- L22 让 Product 的客户数据回流链路从“模板可交付”升级为“数据到达后可机器 intake 校验”。
- 当前没有真实客户 field slice，因此 current artifact 是 `r12_customer_field_slice_intake_validation_pending_no_slice`。
- L22 仍不是 validation artifact；它只决定数据能否进入后续 revalidation，不证明 R12 方法有效，也不允许 Product default / runtime default。

### R12 L23：Customer field slice revalidation

目标：把 L22 的 validated intake 推进为可计算的 customer field metrics。L23 不负责接收原始客户数据，也不绕过 intake；它只在 L22 `ready_for_revalidation=true` 时读取已校验 slice 并计算指标。若没有 validated intake，则 fail-closed。

当前已实现：

- `experiments/r12_customer_field_slice_revalidation.py`
- `tests/test_r12_customer_field_slice_revalidation.py`
- `experiments/results/r12_customer_field_slice_revalidation/r12-customer-field-slice-revalidation-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L23 revalidation artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L23 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L23 revalidation 状态、metrics computed、field outcome validated、MAE、risk ranking quality 和下一步 artifact。

当前 L23 metrics：

- `mean_absolute_error`
- `mean_signed_error`
- `risk_ranking_quality`
- `top_quintile_overlap`
- `mae_threshold`
- `risk_ranking_quality_threshold`

当前 L23 gates：

- `validated_intake_ready=false`。
- `customer_field_slice_present=false`。
- `metrics_computed=false`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L23 结论：

- L23 让客户 field outcome 回流链路具备完整的“handoff -> intake -> metrics revalidation”执行骨架。
- 当前没有 validated intake，因此 current artifact 是 `r12_customer_field_slice_revalidation_blocked_no_validated_intake`。
- 即使未来某个客户 field slice metrics 通过，Product default 仍不会自动打开；它只能进入 customer outcome evidence review 和后续 feedback update。

### R12 L24：Customer field outcome feedback update

目标：把 L23 的 customer field metrics 推进为受约束的 feedback update 候选生成器。L24 不直接修改 prompt/persona，也不把一次客户结果回流升级为 Product default；它只在 L23 `field_outcome_validated=true` 且 `metrics_computed=true` 时，把误差方向和风险排序质量转成结构化参数更新候选，进入 shadow review。

当前已实现：

- `experiments/r12_customer_field_outcome_feedback_update.py`
- `tests/test_r12_customer_field_outcome_feedback_update.py`
- `experiments/results/r12_customer_field_outcome_feedback_update/r12-customer-field-outcome-feedback-update-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L24 feedback update artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L24 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L24 feedback update 状态、metrics consumed、candidate count、prompt/persona patch guard 和下一步 artifact。

当前 L24 gates：

- `field_outcome_validated=false`。
- `metrics_consumed=false`。
- `candidate_updates_generated=false`。
- `prompt_or_persona_manual_patch_allowed=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L24 结论：

- L24 把“真实结果回流后如何优化方法”从口头计划推进为可审计 artifact：验证通过时生成结构化参数更新候选，验证缺失时 fail-closed。
- 当前没有 validated field outcome，因此 current artifact 是 `r12_customer_field_outcome_feedback_update_blocked_no_field_validation`，候选数为 0。
- L24 仍不能证明 R12 已完成客户 field validation；它只能证明 Product 的客户结果回流闭环已经具备从 metrics 到 shadow-review candidate 的机器可验收路径。

### R12 L25：Customer feedback update shadow replay

目标：把 L24 生成的 feedback update 候选推进到 shadow replay gate。L25 不重新接收客户原始数据，也不直接启用候选；它只判断是否存在候选，并在有候选时计算保守 replay 指标，确认候选是否至少具备 shadow-review 价值。

当前已实现：

- `experiments/r12_customer_feedback_update_shadow_replay.py`
- `tests/test_r12_customer_feedback_update_shadow_replay.py`
- `experiments/results/r12_customer_feedback_update_shadow_replay/r12-customer-feedback-update-shadow-replay-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L25 shadow replay artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L25 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L25 shadow replay 状态、replay executed、accepted candidate count 和下一步 artifact。

当前 L25 gates：

- `feedback_candidates_present=false`。
- `shadow_replay_executed=false`。
- `at_least_one_candidate_passed=false`。
- `false_alarm_non_regression=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L25 结论：

- L25 把“候选生成之后如何继续评估”从人工判断推进为可审计 shadow replay gate。
- 当前 L24 没有候选，因此 current artifact 是 `r12_customer_feedback_update_shadow_replay_blocked_no_candidates`，不会执行 replay。
- L25 仍不能证明 feedback update 已有效；它只能证明如果未来 L24 产生候选，系统已有 shadow replay 审核入口，且默认启用仍被阻断。

### R12 L26：Customer feedback shadow replay holdout review

目标：把 L25 accepted shadow replay candidate 继续推进到独立 holdout review gate。L26 不使用客户原始数据、不自动启用 candidate；它只在两类条件同时满足时执行 review：一是 L25 存在 accepted shadow candidate，二是存在独立或客户批准的 holdout source，且 case 数达到最小门槛。否则保持 fail-closed。

当前已实现：

- `experiments/r12_customer_feedback_shadow_replay_holdout_review.py`
- `tests/test_r12_customer_feedback_shadow_replay_holdout_review.py`
- `experiments/results/r12_customer_feedback_shadow_replay_holdout_review/r12-customer-feedback-shadow-replay-holdout-review-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L26 holdout review artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L26 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L26 holdout review status、executed、passed、independent holdout case count 和下一步 artifact。

当前 L26 gates：

- `accepted_shadow_candidates_present=false`。
- `independent_holdout_present=false`。
- `holdout_review_executed=false`。
- `holdout_review_passed=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L26 结论：

- L26 把“shadow replay candidate 是否能进入默认更新”前的最后一层独立复核显式化。
- 当前没有 L25 accepted shadow candidate，因此 current artifact 是 `r12_customer_feedback_shadow_replay_holdout_review_blocked_no_shadow_candidates`，不会执行 holdout review。
- L26 仍不能证明 feedback update 有效；它只能证明如果未来 L25 产生 accepted candidate，系统仍会要求独立或客户批准 holdout review，并继续阻断 Product/runtime default。

### R12 L27：Customer validation workflow status

目标：把 L20-L26 从一串分散 artifact 合并成 Product 可展示、operator 可执行的客户验证工作流状态包。L27 不新增方法效果，不宣称 field validation；它只回答三个问题：当前验证链路卡在哪一步、下一步该执行什么、哪些 source artifact 支撑这个判断。

当前已实现：

- `experiments/r12_customer_validation_workflow_status.py`
- `tests/test_r12_customer_validation_workflow_status.py`
- `experiments/results/r12_customer_validation_workflow_status/r12-customer-validation-workflow-status-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L27 workflow status artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L27 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 blocked claims。
- `demo/app.js` 已展示 L27 workflow status、current stage、next action、source arrived 和 blocking artifact。

当前 L27 gates：

- `workflow_status_package_ready=true`。
- `source_arrival_gate_ready=true`。
- `customer_data_request_ready=true`。
- `customer_slice_ready_for_revalidation=false`。
- `field_outcome_validated=false`。
- `feedback_candidates_present=false`。
- `shadow_replay_executed=false`。
- `holdout_review_executed=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L27 结论：

- L27 把“等待真实 source”从被动 blocker 转成 Product 可执行工作流：客户 field slice 或 target outcome 到达后，先跑 intake validation，再跑 field revalidation、feedback update、shadow replay 和 holdout review。
- 当前状态为 `r12_customer_validation_workflow_waiting_for_source`，current stage 是 `source_arrival_pending`。
- L27 仍不能证明 Research 已全面支撑 Product；它只是让 Product 能清楚展示验证链路、阻断原因和 operator runbook。

### R12 L28：Customer trial readiness package

目标：把 L21 customer field slice handoff package 和 L27 workflow status 合并成 Product 可交付的客户试运行准备包。L28 不新增方法效果、不宣称 field validation；它只回答“是否已经可以向客户发起可审计的数据回流/试运行请求，以及客户和 operator 需要做什么”。

当前已实现：

- `experiments/r12_customer_trial_readiness_package.py`
- `tests/test_r12_customer_trial_readiness_package.py`
- `experiments/results/r12_customer_trial_readiness_package/r12-customer-trial-readiness-package-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L28 trial readiness package artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L28 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 source refs。
- `demo/app.js` 已展示 L28 trial package status、template path、minimum case count 和 current stage。

当前 L28 gates：

- `trial_readiness_package_ready=true`。
- `customer_data_request_ready=true`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。
- `minimum_case_count=10`。
- `required_field_count=7`。
- `manual_approval_point_count=2`。

L28 结论：

- L28 把“等待客户数据”推进成“客户试运行准备已就绪”：Product 可以展示模板、字段、审批点、操作清单和 source-backed 证据链。
- 当前状态为 `r12_customer_trial_readiness_package_ready_guarded_source_pending`，current stage 仍是 `source_arrival_pending`。
- L28 仍不能证明 Research 已全面支撑 Product；它只是让 Product 进入可发起客户 field slice 回流的准备状态。

### R12 L29：Customer trial operational check

目标：对 L28 客户试运行准备包做可操作性检查，防止 Product 只展示纸面 runbook。L29 不新增方法效果、不宣称 field validation；它只确认模板、source registry 和 operator runbook 在当前 repo 中可解析、可交付、可审计。

当前已实现：

- `experiments/r12_customer_trial_operational_check.py`
- `tests/test_r12_customer_trial_operational_check.py`
- `experiments/results/r12_customer_trial_operational_check/r12-customer-trial-operational-check-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L29 operational check artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L29 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 source refs。
- `demo/app.js` 已展示 L29 operational check status、operational ready、source registry resolvable 和 runbook declared。

当前 L29 gates：

- `trial_readiness_package_loaded=true`。
- `template_path_resolvable=true`。
- `template_required_fields_present=true`。
- `source_registry_resolvable=true`。
- `operator_runbook_declared=true`。
- `customer_trial_request_operationally_ready=true`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L29 结论：

- L29 把“客户试运行准备包”从静态清单推进为可操作性已检查的 Product evidence：模板、source、命令和审批点都能被机器检查。
- 当前状态为 `r12_customer_trial_operational_check_ready_source_pending`，current stage 仍是 `source_arrival_pending`。
- L29 仍不能证明 Research 已全面支撑 Product；它只是让 Product 更可靠地发起客户 field slice 回流。

### R12 L30：Customer trial launch handoff package

目标：把 L28/L29 的试运行准备状态转成客户可读、可发起的数据回流交付包。L30 不新增方法效果、不宣称 field validation；它只把数据请求、字段模板、审批清单、提交说明、operator runbook 和 claim boundary 组织成 Product 可展示的 launch handoff package。

当前已实现：

- `experiments/r12_customer_trial_launch_handoff_package.py`
- `tests/test_r12_customer_trial_launch_handoff_package.py`
- `experiments/results/r12_customer_trial_launch_handoff_package/r12-customer-trial-launch-handoff-package-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L30 launch handoff package artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L30 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 source refs。
- `demo/app.js` 已展示 L30 launch package status 和 launch handoff ready。

当前 L30 gates：

- `launch_handoff_package_ready=true`。
- `trial_readiness_package_ready=true`。
- `operational_check_ready=true`。
- `customer_trial_request_operationally_ready=true`。
- `customer_field_slice_present=false`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L30 结论：

- L30 把“试运行准备已就绪”推进成“可向客户发起 field slice 回流请求”的 Product handoff package。
- 当前状态为 `r12_customer_trial_launch_handoff_package_ready_source_pending`，current stage 仍是 `source_arrival_pending`。
- L30 仍不能证明 Research 已全面支撑 Product；它只是把客户验证入口做成更完整的可交付包。

### R12 L31：Customer trial launch packet export

目标：把 L30 launch handoff package 转成客户可读、可审计、可发送的 JSON/Markdown launch packet。L31 不新增方法效果、不宣称 field validation；它只把客户数据回流请求、字段模板摘要、提交说明、operator runbook、claim boundary 和验收门禁导出为 Product 可交付材料。

当前已实现：

- `experiments/r12_customer_trial_launch_packet_export.py`
- `tests/test_r12_customer_trial_launch_packet_export.py`
- `experiments/results/r12_customer_trial_launch_packet_export/r12-customer-trial-launch-packet-export-current-001.json`
- `experiments/results/r12_customer_trial_launch_packet_export/r12-customer-trial-launch-packet-current-001.md`
- `experiments/r12_product_support_gate.py` 已支持消费 L31 launch packet export artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L31 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 source refs。
- `demo/app.js` 已展示 L31 packet export status、Markdown 写入状态、Markdown 输出路径，并通过 source-backed `markdown_output_path` 生成打开 Markdown packet 的入口。

当前 L31 gates：

- `launch_packet_export_ready=true`。
- `markdown_export_written=true`。
- `launch_handoff_ready=true`。
- `customer_field_slice_present=false`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L31 结论：

- L31 把“可向客户发起 field slice 回流请求”的 Product handoff package 推进为可交付 launch packet，并让 `/demo/` 能直接打开该 Markdown packet。
- 当前状态为 `r12_customer_trial_launch_packet_export_ready_source_pending`，current stage 仍是 `source_arrival_pending`。
- L31 仍不能证明 Research 已全面支撑 Product；它只是把客户验证入口从内部 artifact 推进为客户可读导出物。

### R12 L32：Customer trial launch bundle verification

目标：把 L31 launch packet export 推进为可机器校验的客户试运行 bundle。L32 不新增方法效果、不宣称 field validation；它只校验 packet export JSON、客户可读 Markdown packet、L30 handoff JSON 和客户 field slice 模板是否可解析，并记录 size 与 SHA-256，避免客户交付物散落且不可审计。

当前已实现：

- `experiments/r12_customer_trial_launch_bundle_verification.py`
- `tests/test_r12_customer_trial_launch_bundle_verification.py`
- `experiments/results/r12_customer_trial_launch_bundle_verification/r12-customer-trial-launch-bundle-verification-current-001.json`
- `experiments/r12_product_support_gate.py` 已支持消费 L32 launch bundle verification artifact。
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json` 已刷新 L32 边界。
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json` 已刷新 R12 evidence summary。
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json` 已刷新 source registry 与 source refs。
- `demo/app.js` 已展示 L32 bundle verification status、bundle verified、required item count 和 missing required item ids，并新增 source-backed 客户试运行行动面板，展示 current stage、客户下一步、packet 入口和 bundle verification。

当前 L32 gates：

- `launch_bundle_verified=true`。
- `packet_export_json_resolvable=true`。
- `markdown_packet_resolvable=true`。
- `launch_handoff_json_resolvable=true`。
- `field_slice_template_resolvable=true`。
- `all_required_bundle_items_resolvable=true`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L32 结论：

- L32 把“客户可读 launch packet 已导出”推进成“客户试运行交付 bundle 可解析、可审计、可复核”，并让 `/demo/` 从 R12 evidence summary 直接展示客户试运行下一步。
- 当前状态为 `r12_customer_trial_launch_bundle_verification_ready_source_pending`，current stage 仍是 `source_arrival_pending`。
- L32 仍不能证明 Research 已全面支撑 Product；它只是把客户验证入口从可读导出物推进为完整性交付包。

### R12 L33：Public target outcome availability refresh harness

目标：把“等待 May 2026 target outcome”从人工记忆变成可测试的官方来源快照刷新 harness。L33 不新增方法效果、不宣称 field validation；它只消费 DOT 官方页面快照，判断 `July 2026 Air Travel Consumer Report (May 2026 Data)` 是否出现，并记录是否需要进入 raw target outcome slice ingestion。

当前已实现：

- `experiments/r12_public_target_outcome_availability_refresh.py`
- `tests/test_r12_public_target_outcome_availability_refresh.py`

当前 L33 gates：

- `official_source_snapshot_checked=true`。
- `target_report_found` 由官方页面快照解析得出。
- `target_table_available` 只在 target report 和 Table 3 / Consumer Complaints 线索同时出现时为 true。
- `target_outcome_artifact_present=false`。
- `field_or_pre_outcome_revalidation_ready=false`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L33 失败保护：

- 若本地抓取结果是 `Access Denied`、`you don't have permission`、`request blocked` 或页面里没有 `Air Travel Consumer Report`，harness 会直接拒绝该 snapshot。
- 因此 L33 不会把抓取失败误判为 target outcome 尚未发布。
- 当前本地 `curl` DOT 官方页面只能得到 Akamai `Access Denied`，因此没有生成可信 current availability artifact。

L33 结论：

- L33 把 target outcome availability refresh 做成了可测试 harness，但没有解除 R12 的核心阻断。
- 真正的下一步仍是拿到可用官方 HTML/PDF/raw table 或客户授权 field slice，然后进入 raw slice ingestion、intake、revalidation、feedback update 和 holdout review。
- Product `/demo/` 现在新增 source-backed 试运行工作台，展示 `场景输入 -> 群体与先验 -> 运行闸门 -> 报告导出 -> outcome review` 五步；该工作台只消费 `apiManifest` 与 R12 evidence summary，不新增方法效果，也不改变 `field_outcome_validated=false` 和 `runtime_default_allowed=false`。
- Product `/demo/` 现在新增客户 field slice 本地 intake preview，按 L22 同源规则检查 `.csv/.jsonl` 的字段、case 数、审批引用、PII、数值、时间戳和重复 case；preview 通过只生成 `ready_for_operator_review` revalidation handoff 清单和 operator command 模板，不上传服务器、不生成 metrics、不改变 Product default。

## Task 34：Customer field slice operator rehearsal（已完成）

L34 目的不是验证客户效果，而是把 L22/L21 对应的 operator command 从“前端模板”推进到“可实际演练的本地命令链路”。

L34 已新增：

- `experiments/r12_customer_field_slice_operator_rehearsal.py`
- `tests/test_r12_customer_field_slice_operator_rehearsal.py`
- `experiments/results/r12_customer_field_slice_operator_rehearsal/r12-customer-field-slice-operator-rehearsal-current-001.json`
- `experiments/results/r12_customer_field_slice_operator_rehearsal/rehearsal-work-current-001/r12-customer-field-slice-rehearsal-sample.csv`
- `experiments/results/r12_customer_field_slice_operator_rehearsal/rehearsal-work-current-001/r12-customer-field-slice-intake-validation-rehearsal.json`

L34 已接入：

- `experiments/r12_product_support_gate.py`
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json`
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json`
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json`
- Product `/demo/` field slice / workflow / trial / R12 evidence panels

当前 L34 gates：

- `synthetic_rehearsal_fixture_generated=true`。
- `operator_command_rehearsed=true`。
- `intake_validator_executed=true`。
- `sample_slice_intake_ready_for_revalidation=true`。
- `real_customer_field_slice_submitted=false`。
- `metrics_computed=false`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L34 结论：

- Product 现在可以展示“客户 field slice 到达后，operator 入口和 intake 命令已演练过”。
- 这只证明操作链路可执行，不证明真实客户 outcome、真实 field metrics 或 Product default。
- 下一步仍是等待真实客户 field slice 或 public target outcome 到达后，运行 L22/L23/L24/L25/L26。

## Task 35：Customer feedback loop operator rehearsal（已完成）

L35 目的不是验证客户效果，而是把 L22-L26 的客户反馈闭环从“各阶段独立可跑”推进到“完整 operator 链路可连续执行”。

L35 已新增：

- `experiments/r12_customer_feedback_loop_operator_rehearsal.py`
- `tests/test_r12_customer_feedback_loop_operator_rehearsal.py`
- `experiments/results/r12_customer_feedback_loop_operator_rehearsal/r12-customer-feedback-loop-operator-rehearsal-current-001.json`
- `experiments/results/r12_customer_feedback_loop_operator_rehearsal/rehearsal-work-current-001/*feedback-loop-rehearsal*.json`
- `experiments/results/r12_customer_feedback_loop_operator_rehearsal/rehearsal-work-current-001/r12-customer-feedback-loop-rehearsal-sample.csv`

L35 已接入：

- `experiments/r12_product_support_gate.py`
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json`
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json`
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json`
- Product `/demo/` field slice / workflow / trial / R12 evidence panels

当前 L35 gates：

- `synthetic_rehearsal_fixture_generated=true`。
- `l22_intake_validator_executed=true`。
- `l23_field_revalidation_executed=true`。
- `l24_feedback_candidates_generated=true`。
- `l25_shadow_replay_executed=true`。
- `l26_synthetic_holdout_review_executed=true`。
- `real_customer_field_slice_submitted=false`。
- `real_independent_holdout_present=false`。
- `field_outcome_validated=false`。
- `metrics_computed_on_real_customer_slice=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L35 结论：

- Product 现在可以展示“客户 field slice 到达后的 L22-L26 operator 闭环已演练过”。
- 这只证明完整链路可执行，不证明真实客户 outcome、真实 field metrics、真实 independent holdout 或 Product default。
- 下一步仍是等待真实客户 field slice 或 public target outcome 到达后，运行真实 L22-L26，并把 synthetic rehearsal 与真实 validation artifact 分开展示。

## Task 36：Customer trial evidence ledger（已完成）

L36 目的不是新增方法效果，而是把“客户试运行准备度”和“operator 演练”从分散 artifact 聚合成一个可审计账本，方便 Product 对客户说明当前已经准备好哪些东西、哪些仍被阻断。

L36 已新增：

- `experiments/r12_customer_trial_evidence_ledger.py`
- `tests/test_r12_customer_trial_evidence_ledger.py`
- `experiments/results/r12_customer_trial_evidence_ledger/r12-customer-trial-evidence-ledger-current-001.json`

L36 已接入：

- `experiments/r12_product_support_gate.py`
- `experiments/results/r12_product_support_gate/r12-product-support-gate-current-001.json`
- `experiments/results/r6_product_customer_value_report/r6-product-customer-value-report-current-001.json`
- `experiments/results/r6_product_api_manifest/r6-product-api-manifest-current-001.json`
- Product `/demo/` workflow / trial / R12 evidence panels

当前 L36 gates：

- `customer_trial_evidence_ledger_ready=true`。
- `launch_bundle_verified=true`。
- `operator_rehearsal_executed=true`。
- `feedback_loop_rehearsed_l22_to_l26=true`。
- `real_customer_field_slice_submitted=false`。
- `metrics_computed_on_real_customer_slice=false`。
- `field_outcome_validated=false`。
- `product_default_allowed=false`。
- `runtime_default_allowed=false`。

L36 结论：

- Product 现在可以展示“客户试运行交付物、operator 演练和反馈闭环演练已形成可追溯证据账本”。
- 账本包含 1 条 customer-visible readiness evidence、2 条 operator-only rehearsal evidence 和 3 个 blocking gaps。
- 这只证明试运行证据链可审计，不证明真实客户 field slice、真实 field metrics、真实 feedback update 或 Product default。

### 2026-06-29 阶段性 scope 调整：公开数据验证优先

当前阶段先不把真实客户 field validation 作为必须完成项。客户 field slice、客户批准 holdout 和 field outcome validation 继续保留为后续企业试运行能力，但不是本阶段 Product/Research 宣传成立的前置条件。

本阶段允许的对外主张调整为：

> R12 已在公开数据上进行受约束测试，并在 guarded hindcast / replay 指标上显示有效。

该主张只在以下条件同时满足时允许：

- `r12_external_or_customer_holdout_raw_slice` 存在，且来源为可审计公开数据。
- `r12_pre_outcome_or_independent_prediction_packet` 存在，且 prediction source 不直接读取目标 outcome。
- `r12_independent_hindcast_revalidation` 已执行并通过。
- `false_alarm_non_regression=true`。
- Product gate 显式记录 `public_data_effectiveness_claim_allowed=true`、`customer_field_validation_required_for_current_stage=false` 和 `runtime_default_allowed=false`。

该主张不能扩张为：

- 客户 field outcome validated。
- 精准单点预测。
- Product runtime default ready。
- R12 可覆盖 guarded baseline 主决策。

## 当前推荐推进顺序

1. R12 L0/L1 已完成：case registry 和 operator contract 已建立。
2. R12 L2 已完成：train residual 已生成可审计结构化更新。
3. R12 L3 已完成：当前 HPS public-use proxy split 上存在 guarded positive transfer signal。
4. R12 L4 已完成：只以 guarded evidence card / API manifest source refs / blocked claims 的方式接入 Product，不覆盖主决策，不开启 runtime default。
5. R12 L5 已完成：已找到 29 个 source-backed research-only 高风险 holdout 候选，其中 12 个可用于验证静态先验漏报恢复；但 Product 默认可用的低敏感高风险 holdout 仍为 0。
6. R12 L6 已完成：high-risk replay 有 MAE 小幅正向，但 static-prior miss recovery 和 abnormal segment recall 没有提升，false alarm 不可评估，Product default 仍阻断。
7. R12 L7 已完成：activation margin recall-oriented update 让 high-risk recall 相关指标提升 `0.206897`，但引入 false alarm 与 precision 代价，Product default 仍阻断。
8. R12 L8 已完成：false-alarm stress test 保留 L7 recall gain，但确认 Product default 被 global false alarm、precision regression、low-sensitive recall 不可验和 protected-sensitive 年龄轴误报集中共同阻断。
9. R12 L9 已完成：false-alarm mitigation candidate 保留 `0.833333` 的 L7 recall gain，消除当前新增 false alarm，并把 precision delta 改为 `+0.059524`；但候选来自当前 false-alarm band，Product default 仍阻断。
10. R12 L10 已完成：mitigation holdout validation 显示 leave-one pass rate 只有 `0.333333`，端点 holdout 失败 2 个，L9 guard 没有通过泛化验证。
11. R12 L11 已完成：independent holdout data audit 显示当前没有可解除阻断的独立数据、低敏感可召回切片或客户授权 outcome。
12. R12 L12 已完成：external/customer slice contract 就绪，但 raw external/customer holdout slice 仍缺失。
13. R12 L13 已完成：DOT ATCR official raw complaint slice 已接入，raw slice 缺失阻断解除，但预测字段和 revalidation 仍缺失。
14. R12 L14 已完成：external holdout proxy revalidation 已可计算，出现 MAE、区间、风险排序和静态漏报恢复的诊断性正向信号，但 false alarm 上升且 prediction 非独立，因此 Product default 仍阻断。
15. R12 L15 已完成：March 2026 official prior-month source 已生成 independent hindcast prediction packet，prediction 不使用 April target outcome，但不是 pre-outcome locked packet。
16. R12 L16 已完成：independent-feature hindcast revalidation 相对静态均匀先验改善 MAE、区间覆盖、风险排序、静态先验漏报恢复和决策价值，且 false alarm 不退化；但仍不是 pre-outcome locked 或 field outcome validation。
17. R12 L17 已完成：May 2026 target outcome 的 pre-outcome public DOT trial 已锁定，客户 field slice revalidation 合同已就绪；但 target outcome / customer field slice 尚未回流。
18. R12 L18 已完成：outcome ingestion audit 已确认 public target outcome 和 customer field slice 均未回流，Product 只能展示 pending boundary。
19. R12 L19 已完成：fail-closed outcome revalidation harness 已就绪，缺少 target outcome 或客户 field slice 时不计算指标、不解锁 Product default。
20. R12 L20 已完成：target outcome/customer field slice arrival gate 已就绪，当前 source 仍未到达；客户授权 field slice 到达时可先做合同校验并打开 revalidation-ready。
21. R12 L21 已完成：customer field slice handoff package 已就绪，客户数据请求、字段模板、隐私边界和审批要求已可机器校验。
22. R12 L22 已完成：customer field slice intake validator 已就绪，可检查 PII、字段、case 数、审批、数值、时间戳和重复 case；当前没有客户 slice，因此保持 pending。
23. R12 L23 已完成：customer field slice revalidation calculator 已就绪；当前没有 validated intake，因此保持 blocked/no metrics。
24. R12 L24 已完成：customer field outcome feedback update 候选生成器已就绪；当前没有 validated field outcome，因此保持 blocked/no candidates。
25. R12 L25 已完成：customer feedback update shadow replay gate 已就绪；当前没有 L24 候选，因此保持 blocked/no replay。
26. R12 L26 已完成：customer feedback shadow replay holdout review gate 已就绪；当前没有 accepted shadow candidate，因此保持 blocked/no holdout review。
27. R12 L27 已完成：customer validation workflow status 已就绪；当前 stage 是 `source_arrival_pending`，Product 可展示下一步 operator runbook，但仍等待真实 source。
28. R12 L28 已完成：customer trial readiness package 已就绪；Product 可展示客户试运行模板、最少 case 数、必需字段、审批点和 operator runbook，但仍等待真实 source。
29. R12 L29 已完成：customer trial operational check 已就绪；Product 可展示模板、source registry 和 operator runbook 均已通过可操作性检查，但仍等待真实 source。
30. R12 L30 已完成：customer trial launch handoff package 已就绪；Product 可展示客户数据请求、字段模板、审批清单、提交说明、operator runbook 和 claim boundary，但仍等待真实 source。
31. R12 L31 已完成：customer trial launch packet export 已就绪；Product 可展示客户可读 Markdown launch packet、导出状态和 claim boundary，但仍等待真实 source。
32. R12 L32 已完成：customer trial launch bundle verification 已就绪；Product 可展示 launch packet、handoff JSON 和字段模板的文件完整性、size 与 SHA-256，但仍等待真实 source。
33. R12 L33 已完成：public target outcome availability refresh harness 已就绪；Product/Research 可用官方页面快照检查 target report 是否出现，但本地 `curl` 当前被 DOT/Akamai 阻断时必须 fail-closed，不得写成未发布结论。
34. R12 L34 已完成：customer field slice operator rehearsal 已就绪；Product 可展示 operator command 已在 synthetic rehearsal fixture 上调用真实 L22 intake validator 跑通，但仍不宣称真实客户数据到达、metrics computed 或 field validation passed。
35. R12 L35 已完成：customer feedback loop operator rehearsal 已就绪；Product 可展示 L22-L26 完整反馈闭环已在 synthetic fixture 上连续执行，但仍不宣称真实客户 field slice、真实 independent holdout、field validation 或 runtime default。
36. R12 L36 已完成：customer trial evidence ledger 已就绪；Product 可展示客户试运行准备度、operator 演练和反馈闭环演练的统一证据账本，但仍不宣称真实客户 field slice、真实 metrics、field validation 或 runtime default。
37. R12 L37 已完成：real-source validation execution packet 已就绪，source 到达后的 L22-L26 命令、人工审批点、输出路径和 blocked claims 已可审计；它只是执行包，不是验证结果。
38. 下一步优先完成 public-data validation package：把 DOT/BTS/HPS 等公开数据的 benchmark、hindcast、pre-outcome lock、outcome arrival revalidation 和 report export 做成可复现证据链；客户 field validation 链路保留为后续企业试运行扩展，不作为本阶段宣传成立的前置条件。

## 成功信号

R12 的最小成功信号不是“指标全赢”，而是：

- 在 holdout case 上，结构化 outcome update 至少改善一个 Product-relevant 指标；
- 没有牺牲 interval coverage；
- 没有不可解释或不可治理地增加 false alarm；
- 能解释为什么 update 对某类机制或群体可迁移；
- 能明确阻断不该迁移的更新。

## 当前判断

R12 目前拿到了比 R11 更强的最低正向信号：R11 只能证明 feedback ledger 可审计，R12 L3 已证明一个 train-only 结构化 mechanism update 能在 validation / holdout 上产生小幅正向迁移，且没有牺牲区间覆盖和 false alarm；R12 L5/L6 进一步找到了 high-risk replay 材料，并证明当前 update 在 high-risk research-only replay 上有 MAE 小幅正向；R12 L7 则进一步证明 activation margin 这类结构化阈值候选可以提升 static-prior miss recovery 与 abnormal segment recall；R12 L8 又把该召回增益的 false-alarm 失败边界量化出来；R12 L9 进一步说明 false-alarm 代价存在可缓解候选；R12 L10 则证明该候选没有通过 holdout 稳定性，只能保留为 failure diagnosis candidate；R12 L11 进一步证明当前数据条件不足以解除 Product default 阻断；R12 L12 把外部/客户 holdout 接入条件合同化；R12 L13 已接入 DOT ATCR official raw complaint slice；R12 L14/L15/L16 则把 raw outcome slice 推进到 proxy revalidation、independent prediction packet 和 independent-feature hindcast revalidation。L16 当前相对静态均匀先验在 MAE、区间覆盖、风险排序、静态先验漏报恢复和决策价值上都有正向信号，且 false alarm 不退化。L17 进一步把这个正向信号转成真正 pre-outcome trial lock。L18-L32 确认当前 target outcome 尚未回流，并把客户 field slice 入口、fail-closed revalidation harness、source-arrival gate、customer field slice handoff package、intake validator、field metrics calculator、feedback update candidate generator、shadow replay gate、独立 holdout review gate、客户验证工作流状态包、客户试运行准备包、operational check、launch handoff package、launch packet export 和 launch bundle verification 固化。

但这个结果仍不足以说 Research 已全面支撑 Product。当前最准确的表述是：

> R12 在 HPS public-use proxy split 上形成了 guarded positive transfer signal，在 research-only high-risk replay 上取得 MAE 小幅改善，通过 activation margin 候选提升了 high-risk recall，并找到一个能消除当前新增误报的 research-only mitigation candidate；但 L10 已证明该候选未通过 leave-one holdout 稳定性，L11 又证明当前没有可解除阻断的 independent holdout / low-sensitive / customer-approved validation。L13-L32 已把 DOT ATCR official raw complaint slice 推进为 independent-feature hindcast revalidation、pre-outcome trial lock、outcome ingestion pending audit、fail-closed revalidation harness、source-arrival gate、customer field slice handoff package、intake validator、field metrics calculator、feedback update candidate generator、shadow replay gate、独立 holdout review gate、客户验证工作流状态包、客户试运行准备包、operational check、launch handoff package、launch packet export 和 launch bundle verification，并拿到比静态均匀先验更强的历史风险发现信号；因此本阶段可以做“公开数据测试有效”的 guarded claim，但它仍不是 customer field validated、精准预测或 runtime-default-ready 的 Product core method。
