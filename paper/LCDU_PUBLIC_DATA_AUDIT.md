# LCDU Public Data Audit

核验日期：2026-05-23

本审计用于选择 LCDU 跨政策任务验证的数据源。原则是：

1. 优先 official/public-use microdata；
2. 必须能构造 segment-level target distribution；
3. 必须能形成 calibration/heldout/test split；
4. 必须有明确 claim boundary；
5. 不把客户或私有数据混入 paper 主证据。

## 1. 当前主任务：生活成本与食品援助政策反应

数据源：U.S. Census Household Pulse Survey / HTOPS Public Use File

来源：

- https://www.census.gov/programs-surveys/household-pulse-survey/data/datasets.2024.html

可用性：

1. Census 提供 PUF、replicate weight file、data dictionary。
2. HPS cross-sectional collection 已结束，HTOPS 进入 longitudinal design。
3. 主题覆盖 spending、inflation、social/economic well-being、food/housing/health 等。

当前状态：

1. 已作为主任务进入 LCDU L3。
2. 已有 calibration-split held-out evidence。
3. 可继续作为 anchor task。

边界：

1. 是 public-data alignment，不是 field validation。
2. 不能代表所有政策反应任务。

优先级：已采用。

## 2. 候选任务 A：公共卫生/医保政策态度

候选数据源：

1. General Social Survey (GSS)
   - https://www.norc.org/research/projects/gss.html
2. ANES 2024 Time Series Study
   - https://sda.berkeley.edu/sdaweb/docs/anes2024full/DOC/anes_timeseries_2024_userguidecodebook_20250808.pdf
3. Cooperative Election Study / CES cumulative common content
   - https://sda.ist.berkeley.edu/sdaweb/docs/ces-cumulative-2024-v10/DOC/guide_cumulative_2006-2024.pdf

可构造 target：

1. 政府医保、医疗支出、公共卫生政策支持。
2. segment 可用 demographic、party/ideology、income、age、education。
3. 输出可构造为 support/oppose/neutral 分布。

当前精确变量绑定：

1. 主数据源：ANES 2024 Time Series Study。
2. 目标变量：`V241245`，7 点政府医保-私人医保自我定位。
3. 官方 codebook 频数可聚合为：
   - `government_insurance_plan`: code 1/2/3，2288 / 4778 = 0.478861448305
   - `mixed_or_middle_position`: code 4，833 / 4778 = 0.174340728338
   - `private_insurance_plan`: code 5/6/7，1657 / 4778 = 0.346797823357
4. 当前仅使用官方 codebook aggregate frequency table；尚未加载 public-use microdata。

优点：

1. 与当前生活成本任务相对正交。
2. 有公共态度变量，适合政策反应模拟。
3. 可测试 LCDU 是否能处理价值观/意识形态因素，而不仅是经济压力因素。

风险：

1. 不同数据源问题措辞不一致，跨年 harmonization 需要谨慎。
2. 部分变量可能不是每年都有。
3. GSS 样本量可能小于 CES，不适合过细 segment。

建议：

优先用 ANES `V241245` 作为第一层 ingestion smoke target；GSS/CES 后续作为 harmonization 或 robustness source。

优先级：高。

## 3. 候选任务 B：气候/能源政策态度

候选数据源：

1. GSS environment / government spending variables。
2. ANES climate / energy / environment policy attitude variables。
3. CES cumulative policy attitudes。

可构造 target：

1. 支持/反对环境保护、能源补贴、碳税或政府支出。
2. segment 可用 region、party/ideology、income、education、urbanicity。

当前精确变量绑定：

1. 主数据源：ANES 2024 Time Series Study。
2. 目标变量：`V241258`，7 点环境保护-商业负担 tradeoff 自我定位。
3. 官方 codebook 频数可聚合为：
   - `support_more_regulation_or_spending`: code 1/2/3，2670 / 4577 = 0.583351540310
   - `mixed_or_status_quo`: code 4，738 / 4577 = 0.161240987546
   - `oppose_more_regulation_or_spending`: code 5/6/7，1169 / 4577 = 0.255407472143
4. CES cumulative guide 暂时降为 supporting source；后续用于跨数据源 robustness，而不是当前 smoke 的主变量来源。

优点：

1. 与当前 food/cost task 差异大，适合检验 LCDU generalization。
2. 可测试 value-laden policy reaction。
3. 能暴露 prompt/persona 里的 ideology 与 material interest 冲突。

风险：

1. “能源补贴”类直接变量未必稳定存在。
2. 气候态度更像 opinion alignment，不一定是具体政策选择。
3. 容易被 partisan prior 主导，需要 baseline 强化。

