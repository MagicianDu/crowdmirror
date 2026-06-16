# R6 风险发现方法 Spec

## 1. 目标修正

R6 下一阶段不再追求“交互仿真整体比静态先验更准”。静态先验是大规模人群模拟底座，交互层的价值在于：

1. 发现静态先验没有标出的发布前风险；
2. 把这些风险变成可审计的风险假设；
3. 在 outcome 或 holdout 回来后验证这些风险假设是否有决策价值；
4. 只有在通过 runtime guard 后，才允许候选更新进入默认参数。

因此 R6 的 Research 主张应从 accuracy superiority 改为：

> 在强静态先验存在的情况下，交互仿真能否提供可验证的风险发现和决策价值。

## 2. 方法对象

R6 方法对象由四部分组成：

```text
Static Prior Foundation
  -> Interaction Risk Discovery
  -> Decision-Value Evaluation
  -> Outcome-Feedback Guarded Learning
```

### 2.1 Static Prior Foundation

静态先验定义无交互状态：

```text
P_static(y | segment, scenario)
```

它提供：

- 大规模人群底座；
- no-interaction control；
- runtime update guard 的参照。

静态先验不是被 R6 整体击败的对手。

### 2.2 Interaction Risk Discovery

交互层输出相对静态先验的风险偏移：

```text
delta_risk(segment) = P_interaction(reject | segment) - P_static(reject | segment)
```

风险发现候选不是“预测已经更准”，而是：

```text
interaction_flags_new_risk = delta_risk >= threshold
```

### 2.3 Decision-Value Evaluation

风险发现是否有价值，用以下指标评估：

| 指标 | 含义 |
| --- | --- |
| `static_prior_miss_recovery_rate` | 静态先验漏报的高风险中，有多少被交互层提前标出 |
| `top_k_risk_hit_rate` | 交互层标出的风险中，有多少在 outcome 中确实高风险 |
| `false_alarm_rate` | 交互层新增风险中，有多少没有 outcome 支持 |
| `decision_regret_reduction` | 用交互风险替代静态先验风险列表后，漏掉的高风险数量是否下降 |

这些指标评估的是决策价值，不是聚合 MAE 胜出。

### 2.4 Outcome-Feedback Guarded Learning

真实或公开 outcome 回来后，只能产生候选更新：

```text
candidate_update = f(error_attribution, failure_boundary)
```

候选更新进入 runtime default 前必须通过：

- 不伤害静态先验底座；
- same-family holdout validation；
- worst segment guard；
- field outcome 或客户业务 outcome 复核。

## 3. 当前 Artifact 合同

新增核心 artifact：

1. `r6_decision_value_metrics.py`
   - 输出 `r6-decision-value-metrics-v1`
   - 计算风险发现的决策价值指标

2. `r6_risk_discovery_holdout_validation.py`
   - 输出 `r6-risk-discovery-holdout-validation-v1`
   - 冻结 source case 的风险发现规则，在 same-family holdout 上验证

3. `r6_risk_discovery_threshold_sweep.py`
   - 输出 `r6-risk-discovery-threshold-sweep-v1`
   - 扫描 `interaction_delta_threshold`，判断是否能靠阈值调优降低 false alarm

4. `r6_false_alarm_discriminator.py`
   - 输出 `r6-false-alarm-discriminator-v1`
   - 在 threshold sweep 失败后，评估非阈值候选规则是否能区分 true risk 和 false alarm，并显式区分 diagnostic-only 与 accepted discriminator

5. `r6_interaction_signal_validity.py`
   - 输出 `r6-interaction-signal-validity-v1`
   - 用 segment pattern、mechanism alignment、counterfactual sensitivity、prior uncertainty、holdout consistency 五个维度评估交互信号有效性
   - `source_key`、`target_case_id`、`target_case_type` 只能用于 audit/report，不能作为评分特征

6. `r6_interaction_signal_validity_holdout_validation.py`
   - 输出 `r6-interaction-signal-validity-holdout-validation-v1`
   - 固定 Interaction Signal Validity 的评分规则，把 source-supported signal 放到独立 public proxy holdout 上复核
   - holdout 标签不参与 source 规则生成，只用于验收 `interaction_signal_validity_holdout_passed`

总链路 artifact：

- `r6_risk_discovery_value_report.py`
- `r6_ccfa_readiness_report.py`
- `r6_evidence_report.py`

## 4. 当前实验结论

截至 2026-06-11，当前 public proxy 证据结论为：

