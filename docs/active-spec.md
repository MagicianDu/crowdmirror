# Active Spec

## 当前唯一事实源

当前 Research / Product 双线的 active spec 由一个主控 spec 和一个当前阶段 addendum 组成：

- `docs/superpowers/specs/2026-06-05-r6-outcome-feedback-prior-anchored-interaction-simulation-spec.md`
- `docs/superpowers/specs/2026-06-06-r6-method-gates-transfer-protocol-spec.md`
- `docs/superpowers/specs/2026-06-11-r6-risk-discovery-method-spec.md`

工作名：

- 中文：R6 结果反馈约束的先验锚定交互仿真框架
- English: Outcome-Feedback Prior-Anchored Interaction Simulation

其中：

- `2026-06-05-r6-outcome-feedback-prior-anchored-interaction-simulation-spec.md` 定义 R6 的总体问题、方法边界和 foundation artifact chain。
- `2026-06-06-r6-method-gates-transfer-protocol-spec.md` 定义当前阶段的 evidence levels、acceptance gates、cross-case transfer protocol 和止损边界。
- `2026-06-11-r6-risk-discovery-method-spec.md` 定义 R6 下一阶段的风险发现目标、decision-value 指标和 holdout validation 协议。

后续实现若与历史 R2-R5、旧 prompt/persona 优化、单一 proxy 扩张路线冲突，以当前阶段 addendum 为准。

## 当前目标

项目当前目标不是继续证明某个 prompt、persona、TextGrad、LCDU、R4 interaction 或 R5 mechanism-state 变体在单一静态数据集上更准。

当前目标是：

> 基于真实人口、客户或群体先验，构建一个可审计的交互仿真沙盘，用于在政策、规则、价格、权益、服务变更发布前评估人群反应，并在真实结果回流后持续校正方法。

## 当前方法边界

R6 必须同时满足：

1. 强先验作为无交互基础状态和 no-interaction control。
2. 交互仿真用于发现静态先验无法覆盖的风险偏移。
3. 未接入真实 outcome 前，不宣称交互仿真一定更准。
4. 真实 outcome 回来后，必须生成误差归因和受约束的方法更新候选。
5. 垂直场景只能作为 case template，不能把方法过拟合到单一行业。

关键修正：

- 静态先验不是 R6 要击败的“对手”，而是大规模仿真的底座。
- 候选更新如果要进入 runtime default，必须通过不伤害静态先验的护栏。
- Research/Product 的主价值 gate 不是单一 aggregate accuracy race，而是：交互层是否发现静态先验看不到的风险、是否能形成可审计证据链、真实 outcome 回来后是否能学习失败边界并更新方法。

## 当前实现范围

第一阶段只推进 R6 foundation：

1. `r6_prior_manifest`
2. `r6_scenario_manifest`
3. `r6_interaction_trace`
4. `r6_risk_shift_report`
5. `r6_outcome_manifest`
6. `r6_learning_report`
7. `r6_update_registry`

当前阶段已从 foundation artifact 扩展到方法验收层，只推进：

1. `cross-case transfer protocol artifact`
2. `in-condition holdout 搜索标准`
3. `Product evidence card contract`
4. `decision-value metrics`
5. `risk-discovery holdout validation`
6. `risk-discovery threshold sweep / false-alarm discriminator diagnosis`
7. `Interaction Signal Validity Score / holdout validation`

不再把“继续增加 public proxy 数量”作为默认目标；只有当新增数据能触发 acceptance gate，才进入数据接入。

## 降权历史材料

以下材料只作为历史经验或基础设施参考，不再作为当前主线：

- LCDU / LCDU-hybrid / LCDU-LCR-SG：静态强先验、历史校准和 gate 参考。
- DCL-PRS：历史反例和诊断资产，不作为主算法。
- MCR-Gate：accepted/rejected ledger 与 failure diagnosis 基础设施。
- R4：population / environment / interaction / memory / gate artifact chain 参考。
- R5：机制解释和 Product audit 参考。
- TextGrad / DSPy / GA / prompt-persona patch：可选候选生成工具，不是主算法本体。

## 继续开发闸门

继续开发 R6 前必须满足：

- 新代码和测试文件使用 `r6_` 前缀。
- 测试优先运行 `tests/test_r6_*.py`。
- 不运行或修改旧路线测试来证明 R6 成立，除非明确是在复用基础设施。
- Product 报告必须保留 claim boundary，不能展示未验证准确性宣称。
- 候选更新必须通过当前阶段 addendum 定义的 evidence level 和 acceptance gate，才能从 diagnostic 升级。
- same-case outcome feedback improvement 不得直接包装成可迁移更新。
- `beat static prior` 只作为 runtime update guard 使用，不作为 R6 整体研究目标。
- `decision-value metric` 已实现不等于 R6 通过；必须同时报告 hit rate、false alarm、regret reduction 和 holdout validation。
- `interaction_delta_threshold` 调参不足以解释当前 false alarm；若 threshold sweep 显示真风险和误报共享相同 delta，下一步必须做非阈值 discriminator 或寻找 in-condition holdout。
- `false-alarm discriminator` 已实现不等于 R6 通过；当前 case/source family 候选只算 diagnostic-only，不能作为核心规则。
- `Interaction Signal Validity Score` 是当前非阈值主 gate；它必须显式排除 source/family 标签，并通过独立 holdout 或 field outcome 复核后才能从 diagnostic 升级。
- `Interaction Signal Validity holdout validation` 已实现不等于 R6 通过；当前结论是 `source_supported_count=1`、`eligible_independent_holdout_count=2`、`passed_holdout_count=0`、`contradicted_holdout_count=2`，因此正向信号仍停留在 diagnostic。