建议：

作为第二优先候选任务；当前先用 ANES `V241258` 形成 aggregate target skeleton，下一步再加载 public-use microdata 生成 segment-level target distribution。

优先级：高。

## 4. 候选任务 C：福利/住房/税收补贴政策态度

候选数据源：

1. GSS national spending priorities。
2. ANES economic policy and redistribution attitudes。
3. CES policy preference items。
4. American Housing Survey 仅作为住房负担 covariate 候选，不优先作为态度 target。

可构造 target：

1. welfare spending、tax credit、housing assistance、redistribution support。
2. segment 可用 income、housing burden proxy、family status、employment status。

优点：

1. 与 Product 政策研究机构场景贴合。
2. 与当前 food/cost task 有关联但不完全重复。
3. 适合检验 LCDU 是否能迁移 economic hardship factors。

风险：

1. 若仍使用 HPS/HTOPS，可能与当前主任务太接近。
2. GSS/CES 的政策态度变量可能更抽象，难以映射到具体政策 intervention。
3. housing public-use data 多为状态变量，不一定有政策选择。

建议：

优先使用 GSS/CES 态度变量；AHS 只作为后续 covariate enrichment，不作为主 target。

优先级：中高。

## 5. 候选任务 D：制度信任与公共支出优先级

候选数据源：

1. GSS confidence in institutions / spending priorities。
2. ANES trust, government responsibility, policy attitudes。
3. CES political trust and policy modules。

可构造 target：

1. 政府支出优先级；
2. 对政府负责范围的态度；
3. confidence/trust 分层下的政策支持。

优点：

1. 直接检验 LCDU 的 latent factor 表示是否有用。
2. 能测试 institutional_trust 这类 factor 是否跨任务成立。
3. 有利于理论贡献，不只是工程调参。

风险：

1. 目标可能不够“政策反应”，更像政治态度。
2. 需要把 trust variable 放在 segment 还是 target 上界定清楚。

建议：

作为解释性/机制任务，而不是第一批主任务。

优先级：中。

## 6. 推荐选择

第一批进入 ingestion 的两个新增任务：

1. 公共卫生/医保政策态度：GSS + ANES/CES 变量审计后选择一个主数据源。
2. 气候/能源政策态度：优先 ANES/CES，大样本更适合 segment split。

备用任务：

1. 福利/住房/税收补贴政策态度。
2. 制度信任与公共支出优先级。

## 7. 下一步 ingestion gate

每个候选任务必须先输出：

```json
{
  "schema_version": "lcdu-public-task-card-v1",
  "task_id": "public_health_policy_attitude_v1",
  "data_source": "...",
  "policy_options": ["support", "oppose", "neutral"],
  "segment_schema": ["income", "age", "education", "ideology"],
  "target_distribution_fields": ["..."],
  "split_contract": {
    "candidate_generation": "calibration",
    "candidate_acceptance": "heldout",
    "final_claim_check": "test"
  },
  "claim_boundary": "public opinion alignment only; not field validation"
}
```

没有 task card 的数据源不能进入 LCDU 主实验矩阵。

## 8. Task Card Artifacts

当前已经为第一批推荐任务生成 task card smoke artifacts：

1. `experiments/results/lcdu_public_task_cards/public-health-medical-insurance-attitude-v1.json`
2. `experiments/results/lcdu_public_task_cards/climate-energy-regulation-attitude-v1.json`
3. `experiments/results/lcdu_public_task_cards/lcdu-public-task-card-index-current-001.json`

这些 artifact 的含义是：

1. 数据源、候选变量、policy options、segment schema 和 split contract 已明确；
2. 任务可以进入下一步 exact microdata variable binding；
3. 还没有完成 public-use microdata ingestion；
4. 还没有生成真实 target distribution；
5. 不能作为跨任务 LCDU 有效性的证据。

下一步 ingestion smoke 必须输出新的 `lcdu-public-task-ingestion-smoke-v1` artifact，
而不是把 task card 伪装成 ingestion 结果。

## 9. Ingestion Smoke Artifacts

当前已经新增 `lcdu-public-task-ingestion-smoke-v1`，用于把官方 codebook 频数表转成 target distribution skeleton：

1. `experiments/results/lcdu_public_task_ingestion_smoke/public-health-medical-insurance-attitude-v1-smoke.json`
2. `experiments/results/lcdu_public_task_ingestion_smoke/climate-energy-regulation-attitude-v1-smoke.json`
3. `experiments/results/lcdu_public_task_ingestion_smoke/lcdu-public-task-ingestion-smoke-index-current-001.json`

这些 artifact 已关闭两类较小 gate：

