# LCDU CCF-A Research Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 LCDU L3 从“一个有效方法实例”推进为“有理论定义、跨任务验证、强 baseline 对比、可解释失败边界的通用算法框架”。

**Architecture:** Research 线以 `LCDU` 为主方法，围绕理论形式化、跨任务数据、强 baseline、稳定性验证、失败边界解释五条证据链推进。每个实验必须保留 calibration split 产生候选、held-out/test split 接受候选的 contract，并输出可进入 Product 报告的 strict JSON artifact。

**Tech Stack:** Python, pytest, strict JSON artifacts, local/OpenAI-compatible LLM providers, policy-reaction benchmark pipeline, Product policy workflow report.

---

## 1. 论文级目标

目标不是证明 `LCDU L3` 在一个数据集上有效，而是证明：

> LLM 驱动的人群模拟校准不应被建模为自由文本 prompt tuning，而应被建模为带有语义因素、数值约束、segment guard 和 held-out acceptance gate 的 Latent-Constraint Distribution Update 问题。

如果研究成功，论文主张应包括：

1. `Problem`: 定义 LLM population simulator 的 distribution alignment 问题。
2. `Method`: 提出 LCDU，一种语义因素和约束程序同步更新的自动化校准框架。
3. `Evidence`: 在多政策任务、多模型、多 seed/scale 上优于 TextGrad、S2PC、DSPy、遗传/贝叶斯/随机搜索等 baseline。
4. `Boundary`: 明确说明哪些 segment/axis 不能被当前 LCDU 修复，并给出可解释失败边界。
5. `Transfer`: 将 accepted method summary 输出为 Product 可审计 artifact，而不是只给论文表格。

## 2. 核心研究问题

### RQ1: LCDU 是否比自由文本 prompt update 更稳定？

比较对象：

1. 原始 prompt/persona；
2. TextGrad；
3. LLM-as-optimizer 自然语言更新；
4. 手工 residual prompt patch；
5. LCDU prompt-only / anchor-only / prompt-anchor synchronized。

验收标准：

1. LCDU 在 held-out loss 上显著优于 raw prompt 和 TextGrad；
2. 至少 3 个 seed 或 repeat 下 `stable_improvement`；
3. candidate accepted/rejected 显式记录；
4. 不允许只报告 best run。

### RQ2: LCDU 的收益来自什么机制？

需要证明的机制：

1. 语义因素定位 residual axis；
2. 数值 anchor 限制输出分布；
3. segment guard 避免全局 patch 破坏其它 segment；
4. prompt-anchor synchronization 比单边 patch 更稳。

验收标准：

1. prompt-only、anchor-only、guard-only、synchronized 四组 ablation 完整；
2. synchronized 版本至少在稳定性或 worst-segment loss 上优于单边版本；
3. 如果某组失败，必须记录为 negative evidence，而不是删除。

### RQ3: LCDU 是否跨政策任务成立？

候选任务池：

1. 生活成本/食品援助政策反应：当前 HPS/HTOPS 主任务；
2. 公共卫生政策反应：疫苗、医保、公共健康干预，先做公开数据可用性审计；
3. 气候/能源政策反应：能源补贴、碳税、极端天气适应，先做公开数据可用性审计；
4. 福利/税收/住房政策反应：现金补贴、税收抵免、租金援助，先做公开数据可用性审计。

验收标准：

1. 至少 2 个额外 public-data task 完成 ingestion；
2. 每个 task 有 calibration/held-out/test 三层 split；
3. LCDU 至少在 2 个任务上优于强 baseline；
4. 若只能在当前任务有效，论文必须降级为 domain-specific 方法，不能主张通用框架。

### RQ4: LCDU 是否跨模型成立？

模型层级：

1. 本地 `openai/gpt-oss-20b`：主开发模型；
2. DeepSeek v4-flash：低成本 provider 验证；
3. DeepSeek v4-pro：关键矩阵复核；
4. 其它免费/低成本 OpenRouter 模型：只作为补充，不能作为主贡献证据。

验收标准：

1. 至少 2 个 provider 上同向改善；
2. 如果强模型只改善候选生成、不改善 runtime simulation，需要拆开 reporting；
3. provider key、base_url、model id、temperature、token budget 必须写入 artifact；
4. 不允许 Codex/Claude 作为实验 simulator 或 optimizer 进入主证据链，除非后续有正式 API 和可复现实验协议。

### RQ5: LCDU 的失败边界能否被解释？

当前已知失败点：

1. `low_income_food_insecure` residual weakness；
2. `price_stress_level=high` axis weakness；
3. 强修复容易破坏已接受主结构；
4. 非 LCDU route-combo 尚未超过 LCDU L3。

验收标准：

1. 每个 failed route 都有 matrix artifact；
2. 每个 residual weakness 都有 segment/axis attribution；
3. stop-loss 规则写入方法部分；
4. failure boundary 能支持论文讨论，而不是只作为附录日志。

## 3. 方法框架定义

LCDU 应形式化为：

1. `Simulator`: 给定 persona、policy、scenario、prompt program，输出政策选择分布。
2. `Target Distribution`: 来自 public survey 或 public-use microdata 的 segment-level 分布。
3. `Residual`: simulator distribution 与 target distribution 的 weighted JSD、rank error、worst-axis error。
4. `Latent Factor`: 从 residual axis 中抽取的可解释因素，例如 price stress、institutional trust、benefit salience。
5. `Constraint Program`: 对输出分布施加的 soft guard，例如 max/min probability、rank preservation、segment-specific bound。
6. `Update Candidate`: 由 semantic factor、numeric anchor、segment guard、response contract 组成。
7. `Acceptance Gate`: calibration split 生成候选，held-out/test split 决定接受，报告 accepted/rejected。

计划中的最终算法名可以保留为：

`LCDU: Latent-Constraint Distribution Update for LLM Population Simulation`

## 4. 总体阶段

### Phase 0: 固化当前主方法资产

目标：把 LCDU L3 当前证据固化成后续论文和 Product 都能引用的主线。

任务：

- [ ] 确认 `policy-reaction-lcdu-l3-method-summary-current-001.json` 包含 accepted candidates、route coverage、residual weakness、risk flags、claim boundaries。
- [ ] 在 `paper/LCDU_L3_METHOD_DRAFT.md` 中补齐 formal notation 草稿。
- [ ] 在 `paper/RESULTS.md` 中给 LCDU L3、route-combo、negative routes 建立索引表。
- [ ] 在 Product workflow report 中确认 method summary 能被报告引用。

验收标准：

1. Research 全量测试通过；
2. Product workflow report 能消费 method summary；
3. 当前 evidence boundary 不宣称 field validation；
4. 所有 artifact id 可追溯。

### Phase 1: 理论定义与论文主张

目标：把 LCDU 从工程策略提升为可论文审稿的算法定义。

任务：

