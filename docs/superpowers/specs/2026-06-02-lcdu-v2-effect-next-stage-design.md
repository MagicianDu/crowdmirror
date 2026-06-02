# LCDU-hybrid v2 效果提升下一阶段设计 Spec

## 1. 背景

当前 LCDU-hybrid v2 已经从“数值平齐 deterministic anchor”推进到“层级可靠性校准在当前 ANES 两个政策任务上超过 deterministic anchor”：

- `climate_energy_regulation_attitude_v1`: anchor test loss `0.008343247118118962`，v2 test loss `0.007507077724763764`。
- `public_health_medical_insurance_attitude_v1`: anchor test loss `0.006094935382542338`，v2 test loss `0.004320556591493811`。
- 两个任务都选择了 `lcdu_hierarchical_party_k_50`。

但该结果还不能直接升级为 CCF-A 主贡献或产品核心壁垒，因为存在三个关键缺口：

1. `climate` 任务虽然 weighted loss 下降，但 worst-segment loss 相对 anchor 恶化 `0.00839484805307937`。
2. 当前正信号只覆盖一个 public microdata artifact、两个任务、一个 split contract。
3. v2 尚未进入 strong baseline / paper gate，因此还没有形成完整强基线论证。

因此下一阶段不再以“继续证明能跑”为目标，而以“证明 LCDU-hybrid v2 是稳健、可解释、可审计的效果提升方法”为目标。

## 2. 下一阶段总目标

将 LCDU-hybrid v2 从当前的单次正信号推进为一个受约束的校准优化框架：

> 在 heldout split 上选择候选时，不只最小化平均 weighted JSD，还要加入 worst-segment non-inferiority guard，避免用局部人群风险换取平均指标改善。

研究侧目标：

- 证明 v2 的效果提升来自层级可靠性校准机制，而不是一次性候选网格偶然命中。
- 证明该方法相对 deterministic anchor、aggregate prior、population search、prompt optimizer 等强基线具有可比优势或明确边界。
- 形成可进入 paper gate 的 artifact，而不是临时实验输出。

产品侧目标：

- 把每个 cohort 的预测结果和其校准来源绑定。
- 对存在 worst-segment 风险的任务或 cohort 给出风险标记。
- 输出客户可理解的“为什么此处使用层级收缩、为什么可信、哪里不应强结论”的证据链。

## 3. 本阶段优先级

本阶段分四条线，但第一轮执行只关闭第一条线，避免把范围铺得过大。

### 3.1 线路 A：约束选择规则

目标：修复当前 v2 “平均 loss 胜出但 worst-segment 可能恶化”的缺口。

方法：

1. 继续从 calibration split 生成候选。
2. 在 heldout split 上同时计算：
   - weighted segment JSD；
   - worst-segment JSD；
   - 相对 deterministic anchor 的 worst-segment delta。
3. 选择候选时加入 guard：
   - 候选必须在 heldout weighted loss 上优于 anchor；
   - 候选的 heldout worst-segment delta 不得超过阈值；
   - 若无候选满足 guard，则回退到 deterministic anchor。

默认阈值：

- `max_worst_segment_delta = 0.0`，即不允许 worst-segment 比 anchor 更差。

第一轮允许输出两个结果：

- `unconstrained_selection`: 原 v2 规则，只按 heldout weighted loss 选。
- `constrained_selection`: 新规则，加入 worst-segment guard。

验收标准：

- artifact 中每个任务同时报告 unconstrained 与 constrained 结果。
- constrained 结果不得出现 heldout worst-segment guard violation。
- test split 必须报告 constrained 是否仍 beats deterministic anchor。
- 若 constrained 回退到 anchor，必须明确写出回退原因。

### 3.2 线路 B：消融矩阵

目标：证明 `party_k_50` 不是偶然。

方法：

- prior family ablation：
  - global only；
  - party only；
  - income only；
  - shared-axis neighbor only；
  - all priors。
- k-grid ablation：
  - 固定 prior family，比较不同 k；
  - 固定 k，比较不同 prior family。
- segment-size ablation：
  - 按 calibration segment row count 分桶；
  - 观察小样本 segment 是否更受益于收缩。

