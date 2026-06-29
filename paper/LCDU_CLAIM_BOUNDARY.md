# LCDU Claim Boundary

## 1. 当前可写结论

当前证据允许写：

1. LCDU L3 是当前 policy-reaction public-data benchmark 上的 active mainline。
2. `h02` 与 `i01` 在 calibration-split held-out repeat 中表现为 stable improvement。
3. 当前有限 route-combo grid 中，非 LCDU 路线没有超过 LCDU L3。
4. LCDU L3 的机制证据支持 prompt-anchor synchronized guard 比单边 patch 更有解释力。
5. LCDU method summary 可以进入 Product report，作为 bounded transfer evidence。
6. 两个新增 public task 已完成 exact variable binding 和 aggregate target skeleton smoke。
7. ANES 2024 SDA public-use sample slice 已生成 microdata-derived aggregate 与部分 segment-level target distributions。
8. ANES 两个 public tasks 的 split-gated segment anchor transfer smoke 呈正向：heldout 接受，test 改善。
9. DeepSeek v4-flash 小规模 LLM simulator smoke 显示 `lcdu_segment_anchor_prompt` 在两个 ANES task 的 heldout 与 test 上优于 raw prompt。
10. DeepSeek v4-flash seed/scale/repeat 矩阵为 mixed：气候/能源稳定，公共卫生/医保在 conservative upper/middle segment 出现不接受。
11. 针对该 mixed signal 的 instability diagnosis 显示，失败 case 可被 `compact` / `deliberative` prompt variant 恢复。
12. DeepSeek v4-flash prompt-variant seed/scale/repeat 矩阵显示 8/8 runs 为 positive，两个 ANES task 的 accepted rate 与 test improved rate 均为 1.0。
13. DeepSeek v4-flash 与本地 LM Studio `openai/gpt-oss-20b` 的 cross-provider matrix 显示 `deliberative` 是跨执行环境稳定的 selected prompt variant。
14. DeepSeek v4-flash selected variant=`deliberative` 的 scale stability matrix 在 segment scale 8/12/16 上 3/3 positive，覆盖当前 ANES `party_or_ideology × income` schema 下全部 16 个 segment。
15. ANES strong baseline matrix 已补齐第一层 required baseline families：`llm_raw_prompt`、`llm_aggregate_anchor`、`deterministic_anchor_search`、`population_search`、`textgrad_or_prompt_optimizer`。
16. 在该完整第一层矩阵中，LCDU LLM prompt 明显优于 LLM raw/aggregate 与 prompt-optimizer baseline，但没有优于 deterministic segment-anchor / population-search alpha=1 baseline。
17. Anchor-fidelity repair diagnostic 显示：当 prompt 明确要求 LLM strict-copy segment anchor 时，DeepSeek v4-flash 在当前 16 segment schema 上 32/32 调用可保真复制，test loss 与 deterministic anchor 基本一致。
18. LCDU-hybrid method validation 显示：hybrid/strict candidate 在两个 ANES task 上达到 best deterministic numeric baseline parity，但 research decision 是“reframe as hybrid auditable constraint framework, not accuracy win”。
19. Bounded theoretical identification proof 已形式化 split isolation、anchor-copy identification 和 non-superiority boundary，并关闭 `theoretical_identification_proof_ready` 子门控。
20. Finer schema robustness matrix 在 `party_or_ideology+income`、加 `age`、加 `education`、以及四轴 schema 上 4/4 positive，最大 common segment count 达到 143。

## 2. 当前不能写的结论

当前证据不能写：

1. LCDU 是通用人群模拟校准算法。
2. LCDU 已达到 CCF-A 论文充分证据。
3. LCDU 已经跨政策任务成立。
4. LCDU 已经跨 provider 成立。
5. LCDU 已经完成客户现场验证。
6. LCDU 能预测真实政策实施后的行为反应。
7. route coverage 已经穷尽完整算法空间。
8. 新增 public task 已完成完整 task-card segment schema 覆盖；当前 finer schema 只覆盖 SDA slice 中可用的 `age`、`education`、`income`、`party_or_ideology`，仍缺 region、urbanicity、health-insurance context。
9. SDA sample slice 等价于完整 ANES raw release archive ingestion。
10. cross-task anchor smoke 等价于 LLM simulator、prompt update 或 provider generalization 证据。
11. 2 segment/task 的 DeepSeek v4-flash smoke 等价于 seed/scale/repeat、strong baseline 或跨 provider 证据。
12. 当前 LCDU 已经跨 provider 稳定通过；现有 prompt-variant 稳定性仍只来自 DeepSeek v4-flash。
13. prompt-variant repeat 的 8/8 positive 可以等同于强 baseline 胜出或 CCF-A 充分证据。
14. cross-provider selected variant positive 可以写成“所有 prompt variants 都跨 provider 稳定”；本地 `compact` 仍有 1 个公共卫生/医保失败 case。
15. scale=16 的 ANES segment schema 覆盖可以等同于真实 full-population 或客户现场规模验证。
16. LCDU 已经通过 strong baseline gate；当前 strong baseline artifact 虽然 missing family count 为 0，但状态仍为 `strong_baseline_lcdu_not_leading`。
17. Anchor-fidelity repair positive 可以写成原 LCDU prompt 已通过 strong baseline；repair diagnostic 只是说明 gap 可由 strict-copy/hybrid architecture 关闭。
18. LCDU-hybrid 已经是 accuracy-superior algorithm；当前 evidence 只支持 numeric parity + audit decomposition。
19. bounded theoretical proof 等价于跨任务 generalization bound；它只覆盖当前 ANES schema 下的 hybrid identification。