- [ ] 写 `paper/LCDU_THEORY.md`，定义 simulator、target distribution、residual、update candidate、acceptance gate。
- [ ] 写 `paper/LCDU_ALGORITHM.md`，给出算法伪代码。
- [ ] 写 `paper/LCDU_CLAIM_BOUNDARY.md`，定义哪些结论可以写、哪些不能写。
- [ ] 为 theory 文档增加 artifact schema contract，保证每个理论对象都能对应到实验 JSON 字段。

验收标准：

1. 理论对象与现有 artifact 字段一一对应；
2. 能解释为什么 LCDU 不是普通 prompt tuning；
3. 能解释为什么 split-gated acceptance 是必要组件；
4. 能解释失败边界为什么是方法的一部分。

### Phase 2: 数据与任务扩展

目标：让 LCDU 不再只依赖当前 HPS/HTOPS 任务。

任务：

- [ ] 做公开数据可用性审计，列出每个候选政策任务的数据源、字段、样本量、segment 可构造性、license。
- [ ] 选择 2 个额外任务进入 ingestion。
- [ ] 为每个任务建立 `calibration/heldout/test` split。
- [ ] 输出每个任务的 `task_card.json`，记录政策选项、segment schema、target distribution、claim boundary。

验收标准：

1. 至少 2 个新任务通过 ingestion smoke；
2. 每个任务都能产出 target distribution；
3. 每个任务都有 no-leakage split contract；
4. 数据不足的任务必须明确 rejected，不强行纳入。

### Phase 3: 强 baseline 矩阵

目标：让 LCDU 面对足够强的替代方案，而不是只和 TextGrad 比。

baseline 组：

1. `Raw Prompt`: 不校准；
2. `TextGrad`: 当前已有负结果和补充验证；
3. `DSPy`: prompt optimizer/program optimizer；
4. `Random/LHS Search`: 参数空间随机或 Latin Hypercube 搜索；
5. `Bayesian/TPE Search`: Optuna/TPE 或等价轻量实现；
6. `Genetic/CEM Search`: 遗传算法或 cross-entropy method；
7. `LLM-as-Optimizer`: DeepSeek 生成候选，held-out gate 接受；
8. `S2PC`: 结构化参数搜索历史路线；
9. `Retrieval-only`: 只使用语义检索，不做约束；
10. `Constraint-only`: 只做数值约束，不做语义因素。

验收标准：

1. 每个 baseline 都有统一 candidate schema；
2. 每个 baseline 都使用同一 split contract；
3. 每个 baseline 至少跑 current task 的 seed/scale/repeat；
4. 进入论文主表的 baseline 必须有足够预算和失败记录。

### Phase 4: LCDU 通用化实现

目标：把 LCDU L3 抽象成可配置算法，而不是 hard-coded 当前 segment。

任务：

- [ ] 定义 `LCDUFactorExtractor`：从 residual matrix 抽取 weak axis / weak segment / semantic factors。
- [ ] 定义 `LCDUConstraintBuilder`：从 factor 生成 soft constraint program。
- [ ] 定义 `LCDUCandidateGenerator`：同步生成 segment prompt、calibration anchor、response contract。
- [ ] 定义 `LCDUAcceptanceGate`：统一 calibration -> held-out -> test 的接受规则。
- [ ] 定义 `LCDUFailureAttributor`：为失败候选输出 residual axis、bias signature、stop-loss reason。

验收标准：

1. 当前 LCDU L3 h02/i01 能由通用 pipeline 重建；
2. 新任务不需要写 hard-coded segment logic；
3. 每个 candidate 都能导出 Product 可读 method summary；
4. 每个 rejected candidate 都能解释失败原因。

### Phase 5: 多任务、多模型、多规模验证

目标：形成 CCF-A 级别的主实验表。

实验矩阵：

1. task: current HPS/HTOPS + 2 个新增 public policy tasks；
2. model: gpt-oss-20b + deepseek-v4-flash + deepseek-v4-pro；
3. scale: 12x3、16x3、50x3，视成本增加 100x3；
4. seed: 至少 3 个；
5. method: LCDU + strong baselines；
6. split: calibration、heldout、test。

指标：

1. weighted JSD；
2. segment rank correlation；
3. worst-segment loss；
4. axis-level loss；
5. accepted/rejected count；
6. stability improvement rate；
7. token/cost/latency；
8. failure attribution coverage。

验收标准：

1. LCDU 在主任务和至少 1 个新增任务上显著优于强 baseline；
2. 至少 2 个模型同向；
3. worst-segment loss 不因平均 loss 改善而恶化；
4. test split 不能明显回退；
5. 失败任务能解释边界并降级论文主张。

### Phase 6: 论文打包与 Product transfer

目标：让 Research 结果同时满足论文和 Product 技术壁垒叙事。

任务：

- [ ] 写 `paper/METHOD.md`，正式描述 LCDU。
- [ ] 写 `paper/EXPERIMENTS.md`，组织 main table、ablation、cross-task、cross-model、failure analysis。
- [ ] 写 `paper/PRODUCT_TRANSFER.md`，说明 artifact 如何进入 Product 报告，但不宣称 field validation。
- [ ] 输出 `experiments/results/lcdu_paper_gate/*.json`，作为论文主证据索引。
- [ ] 输出 Product-facing method card，供 demo/report/客户材料引用。

验收标准：

1. 论文主 claim 与 artifact 一致；
2. 所有表格能由 artifact 重建；
3. Product claim boundary 不越界；
4. negative result 被保留；
5. CCF-A gap 清单中只剩“真实客户 field validation”一类非论文必须项。

## 5. 停损标准

LCDU 不是无条件继续推进。触发以下任一条件，应降级或转向：

1. 新增两个政策任务均无法复现 LCDU 优势；
2. 强 baseline 中至少两个方法稳定超过 LCDU；
3. LCDU 只在单一模型有效，跨模型明显失效；
4. LCDU 平均 loss 改善但 worst-segment loss 系统性恶化；
5. 失败边界无法被解释，只能靠手动调参。

触发停损后，论文主张改为：

> LCDU is a domain-specific calibration diagnostic and bounded transfer mechanism, not a general LLM population simulation calibration algorithm.

## 6. 用户需要提供的帮助

优先级从高到低：

1. 选择新增政策任务方向：公共卫生、气候能源、福利住房、税收补贴中至少选 2 个。
2. 确认可接受的 API 预算：DeepSeek v4-flash 用于大矩阵，v4-pro 用于关键复核。
3. 确认目标论文场景：偏 AI/WWW/KDD 方法论文，还是计算社会科学/政策模拟论文。
4. 如果后续有真实客户或机构数据，只能作为独立 Product/field validation 线进入，不能污染 public-data paper split。

## 7. 下一轮执行建议

下一轮不要直接扩大运行，而是先做四个并行任务：