验收标准：

- 输出每个 prior family 的 heldout/test loss、worst loss、win/loss。
- 能解释当前为什么 `party_or_ideology` 有效。
- 如果只在 ANES 政治态度任务有效，要写成方法边界。

### 3.3 线路 C：schema / split / repeat 稳健性

目标：证明 v2 不是当前 schema 和 hash split 的偶然产物。

方法：

- schema：
  - `party+income`
  - `party+income+age`
  - `party+income+education`
  - `party+income+age+education`
- repeat：
  - 多个 hash salt；
  - 或多个 split assignment repeat。
- task：
  - 当前 health、climate；
  - 后续扩展更多公开政策态度任务。

验收标准：

- 输出 task × schema × repeat × method 矩阵。
- 报告 win rate、mean delta、worst-segment delta、失败案例。
- 如果胜率不稳定，降级为“任务特定方法”，不得写成通用方法。

### 3.4 线路 D：strong baseline / paper gate 接入

目标：把 v2 结果纳入完整论文证据链。

方法：

- 将 `LCDU-hybrid-v2-constrained` 作为独立 LCDU method family 输入 strong baseline。
- 与以下方法比较：
  - deterministic anchor；
  - aggregate prior；
  - population search；
  - prompt optimizer；
  - LCDU-soft；
  - LCDU-hybrid strict-copy；
  - LCDU-hybrid v2 unconstrained；
  - LCDU-hybrid v2 constrained。

验收标准：

- 如果 constrained v2 在 expanded matrix 中领先，paper gate 可以从 `not_passed_under_accuracy_superiority_criterion` 推进到新的条件状态。
- 如果 constrained v2 不领先，但 auditability 或 worst-segment 风险控制更好，必须只写成“受约束校准/可审计贡献”，不得写成 accuracy 主贡献。

## 4. 本轮执行范围

本轮执行只做线路 A 的完整闭环：

1. 修改 `experiments/lcdu_anes_hierarchical_calibration_matrix.py`。
2. 增加 constrained selection rule。
3. 保留原 unconstrained selection 作为对照。
4. 扩展测试覆盖：
   - constrained rule 能避开 worst-segment 退化候选；
   - 无候选满足 guard 时回退 anchor；
   - CLI 能写出 constrained artifact。
5. 基于当前 ANES microdata artifact 生成新结果。
6. 汇报：
   - constrained 是否仍能 beat anchor；
   - 是否解决 climate worst-segment 退化；
   - 如果回退 anchor，说明它对 research/product 的含义。

## 5. 成功与止损标准

成功标准：

- constrained v2 至少在一个任务上 beat deterministic anchor。
- 所有任务在 test 上报告 worst-segment delta。
- constrained selection 不出现未标记的 worst-segment guard violation。
- 全量或定向测试通过。

强成功标准：

- constrained v2 在两个任务上都 beat deterministic anchor；
- 且 test worst-segment delta 均不恶化。

止损标准：

- 如果 constrained rule 全部回退 anchor，则说明当前 v2 的平均提升依赖允许局部恶化，不能继续包装为稳健效果提升。
- 如果 constrained rule 在 heldout 通过但 test 大幅恶化，则下一阶段必须优先做 repeat/split robustness，而不是接入 paper gate。

## 6. 输出 artifact 要求

新 artifact 必须保留现有字段，并新增：

- `selection_modes`
- `unconstrained_anchor_win_task_count`
- `constrained_anchor_win_task_count`
- `constrained_worst_guard_pass_task_count`
- `max_worst_segment_delta`
- 每个 task：
  - `unconstrained_selection`
  - `constrained_selection`
  - `constrained_fallback_reason`
  - `heldout_worst_guard_pass`
  - `test_worst_guard_pass`
  - `method_interpretation`

## 7. 当前结论边界

本阶段完成后，即使结果正向，也只能声明：

> LCDU-hybrid v2 在当前 ANES public microdata slice 的两个政策态度任务上，具备受约束层级校准改善信号。

不能声明：

- 已经达到 CCF-A 主贡献标准；
- 已经证明跨数据集通用；
- 已经完成产品级客户验证；
- LLM simulator 本身已经优于强基线。