1. exact public variable binding；
2. aggregate target distribution skeleton materialization。

但它们仍然不能关闭以下 gate：

1. public-use microdata ingestion；
2. segment-level target distribution construction；
3. calibration/heldout/test split materialization；
4. LCDU cross-task effectiveness validation。

因此 paper gate 下一步应进入 `load_public_use_microdata_or_verified_sample_slice`，而不是直接宣称跨任务有效。

## 10. ANES SDA Public-use Sample Slice

当前已经通过 SDA custom subset 下载 ANES 2024 public-use microdata slice：

1. fetch script：`experiments/lcdu_anes_sda_subset_fetch.py`
2. ingestion script：`experiments/lcdu_anes_public_microdata_ingestion.py`
3. raw local file：`data/raw/anes_2024/anes2024_sda_lcdu_subset.csv`
4. artifact：`experiments/results/lcdu_public_task_microdata/lcdu-anes-2024-sda-public-microdata-001.json`

该 sample slice 包含 5521 行、10 个变量：

1. case id / weight：`V240001`, `V240103a`
2. target variables：`V241245`, `V241258`
3. segment variables：`V241458x`, `V241465x`, `V241566x`, `V241177`, `V241550`, `V241501x`

已完成的证据：

1. `V241245` 与 `V241258` 的 microdata-derived aggregate distribution 与 codebook smoke 完全对齐；
2. 已生成 `party_or_ideology × income` segment-level target distributions；
3. 已按 `V240001` 的 hash modulo 建立 `calibration/heldout/test` split；
4. paper gate 已关闭 `load_public_use_microdata_or_verified_sample_slice`。

仍未完成的证据：

1. task card 要求的部分 segment axes 尚未覆盖：
   - 公共卫生/医保缺 `health_insurance_context`
   - 气候/能源缺 `region` 与 `urbanicity`
2. 当前 artifact 是 SDA subset，不是完整 raw release archive ingestion；
3. 尚未把这些新增任务接入 LCDU simulator benchmark；
4. 尚未跑 strong baseline、cross-provider、scale/seed/repeat。

因此它能支撑“public-use sample-slice ingestion 与 segment target materialization 已完成”，但不能支撑“LCDU 跨任务有效”。

## 11. Cross-task Anchor Validation Smoke

当前已经新增第一层 cross-task validation：

1. script：`experiments/lcdu_anes_cross_task_validation.py`
2. artifact：`experiments/results/lcdu_cross_task_validation/lcdu-anes-cross-task-validation-current-001.json`
3. validation type：`split_gated_segment_anchor_transfer_smoke`

该 smoke 的设计：

1. calibration split 生成候选 anchor：
   - `uniform_prior`
   - `calibration_aggregate_prior`
   - `calibration_segment_anchor`
   - `lcdu_smoothed_segment_anchor_alpha_*`
2. heldout split 决定 candidate accepted/rejected；
3. test split 只做最终检查；
4. loss metric 为 `weighted_choice_distribution_jsd`。

真实 ANES 结果：

1. 公共卫生/医保任务：
   - heldout initial loss: 0.04457889833805818
   - heldout best/final loss: 0.005397143516893713
   - test initial loss: 0.04434039490706278
   - test final loss: 0.006094935382542338
   - accepted method: `calibration_segment_anchor`
2. 气候/能源任务：
   - heldout initial loss: 0.05061340525537323
   - heldout best/final loss: 0.006892295320535387
   - test initial loss: 0.06532217743555663
   - test final loss: 0.008343247118118962
   - accepted method: `calibration_segment_anchor`

当前结论：

1. ANES 两个 public tasks 上，segment-level calibration anchor 在 heldout 和 test 上均优于 aggregate prior；
2. 这说明 LCDU 的“segment anchor / constraint transfer”组件有跨任务正信号；
3. 但这还不是 LLM simulator validation，也不是 prompt update validation；
4. paper gate 因此关闭 `run_cross_task_public_data_validation` 的第一层 anchor smoke，并进入 `run_cross_task_llm_simulator_validation`。

## 12. Cross-task LLM Simulator Smoke

当前已经新增第一层真实 LLM simulator validation：

1. script：`experiments/lcdu_anes_llm_simulator_validation.py`
2. artifact：`experiments/results/lcdu_llm_simulator_validation/lcdu-anes-llm-simulator-validation-deepseek-v4-flash-2seg-current-001.json`
3. provider：DeepSeek OpenAI-compatible endpoint
4. model：`deepseek-v4-flash`
5. validation type：`split_gated_llm_segment_simulator_smoke`
6. scale：每个任务选择 heldout N 最大且 calibration/test 均存在的 2 个 segment；共 12 次 LLM 调用。