1. `Theory Track`: 写 LCDU formal definition 和 algorithm draft。
2. `Data Track`: 做 4 个候选政策任务的数据可用性审计。
3. `Baseline Track`: 先实现 DSPy、TPE、GA/CEM 的统一 baseline spec。
4. `Evidence Track`: 建立 paper gate index，把 method summary、route coverage、negative result 串成论文证据账本。

这四条完成后，才能进入大规模实验矩阵。否则会出现“算力花了，但论文主张仍然不清楚”的问题。

## 8. 第一轮执行记录

执行日期：2026-05-23

已完成：

1. `Theory Track`
   - 新增 `paper/LCDU_THEORY.md`
   - 新增 `paper/LCDU_ALGORITHM.md`
   - 新增 `paper/LCDU_CLAIM_BOUNDARY.md`
   - 明确 formal objects、acceptance gate、artifact schema contract、降级规则。

2. `Data Track`
   - 新增 `paper/LCDU_PUBLIC_DATA_AUDIT.md`
   - 核验并记录 HPS/HTOPS、GSS、ANES、CES 作为 public-data 候选来源。
   - 第一批推荐新增任务为公共卫生/医保政策态度与气候/能源政策态度。

3. `Baseline Track`
   - 新增 `paper/LCDU_BASELINE_SPEC.md`
   - 统一 Raw Prompt、TextGrad、DSPy、Random/LHS、TPE、GA/CEM、LLM-as-Optimizer、S2PC、Retrieval-only、Constraint-only 的候选 schema、split contract 和接受标准。

4. `Evidence Track`
   - 新增 `experiments/lcdu_paper_gate_index.py`
   - 新增 `tests/test_lcdu_paper_gate_index.py`
   - 生成 `experiments/results/lcdu_paper_gate/lcdu-paper-gate-index-current-001.json`
   - 当前 paper gate 状态仍为 `open`，blocking gaps 为：
     - `ccf_a_external_validity_missing`
     - `cross_provider_generalization_missing`
     - `full_population_scale_validation_missing`
     - `finer_schema_robustness_open`
     - `theoretical_identification_needs_formalization`

下一轮应从两个方向继续：

1. 把 `LCDU_THEORY.md` 中的 formal objects 变成可测试 schema contract；
2. 为 `LCDU_PUBLIC_DATA_AUDIT.md` 推荐的前两个任务生成 `lcdu-public-task-card-v1`，并开始 ingestion smoke。

## 9. 第二轮执行记录

执行日期：2026-05-23

已完成：

1. Theory contract
   - 新增 `experiments/lcdu_theory_contract.py`
   - 新增 `tests/test_lcdu_theory_contract.py`
   - 生成 `experiments/results/lcdu_theory/lcdu-theory-contract-current-001.json`
   - 将 `LCDU_THEORY.md` 中的 8 个 formal objects 映射到 artifact fields。

2. Public task cards
   - 新增 `experiments/lcdu_public_task_cards.py`
   - 新增 `tests/test_lcdu_public_task_cards.py`
   - 生成：
     - `experiments/results/lcdu_public_task_cards/public-health-medical-insurance-attitude-v1.json`
     - `experiments/results/lcdu_public_task_cards/climate-energy-regulation-attitude-v1.json`
     - `experiments/results/lcdu_public_task_cards/lcdu-public-task-card-index-current-001.json`
   - 两个 task card 当前状态均为 `task_card_smoke_passed`，不是 microdata ingestion completed。

3. Paper gate index
   - 更新 `experiments/lcdu_paper_gate_index.py`
   - 重新生成 `experiments/results/lcdu_paper_gate/lcdu-paper-gate-index-current-001.json`
   - `completed_subgates` 已包含：
     - `complete_lcdu_theory_contract`
     - `public_task_cards_ready`
   - CCF-A gate 仍然为 `open`，因为跨任务真实 ingestion、跨模型验证、规模验证、finer-schema robustness、理论识别证明都还未完成。

下一轮应继续：

1. 为两个 public task cards 绑定 exact microdata variables；
2. 实现 `lcdu-public-task-ingestion-smoke-v1`，从真实 public-use 文件或样本切片生成 target distribution skeleton；
3. 同步准备 strong baseline matrix 的候选生成接口。

## 10. 第三轮执行记录

执行日期：2026-05-23

已完成：

1. Exact variable binding
   - 公共卫生/医保任务绑定 ANES 2024 `V241245`。
   - 气候/能源任务绑定 ANES 2024 `V241258`。
   - 气候任务的主数据源从 CES 占位项调整为 ANES exact codebook page；CES 保留为 supporting source。

2. Ingestion smoke
   - 新增 `experiments/lcdu_public_task_ingestion_smoke.py`
   - 新增 `tests/test_lcdu_public_task_ingestion_smoke.py`
   - 生成：
     - `experiments/results/lcdu_public_task_ingestion_smoke/public-health-medical-insurance-attitude-v1-smoke.json`
     - `experiments/results/lcdu_public_task_ingestion_smoke/climate-energy-regulation-attitude-v1-smoke.json`
     - `experiments/results/lcdu_public_task_ingestion_smoke/lcdu-public-task-ingestion-smoke-index-current-001.json`
   - 当前 smoke 只 materialize official codebook aggregate frequency target skeleton，不等价于 public-use microdata ingestion。

3. Paper gate index
   - 更新 `experiments/lcdu_paper_gate_index.py`
   - `completed_subgates` 新增 `public_task_ingestion_smoke_ready`
   - 下一 gate 从 task-card 层推进到 `load_public_use_microdata_or_verified_sample_slice`。

4. Source correction
   - `V241258` 官方 codebook 的 `99` 频数为 681；气候任务 target skeleton 按 substantive codes 1-7 的 4577 个样本计算。
   - 因此 `mixed_or_status_quo` 为 738 / 4577 = 0.161240987546，`oppose_more_regulation_or_spending` 为 1169 / 4577 = 0.255407472143。

当前仍未完成：

1. 下载或加载 ANES public-use microdata / verified sample slice；
2. 生成 segment-level target distribution；
3. 为两个新增任务建立 calibration/heldout/test split；
4. 运行 LCDU 与强 baseline 的 cross-task validation。

下一轮应继续：

1. 接入 ANES public-use microdata 或构建可复核 sample slice；
2. 将 aggregate target skeleton 扩展为 segment-level target distribution；
3. 为新增任务生成 LCDU cross-task benchmark harness；
4. 同步推进 strong baseline matrix 的统一候选接口。

## 11. 第四轮执行记录

执行日期：2026-05-30

已完成：

1. ANES SDA subset fetch
   - 新增 `experiments/lcdu_anes_sda_subset_fetch.py`
   - 已实测可从 `https://sda.berkeley.edu/sdaweb/analysis/?dataset=anes2024full` 下载 5521 行、10 个变量的 SDA custom subset。
   - 本地 raw file 为 `data/raw/anes_2024/anes2024_sda_lcdu_subset.csv`，该路径受 `.gitignore` 保护，不进入 git。

