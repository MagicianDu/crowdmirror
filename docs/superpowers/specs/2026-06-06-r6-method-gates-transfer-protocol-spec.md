# R6 方法验收与跨 Case 迁移协议 Spec

## 1. 文档目的

本 spec 是 R6 主控 spec 的阶段性 addendum，用来把工作从“继续补 public proxy / artifact 细节”切回方法主线：

> R6 要形成的是一个以强先验为底座、以交互偏移为风险假设、以 outcome feedback 为受约束学习信号的可审计仿真框架。

当前阶段不再以“增加更多 proxy 数量”为主要推进方式。后续只做能回答以下问题的工作：

1. R6 方法定义是否清楚？
2. 哪些证据能让候选更新升级？
3. 哪些证据只能保留为诊断？
4. outcome feedback 如何跨 case 迁移？
5. Product 如何展示证据链而不宣称未验证准确性？

## 2. 当前事实边界

截至本 spec，R6 已有三类 public proxy：

| proxy | 作用 | 当前结论 |
| --- | --- | --- |
| HTOPS cost pressure | public service / policy change proxy | prior-anchored interaction 相对 no-interaction 有正向信号 |
| ANES health heldout | rights/rule 同类 source case | 暴露 interaction over-amplification；cap 可在 source case 修复 |
| ANES climate heldout | rights/rule 同 family holdout | 可用作同 family holdout，但未覆盖 cap 触发条件 |

当前不能宣称：

- R6 已经稳定比静态先验更准；
- mechanism cap 已可进入 runtime default；
- outcome feedback 已能跨 case 泛化；
- public proxy 等价于真实 field outcome；
- 多个 artifact 数量本身构成研究贡献。

当前可以宣称：

- R6 已形成可审计证据链；
- R6 能发现静态先验之外的风险偏移；
- R6 能暴露失败边界；
- R6 能生成受约束候选修复；
- R6 能阻断未验证更新进入全局默认。

## 3. 方法对象定义

R6 的方法对象不是某个 prompt、persona、TextGrad、LCDU、S2PC 或单一 cap 规则，而是：

```text
Prior-Anchored Interaction Simulation
  + Outcome-Feedback-Gated Update
  + Failure-Boundary Governance
```

中文描述：

> 先验锚定交互仿真 + 结果反馈门控更新 + 失败边界治理。

三个组成部分必须同时存在：

1. **Prior-Anchored Interaction Simulation**：强先验给出 no-interaction control，交互层只解释相对先验的偏移。
2. **Outcome-Feedback-Gated Update**：真实或公开 outcome proxy 回来后只能产生候选更新，不能直接污染全局参数。
3. **Failure-Boundary Governance**：任何局部正效应都必须报告适用条件、失败条件和不可宣称范围。

如果一个工作只是在调 prompt、补 persona、堆 proxy、写 demo 文案，而没有进入这三部分之一，就不属于当前主线。

## 4. Evidence Levels

R6 后续所有结论按证据等级汇报。

| Level | 名称 | 允许宣称 | 不允许宣称 |
| --- | --- | --- | --- |
| L0 | Contract Ready | artifact/schema/报告链路成立 | 方法有效 |
| L1 | Diagnostic Signal | 某 case 有风险偏移或失败边界 | 泛化有效 |
| L2 | Source Fix | 候选修复在 source case 有效 | 可进入 runtime default |
| L3 | Holdout Non-Regression | 候选修复在 holdout 不造成回归 | 已覆盖触发条件 |
| L4 | In-Condition Transfer | 候选修复在独立、同 family、同触发条件 holdout 上通过 | 全行业有效 |
| L5 | Field-Gated Update | 真实业务或 field outcome 支持受控更新 | 永久有效或无需监控 |

当前 R6 状态：

- mechanism cap：L3 partial，但没有达到 L4。
- outcome feedback：L2 same-case improvement，但没有达到 cross-case transfer。
- Product report：L1/L2 证据展示链路成立，但不是准确性产品。

## 5. Acceptance Gates

### 5.1 mechanism cap 升级 gate

cap 候选从 `diagnostic_only` 升级必须同时满足：

1. source case 修复成立；
2. 至少一个 cross-proxy holdout 不回归；
3. 至少一个 same-family holdout 可用；
4. same-family holdout 覆盖 cap 触发条件；
5. cap 后误差不高于 static prior；
6. worst segment 不产生新增严重回归；
7. 所有 source refs、risk flags、claim boundaries 完整。

当前失败点：

```text
same-family holdout available = true
same-family cap condition covered = false
global update accepted = false
```

因此下一步不是继续泛泛找 proxy，而是寻找或构造：

> static prior error 已足够低，且 interaction amplification 会触发 cap 的同 family rights/rule holdout。

### 5.2 outcome feedback 升级 gate

outcome feedback 从 `blocked_same_case_only` 升级必须满足：

1. source case feedback update 降低误差；
2. 更新规则不是直接用 observed value 回填；
3. 更新规则可表达为可迁移参数；
4. 在至少一个未参与更新的 holdout case 上不回归；
5. 在至少一个同 family case 上降低误差；
6. 更新适用范围、回滚条件、监控指标明确。

当前失败点：

```text
same-case improvement = true
cross-case transfer protocol = missing
global update accepted = false
```

## 6. Cross-Case Transfer Protocol

跨 case 迁移不是把 source case 的结果复制到 holdout，而是测试“更新规则”是否可迁移。

