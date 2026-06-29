# LCDU 通用性验证计划

**日期：** 2026-05-21

**适用范围：** `cc-社会计算器` Research 线，在 `LCDU L3` 已经拿到稳定 held-out 改善之后的下一阶段外推验证。

---

## 1. 当前前提

现在已经有两个关键事实：

1. `h02` 是当前 repeat 平均更强的 accepted method；
2. `i01` 证明了同步、数值化 prompt-anchor program 的机制有效性。

这说明项目已经从“寻找有效自动化更新方法”推进到“验证该方法是否可泛化”的阶段。

---

## 2. 通用性问题的三层拆分

### 2.1 当前任务内通用性

问题：

- 同一 benchmark family 内，换 split / seed / scale / segment granularity 后，LCDU L3 是否仍然成立？

当前状态：

- 部分已验证；
- `seed/scale` repeat 已成立；
- 但更换 split 定义与 segment granularity 仍未验证。

### 2.2 同类 policy-reaction 任务通用性

问题：

- 换另一个 public-use policy topic 或另一组政策选项时，LCDU L3 这套范式还能否找到稳定候选？

当前状态：

- 未验证。

### 2.3 方法范式通用性

问题：

- 可迁移的究竟是 `h02` 这个具体候选，还是 “latent + segment-targeted prompt-anchor guarded program” 这套构造范式？

当前状态：

- 倾向后者，但还缺跨任务证据。

---

## 3. 验证优先级

### P1：同任务内外推

优先验证：

1. 更换 held-out split
2. 更换 segment 粒度
3. 更换 cohort scale

原因：

- 成本最低；
- 最容易回答“当前结果是不是偶然依赖某一切分”。

### P2：同类政策题目迁移

优先验证：

1. 另一组 public-use 政策反应题目
2. 保持同样的 LCDU L3 流程
3. 看能否再次找到 stable-improvement candidate

原因：

- 直接决定 research 贡献能否从“单任务成立”上升到“方法范式成立”。

### P3：跨模型/跨 provider 迁移

优先验证：

1. 本地 `openai/gpt-oss-20b`
2. 备用 provider（仅作诊断，不作为主证据）

原因：

- 可辅助判断方法是否过度依赖当前模型；
- 但不应优先于任务外推。

---

## 4. 建议实验包

### 4.1 包 A：同任务内 split / segment 外推

目标：

- 验证 LCDU L3 是否仅依赖当前 split 和当前 segment schema。

最小实验：

1. 保持同一政策题目；
2. 改变 calibration/evaluation split；
3. 改变 segment 聚合方式；
4. 对 `h02` 和 `i01` 重跑 held-out gate。

验收：

- 至少一个候选保持 accepted；
- 如果全部失效，则说明当前结果更依赖切分结构。

### 4.2 包 B：同类题目迁移

目标：

- 验证 LCDU L3 范式是否能迁移到另一组政策反应 benchmark。

最小实验：

1. 选择一个新的 public-use policy topic；
2. 复用同样的:
   - latent representation
   - segment-targeted guard construction
   - prompt-anchor interaction analysis
3. 重新做单轴 + repeat gate。

验收：

- 出现至少一个 stable-improvement candidate；
- 或至少重复出现“interaction 优于单边 patch”的机制模式。

### 4.3 包 C：跨模型诊断

目标：

- 验证 LCDU L3 是否过分依赖当前 `gpt-oss-20b`。

最小实验：

1. 选一个成本可控的替代模型；
2. 只复验 `h02` 与 `i01`；
3. 不做新的候选搜索。

验收：

- 只作为诊断，不作为主证据；
- 若完全失效，记录为模型依赖风险。

---

## 5. 止损标准

以下任何一种情况成立，就不应继续扩大 LCDU 外推预算：

1. 同任务内只要略改 split/segment granularity 就全部失效；
2. 新题目完全找不到稳定候选；
3. 方法只能在单一模型上成立；
4. 需要大量特定 task-specific handcraft 才能重新成立。

如果出现这些情况，LCDU L3 更适合被表述为“当前 benchmark 上的强局部方法”，而不是“具备广义通用性的范式”。

---

## 6. 推荐执行顺序

1. **先做包 A**
   - 成本最低
   - 信息密度最高

2. **再做包 B**
   - 真正决定 research 外推价值

3. **最后做包 C**
   - 只做补充诊断

---

## 7. 当前建议

如果下一阶段继续推进，我建议第一优先级是：

> 先做同任务内 split / segment 外推，而不是马上换题目或换模型。

原因：

1. 这一步能最快判断 LCDU L3 是否已经脱离“当前切分偶然性”；
2. 一旦这一步成立，再去做跨题目迁移，论证会更稳；
3. 这也更节省实验预算。