2. Public-use sample-slice ingestion
   - 新增 `experiments/lcdu_anes_public_microdata_ingestion.py`
   - 新增 `tests/test_lcdu_anes_public_microdata_ingestion.py`
   - 新增 fixture：`benchmarks/fixtures/anes2024_sda_lcdu_subset_smoke.csv`
   - 生成 `experiments/results/lcdu_public_task_microdata/lcdu-anes-2024-sda-public-microdata-001.json`

3. Segment-level target distribution
   - `V241245` valid substantive N = 4778，与 codebook smoke 对齐。
   - `V241258` valid substantive N = 4577，与 codebook smoke 对齐。
   - 已生成 `party_or_ideology × income` segment target distributions。
   - 已生成 `calibration/heldout/test` split：
     - calibration row count: 3328
     - heldout row count: 1108
     - test row count: 1085

4. Paper gate index
   - 更新 `experiments/lcdu_paper_gate_index.py`
   - `completed_subgates` 新增 `public_task_microdata_sample_slice_ready`
   - `required_next_gates` 不再包含 `load_public_use_microdata_or_verified_sample_slice`
   - CCF-A gate 仍然为 `open`。

当前仍未完成：

1. ANES segment schema 仍为 partial coverage：
   - 公共卫生/医保缺 `health_insurance_context`
   - 气候/能源缺 `region` 与 `urbanicity`
2. 尚未把 ANES 两个新增任务接入 LCDU simulator benchmark；
3. 尚未运行 LCDU vs strong baseline 的 cross-task validation；
4. 尚未运行 DeepSeek / 本地模型的 cross-provider validation；
5. 尚未完成更正式的理论识别证明。

下一轮应继续：

1. 定义 ANES task benchmark harness：把 segment target distribution 转成 simulator 可消费的 policy reaction benchmark。
2. 在两个 ANES task 上先跑 raw prompt / LCDU-lite / constraint-only 的最小 cross-task smoke。
3. 若 smoke 有正信号，再进入 strong baseline matrix；若无正信号，先定位是任务映射、segment schema 还是 LCDU 机制失效。

## 12. 第五轮执行记录

执行日期：2026-05-30

已完成：

1. ANES cross-task anchor validation
   - 新增 `experiments/lcdu_anes_cross_task_validation.py`
   - 新增 `tests/test_lcdu_anes_cross_task_validation.py`
   - 生成 `experiments/results/lcdu_cross_task_validation/lcdu-anes-cross-task-validation-current-001.json`
   - validation type 为 `split_gated_segment_anchor_transfer_smoke`

2. Split-gated candidate flow
   - calibration split 生成候选：
     - `uniform_prior`
     - `calibration_aggregate_prior`
     - `calibration_segment_anchor`
     - `lcdu_smoothed_segment_anchor_alpha_*`
   - heldout split 决定 acceptance；
   - test split 只做 final claim check；
   - artifact 显式报告 initial/best/final loss 与 accepted method。

3. 真实 ANES 结果
   - 公共卫生/医保任务 accepted method: `calibration_segment_anchor`
     - heldout initial loss: 0.04457889833805818
     - heldout final loss: 0.005397143516893713
     - test initial loss: 0.04434039490706278
     - test final loss: 0.006094935382542338
   - 气候/能源任务 accepted method: `calibration_segment_anchor`
     - heldout initial loss: 0.05061340525537323
     - heldout final loss: 0.006892295320535387
     - test initial loss: 0.06532217743555663
     - test final loss: 0.008343247118118962

4. Paper gate index
   - 更新 `experiments/lcdu_paper_gate_index.py`
   - `completed_subgates` 新增 `cross_task_anchor_validation_ready`
   - `required_next_gates` 不再包含 `run_cross_task_public_data_validation`
   - 下一步变为 `run_cross_task_llm_simulator_validation`

当前解释边界：

1. 这是 LCDU 的 anchor/constraint transfer 正信号，不是 LLM simulator 正信号；
2. 它支持继续推进 LCDU，而不是直接证明 LCDU 已具备 CCF-A 主贡献；
3. 如果后续 LLM simulator validation 无法复现该方向，论文主张仍需要降级。

下一轮应继续：

1. 把 ANES task target distribution 转成 LLM simulator prompt/response contract；
2. 跑 raw prompt、aggregate-anchor、segment-anchor、LCDU-smoothed-anchor 的小规模 LLM simulator validation；
3. 使用本地模型先跑，随后用 DeepSeek v4-flash/pro 做关键复核；
4. 将 LLM 结果与 anchor-only 结果分开报告，判断瓶颈在 simulator 还是 calibration 方法。

## 13. 第六轮执行记录

执行日期：2026-05-30

已完成：

1. ANES LLM simulator validation harness
   - 新增 `experiments/lcdu_anes_llm_simulator_validation.py`
   - 新增 `tests/test_lcdu_anes_llm_simulator_validation.py`
   - validation type 为 `split_gated_llm_segment_simulator_smoke`
   - 显式记录 provider、model、base_url、selected segments、prompt/response hash、parse success、token accounting、initial/best/final loss。

2. 本地 provider 探测
   - `http://127.0.0.1:1234/v1/models` 当前 connection refused；
   - 因此本轮没有生成本地 LM Studio 模型证据。

3. DeepSeek v4-flash 最小真实 run
   - artifact：`experiments/results/lcdu_llm_simulator_validation/lcdu-anes-llm-simulator-validation-deepseek-v4-flash-1seg-current-001.json`
   - task_count: 2
   - total_call_count: 6
   - status: `cross_task_llm_signal_positive`
   - parse_failure_count: 0

4. DeepSeek v4-flash 2-segment 主 smoke
   - artifact：`experiments/results/lcdu_llm_simulator_validation/lcdu-anes-llm-simulator-validation-deepseek-v4-flash-2seg-current-001.json`
   - task_count: 2
   - total_call_count: 12
   - parse_failure_count: 0
   - status: `cross_task_llm_signal_positive`
   - 公共卫生/医保：
     - accepted method: `lcdu_segment_anchor_prompt`
     - heldout loss: 0.012487921594210112 -> 0.0031735148745522168
     - test loss: 0.022035673895836442 -> 0.00907997791800591
   - 气候/能源：
     - accepted method: `lcdu_segment_anchor_prompt`
     - heldout loss: 0.02425280708371007 -> 0.005099641773424251
     - test loss: 0.027324620607139388 -> 0.006253621712622866

5. Paper gate index
   - 更新 `experiments/lcdu_paper_gate_index.py`
   - `completed_subgates` 新增 `cross_task_llm_simulator_validation_ready`
   - `required_next_gates` 不再包含 `run_cross_task_llm_simulator_validation`
   - 下一步为 `run_cross_task_llm_seed_scale_repeat_validation`

当前解释边界：