| 指标 | 当前值 | 解释 |
| --- | ---: | --- |
| `static_prior_miss_recovery_rate` | 1.0 | HTOPS 中存在一个静态先验漏报，被交互风险发现恢复 |
| `top_k_risk_hit_rate` | 0.333 | 交互层标出的风险只有 1/3 得到 outcome 支持 |
| `false_alarm_rate` | 0.667 | ANES health / climate 暴露过度风险放大 |
| `decision_regret_reduction` | 1 | 相对静态先验，交互层减少了一个漏报高风险 |
| `risk_discovery_holdout_passed` | false | same-family ANES health -> climate / climate -> health 没有通过 |
| `threshold_tuning_sufficient` | false | HTOPS 真风险和 ANES 误报的 `interaction_delta_vs_static` 都是 0.07，阈值无法分离 |
| `false_alarm_discriminator_ready` | false | 当前 case/source family 候选能分开 1 个 true positive 与 2 个 false alarm，但无 in-family positive signal 或 holdout，因此不能验收 |
| `interaction_signal_validity_generalized` | false | HTOPS 为 `diagnostic_only`，ANES health / climate 为 `reject_as_likely_false_alarm`，但 `accepted_count=0`，尚未在 holdout/field outcome 上泛化 |
| `interaction_signal_validity_holdout_passed` | false | 1 个 source-supported signal 在 2 个独立 public proxy holdout 上 0 个通过、2 个 contradicted，不能升级为泛化规则 |

当前状态：

```text
decision_value_partial_high_false_alarm
risk_discovery_holdout_failed_current_public_proxies
threshold_sweep_no_separating_rule
false_alarm_discriminator_diagnostic_only
interaction_signal_validity_diagnostic_only
interaction_signal_validity_holdout_failed_current_public_proxies
```

## 5. 当前 Claim Boundary

可以宣称：

- R6 已经有可计算的风险发现价值指标；
- R6 在 HTOPS 上发现了一个静态先验漏报的风险；
- R6 能把 ANES health / climate 的交互过度放大识别为 false alarm；
- R6 已证明当前 false alarm 不是简单调 `interaction_delta_threshold` 能解决的问题；
- R6 已诊断出当前 case/source family 规则可以分离 public proxy 样本，但这更像过拟合记忆而非泛化能力；
- R6 已实现不依赖 source/family 标签的 Interaction Signal Validity Score，并识别出一个 current-proxy-supported 正向信号和两个 likely false alarm；
- R6 已实现 Interaction Signal Validity holdout validation，并证明当前 source-supported 正向信号没有通过独立 public proxy holdout；
- R6 能阻断未通过 holdout 的候选更新。

不能宣称：

- R6 已经证明交互仿真整体比静态先验更准；
- R6 已经具备 CCF-A 主贡献算法水准；
- R6 已经通过 same-family risk-discovery holdout；
- R6 已经形成可泛化 Interaction Signal Validity 规则；
- R6 已经通过 Interaction Signal Validity 的独立 holdout validation；
- R6 可以进入 runtime default update。

## 6. CCF-A Gate

R6 达到 CCF-A 主贡献前，至少需要关闭六个 gap：

1. `needs_formal_problem_and_theory_section`
2. `needs_decision_value_metric_to_pass`
3. `needs_risk_discovery_holdout_validation`
4. `needs_interaction_signal_validity_generalization`
5. `needs_signal_validity_holdout_validation`
6. `needs_field_outcome_validation`

其中第 2 项已经从“指标缺失”升级为“指标已实现但未通过”。
第 4 项已经从“缺少非阈值方向”升级为“Interaction Signal Validity 诊断组件已实现，但当前只在 public proxy 上形成 supported/rejected 诊断，尚未泛化验收”。
第 5 项已经从“未显式定义”升级为“holdout validation 已实现但当前未通过”。

## 7. 下一步实验要求

下一步不应继续泛泛增加 proxy，也不应只调阈值。当前 threshold sweep 已显示 true signal
和 false alarm 共享相同 `interaction_delta_vs_static=0.07`；第一版 false-alarm discriminator
已证明 case/source family 规则可以分开当前样本，但属于 diagnostic-only。Interaction Signal Validity
已经把主线从 family gate 升级为通用评分；新增 holdout validation 显示当前 HTOPS 正向信号在 ANES health / climate heldout 上未通过。后续必须验证这些评分维度是否能在独立 supported holdout 或 field outcome 上泛化。新增 holdout 应满足以下条件：

1. same-family；
2. source case 有 positive risk-discovery signal；
3. holdout outcome 可评估 top-k risk hit；
4. segment 或 case mapping 可审计；
5. 能区分真实风险发现和 false alarm。

当前已经尝试的 target case family / source family discriminator 不能直接作为方法结论。Interaction Signal Validity 只有在满足以下任一条件后，才允许从 diagnostic 升级：

1. 独立 holdout 上保持 current-proxy-supported signal，同时降低 likely false alarm；
2. 发布前可用特征能跨 source family 解释 true positive 与 false alarm；
3. field outcome 或客户业务 outcome 复核证明该 score 能降低误报且不漏掉真实高风险。

如果新增 holdout 后仍满足：

```text
false_alarm_rate > 0.5
risk_discovery_holdout_passed = false
```

则 R6 方法主张需要降级为 Product audit / failure diagnosis，而不是继续作为 CCF-A 主贡献推进。