真实 LLM 结果：

1. 公共卫生/医保任务：
   - selected segments:
     - `party_or_ideology=liberal|income=upper`
     - `party_or_ideology=conservative|income=upper`
   - accepted method: `lcdu_segment_anchor_prompt`
   - heldout initial loss: 0.012487921594210112
   - heldout final loss: 0.0031735148745522168
   - test initial loss: 0.022035673895836442
   - test final loss: 0.00907997791800591
2. 气候/能源任务：
   - selected segments:
     - `party_or_ideology=liberal|income=upper`
     - `party_or_ideology=conservative|income=upper`
   - accepted method: `lcdu_segment_anchor_prompt`
   - heldout initial loss: 0.02425280708371007
   - heldout final loss: 0.005099641773424251
   - test initial loss: 0.027324620607139388
   - test final loss: 0.006253621712622866

LLM accounting：

1. total calls: 12
2. input tokens: 2839
3. output tokens: 534
4. parse failure count: 0

当前结论：

1. DeepSeek v4-flash 的小规模真实 LLM run 能消费 LCDU segment anchor prompt；
2. 两个 ANES public tasks 在 heldout 与 test 上均显示 `lcdu_segment_anchor_prompt` 优于 raw prompt；
3. 这比 anchor-only smoke 更强，因为它通过了真实 provider、prompt、parser 和 manifest 线路；
4. 但它仍只是 2 segment/task 的 smoke，不是 seed/scale/repeat 或 strong baseline matrix。

因此 paper gate 已关闭 `run_cross_task_llm_simulator_validation`，下一步进入 `run_cross_task_llm_seed_scale_repeat_validation`。

## 13. Cross-task LLM Seed/Scale/Repeat Matrix

当前已经执行第一层 seed/scale/repeat 矩阵：

1. script：`experiments/lcdu_anes_llm_seed_scale_repeat_matrix.py`
2. artifact：`experiments/results/lcdu_llm_seed_scale_repeat/lcdu-anes-llm-seed-scale-repeat-deepseek-v4-flash-s2s4-o0o1-standard-001.json`
3. provider：DeepSeek OpenAI-compatible endpoint
4. model：`deepseek-v4-flash`
5. matrix：
   - segment scales: 2, 4
   - segment offsets: 0, 1
   - prompt variant: `standard`
   - run count: 4
   - total LLM calls: 72
   - parse failure count: 0

矩阵结果：

1. overall status: `seed_scale_repeat_signal_mixed`
2. positive run count: 3 / 4
3. 气候/能源任务：
   - accepted rate: 1.0
   - test improved rate: 1.0
4. 公共卫生/医保任务：
   - accepted rate: 0.75
   - test improved rate: 0.75
5. 失败 run：
   - scale: 2
   - offset: 1
   - task: 公共卫生/医保
   - selected segments:
     - `party_or_ideology=conservative|income=upper`
     - `party_or_ideology=conservative|income=middle`
   - heldout raw/final loss 均为 0.0037091448532385113
   - test raw/final loss 均为 0.009770047302380963

当前结论：

1. LCDU segment anchor prompt 在气候/能源任务上表现稳定；
2. 公共卫生/医保任务存在 segment-specific instability，尤其是 conservative upper/middle segment；
3. 这不是方法失败，但已经说明“跨任务 LLM seed/scale/repeat 稳定性”还不能关闭；
4. paper gate 因此新增 `cross_task_llm_seed_scale_repeat_signal_not_positive`，并把下一步设为 `diagnose_cross_task_llm_seed_scale_repeat_instability`。

## 14. LLM Instability Diagnosis

当前已经对第 13 节中的 mixed signal 执行 targeted diagnosis：

1. script：`experiments/lcdu_anes_llm_instability_diagnosis.py`
2. artifact：`experiments/results/lcdu_llm_instability_diagnosis/lcdu-anes-llm-instability-diagnosis-deepseek-v4-flash-prompt-variants-current-001.json`
3. provider：DeepSeek OpenAI-compatible endpoint
4. model：`deepseek-v4-flash`
5. diagnosis type：`targeted_prompt_variant_recovery_probe`
6. targeted failure：
   - task：公共卫生/医保
   - scale：2
   - offset：1
   - original prompt variant：`standard`
   - selected segments：
     - `party_or_ideology=conservative|income=upper`
     - `party_or_ideology=conservative|income=middle`

诊断结果：

1. overall status：`instability_recovered_by_prompt_variant`
2. failure count：1
3. recovered failure count：1
4. persistent failure count：0
5. total LLM calls：24
6. parse failure count：0

恢复证据：