1. LLM simulator smoke 显示 LCDU segment anchor prompt 可以被真实 provider 消费，并在两个 ANES tasks 上优于 raw prompt；
2. 这支持继续投入 seed/scale/repeat 与 strong baseline matrix；
3. 它仍不是 CCF-A 主贡献证据，因为规模小、provider 单一、segment schema 部分缺失、baseline 不够强。

下一轮应继续：

1. 扩大到 `max_segments_per_task=4` 或更多；
2. 增加 seed/repeat：改变 segment selection / prompt paraphrase / provider sampling seed；
3. 加入 strong baseline：aggregate anchor、segment anchor、LCDU smoothed anchor、LLM self-estimate、constraint-only；
4. 用 DeepSeek v4-pro 复核关键结果，若本地 LM Studio 恢复则同步跑本地模型。

## 14. 第七轮执行记录

执行日期：2026-05-30

已完成：

1. LLM simulator repeat 参数化
   - 更新 `experiments/lcdu_anes_llm_simulator_validation.py`
   - 新增 `segment_offset`，用于改变 selected segment 起点；
   - 新增 `prompt_variant`，支持 `standard`、`compact`、`deliberative`；
   - call record 记录 prompt variant 和 prompt hash。

2. Seed/scale/repeat matrix
   - 新增 `experiments/lcdu_anes_llm_seed_scale_repeat_matrix.py`
   - 新增 `tests/test_lcdu_anes_llm_seed_scale_repeat_matrix.py`
   - artifact：`experiments/results/lcdu_llm_seed_scale_repeat/lcdu-anes-llm-seed-scale-repeat-deepseek-v4-flash-s2s4-o0o1-standard-001.json`

3. DeepSeek v4-flash 真实矩阵
   - segment scales: 2, 4
   - segment offsets: 0, 1
   - prompt variants: `standard`
   - run count: 4
   - total LLM calls: 72
   - parse failure count: 0
   - status: `seed_scale_repeat_signal_mixed`
   - positive run count: 3 / 4

4. 任务级稳定性
   - 气候/能源：
     - accepted rate: 1.0
     - test improved rate: 1.0
   - 公共卫生/医保：
     - accepted rate: 0.75
     - test improved rate: 0.75

5. 已定位的失败点
   - run: scale=2, offset=1, standard
   - task: 公共卫生/医保
   - selected segments:
     - `party_or_ideology=conservative|income=upper`
     - `party_or_ideology=conservative|income=middle`
   - accepted: false
   - heldout raw/final loss: 0.0037091448532385113 -> 0.0037091448532385113
   - test raw/final loss: 0.009770047302380963 -> 0.009770047302380963

6. Paper gate index
   - 更新 `experiments/lcdu_paper_gate_index.py`
   - `completed_subgates` 新增：
     - `cross_task_llm_seed_scale_repeat_matrix_ready`
     - `cross_task_llm_seed_scale_repeat_signal_not_positive`
   - 下一 gate 为 `diagnose_cross_task_llm_seed_scale_repeat_instability`

当前解释边界：

1. LCDU 在 ANES 气候/能源任务上已出现 seed/scale repeat 稳定正信号；
2. LCDU 在 ANES 公共卫生/医保任务上不是全稳，conservative upper/middle segment 出现 no-acceptance；
3. 这说明 LCDU 尚不能被判断为 CCF-A 级通用算法框架；
4. 当前最有价值的问题已经从“有没有跨任务信号”转为“为什么医保 conservative segment 无法被 LCDU segment anchor 改善”。

下一轮应继续：

1. 对失败 run 做 residual attribution：比较 raw、aggregate anchor、segment anchor 的响应分布与目标分布；
2. 增加 `compact`/`deliberative` prompt variant 验证失败是否由 prompt wording 触发；
3. 对公共卫生/医保 conservative segment 尝试 constraint-only / smoothed-anchor / ideology-specific guard；
4. 若失败稳定存在，应把它写入 failure boundary，而不是继续调参包装成全正。

## 15. 第八轮执行记录

执行日期：2026-05-30

已完成：

1. Instability diagnosis artifact
   - 新增 `experiments/lcdu_anes_llm_instability_diagnosis.py`
   - 新增 `tests/test_lcdu_anes_llm_instability_diagnosis.py`
   - artifact：`experiments/results/lcdu_llm_instability_diagnosis/lcdu-anes-llm-instability-diagnosis-deepseek-v4-flash-prompt-variants-current-001.json`
   - status：`instability_recovered_by_prompt_variant`
   - failure count：1
   - recovered failure count：1
   - persistent failure count：0
   - total LLM calls：24
   - parse failure count：0

2. 已诊断的失败 case
   - source run：`scale2-offset1-standard`
   - task：公共卫生/医保
   - selected segments：
     - `party_or_ideology=conservative|income=upper`
     - `party_or_ideology=conservative|income=middle`
   - original heldout raw/final loss：0.0037091448532385113 -> 0.0037091448532385113
   - original test raw/final loss：0.009770047302380963 -> 0.009770047302380963
   - failure type：`candidate_rejected_and_test_not_improved`

3. Prompt variant recovery
   - `compact` 恢复失败 case：
     - accepted method：`lcdu_segment_anchor_prompt`
     - heldout loss：0.015178675354336436 -> 0.010071105701142835
     - test loss：0.022127444878231053 -> 0.008182949068345598
   - `deliberative` 也恢复失败 case：
     - accepted method：`lcdu_segment_anchor_prompt`
     - test loss：0.011365115141783556 -> 0.0019129589058892909

4. Prompt-variant seed/scale/repeat matrix
   - artifact：`experiments/results/lcdu_llm_seed_scale_repeat/lcdu-anes-llm-seed-scale-repeat-deepseek-v4-flash-s2s4-o0o1-promptvariants-001.json`
   - prompt variants：`compact`, `deliberative`
   - segment scales：2, 4
   - segment offsets：0, 1
   - run count：8
   - positive run count：8
   - total LLM calls：144
   - parse failure count：0
   - 两个 ANES task 的 accepted rate 与 test improved rate 均为 1.0

5. Paper gate index
   - 更新 `experiments/lcdu_paper_gate_index.py`
   - 新增可选 artifact：`llm_instability_diagnosis`
   - 新增可选 artifact：`llm_prompt_variant_repeat_matrix`
   - `completed_subgates` 新增：
     - `cross_task_llm_instability_diagnosis_ready`
     - `cross_task_llm_instability_recovered_by_prompt_variant`
     - `cross_task_llm_prompt_variant_seed_scale_repeat_matrix_ready`
     - `cross_task_llm_prompt_variant_seed_scale_repeat_signal_positive`
   - 当前 `required_next_gates`：
     - `formalize_theoretical_identification_proof`
     - `run_cross_provider_stability_matrix`
     - `run_scale_stability_matrix`
     - `run_finer_schema_robustness_matrix`
     - `run_strong_baseline_matrix`

当前解释边界：

