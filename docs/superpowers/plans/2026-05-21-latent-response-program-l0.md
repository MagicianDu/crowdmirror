# Latent Response Program L0 设计

## 1. 目标

把当前 `LCDU L3/L5` 之后的下一步研究，明确收敛到一件事：

> 不再继续增加更细粒度的 prompt/anchor patch，而是先把更新对象提升为一个更高层的 `latent response program`，再由编译器把这个程序落回 Product 可消费的 candidate artifact。

本轮只做 `L0`，目标是证明这层表示可以被清晰定义、严格写盘、稳定导出，不对 runtime 效果做任何正向承诺。

## 2. 为什么要换表示

当前证据已经够说明：

1. `LCDU L3` 在 4 个主 segment 上成立；
2. finer-schema 弱点也已经被稳定定位：
   - `price_stress_level=high` 的分布形状偏差；
   - `income_band=low` 的排序失真；
3. 但 `LCDU L5` 这类 axis-level prompt/anchor repair 全部回退。

因此问题不再是“还差一个更细的 patch”，而是：

> 直接修 prompt/anchor 这层表示已经不够，细粒度弱点需要先在更高层的响应机制里被统一表达，再编译到 runtime。

## 3. L0 的最小方法假设

`L0` 先不追求找到有效候选，只验证下面这条表示链是否可成立：

1. 用一组稳定、可解释的 latent response 变量表示群体响应机制；
2. 用一组 selector-based regime rule 表达不同 axis 人群如何偏移这些 latent；
3. 用一组 response constraint 保持主方法声明边界；
4. 最后统一编译成 `policy-reaction-s2pc-candidate-v1` 兼容 artifact。

## 4. L0 的内部表示

### 4.1 全局 latent

L0 只保留 4 个最小变量：

1. `baseline_inertia`
2. `relief_preference`
3. `price_stress_reactivity`
4. `targeting_sensitivity`

它们不是直接概率，也不是 prompt 文案，而是中间响应程序的状态。

### 4.2 regime rule

每条 rule 包含：

1. `selector`
   - 例如 `income_band=low`
   - 或 `price_stress_level=high`
2. `latent_delta`
   - 对 4 个 latent 的局部增减
3. `program_intent`
   - 说明这条 rule 的机制意图

### 4.3 response constraint

L0 继续保留 reviewer-facing 的约束层，但不再把它当成 patch 文案：

1. `distribution_shape_guard`
2. `rank_guard`
3. `baseline_cap`
4. `relief_floor`

## 5. 编译路径

`latent response program -> Product candidate artifact` 的编译分两层：

1. **Research 解释层**
   - `latent_response_program`
   - `regime_rules`
   - `response_constraints`
   - `compiled_parameter_patches`

2. **Product 运行层**
   - `candidate_prompt_components.segment_prompt`
   - `candidate_prompt_components.calibration_anchor`
   - `response_contract`

也就是说，Product 仍然不直接消费 latent 对象；它消费的是由 latent program 编译出来的 prompt/anchor 结果。

## 6. L0 候选族

L0 只生成 4 个最小候选：

1. `p01 low_income_compensatory_program`
2. `p02 high_price_reactive_program`
3. `p03 dual_axis_balanced_program`
4. `p04 dual_axis_targeted_program`

这 4 个候选都围绕已知 axis-level 弱点构造，但表达方式从 “给某条 axis 加一句 patch” 变成 “给某条 axis 施加一个 latent regime rule”。

## 7. 本轮验收标准

本轮只接受工程与表示层验收，不接受效果层过度宣称。

### 必须满足

1. 新增中文设计文档；
2. 新增 `latent response program L0` 编译脚手架；
3. 能从真实 `LCDU L3 h02` 候选和真实 axis weakness artifact 生成严格 JSON candidate set；
4. 能导出单个 Product 兼容 candidate artifact；
5. 补最小测试并通过；
6. 明确 claim boundary：`candidate-generation / representation evidence only`。

### 本轮不要求

1. 不要求 runtime matrix；
2. 不要求 held-out 改善；
3. 不把 L0 包装成“已经证明更高层表示有效”。

## 8. 止损线

如果 `L0` 最终只是把现有 axis patch 重新命名，而没有形成明确的：

1. latent state；
2. regime rule；
3. response constraint；
4. compile-to-runtime 路径；

那这条线应当立即停止，不进入 `L1`。

## 9. 下一步接口

如果 `L0` 验收通过，下一步只做一件事：

> 用这 4 个 `latent response program` 候选跑一轮单轴 runtime prefilter，看“更高层表示”是否至少比 `L5` 这种直接 axis patch 更合理。