## 3. Product 可用边界

Product 可以写：

1. 该报告引用了 Research accepted method summary。
2. 当前方法有 public-data held-out evidence。
3. 报告中的 method summary 包含 accepted candidates、risk flags、claim boundaries。
4. 当前结果是可审计 workflow evidence。

Product 不能写：

1. 客户人群预测已验证。
2. 政策效果已实地验证。
3. 当前模拟具有生产级准确率保证。
4. 本地 LLM 结果等价于跨模型结论。

## 4. CCF-A Gate

LCDU 从当前状态进入 CCF-A 主张，需要至少满足：

1. 理论定义闭合：formal objects 与 artifact schema 一一对应，当前 bounded proof 已覆盖 hybrid numeric identification，但仍缺跨任务 generalization bound。
2. 跨任务验证：至少 2 个新增 public policy tasks 完成更完整的 segment target construction 和 test split model validation。
3. 强 baseline 对比：第一层 family coverage 已补齐；若要支撑主表，还需要 DSPy、TPE、GA/CEM、LLM-as-optimizer 等更强 optimizer/repeat baseline 进入统一矩阵。
4. 跨 provider 验证：至少 2 个 provider 同向。
5. 失败边界解释：residual weakness 与 negative routes 可解释。
6. test split 冻结：最终主表不能继续使用 held-out 调参。

## 5. 降级规则

若出现以下情况，论文主张必须降级：

1. LCDU 只在当前 HPS/HTOPS 任务有效。
2. LCDU 被两个以上强 baseline 稳定超过。
3. LCDU 平均 loss 改善但 worst-segment loss 系统性恶化。
4. LCDU 只能靠人工 hard-code segment patch 才有效。
5. 跨 provider 结果方向相反。

降级后的表述：

> LCDU is a domain-specific calibration diagnostic and bounded transfer mechanism, not a general LLM population simulation calibration algorithm.

## 6. 审稿风险

最大审稿风险：

1. 被认为只是 prompt engineering。
2. 被认为只在单一任务调参。
3. baseline 不够强。
4. 数据任务不够外部。
5. 失败边界没有理论解释。
6. Product transfer 被误解为 field validation。
7. aggregate codebook smoke 被误写成 microdata-level validation。
8. SDA sample slice 被误写成完整数据 release ingestion 或模型有效性证明。

应对方式：

1. 在方法部分强调 latent-constraint update 与 split-gated acceptance。
2. 在实验部分加入强 baseline 和 negative results。
3. 在讨论部分主动写明不能宣称的边界。
4. 在 artifact 中保留 exact split/model/run/candidate ids。
5. 在 public task evidence 中区分 task card、codebook smoke、microdata ingestion 和 model validation 四层。
6. 在 ANES evidence 中明确 `segment_schema_partial_coverage`，不把缺失轴隐去。
7. 在 cross-task evidence 中明确 `anchor_transfer_only`，不把 split-gated anchor 结果包装成 LLM 运行结果。
8. 在 LLM evidence 中明确 `small_segment_smoke` 与 provider/model/segment scale，不把小规模 smoke 包装成主实验表。
9. 对 mixed seed/scale/repeat 结果必须保留失败 segment 和 no-acceptance case，不能只报告 3/4 positive runs。
10. 对 prompt-variant 恢复结果必须写成“prompt wording sensitivity 被定位并在单 provider 上恢复”，不能写成“LCDU 已经无失败边界”。
11. 对 cross-provider 结果必须写成“selected variant=deliberative 跨 provider 正向”，不能写成“全 prompt family 跨 provider 无失败”。
12. 对 scale stability 必须写成“当前 ANES 16 segment schema 内的规模扩展”，不能写成“全人群规模仿真已验证”。
13. 对 strong baseline 必须写成“第一层 baseline family coverage 已完整，但 LCDU LLM 未领先 deterministic anchor / population-search alpha=1”，不能写成“LCDU 已强基线胜出”。
14. 对 anchor-fidelity repair 必须写成“strict-copy/hybrid 可关闭数值 gap”，不能写成“原 LCDU LLM prompt 已自然学会校准”。
15. 对 hybrid method validation 必须写成“numeric parity + auditability”，不能写成“accuracy superiority”。
16. 对 theoretical proof 必须写成“bounded identification proof”，不能写成“完整 CCF-A 理论证明”。
17. 对 finer schema 必须写成“当前 SDA slice 可用轴下 robust”，不能写成“完整 task-card schema robust”。