1. 当前 mixed signal 已被定位为 prompt-variant sensitivity，而不是 LCDU segment anchor 必然失效；
2. 将 prompt variant 作为显式方法轴后，DeepSeek v4-flash 上的 ANES seed/scale/repeat 变为稳定正向；
3. 这提升了 LCDU 的论文潜力，因为失败定位、恢复候选和 repeat 验证都已 artifact 化；
4. 但它仍然只是单 provider 证据，不能关闭 cross-provider、strong baseline、scale stability 和理论证明 gate。

下一轮应继续：

1. 用 DeepSeek v4-pro 或本地 gpt-oss-20b 跑同一 prompt-variant matrix，验证跨 provider 方向是否一致；
2. 把 prompt variant 选择纳入 LCDU 方法定义，而不是作为事后修补；
3. 进入 strong baseline matrix，优先比较 TextGrad、LLM-as-optimizer、GA/CEM、TPE/DSPy；
4. 若跨 provider 方向不一致，必须把结论降级为 provider-sensitive LCDU calibration mechanism。

## 16. 第九轮执行记录

执行日期：2026-05-30

已完成：

1. Cross-provider matrix artifact
   - 新增 `experiments/lcdu_anes_llm_cross_provider_matrix.py`
   - 新增 `tests/test_lcdu_anes_llm_cross_provider_matrix.py`
   - artifact：`experiments/results/lcdu_llm_cross_provider/lcdu-anes-llm-cross-provider-matrix-deepseek-flash-lmstudio-gptoss-current-001.json`
   - status：`cross_provider_selected_variant_positive`

2. 本地 LM Studio gpt-oss-20b prompt-variant matrix
   - artifact：`experiments/results/lcdu_llm_seed_scale_repeat/lcdu-anes-llm-seed-scale-repeat-lmstudio-gpt-oss-20b-s2s4-o0o1-promptvariants-001.json`
   - base_url：`http://127.0.0.1:1234/v1`
   - model：`openai/gpt-oss-20b`
   - prompt variants：`compact`, `deliberative`
   - segment scales：2, 4
   - segment offsets：0, 1
   - run count：8
   - positive run count：7
   - total LLM calls：144
   - parse failure count：0

3. 本地模型失败点
   - task：公共卫生/医保
   - scale：2
   - offset：1
   - prompt variant：`compact`
   - selected segments：
     - `party_or_ideology=conservative|income=upper`
     - `party_or_ideology=conservative|income=middle`
   - heldout raw/final loss：0.005201882389374862 -> 0.005201882389374862
   - test raw/final loss：0.010402540574739057 -> 0.010402540574739057

4. Cross-provider selector 结论
   - DeepSeek v4-flash：prompt-variant matrix 8 / 8 positive
   - LM Studio gpt-oss-20b：prompt-variant matrix 7 / 8 positive
   - `compact`：2 个 provider environment 中只有 1 个全正
   - `deliberative`：2 个 provider environment 中 2 个全正
   - selected prompt variant：`deliberative`

5. Paper gate index
   - 更新 `experiments/lcdu_paper_gate_index.py`
   - `completed_subgates` 新增：
     - `cross_provider_stability_matrix_ready`
     - `cross_provider_stability_signal_positive`
   - 当前 `required_next_gates`：
     - `formalize_theoretical_identification_proof`
     - `run_scale_stability_matrix`
     - `run_finer_schema_robustness_matrix`
     - `run_strong_baseline_matrix`

当前解释边界：

1. LCDU 已经有第一层跨执行环境正向证据，但必须写成 selected variant positive；
2. 不能说全 prompt family 跨 provider 稳定，因为 `compact` 在本地模型上仍失败；
3. `deliberative` 进入当前 LCDU 方法定义时，必须保留 selector 规则、失败 variant 和 provider environment；
4. 这进一步增强 LCDU 的通用算法潜力，但仍未达到 CCF-A 充分证据。

下一轮应继续：

1. 跑 scale stability matrix，至少把 segment scale 从 2/4 扩到更大 segment 覆盖；
2. 进入 strong baseline matrix，优先建立可复现实验 schema；
3. 补 finer schema robustness，处理 ANES task card 中尚缺的 region / urbanicity / health insurance context；
4. 将 variant selector 写入理论定义和伪代码的正式章节。

## 17. 第十轮执行记录

执行日期：2026-05-30

已完成：

1. Scale stability artifact
   - 新增 `experiments/lcdu_anes_llm_scale_stability_matrix.py`
   - 新增 `tests/test_lcdu_anes_llm_scale_stability_matrix.py`
   - scale stability artifact：`experiments/results/lcdu_llm_scale_stability/lcdu-anes-llm-scale-stability-matrix-deepseek-v4-flash-deliberative-8x12x16-current-001.json`
   - status：`scale_stability_signal_positive`

2. Selected-variant 大 scale LLM matrix
   - source matrix artifact：`experiments/results/lcdu_llm_seed_scale_repeat/lcdu-anes-llm-seed-scale-repeat-deepseek-v4-flash-scale8x12x16-deliberative-001.json`
   - provider：DeepSeek OpenAI-compatible endpoint
   - model：`deepseek-v4-flash`
   - selected prompt variant：`deliberative`
   - segment scales：8, 12, 16
   - segment offsets：0
   - run count：3
   - positive run count：3
   - total LLM calls：216
   - parse failure count：0

3. Scale=16 结果
   - 当前 ANES `party_or_ideology × income` schema available segments：16
   - 气候/能源：
     - accepted method：`lcdu_segment_anchor_prompt`
     - test loss：0.046377 -> 0.008789
   - 公共卫生/医保：
     - accepted method：`lcdu_segment_anchor_prompt`
     - test loss：0.031566 -> 0.008113

4. Paper gate index
   - 更新 `experiments/lcdu_paper_gate_index.py`
   - `completed_subgates` 新增：
     - `scale_stability_matrix_ready`
     - `scale_stability_signal_positive`
   - 当前 `required_next_gates`：
     - `formalize_theoretical_identification_proof`
     - `run_finer_schema_robustness_matrix`
     - `run_strong_baseline_matrix`

当前解释边界：

1. LCDU selected variant=`deliberative` 已在当前 ANES 16 segment schema 内通过 scale stability；
2. 这不是 full-population field validation，也不是产品级大规模人群仿真；
3. 规模证据仍是单 provider，且 segment schema 只覆盖 `party_or_ideology × income`；
4. 下一步的核心判断点转向 strong baseline 和 finer schema robustness。

下一轮应继续：

1. 建立 strong baseline matrix，至少纳入 raw prompt、aggregate anchor、segment anchor、selected LCDU、compact/deliberative selector、TextGrad/LLM-as-optimizer/搜索类 baseline 的可比 schema；
2. 对 ANES task card 缺失轴做 finer schema robustness；
3. 把理论识别证明补成正式 artifact，而不是只停留在文档草案。

## 18. 第十一轮执行记录

执行日期：2026-05-30

已完成：

