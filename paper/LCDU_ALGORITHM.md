# LCDU 算法草案

## 1. 输入与输出

输入：

1. `D_cal`: calibration split，用于 residual mining 与 candidate generation。
2. `D_hold`: held-out split，用于 candidate acceptance。
3. `D_test`: test split，用于论文级最终确认。
4. `theta_0`: 当前 accepted simulator state。
5. `B`: baseline method set。
6. `M`: model/provider set。
7. `K`: candidate budget。

输出：

1. accepted candidate 或 rejected matrix；
2. runtime effect artifact；
3. stability artifact；
4. method summary artifact；
5. paper gate index。

## 2. 主算法

```text
Algorithm LCDU

Input: D_cal, D_hold, D_test, theta_0, K
Output: theta_best, evidence_index

1. Evaluate theta_0 on D_cal and D_hold.
2. Mine residual signatures R from D_cal.
3. Extract semantic factors F from R.
4. Build constraint programs C from F.
5. Generate candidate set U = {u_1, ..., u_K}.
6. For each candidate u_i:
     a. Realize u_i as synchronized prompt-anchor program.
     b. Run simulator theta_0 + u_i on D_hold.
     c. Compute weighted JSD, rank error, worst-segment loss, axis loss.
     d. Mark u_i as improved, regressed, or no_change.
7. Accept the best improving candidate only if:
     a. held-out loss improves over theta_0;
     b. segment coverage is complete;
     c. worst-segment guard passes;
     d. artifact schema is strict JSON;
     e. source split contract is valid.
8. Run repeat validation over accepted candidate.
9. Run ablation: prompt-only, anchor-only, guard-only, synchronized.
10. Run strong baseline matrix.
11. If paper stage, run D_test once after method selection is frozen.
12. Emit evidence index and claim boundary.
```

## 3. Candidate Generation

候选生成不能读取 held-out/test target。允许读取：

1. calibration residual；
2. segment schema；
3. policy schema；
4. prior accepted candidate；
5. public codebook metadata。

候选必须包含：

1. `candidate_id`
2. `generator`
3. `source_split_contract`
4. `latent_factors`
5. `constraint_program`
6. `candidate_prompt_components`
7. `expected_effect`
8. `claim_boundary`
9. `prompt_variant`

`prompt_variant` 不是展示层措辞，而是 LCDU 的方法轴。当前 ANES evidence 显示，`standard` prompt 在公共卫生/医保 conservative segment 上出现 no-acceptance，而 `compact` 与 `deliberative` 能恢复该失败 case。因此论文方法应把 prompt variant 作为 candidate program 的一部分，并通过 held-out gate 接受，而不是事后人工选择。

## 4. Acceptance Gate

```text
Accept(u) =
  improved_loss(u)
  and complete_coverage(u)
  and no_forbidden_worst_segment_regression(u)
  and valid_artifact(u)
  and split_contract_valid(u)
```

失败候选必须记录原因：

1. `loss_not_improved`
2. `segment_coverage_incomplete`
3. `worst_segment_regressed`
4. `not_best_improving_candidate`
5. `split_contract_invalid`
6. `artifact_schema_invalid`

## 5. Repeat Stability

一个 candidate 进入主方法前必须通过 repeat stability：

```text
stable_improvement iff
  improved_count >= required_improved_count
  and regressed_count = 0
  and mean_relative_loss_reduction > 0
```

当前 LCDU L3 的 `h02` 与 `i01` 已经满足这一层，但它们仍然不是 CCF-A 充分证据。

## 6. Ablation

每个 accepted LCDU 方法至少需要：

1. `prompt_only`
2. `anchor_only`
3. `guard_only`
4. `prompt_anchor_synchronized`

论文主张只能写同步机制的经验优势，不能把一次 ablation 写成理论证明。

## 7. Stop-Loss

停止规则：

1. 单候选 held-out loss 明显差于 baseline：停止该候选。
2. 一个 family 多数候选退化：停止该 family。
3. repeat 中出现回退：停止晋级。
4. 修补 residual weakness 破坏 accepted mainline：停止局部修补。
5. 连续两轮 route 不能超过 LCDU L3：归档为 weak/negative route。
6. prompt variant 只能在失败被 artifact 定位后进入恢复矩阵；如果恢复不能通过 repeat validation，必须记录为 prompt-sensitive failure boundary。

## 8. 当前 LCDU L3 映射