1. `compact` variant 恢复公共卫生/医保失败 case：
   - accepted method：`lcdu_segment_anchor_prompt`
   - heldout loss：0.015178675354336436 -> 0.010071105701142835
   - test loss：0.022127444878231053 -> 0.008182949068345598
2. `deliberative` variant 同样恢复该 case：
   - accepted method：`lcdu_segment_anchor_prompt`
   - test loss：0.011365115141783556 -> 0.0019129589058892909

当前解释：

1. 失败不是固定 segment target 不可校准，而是明显受 prompt wording 影响；
2. LCDU 的 segment anchor 机制仍然有效，但 standard prompt 对公共卫生/医保 conservative segment 的表达不稳；
3. 这支持把 prompt variant 纳入方法组件，而不是把失败隐藏；
4. diagnosis 仍只是 targeted probe，不等价于完整 repeat matrix。

## 15. Prompt-variant Seed/Scale/Repeat Matrix

为验证第 14 节的恢复不是单点偶然，已经执行 prompt-variant repeat matrix：

1. script：`experiments/lcdu_anes_llm_seed_scale_repeat_matrix.py`
2. artifact：`experiments/results/lcdu_llm_seed_scale_repeat/lcdu-anes-llm-seed-scale-repeat-deepseek-v4-flash-s2s4-o0o1-promptvariants-001.json`
3. provider：DeepSeek OpenAI-compatible endpoint
4. model：`deepseek-v4-flash`
5. prompt variants：`compact`, `deliberative`
6. segment scales：2, 4
7. segment offsets：0, 1
8. run count：8
9. total LLM calls：144
10. parse failure count：0

矩阵结果：

1. overall status：`seed_scale_repeat_signal_positive`
2. positive run count：8 / 8
3. 气候/能源：
   - accepted rate：1.0
   - test improved rate：1.0
4. 公共卫生/医保：
   - accepted rate：1.0
   - test improved rate：1.0
5. `compact`：4 / 4 runs positive
6. `deliberative`：4 / 4 runs positive

当前结论：

1. 在 DeepSeek v4-flash 上，LCDU segment anchor prompt 的稳定性依赖 prompt variant；
2. 将 prompt variant 作为显式方法轴后，原 mixed signal 被恢复为 positive；
3. 这增强了 LCDU 作为算法框架的证据，因为失败诊断、候选恢复和 repeat validation 都被 artifact 化；
4. 但它仍不是 CCF-A 充分证据，因为还缺跨 provider、强 baseline、规模扩展和更完整 segment schema。

## 16. Cross-provider Prompt Variant Stability

当前已经执行第一层 cross-provider stability matrix：

1. script：`experiments/lcdu_anes_llm_cross_provider_matrix.py`
2. artifact：`experiments/results/lcdu_llm_cross_provider/lcdu-anes-llm-cross-provider-matrix-deepseek-flash-lmstudio-gptoss-current-001.json`
3. provider environments：
   - `https://api.deepseek.com::deepseek-v4-flash`
   - `http://127.0.0.1:1234/v1::openai/gpt-oss-20b`
4. source matrices：
   - DeepSeek v4-flash prompt variants：8 / 8 positive
   - LM Studio gpt-oss-20b prompt variants：7 / 8 positive

本地 LM Studio 结果：

1. artifact：`experiments/results/lcdu_llm_seed_scale_repeat/lcdu-anes-llm-seed-scale-repeat-lmstudio-gpt-oss-20b-s2s4-o0o1-promptvariants-001.json`
2. status：`seed_scale_repeat_signal_mixed`
3. total LLM calls：144
4. parse failure count：0
5. 气候/能源：
   - accepted rate：1.0
   - test improved rate：1.0
6. 公共卫生/医保：
   - accepted rate：0.875
   - test improved rate：0.875
7. 失败 run：
   - scale：2
   - offset：1
   - prompt variant：`compact`
   - selected segments：
     - `party_or_ideology=conservative|income=upper`
     - `party_or_ideology=conservative|income=middle`
   - heldout raw/final loss：0.005201882389374862 -> 0.005201882389374862
   - test raw/final loss：0.010402540574739057 -> 0.010402540574739057

Cross-provider 聚合结果：

1. overall status：`cross_provider_selected_variant_positive`
2. provider environment count：2
3. positive provider environment count：1
4. selected prompt variant：`deliberative`
5. `compact`：
   - provider environment count：2
   - positive provider environment count：1
   - all provider environments positive：false
6. `deliberative`：
   - provider environment count：2
   - positive provider environment count：2
   - all provider environments positive：true

当前解释：