### 6.1 case family 定义

一个 case family 至少由以下轴定义：

- `case_type`：price / rule / benefit / service / public policy；
- `impact_dimension`：cost increase / rights reduction / access constraint / regulation expansion；
- `proxy_family`：cost pressure / insurance preference / regulation preference；
- `population_axis`：segment schema 是否相近；
- `measurement_level`：field outcome / public proxy / fixture proxy；
- `cap_condition`：候选更新的触发条件是否被覆盖。

### 6.2 transfer 流程

```text
source case
  -> derive candidate update rule
  -> freeze update rule
  -> apply to holdout case without peeking at holdout outcome
  -> compare static prior / original interaction / updated interaction
  -> report pass, regression, or condition-not-covered
```

### 6.3 transfer 结果状态

| 状态 | 含义 | 后续动作 |
| --- | --- | --- |
| `passed` | 更新在同 family、同触发条件 holdout 上降低误差且不伤 worst segment | 可进入更高等级受控 policy |
| `non_regression_only` | 没有变差，但没有覆盖关键条件或没有改善 | 保持 diagnostic |
| `condition_not_covered` | holdout 可用，但没有触发候选规则 | 继续找 in-condition holdout |
| `regressed` | holdout 变差 | 降级或拒绝更新 |
| `invalid_proxy` | proxy mapping 不成立 | 不能用于方法验收 |

当前 ANES climate 的状态应是：

```text
condition_not_covered
```

## 7. Research 主线收束

后续 Research 不再把主要精力放在：

- 继续增加 proxy 数量；
- 继续手工微调 cap 阈值；
- 继续产出更多 JSON 变体；
- 继续证明单个局部 artifact 正效应。

Research 后续只推进三件事：

1. **理论定义**：把 R6 写成可投稿的方法框架，而不是工程流水线。
2. **迁移协议**：证明候选更新是否能跨 case 迁移。
3. **失败边界**：解释何时交互有价值，何时强先验应压制交互。

CCF-A 级主贡献至少需要：

- 明确 formal problem；
- 明确 no-interaction baseline 与 interaction operator；
- 明确 outcome-feedback gated update；
- 至少一个候选更新通过 L4；
- 至少一个失败边界被系统性解释；
- 与 prompt-only persona simulation、strong prior、random interaction、same-case feedback copy 做强 baseline 对比；
- 不把 public proxy 包装成 field validation。

## 8. Product 主线收束

Product 后续不再以“demo 叙事更顺”为目标，而以“客户可理解的证据链”为目标。

Product report 必须展示：

1. 静态先验是什么；
2. 交互带来什么偏移；
3. 这个偏移是风险假设还是已验证结果；
4. outcome 回来后发现了什么失败边界；
5. 哪些候选修复被阻断；
6. 要采集什么后续数据才能升级；
7. 当前系统不能承诺什么。

Product 可以讲：

> 这是发布前风险沙盘和发布后学习系统。

Product 不能讲：

> 这是保证准确预测大众反应的模型。

## 9. 后续任务优先级

### P0：写出 cross-case transfer protocol artifact

目标：

> 把 outcome feedback 和 mechanism cap 的迁移验证变成统一 artifact，而不是散落在 evidence report 里。

验收：

- 能区分 `passed`、`non_regression_only`、`condition_not_covered`、`regressed`、`invalid_proxy`；
- 能记录 source case、candidate update、holdout case、frozen rule；
- 能明确阻断 global update 的原因。

### P1：设计 in-condition holdout 搜索标准

目标：

> 不再泛泛找数据，而是按 cap 触发条件找数据。

验收：

- 明确候选数据必须满足哪些条件；
- 明确哪些公开数据即使可用也只能当 out-of-condition holdout；
- 输出数据选择 ledger。

### P2：Product evidence card contract

目标：

> 把当前 JSON evidence chain 转成 Product 可展示的 evidence card contract。

验收：

- 每张卡有 claim status；
- 每张卡有 allowed claim / blocked claim；
- 每张卡能链接 source artifact；
- demo/API 只能消费 artifact 字段，不写静态叙事兜底。

## 10. 止损规则

如果后续连续出现以下情况，应暂停 R6 作为主研究贡献推进：

1. 找到 in-condition holdout 后 cap 仍回归；
2. outcome feedback 只能 same-case copy，无法形成可迁移规则；
3. interaction shift 在多数 public proxy 上稳定劣于 no-interaction prior；
4. failure boundary 只能事后解释，不能提前形成 gate；
5. Product 价值只能靠叙事展示，不能靠 artifact 证据链支撑。

即使止损，也保留：

- prior/no-interaction baseline；
- Product evidence chain；
- failure diagnosis；
- outcome collection checklist；
- update registry。

这些资产仍可作为产品审计能力，而不是 CCF-A 主算法贡献。

## 11. 当前阶段结论

R6 没有偏离主线，但已到达细节扩张边界。

后续正确推进方式是：

```text
停止泛泛补 proxy
  -> 固化方法定义
  -> 固化 acceptance gates
  -> 实现 cross-case transfer protocol
  -> 只寻找能触发关键 gate 的数据
  -> 再判断是否继续作为 Research 主贡献
```

当前 R6 最强主张是：

> R6 已形成一个能连接强先验、交互风险偏移、结果反馈、失败边界和受约束更新的可审计框架；它已经展示出诊断价值和产品证据链价值，但尚未证明稳定准确性优势或全局可迁移更新能力。