1. Strong baseline matrix artifact
   - 新增 `experiments/lcdu_anes_strong_baseline_matrix.py`
   - 新增 `tests/test_lcdu_anes_strong_baseline_matrix.py`
   - artifact：`experiments/results/lcdu_strong_baseline/lcdu-anes-strong-baseline-matrix-anes-current-001.json`
   - status：`strong_baseline_lcdu_not_leading`

2. Full-scale method-level LLM validation
   - artifact：`experiments/results/lcdu_llm_simulator_validation/lcdu-anes-llm-simulator-validation-deepseek-v4-flash-16seg-deliberative-current-001.json`
   - provider：DeepSeek OpenAI-compatible endpoint
   - model：`deepseek-v4-flash`
   - prompt variant：`deliberative`
   - max segments per task：16
   - total LLM calls：96
   - parse failure count：0

3. Covered baseline families
   - `llm_raw_prompt`
   - `llm_aggregate_anchor`
   - `deterministic_anchor_search`

4. Missing baseline families
   - `textgrad_or_prompt_optimizer`
   - `population_search`

5. Strong baseline 结果
   - 气候/能源：
     - LCDU LLM test loss：0.008914242922780178
     - best covered baseline：`deterministic_anchor_search / calibration_segment_anchor`
     - best baseline test loss：0.008343247118118962
     - LCDU leads covered baselines：false
   - 公共卫生/医保：
     - LCDU LLM test loss：0.008629284025508175
     - best covered baseline：`deterministic_anchor_search / calibration_segment_anchor`
     - best baseline test loss：0.006094935382542338
     - LCDU leads covered baselines：false

6. Paper gate index
   - 更新 `experiments/lcdu_paper_gate_index.py`
   - `completed_subgates` 新增：
     - `strong_baseline_matrix_ready`
     - `strong_baseline_signal_not_positive`
   - 当前 `required_next_gates` 仍包含：
     - `run_strong_baseline_matrix`

当前解释边界：

1. LCDU selected LLM prompt 明显优于 raw prompt 和 aggregate-anchor prompt；
2. 但 deterministic segment-anchor baseline 仍更强；
3. 当前不能说 LCDU 已经通过 strong baseline；
4. 这暴露出 `anchor_fidelity_gap`：LLM simulator 没有完全复现 deterministic anchor 的数值校准能力；
5. 论文主张应从“强 baseline 胜出”暂时降为“稳定、可审计地把 segment anchor 注入 LLM simulator，但仍需解释/缩小 anchor fidelity gap”。

下一轮应继续：

1. 补 `textgrad_or_prompt_optimizer` 与 `population_search` 两类缺失 baseline；
2. 设计 anchor-fidelity repair 或 hybrid 模式：数值分布由 deterministic anchor 保证，LLM 负责解释和情境化；
3. 判断 deterministic anchor 是否应被视为 oracle upper bound、constraint-only baseline，还是产品不可替代的核心组件。

## 19. 第十二轮执行记录

执行日期：2026-05-30

已完成：

1. 新增 baseline family matrix
   - 新增 `experiments/lcdu_anes_baseline_family_matrix.py`
   - 新增 `tests/test_lcdu_anes_baseline_family_matrix.py`
   - artifact：`experiments/results/lcdu_baseline_family/lcdu-anes-baseline-family-matrix-anes-current-001.json`
   - status：`baseline_family_matrix_ready`

2. 扩展 strong baseline matrix
   - `experiments/lcdu_anes_strong_baseline_matrix.py` 新增 `--baseline-family-artifacts`
   - LCDU 选择逻辑修正为 heldout 选源 artifact，再报告 test loss，避免多个 prompt variant 下出现 test peeking
   - 新增测试覆盖该 anti-test-peeking contract

3. 补充 full-scale LLM validation
   - 新增 standard variant artifact：`experiments/results/lcdu_llm_simulator_validation/lcdu-anes-llm-simulator-validation-deepseek-v4-flash-16seg-standard-current-001.json`
   - 保留 deliberative variant artifact：`experiments/results/lcdu_llm_simulator_validation/lcdu-anes-llm-simulator-validation-deepseek-v4-flash-16seg-deliberative-current-001.json`
   - compact variant 曾尝试执行，但 provider 调用超过合理等待时间；由于当前 LLM client CLI 尚无 timeout 参数，本轮中断，未作为证据写入。

4. 重建 strong baseline artifact
   - artifact：`experiments/results/lcdu_strong_baseline/lcdu-anes-strong-baseline-matrix-anes-current-001.json`
   - status：`strong_baseline_lcdu_not_leading`
   - missing baseline family count：0
   - covered baseline families：
     - `llm_raw_prompt`
     - `llm_aggregate_anchor`
     - `deterministic_anchor_search`
     - `population_search`
     - `textgrad_or_prompt_optimizer`

5. 重建 paper gate
   - artifact：`experiments/results/lcdu_paper_gate/lcdu-paper-gate-index-current-001.json`
   - status：`research_plan_ready_but_ccf_a_gate_open`
   - completed subgate 保留 `strong_baseline_signal_not_positive`
   - required next gates 仍包含 `run_strong_baseline_matrix`

关键结果：

1. 气候/能源：
   - LCDU selected source：`lcdu-anes-llm-simulator-validation-deepseek-v4-flash-16seg-deliberative-current-001`
   - LCDU heldout loss：0.007947427883157627
   - LCDU test loss：0.008914242922780178
   - best covered baseline：`deterministic_anchor_search / calibration_segment_anchor`
   - best covered baseline test loss：0.008343247118118962
   - LCDU leads covered baselines：false

2. 公共卫生/医保：
   - LCDU selected source：`lcdu-anes-llm-simulator-validation-deepseek-v4-flash-16seg-deliberative-current-001`
   - LCDU heldout loss：0.005765230652219242
   - LCDU test loss：0.008629284025508175
   - best covered baseline：`deterministic_anchor_search / calibration_segment_anchor`
   - best covered baseline test loss：0.006094935382542338
   - LCDU leads covered baselines：false

当前结论：

1. 第一层 missing family gap 已关闭；
2. strong baseline 仍未通过，且这是更强的负面证据；
3. 当前核心 gap 从“baseline 不完整”转为“anchor fidelity gap”；
4. 下一步不应继续包装 LCDU 已胜出，而应尝试 anchor-fidelity repair / hybrid mode，并判断 LCDU 的论文主贡献是否应转向“可审计 LLM simulator update framework + deterministic constraint upper bound”。

## 20. 第十三轮执行记录

执行日期：2026-05-30

已完成：

1. 新增 anchor-fidelity repair diagnostic
   - 新增 `experiments/lcdu_anes_anchor_fidelity_repair.py`
   - 新增 `tests/test_lcdu_anes_anchor_fidelity_repair.py`
   - 支持 deterministic anchor-copy、LLM strict-copy、LLM anchor L1 deviation、parse failure accounting
   - CLI 增加 `--timeout-seconds`，避免 provider hang 长时间阻塞