1. LCDU 的跨 provider 证据不是“所有 prompt variant 都稳定”，而是“存在一个可显式选择的稳定 variant：`deliberative`”；
2. `compact` 在本地 gpt-oss-20b 上复现了公共卫生/医保 conservative segment 的不稳定性；
3. 因此 LCDU 方法定义必须包含 prompt variant selector，并保留 rejected/unstable variant；
4. 该结果可关闭第一层 cross-provider direction gate，但仍不能关闭 strong baseline、scale stability、finer schema robustness 或理论证明。

## 17. Selected-variant Scale Stability

当前已经对 cross-provider selected variant 执行规模扩展矩阵：

1. source script：`experiments/lcdu_anes_llm_seed_scale_repeat_matrix.py`
2. scale gate script：`experiments/lcdu_anes_llm_scale_stability_matrix.py`
3. source matrix artifact：`experiments/results/lcdu_llm_seed_scale_repeat/lcdu-anes-llm-seed-scale-repeat-deepseek-v4-flash-scale8x12x16-deliberative-001.json`
4. scale stability artifact：`experiments/results/lcdu_llm_scale_stability/lcdu-anes-llm-scale-stability-matrix-deepseek-v4-flash-deliberative-8x12x16-current-001.json`
5. provider：DeepSeek OpenAI-compatible endpoint
6. model：`deepseek-v4-flash`
7. selected prompt variant：`deliberative`
8. segment scales：8, 12, 16
9. segment offsets：0
10. run count：3
11. total LLM calls：216
12. parse failure count：0

规模结果：

1. overall status：`scale_stability_signal_positive`
2. positive run count：3 / 3
3. max segment scale：16
4. 当前 ANES `party_or_ideology × income` schema 的 available segment count：16
5. 气候/能源：
   - accepted rate：1.0
   - test improved rate：1.0
   - scale=16 test loss：0.046377 -> 0.008789
6. 公共卫生/医保：
   - accepted rate：1.0
   - test improved rate：1.0
   - scale=16 test loss：0.031566 -> 0.008113

当前解释：

1. LCDU selected variant=`deliberative` 已从 top-2/top-4 segment 扩展到当前 ANES schema 下全 16 segment；
2. 这关闭了第一层 scale stability gate；
3. 但该证据仍是单 provider、单 ANES sample-slice、固定 `party_or_ideology × income` schema；
4. 它不能写成真实 full-population 或客户现场规模验证；
5. 下一步仍必须做 strong baseline matrix 与 finer schema robustness。

## 18. Strong Baseline Matrix

当前已经执行第一层 ANES strong baseline matrix，并补齐 required baseline family coverage：

1. strong baseline script：`experiments/lcdu_anes_strong_baseline_matrix.py`
2. baseline family script：`experiments/lcdu_anes_baseline_family_matrix.py`
3. LLM method-level source artifact：
   - `experiments/results/lcdu_llm_simulator_validation/lcdu-anes-llm-simulator-validation-deepseek-v4-flash-16seg-deliberative-current-001.json`
   - `experiments/results/lcdu_llm_simulator_validation/lcdu-anes-llm-simulator-validation-deepseek-v4-flash-16seg-standard-current-001.json`
4. deterministic anchor source artifact：`experiments/results/lcdu_cross_task_validation/lcdu-anes-cross-task-validation-current-001.json`
5. baseline family artifact：`experiments/results/lcdu_baseline_family/lcdu-anes-baseline-family-matrix-anes-current-001.json`
6. strong baseline artifact：`experiments/results/lcdu_strong_baseline/lcdu-anes-strong-baseline-matrix-anes-current-001.json`
7. status：`strong_baseline_lcdu_not_leading`

覆盖的 baseline families：

1. `llm_raw_prompt`
2. `llm_aggregate_anchor`
3. `deterministic_anchor_search`
4. `population_search`
5. `textgrad_or_prompt_optimizer`

尚未覆盖的 required families：无。

结果：

1. 气候/能源：
   - LCDU LLM test loss：0.008914242922780178
   - best covered baseline：`deterministic_anchor_search / calibration_segment_anchor`
   - best covered baseline test loss：0.008343247118118962
   - LCDU leads covered baselines：false
2. 公共卫生/医保：
   - LCDU LLM test loss：0.008629284025508175
   - best covered baseline：`deterministic_anchor_search / calibration_segment_anchor`
   - best covered baseline test loss：0.006094935382542338
   - LCDU leads covered baselines：false

当前解释：