| 算法对象 | 当前实例 |
| --- | --- |
| `theta_0` | calibration-split baseline Product run |
| residual focus | `working_family_price_stressed` 与 axis weakness |
| accepted candidate | `h02`, `i01` |
| mechanism | prompt-anchor synchronized guard |
| best held-out runtime loss | `0.000092334757` |
| challenger ceiling | `0.000111545213` |
| remaining weakness | `low_income_food_insecure`, `price_stress_level=high` |

## 9. CCF-A 级扩展要求

LCDU 算法进入论文主表前，还必须完成：

1. 跨任务 public-data ingestion；
2. 跨 provider 稳定性；
3. 强 baseline 矩阵；
4. test split 冻结后最终评估；
5. negative result 与 failure attribution。

## 10. 当前 Prompt-variant 证据

DeepSeek v4-flash 上的 ANES 结果显示：

1. `standard` seed/scale/repeat matrix 为 mixed，公共卫生/医保 conservative upper/middle segment 失败；
2. targeted instability diagnosis 显示该失败可由 `compact` / `deliberative` prompt variant 恢复；
3. prompt-variant seed/scale/repeat matrix 在 8 个 runs 中全部 positive；
4. 这说明 LCDU 的 candidate program 需要包含 prompt variant axis，并把“候选 prompt 是否接受”交给 split-gated acceptance，而不是人工挑选。

该证据提升了 LCDU 的算法框架潜力，但仍不能替代跨 provider、强 baseline 和理论识别证明。

## 11. Cross-provider Variant Selector

当前 cross-provider evidence 进一步要求 LCDU 显式定义 variant selector：

```text
SelectVariant(V) =
  argmax_v stability(v)
  subject to
    all_provider_environments_positive(v)
    and no_parse_failure(v)
    and split_contract_valid(v)
```

在当前 ANES evidence 中：

1. `compact` 在 DeepSeek v4-flash 上稳定，但在本地 gpt-oss-20b 的公共卫生/医保 conservative upper/middle segment 失败；
2. `deliberative` 在 DeepSeek v4-flash 与本地 gpt-oss-20b 两个执行环境中均为 positive；
3. 因此 `deliberative` 是当前 cross-provider selected prompt variant；
4. `compact` 必须保留为 unstable/rejected variant，不能从 artifact 中删除。

这使 LCDU 更接近算法框架：方法不再依赖人工挑 prompt，而是把 prompt variant 作为候选程序，通过跨 provider stability gate 选择。

## 12. Scale Stability Gate

当前 LCDU 还需要把候选方法从 small segment smoke 推进到更大 segment coverage。Scale stability gate 定义为：

```text
ScaleStable(u, S) =
  max(S) >= required_segment_scale
  and all_runs_positive(u, S)
  and all_task_test_improved(u, S)
  and no_parse_failure(u, S)
```

当前 ANES evidence 中：

1. selected variant：`deliberative`
2. segment scales：8, 12, 16
3. available segment count under current schema：16
4. run count：3
5. positive run count：3
6. parse failure count：0

这表示 LCDU 已经在当前 ANES `party_or_ideology × income` schema 下完成 scale stability smoke，但还不是 full-population field validation。论文中应把它表述为 schema-bounded segment scale stability。

## 13. Strong Baseline Boundary

当前 ANES strong baseline matrix 暴露了一个关键边界：

1. LCDU selected LLM prompt 优于 `raw_prompt` 与 `aggregate_anchor_prompt`；
2. 第一层 required baseline families 已经补齐，包括 `population_search` 与 `textgrad_or_prompt_optimizer`；
3. 但 deterministic `calibration_segment_anchor` 与 `population_search_alpha_1` 的 test loss 仍低于 LCDU LLM prompt；
4. 因此 LCDU 的主张不能是“比所有 anchor/search baseline 更准”；
5. 当前更稳妥的算法主张是：

```text
LCDU converts calibration-derived segment constraints into an auditable,
split-gated LLM simulator update, but current LLM realization still has an
anchor-fidelity gap relative to direct deterministic segment anchors.
```

后续算法必须解决 `anchor_fidelity_gap`：

1. 在 prompt 中更强地约束输出贴近 segment anchor；
2. 或把 deterministic anchor 与 LLM narrative 分离：数值分布由 anchor 程序保证，LLM 只生成解释；
3. 或证明在需要语言叙事、反事实解释和产品可交付报告的场景中，LLM simulator 的价值不只来自最低 JSD。

