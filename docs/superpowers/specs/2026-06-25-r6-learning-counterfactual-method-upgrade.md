# R6 学习型反事实机制仿真方法升级 Spec

## 背景判断

当前 R6 已经补齐 Product 所需的证据链、claim boundary、false-alarm gate 和 outcome feedback protocol，但方法本身仍不够强。现有 `behavioral_update_operator_v3` 更接近“误报 gate 后选择是否应用交互 delta”，并没有真正学习人群交互机制，因此只能支撑 guarded/proxy 级别结论，不能充分支撑 Product 的核心竞争力。

本阶段不再继续围绕 TextGrad、DSPy、prompt/persona patch、阈值搜索或旧 scoring candidate 小修小补。新的方法升级方向是：

> 用 outcome residual 学习机制层权重，并把交互仿真从单一风险评分推进为可比较的反事实策略沙盘。

## 方法目标

新方法不承诺精准单点预测，也不宣称已完成 field validation。它要优先解决 Product 最需要的三个能力：

1. 降低 raw interaction 容易制造 false alarm 的问题。
2. 保留静态先验漏报高风险时，交互层能够恢复风险发现的价值。
3. 给 Product 提供反事实策略比较：不同缓释策略下，风险区间、异常群体和机制路径如何变化。

## 方法定义

工作名：

- 中文：学习型反事实机制仿真器
- English: Learning Counterfactual Mechanism Simulator

核心输入：

- 静态先验预测
- raw interaction prediction
- observed/proxy outcome
- segment-level mechanism trace
- Product claim boundary / false-alarm guard

核心计算：

1. 对每个 case 计算 outcome residual：
   - `observed_reject_proxy - static_prior_prediction`
2. 对每个 case 计算 raw interaction delta：
   - `raw_interaction_prediction - static_prior_prediction`
3. 用二者比值估计机制放大/衰减权重：
   - `mechanism_weight = clipped(outcome_residual / raw_interaction_delta)`
4. 对 segment mechanism trace 做加权，形成 learned operator delta。
5. 对多个 policy alternative 做 attenuation，输出反事实策略排序。

### 迁移失败修复

第一轮 leave-one-case holdout 暴露出一个关键失败边界：如果 heldout case 的高风险机制在训练 case 中完全未出现，机制权重会被置零，导致静态先验漏报恢复信号丢失。

因此当前 MVP 增加一个保守迁移 guard：

- `unseen_mechanism_transfer_floor=0.65`
- 只在 heldout case 存在 raw interaction risk signal 且机制未见过时启用。
- 该 floor 只用于保留风险发现信号，不用于宣称准确性提升。
- 即使 floor 恢复了 static prior miss recovery，只要 non-regression gate 未通过，仍必须保持 `runtime_default_allowed=false`。

第二轮修复进一步增加一个非回归护栏：

- `risk_preserving_calibration_target=raw_interaction_prediction`
- 只在以下条件同时满足时启用：
  - heldout case 是静态先验漏报高风险；
  - learned operator 已经保留风险发现信号；
  - learned operator prediction 低于 raw interaction prediction，导致相对 raw interaction 的 non-regression 失败。
- 校准目标不是超过 raw interaction，而是最多拉回 raw interaction prediction，用于避免 learned operator 抹掉交互层原有风险发现价值。
- 该校准通过 current proxy leave-one-case 不等于 field/customer outcome validation，仍不得开启 runtime default。

## 当前 MVP Artifact

新增 artifact：

- `r6_learning_counterfactual_simulator`

必须包含：

- `learned_mechanism_weights`
- `case_results`
- `counterfactual_policy_results`
- `summary`
- `product_support_delta`
- `acceptance_gates`
- `allowed_claims`
- `blocked_claims`
- `claim_boundary`

## MVP 验收标准

在当前 public proxy fixture 上，MVP 只要求拿到 current-proxy positive signal：

1. `learned_operator_false_alarm_rate < raw_interaction_false_alarm_rate`
2. `static_prior_miss_recovery_rate == 1.0`
3. 每个 case 至少输出 3 个可排序 counterfactual policies
4. `field_outcome_validated=false`
5. `runtime_default_allowed=false`
6. Product claim 只能升级为 guarded/diagnostic，不能进入 field-validated 或 runtime-default

## 当前可讲结论

如果 MVP 通过，只能讲：

> 学习型机制权重在当前 public proxy 上显示出降低 raw interaction false alarm、保留静态先验漏报恢复能力的正向信号，并能产出反事实策略排序，因此值得作为下一阶段 Research 主线继续推进。

不能讲：

- 已完成 field validation
- 已证明跨域泛化
- 已可默认启用 runtime update
- 已能精准预测单点结果
- 已经全面支撑 Product 核心价值

## 下一阶段验证

下一阶段必须做：

1. 独立 holdout 验证 learned mechanism weights 是否迁移。
2. outcome feedback 到 mechanism weight 的 bounded update / rollback。
3. Product report/API 消费 counterfactual policy ranking。
4. 与当前 `behavioral_update_operator_v3`、static prior、raw interaction、false-alarm gate 做 ablation。
5. 明确失败边界：哪些机制权重只是当前 proxy 过拟合，哪些能跨 case 保留。
6. 验证 unseen mechanism transfer floor 是否能在更多独立 holdout 上同时保持风险发现和 non-regression。
7. 验证 risk-preserving calibration 是否在 field/customer outcome 或更严格跨源 holdout 中仍然成立。