1. LCDU LLM prompt 已经明显优于 LLM raw prompt、LLM aggregate anchor 与当前 prompt-optimizer baseline；
2. `population_search_alpha_1` 与 deterministic `calibration_segment_anchor` 收敛到同一数值边界，并且仍低于 LCDU LLM prompt；
3. 因此 strong baseline 的当前问题已经不是“缺 family”，而是完整第一层 family coverage 下仍存在 `anchor_fidelity_gap`；
4. 这不是流程失败，而是重要研究边界：LCDU 的贡献不能写成“强 baseline 胜出”，只能写成“把 segment anchor 机制稳定注入 LLM simulator，但当前 LLM realization 仍损失了一部分 anchor fidelity”；
5. Paper gate 因此保留 `run_strong_baseline_matrix`；
6. 下一步必须转向 anchor-fidelity repair / hybrid 模式，或在理论上说明 deterministic anchor 是 constraint-only upper bound，而 LLM simulator 的价值来自可解释叙事和反事实报告，不只来自最低 JSD。

## 19. Anchor-Fidelity Repair Diagnostic

当前已经执行 anchor-fidelity repair diagnostic：

1. script：`experiments/lcdu_anes_anchor_fidelity_repair.py`
2. hybrid artifact：`experiments/results/lcdu_anchor_fidelity_repair/lcdu-anes-anchor-fidelity-repair-hybrid-16seg-current-001.json`
3. LLM strict-copy 2-seg smoke artifact：`experiments/results/lcdu_anchor_fidelity_repair/lcdu-anes-anchor-fidelity-repair-deepseek-v4-flash-copy-2seg-current-001.json`
4. LLM strict-copy 16-seg artifact：`experiments/results/lcdu_anchor_fidelity_repair/lcdu-anes-anchor-fidelity-repair-deepseek-v4-flash-copy-16seg-current-001.json`
5. status：`llm_anchor_copy_repair_positive`
6. total LLM calls：32
7. parse failure count：0

结果：

1. 气候/能源：
   - current LCDU test loss：0.008914242922780178
   - deterministic anchor-copy test loss：0.008343247118118962
   - LLM strict-copy test loss：0.008343247118118954
   - mean anchor L1 deviation：1.2500937784931665e-13
2. 公共卫生/医保：
   - current LCDU test loss：0.008629284025508175
   - deterministic anchor-copy test loss：0.006094935382542338
   - LLM strict-copy test loss：0.006094935382542342
   - mean anchor L1 deviation：3.1250696475026984e-13

当前解释：

1. Anchor-fidelity gap 不是因为 DeepSeek v4-flash 无法输出精确 anchor JSON；
2. gap 来自原 LCDU prompt 的“soft constraint / 可调整”设计，它让 LLM 在数值分布上偏离 calibration anchor；
3. strict-copy 或 hybrid architecture 可以关闭当前 JSD gap；
4. 但这不是原 LCDU prompt 的胜利，而是提示论文主贡献需要重定义为“可审计的约束注入与 LLM 叙事分离框架”，或继续研究如何在不牺牲解释能力的情况下保留 anchor fidelity。

## 20. Hybrid Method Validation

当前已经执行 LCDU-hybrid method validation：

1. script：`experiments/lcdu_anes_hybrid_method_validation.py`
2. artifact：`experiments/results/lcdu_hybrid_method/lcdu-anes-hybrid-method-validation-current-001.json`
3. status：`hybrid_candidate_numeric_parity_soft_not_leading`
4. research decision：`reframe_as_hybrid_auditable_constraint_framework_not_accuracy_win`
5. product decision：`adopt_hybrid_for_auditable_product_reports`

结果：

1. 气候/能源：
   - soft LCDU test loss：0.008914242922780178
   - best deterministic baseline test loss：0.008343247118118962
   - hybrid strict-copy test loss：0.008343247118118954
   - interpretation：`hybrid_ties_best_numeric_baseline_but_does_not_beat_it`
2. 公共卫生/医保：
   - soft LCDU test loss：0.008629284025508175
   - best deterministic baseline test loss：0.006094935382542338
   - hybrid strict-copy test loss：0.006094935382542342
   - interpretation：`hybrid_ties_best_numeric_baseline_but_does_not_beat_it`

当前解释：

1. `LCDU-hybrid` 可以作为 Product 的可信方法路线，因为它保持 numeric parity 并保留 LLM 报告能力；
2. `LCDU-hybrid` 不能作为“比 deterministic anchor 更准”的论文主张；
3. 若作为 CCF-A 主贡献，必须把评价目标从单一 JSD superiority 扩展到 auditability、explanation faithfulness、counterfactual reporting 和 split-gated evidence composition。

## 21. Theoretical Identification Proof

当前已经生成 bounded theoretical identification proof：