## 14. Anchor-Fidelity Repair Result

最新 repair diagnostic 显示：

1. deterministic anchor-copy 在两个 ANES task 上都关闭了 current LCDU LLM 与 best anchor baseline 的 gap；
2. DeepSeek v4-flash strict-copy prompt 在 16 segment schema 上完成 32 次调用，parse failure 为 0；
3. LLM strict-copy 的 test loss 与 deterministic anchor 基本一致，mean anchor L1 deviation 接近 0；
4. 因此当前失败边界不是“LLM 不能承载 anchor”，而是“原 LCDU prompt 把 anchor 当 soft constraint，允许模型偏移”。

这给出一个新的算法分叉：

1. `LCDU-soft`：当前路线，LLM 可根据 segment semantics 调整 anchor，但会损失数值 fidelity；
2. `LCDU-strict`：LLM 必须复制 anchor 分布，只负责格式化、解释和审计链路；
3. `LCDU-hybrid`：数值分布由 deterministic anchor/search 程序生成，LLM 负责 narrative、counterfactual explanation 和产品报告。

从 CCF-A 角度，只有 `LCDU-hybrid` 或带理论约束的 `LCDU-strict` 有机会把当前 negative strong-baseline 结果转化为可辩护贡献；继续优化 `LCDU-soft` prompt 本身不再是最高优先级。

## 15. Hybrid Method Validation

当前已经把 `LCDU-hybrid` 从 repair diagnostic 提升为方法候选 artifact：

1. script：`experiments/lcdu_anes_hybrid_method_validation.py`
2. artifact：`experiments/results/lcdu_hybrid_method/lcdu-anes-hybrid-method-validation-current-001.json`
3. status：`hybrid_candidate_numeric_parity_soft_not_leading`
4. research decision：`reframe_as_hybrid_auditable_constraint_framework_not_accuracy_win`
5. product decision：`adopt_hybrid_for_auditable_product_reports`

算法含义：

1. `LCDU-soft` 继续作为 negative/diagnostic route 保留；
2. `LCDU-hybrid-strict-anchor-copy` 在当前 ANES task 上与 best deterministic numeric baseline 达到 parity；
3. 该方法不是 accuracy-superior algorithm，而是把数值校准和 LLM 解释层拆开；
4. 论文若继续推进，应把主贡献写成“可审计的约束识别与 LLM 叙事分离框架”，并增加 narrative utility / auditability / counterfactual reporting 指标。

当前 paper gate 已记录：

1. `hybrid_method_validation_ready`
2. `hybrid_method_numeric_parity_not_accuracy_win`
3. `theoretical_identification_proof_ready`
4. `finer_schema_robustness_signal_positive`

因此理论和方法定义已向 CCF-A 目标前进，但 strong-baseline gate 仍不能关闭，因为原始 accuracy criterion 下 LCDU 没有超过 deterministic anchor。

## 16. Current Algorithm Decision

当前应把 LCDU 算法分成三条线判断：

1. `LCDU-soft`
   - 结论：停止作为主贡献方向；
   - 原因：完整第一层 strong baseline 下不领先 deterministic anchor；
   - 用途：保留为 negative result 和 prompt-sensitivity 诊断。
2. `LCDU-strict`
   - 结论：可作为 bounded proof 的构件；
   - 原因：LLM strict-copy 可保真承载 anchor distribution；
   - 用途：证明 LLM 层不会必然破坏 numeric fidelity。
3. `LCDU-hybrid`
   - 结论：当前最有 Product 价值和论文候选潜力；
   - 原因：numeric component 与 deterministic anchor parity，LLM component 负责 audit/explanation/report；
   - 风险：如果论文只用 JSD accuracy 评价，它只能 tie baseline，不能 win。

因此下一阶段算法工作不应继续围绕“让 soft prompt 击败 deterministic anchor”，而应围绕：

1. auditability 指标；
2. explanation faithfulness 指标；
3. counterfactual reporting 指标；
4. customer-facing reproducibility / manifest 指标。

当前 research decision index 已将该判断固化：

`experiments/results/lcdu_research_decision/lcdu-research-decision-index-current-001.json`

核心结论：

1. `LCDU-soft`：`reject_as_ccf_a_main_contribution_accuracy_optimizer`
2. `LCDU-hybrid`：`conditionally_promising_as_auditable_constraint_framework`
3. CCF-A gate：`not_passed_under_accuracy_superiority_criterion`
