# Active Spec

## 当前唯一事实源

当前 Research / Product 双线的唯一 active spec 是：

- `docs/superpowers/specs/2026-06-05-r6-outcome-feedback-prior-anchored-interaction-simulation-spec.md`

工作名：

- 中文：R6 结果反馈约束的先验锚定交互仿真框架
- English: Outcome-Feedback Prior-Anchored Interaction Simulation

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

## 当前实现范围

第一阶段只推进 R6 foundation：

1. `r6_prior_manifest`
2. `r6_scenario_manifest`
3. `r6_interaction_trace`
4. `r6_risk_shift_report`
5. `r6_outcome_manifest`
6. `r6_learning_report`
7. `r6_update_registry`

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