1. script：`experiments/lcdu_theoretical_identification_proof.py`
2. artifact：`experiments/results/lcdu_theory/lcdu-theoretical-identification-proof-current-001.json`
3. status：`bounded_hybrid_identification_proof_ready`
4. closed gate：`theoretical_identification_proof_ready`
5. identification result：`hybrid_numeric_distribution_identified_with_segment_anchor`

该 proof 覆盖：

1. split isolation；
2. anchor-copy identification；
3. non-superiority boundary。

当前解释：

1. 理论门控从“formal objects mapped”推进到“bounded hybrid identification proof ready”；
2. 但 proof 仍不覆盖 finer schema、external validity、customer field validation 或 narrative utility；
3. paper gate 因此移除了 `formalize_theoretical_identification_proof`，但仍保留 `run_finer_schema_robustness_matrix` 与 `run_strong_baseline_matrix`。

## 22. Finer Schema Robustness Matrix

当前已经执行 finer schema robustness matrix：

1. script：`experiments/lcdu_anes_finer_schema_robustness_matrix.py`
2. artifact：`experiments/results/lcdu_finer_schema/lcdu-anes-finer-schema-robustness-current-001.json`
3. status：`finer_schema_robustness_signal_positive`
4. schema count：4
5. positive schema count：4
6. max axis count：4

覆盖的 schema：

1. `party_or_ideology + income`
2. `party_or_ideology + income + age`
3. `party_or_ideology + income + education`
4. `party_or_ideology + income + age + education`

关键结果：

1. 2-axis schema：
   - climate segment count：16，test loss：0.06532217743555663 -> 0.008343247118118962
   - health segment count：16，test loss：0.04434039490706278 -> 0.006094935382542338
2. 3-axis age schema：
   - climate segment count：58，test loss：0.08099375979142331 -> 0.025233481357207873
   - health segment count：57，test loss：0.06332649600105623 -> 0.022927051701635354
3. 3-axis education schema：
   - climate segment count：61，test loss：0.08602823999190891 -> 0.03334281048599279
   - health segment count：62，test loss：0.06371247859616144 -> 0.025833643667061895
4. 4-axis schema：
   - climate segment count：140，test loss：0.11850674510216083 -> 0.06799475059120803
   - health segment count：143，test loss：0.09766842328023506 -> 0.06572667209494434

当前解释：

1. Calibration-derived segment anchor 在更细 schema 下仍正向；
2. 细分越多，segment sparsity 增加，candidate loss 也升高，但仍显著优于 aggregate prior；
3. 该结果关闭 `run_finer_schema_robustness_matrix`；
4. 但它仍不覆盖 ANES 当前 slice 中缺失的 task-card axes：climate 的 region/urbanicity，以及 public health 的 health-insurance context。

## 23. Current Decision Boundary

截至当前 paper gate：

1. 已关闭：
   - theoretical identification proof；
   - public task ingestion；
   - microdata sample slice；
   - cross-task anchor validation；
   - LLM simulator validation；
   - seed/scale/repeat diagnosis；
   - cross-provider selected variant；
   - scale stability；
   - finer schema robustness；
   - anchor-fidelity repair；
   - hybrid method validation。
2. 未关闭：
   - `run_strong_baseline_matrix`

当前判断：

1. `LCDU-soft` 不能升级为 CCF-A 主贡献算法，因为完整第一层 strong baseline 下不领先；
2. `LCDU-hybrid` 有 Product 核心方法价值，因为它达到 deterministic numeric parity，并保留 LLM explanation/reporting layer；
3. `LCDU-hybrid` 若要作为论文主贡献，必须重写贡献目标：不是 accuracy-superior optimizer，而是 auditable constraint-identification framework；
4. 下一步如果继续 Research，应新增 auditability / explanation faithfulness / counterfactual reporting 指标，而不是继续追求 soft prompt 击败 deterministic anchor。

当前已经生成 research decision index：

1. script：`experiments/lcdu_research_decision_index.py`
2. artifact：`experiments/results/lcdu_research_decision/lcdu-research-decision-index-current-001.json`
3. status：`decision_boundary_reached_hybrid_conditional`
4. soft decision：`reject_as_ccf_a_main_contribution_accuracy_optimizer`
5. hybrid decision：`conditionally_promising_as_auditable_constraint_framework`
6. CCF-A gate：`not_passed_under_accuracy_superiority_criterion`

这意味着当前已经可以给出研究方向判断：

1. 原 `LCDU-soft` 路线应止损，不再作为主贡献推进；
2. `LCDU-hybrid` 路线值得保留并并入 Product 核心能力；
3. 若继续追求 CCF-A，必须围绕新的贡献目标设计指标，而不是继续在 soft prompt 上追求 JSD 胜出。
