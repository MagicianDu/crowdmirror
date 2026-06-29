# 路线 B MVP 实施设计

**日期：** 2026-05-21

**适用范围：** `cc-社会计算器` Research 线，policy-reaction 自动化更新方法主线切换。

**当前状态：** MVP 设计稿，已包含最小脚手架落地要求。

---

## 1. 目标

路线 B 的目标不是再找一个单次 held-out 更低的 patch，而是验证：

> 在固定预算下，基于鲁棒目标的结构化黑盒优化，能否比当前 `s02/trust_only` 更稳定地生成 candidate。

这里的“更稳定”不是口头描述，而是显式写进目标函数和止损规则。

---

## 2. 当前已知基线

当前 route-B 前需要对齐的已知事实：

1. `s02/trust_only` 是 S2PC 当前最佳单点：
   - `12x3 seed11`
   - `baseline_loss=0.000112890954`
   - `runtime_loss=0.000111545213`
   - `relative_loss_reduction=0.011920716018`

2. `s02/trust_only` repeat 结果不稳：
   - `12x3 seed17`：`no_change`
   - `16x3 seed11`：`regressed`
   - 稳定性结论：`mixed`

3. 参数级进一步拆分没有带来更强候选：
   - `p01` 回退
   - `p02` 弱正向，但弱于 `s02`

因此，路线 B 的第一阶段不需要再次证明 S2PC 的局部信号存在，而需要回答：

> 把稳定性直接写进目标函数后，是否能避免继续追逐单点 improvement？

---

## 3. MVP 范围

### 3.1 本轮做什么

1. 定义鲁棒目标 artifact；
2. 用当前 `s02/trust_only` repeat 结果生成 route-B 基线分数；
3. 固定变量空间；
4. 为下一轮搜索器接入预留统一输入输出格式。

### 3.2 本轮不做什么

1. 不直接跑大规模进化搜索；
2. 不引入新 provider；
3. 不同时探索 DSPy；
4. 不尝试自由 prompt rewrite；
5. 不做 Product 侧 runtime 渲染改造。

---

## 4. 变量空间

路线 B 的第一轮变量空间只保留 `4-6` 个结构化变量：

1. `prior_anchor_strength`
2. `trust_multiplier`
3. `segment_prior_weight`
4. `selector_gate_threshold`
5. `prototype_activation_flag`（可选）

约束：

- 不允许自由文本 persona rewrite
- 不允许无限新增 latent factor
- 不允许跨 held-out 生成候选

---

## 5. 鲁棒目标

路线 B 使用以下统一目标：

```text
score =
  mean(loss over repeat axes)
  + alpha * std(loss over repeat axes)
  + beta * max(loss over repeat axes)
  + gamma * complexity_penalty
```

默认参数：

- `alpha = 1.0`
- `beta = 1.0`
- `gamma = 0.001`

解释：

1. `mean(loss)` 控制平均校准质量；
2. `std(loss)` 惩罚不稳定；
3. `max(loss)` 惩罚最坏情况；
4. `complexity_penalty` 避免为了极小收益增加过多 patch 或 prompt 组件。

---

## 6. 评估轴

路线 B MVP 固定使用以下 repeat 轴：

1. `12x3 seed11`
2. `12x3 seed17`
3. `16x3 seed11`

原因：

1. 这三轴已经存在，可直接复用现有 artifact；
2. 它们已经能暴露 S2PC 当前“不稳”的问题；
3. 预算可控，不会一开始就把 local LLM 评估成本拉爆。

---

## 7. 接受规则

候选只有在同时满足以下条件时，才可进入下一轮搜索：

1. `improved_count >= 2`
2. `regressed_count <= 0`
3. `mean_loss` 优于当前 `s02`
4. `worst_case_loss` 不明显差于 calibration baseline

如果达不到，直接标记为：

- `blocked_by_stop_loss`

而不是继续追加 repeat 或调更多变量。

---

## 8. 当前脚手架

本轮已要求实现的最小脚手架：

1. `policy_reaction_route_b_robust_search.py`
   - 输入 candidate artifact + 多个 runtime effect artifact
   - 输出 repeat-aware robust score artifact

2. route-B 基线 artifact
   - 先对当前 `s02/trust_only` 生成 route-B 分数
   - 作为后续所有候选的统一对照

3. 单元测试
   - 至少覆盖：
     - 不稳定 candidate 被 stop-loss 拦截
     - 稳定 candidate 可被标记 accepted

---

## 9. 止损规则

路线 B 的第一轮止损规则非常明确：

1. 如果 route-B 目标下，当前 `s02` 自己就是 `blocked_by_stop_loss`，
   这不代表路线 B 失败；
   它只说明旧候选不满足新目标。

2. 如果下一轮搜索器产生的新候选：
   - 单次优于 `s02`，
   - 但 repeat 仍然 `mixed`，
   则不进入下一轮。

3. 如果需要不断增加变量维度或 generation 数才能勉强找到弱正向，
   则说明问题可能不在搜索器，而在变量表示本身。

4. 出现上述情况时，应转向：
   - 分布约束路线
   - latent state 路线

---

## 10. 下一步实现口径

完成本轮脚手架后，下一步实现应严格按以下顺序：

1. 用当前 `s02/trust_only` 生成 route-B 基线 artifact；
2. 固定变量空间；
3. 接一个小种群、低代数的搜索器；
4. 每轮只比较：
   - route-B robust score
   - `s02` 基线
   - calibration baseline

不允许绕过 route-B score 直接用单次 held-out improvement 宣称候选有效。
