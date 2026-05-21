# LCDU L3 下一阶段双线实施计划

**日期：** 2026-05-21

**适用范围：** `cc-社会计算器` 的 `research/` 与 `product/` 双线，在 `LCDU L3 h02` 已通过 repeat gate 之后的下一阶段推进。

**当前状态：** 计划稿，包含本轮立即实施范围。

---

## 1. 当前判断

`LCDU L3 h02` 已经是当前 policy-reaction 主线里第一条真正通过 repeat gate 的自动化更新候选：

1. `12x3 seed11` improved；
2. `12x3 seed17` improved；
3. `16x3 seed11` improved；
4. stability 结论为 `stable_improvement`。

这意味着主线已经从“存在局部信号”推进到了“存在稳定候选方法”。

但它距离 Research 和 Product 的最终目标都还有明显 gap：

1. **Research gap**
   - 还缺解释性证据；
   - 还缺 ablation；
   - 还缺跨任务/跨切分通用性验证；
   - 还缺把方法提升到 reviewer-facing contribution 的表述框架。

2. **Product gap**
   - 目前仍主要停留在实验 artifact 注入；
   - 还没有形成通用的 runtime 校准入口；
   - 还没有把成功候选收敛成可配置能力；
   - 还没有形成面向产品报告和客户解释的稳定链路。

---

## 2. 本阶段目标

本阶段不再扩无边界的新候选家族，而是围绕 `LCDU L3 h02` 做两件事：

1. **Research 目标：解释 `h02` 为什么成功**
2. **Product 目标：把 `h02` 变成可复用的 runtime 校准入口**

也就是说，本阶段不是继续找“下一个偶然更优点”，而是把当前最强候选沉淀成：

- 更可解释的方法证据；
- 更可迁移的产品接入方式。

---

## 3. 双线拆解

### 3.1 Research 线

Research 线分两步推进：

1. **L3 explanation / ablation**
   - 目标：解释 `h02` 的有效成分；
   - 回答问题：
     - 是 `working_family` segment prompt 在起作用？
     - 是 calibration anchor 在起作用？
     - 还是阈值数值本身在起作用？

2. **L3 generalization design**
   - 目标：设计后续通用性验证路线；
   - 本轮先不大规模执行，只形成实验边界与任务列表。

### 3.2 Product 线

Product 线本阶段只做一件高价值收敛：

1. **把 `S2PC candidate` 接入口抽象成更通用的 calibration candidate 接口**
   - 保持兼容旧路径；
   - 允许 `LCDU` 与后续方法族共用同一 runtime 注入位；
   - 避免产品逻辑继续被 `S2PC` 命名锁死。

---

## 4. 本轮立即实施范围

### 4.1 Research 立即实施

实现一个 `LCDU L3 ablation family`：

1. `prompt_only_guard`
   - 保留 `working_family` 的 segment prompt guard；
   - 去掉对应 calibration anchor guard。

2. `anchor_only_guard`
   - 保留 `working_family` 的 calibration anchor guard；
   - 去掉对应 segment prompt guard。

3. `qualitative_guard`
   - 保留 guard 结构；
   - 去掉数值阈值，只保留定性约束语义。

必要时保留：

4. `no_working_family_override`
   - 作为 `h02` 的局部去激活对照。

然后：

1. 生成 Product 可消费候选；
2. 在 `12x3 seed11` 上做单轴 runtime 预筛；
3. 构建 `ablation matrix`；
4. 与 `h02` 和 `l04` 对比。

### 4.2 Product 立即实施

实现一个兼容层：

1. 保留原有 `--s2pc-candidate-artifact`；
2. 增加更通用的 `--calibration-candidate-artifact`；
3. 内部统一走 `policy-reaction-s2pc-candidate-v1` 解析逻辑；
4. manifest/report 中同时保留兼容字段与更通用字段。

目标不是改 schema，而是把“Research candidate 注入位”从单一命名升级成通用能力。

---

## 5. 测试方案

### 5.1 Research 测试

1. 新增 `LCDU L3 ablation` 生成器单测：
   - schema 正确；
   - prompt/anchor 的 ablation 结构正确；
   - strict JSON 通过。

2. 如果执行 runtime：
   - 导出 cohort manifest；
   - 导出 segment prediction artifact；
   - 导出 held-out benchmark；
   - 导出 runtime effect matrix。

### 5.2 Product 测试

1. CLI 单测：
   - `--calibration-candidate-artifact` 能正确透传；
   - 与 `--s2pc-candidate-artifact` 保持兼容。

2. runner 单测：
   - generic calibration candidate context 解析正确；
   - 原有 `s2pc_context` 不回归。

---

## 6. 验收标准

### 6.1 Research 验收

本轮至少满足以下条件：

1. `LCDU L3 ablation` 候选生成器完成；
2. 相关测试通过；
3. 如果 runtime 跑通，能形成 single-axis ablation matrix；
4. `RESULTS.md` 能明确写出：
   - `h02` 的成功是否主要来自 prompt、anchor、还是阈值联动。

### 6.2 Product 验收

本轮至少满足以下条件：

1. Product CLI 支持更通用 candidate 注入入口；
2. 旧命令不回归；
3. runtime report/manifest 仍保持兼容；
4. 能用新入口跑通至少一个校准候选。

---

## 7. 止损标准

### 7.1 Research 止损

如果 `L3 ablation` 结果表明：

1. 成功来源不可分解；
2. 每个子组件单独都完全崩塌；
3. 没有任何可解释结构可复述，

则说明当前 `h02` 更接近偶然组合命中，不应过度包装成方法优势。

### 7.2 Product 止损

如果通用 candidate 接入口必须引入新的 Product schema，或者破坏现有 `S2PC` 兼容性，则本轮停止扩展，保留旧接口。

---

## 8. 本轮执行顺序

1. 写入本计划；
2. 实现 `LCDU L3 ablation family`；
3. 实现 Product 通用 calibration candidate 接入口；
4. 跑相关测试；
5. 若时间和成本允许，执行 `12x3 seed11` ablation 预筛；
6. 回填 `RESULTS.md` 与必要 artifact。