2. 运行 repair artifacts
   - hybrid full-segment artifact：`experiments/results/lcdu_anchor_fidelity_repair/lcdu-anes-anchor-fidelity-repair-hybrid-16seg-current-001.json`
   - LLM strict-copy 2-seg smoke：`experiments/results/lcdu_anchor_fidelity_repair/lcdu-anes-anchor-fidelity-repair-deepseek-v4-flash-copy-2seg-current-001.json`
   - LLM strict-copy 16-seg artifact：`experiments/results/lcdu_anchor_fidelity_repair/lcdu-anes-anchor-fidelity-repair-deepseek-v4-flash-copy-16seg-current-001.json`
   - 16-seg status：`llm_anchor_copy_repair_positive`
   - total LLM calls：32
   - parse failure count：0

3. 接入 paper gate
   - `experiments/lcdu_paper_gate_index.py` 新增 `--anchor-fidelity-repair`
   - paper gate completed subgates 新增：
     - `anchor_fidelity_repair_ready`
     - `anchor_fidelity_repair_llm_copy_positive`
   - strong baseline gate 仍保持打开，避免把 repair diagnostic 误当成原 LCDU prompt 胜出

关键结果：

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

当前结论：

1. Anchor-fidelity gap 可以被 strict-copy/hybrid 结构关闭；
2. 当前 strong-baseline failure 不是 LLM 无法复制 anchor，而是 `LCDU-soft` prompt 设计允许 LLM 偏离 anchor；
3. 后续 Research 应转向 `LCDU-hybrid` 或理论约束版 `LCDU-strict`，而不是继续无限调 soft prompt；
4. Product 侧应优先采用 hybrid：数值分布由 deterministic anchor/search 保证，LLM 负责解释、叙事、反事实和报告生成。

## 21. 第十四轮执行记录

执行日期：2026-05-30

已完成：

1. 新增 LCDU-hybrid method validation
   - 新增 `experiments/lcdu_anes_hybrid_method_validation.py`
   - 新增 `tests/test_lcdu_anes_hybrid_method_validation.py`
   - artifact：`experiments/results/lcdu_hybrid_method/lcdu-anes-hybrid-method-validation-current-001.json`
   - status：`hybrid_candidate_numeric_parity_soft_not_leading`
   - research decision：`reframe_as_hybrid_auditable_constraint_framework_not_accuracy_win`
   - product decision：`adopt_hybrid_for_auditable_product_reports`

2. 新增 bounded theoretical identification proof
   - 新增 `experiments/lcdu_theoretical_identification_proof.py`
   - 新增 `tests/test_lcdu_theoretical_identification_proof.py`
   - artifact：`experiments/results/lcdu_theory/lcdu-theoretical-identification-proof-current-001.json`
   - status：`bounded_hybrid_identification_proof_ready`
   - closed gate：`theoretical_identification_proof_ready`
   - identification result：`hybrid_numeric_distribution_identified_with_segment_anchor`

3. 扩展 paper gate
   - `experiments/lcdu_paper_gate_index.py` 新增：
     - `--hybrid-method-validation`
     - `--theoretical-identification-proof`
   - completed subgates 新增：
     - `hybrid_method_validation_ready`
     - `hybrid_method_numeric_parity_not_accuracy_win`
     - `theoretical_identification_proof_artifact_ready`
     - `theoretical_identification_proof_ready`
   - required next gates 从 3 个变为 2 个：
     - `run_finer_schema_robustness_matrix`
     - `run_strong_baseline_matrix`

关键结论：

1. `LCDU-soft` 不能作为 CCF-A 主贡献，因为它在完整第一层 strong baseline 下不领先；
2. `LCDU-hybrid` 具备 Product 竞争力：数值部分达到 deterministic anchor parity，LLM 可用于解释和报告；
3. `LCDU-hybrid` 具备论文候选潜力，但主张必须重写为“auditable constraint framework”，而不是“accuracy-superior optimizer”；
4. 当前还不能判断它最终足够 CCF-A，因为还缺 finer schema robustness，以及围绕 auditability / explanation faithfulness 的新增评价指标。

## 22. 第十五轮执行记录

执行日期：2026-05-30

已完成：

1. 新增 finer schema robustness matrix
   - 新增 `experiments/lcdu_anes_finer_schema_robustness_matrix.py`
   - 新增 `tests/test_lcdu_anes_finer_schema_robustness_matrix.py`
   - artifact：`experiments/results/lcdu_finer_schema/lcdu-anes-finer-schema-robustness-current-001.json`
   - status：`finer_schema_robustness_signal_positive`
   - schema count：4
   - positive schema count：4
   - max axis count：4

2. 扩展 paper gate
   - `experiments/lcdu_paper_gate_index.py` 新增 `--finer-schema-robustness-matrix`
   - completed subgates 新增：
     - `finer_schema_robustness_matrix_ready`
     - `finer_schema_robustness_signal_positive`
   - required next gates 只剩：
     - `run_strong_baseline_matrix`

关键结果：

1. `party_or_ideology + income`：2/2 tasks positive；
2. `party_or_ideology + income + age`：2/2 tasks positive；
3. `party_or_ideology + income + education`：2/2 tasks positive；
4. `party_or_ideology + income + age + education`：2/2 tasks positive；
5. 最大 common segment count：
   - climate：140
   - public health：143

当前结论：

1. 当前 SDA slice 可用轴下，segment anchor 在更细 schema 中仍 robust；
2. 但缺失 task-card axes 仍存在：region、urbanicity、health-insurance context；
3. paper gate 的唯一剩余 gate 是 strong baseline；
4. 这进一步确认：当前真正的 Research 决策点不是“再补常规验证”，而是是否接受 `LCDU-hybrid` 的贡献重定义。

## 23. 第十六轮执行记录

执行日期：2026-05-30

已完成：

1. 新增 research decision index
   - 新增 `experiments/lcdu_research_decision_index.py`
   - 新增 `tests/test_lcdu_research_decision_index.py`
   - artifact：`experiments/results/lcdu_research_decision/lcdu-research-decision-index-current-001.json`
   - status：`decision_boundary_reached_hybrid_conditional`

2. 决策结果
   - `LCDU-soft`：`reject_as_ccf_a_main_contribution_accuracy_optimizer`
   - `LCDU-strict`：`use_as_identification_component`
   - `LCDU-hybrid`：`conditionally_promising_as_auditable_constraint_framework`
   - CCF-A gate：`not_passed_under_accuracy_superiority_criterion`

3. 建议路线
   - Product：采用 hybrid 作为可信报告方法，数值由 deterministic anchor/search 保证，LLM 负责解释和报告；
   - Research：停止把 soft prompt JSD 胜出作为主目标，改为验证 auditable constraint-identification framework；
   - Paper：新增 auditability、explanation faithfulness、counterfactual reporting 指标，否则 hybrid 只能证明 parity，不能证明主贡献。
