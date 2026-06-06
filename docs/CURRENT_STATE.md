# Current State

## 当前状态

截至 2026-06-06，项目已从 R4/R5 的静态 heldout accuracy race 转向 R6：

> 结果反馈约束的先验锚定交互仿真框架。

已提交的 R6 spec：

- commit: `2d57ad7 docs: add R6 outcome feedback simulation spec`
- file: `docs/superpowers/specs/2026-06-05-r6-outcome-feedback-prior-anchored-interaction-simulation-spec.md`

已提交的 R6 foundation：

- commit: `26edc7d feat: add R6 foundation artifact chain`
- 覆盖 `prior -> scenario -> interaction -> risk shift -> outcome -> learning -> update registry`

当前新增的 R6 第二阶段最小单元：

- `experiments/r6_case_templates.py`：3 个行业无关 fixture。
- `experiments/r6_case_matrix.py`：跨 case 跑通完整 R6 chain。
- `experiments/r6_product_report.py`：生成 Product 可消费的发布前风险和发布后复盘报告。
- `experiments/results/r6_case_matrix/r6-case-matrix-current-001.json`
- `experiments/results/r6_product_report/r6-product-report-current-001.json`

当前新增的 R6 证据升级单元：

- `experiments/r6_public_outcome_proxy.py`：将 HTOPS/HPS public-use ingestion artifact 转成 R6 public outcome proxy。
- `experiments/r6_ablation_report.py`：比较 no-interaction prior、random noise、uncalibrated interaction、prior-anchored interaction 和 same-case outcome feedback update。
- `experiments/r6_evidence_report.py`：回答当前 R6 是继续推进还是触发止损。
- `experiments/results/r6_public_outcome_proxy/r6-public-outcome-proxy-current-001.json`
- `experiments/results/r6_ablation_report/r6-ablation-report-current-001.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-001.json`

当前新增的 R6 双 proxy 证据单元：

- `experiments/results/r6_public_outcome_proxy/r6-public-outcome-proxy-anes-health-current-001.json`
- `experiments/results/r6_ablation_report/r6-ablation-report-anes-health-current-001.json`
- `experiments/results/r6_case_matrix/r6-case-matrix-current-002.json`
- `experiments/results/r6_product_report/r6-product-report-current-002.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-002.json`

当前新增的 R6 诊断收束单元：

- `experiments/r6_proxy_mapping_review.py`
- `experiments/r6_failure_boundary_report.py`
- `experiments/results/r6_proxy_mapping_review/r6-proxy-mapping-review-current-001.json`
- `experiments/results/r6_failure_boundary_report/r6-failure-boundary-report-anes-health-current-001.json`

当前新增的 R6 mechanism cap ablation 单元：

- `experiments/r6_mechanism_cap_ablation.py`
- `experiments/results/r6_mechanism_cap_ablation/r6-mechanism-cap-ablation-current-001.json`

当前新增的 R6 Product 证据链接入单元：

- `experiments/r6_product_report.py` 支持 `mechanism_cap_ablation` ingestion。
- `experiments/r6_evidence_report.py` 将 Product ingestion 纳入 acceptance gate。
- `experiments/results/r6_product_report/r6-product-report-current-003.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-003.json`

当前新增的 R6 follow-up / holdout 验证单元：

- `experiments/r6_followup_holdout_validation.py`
- `experiments/r6_evidence_report.py` 将 follow-up / holdout validation 纳入 acceptance gate。
- `experiments/results/r6_followup_holdout_validation/r6-followup-holdout-validation-current-001.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-004.json`

当前新增的 R6 第三个 public proxy 单元：

- `experiments/r6_public_outcome_proxy.py` 支持 `anes_climate_heldout`。
- `experiments/results/r6_public_outcome_proxy/r6-public-outcome-proxy-anes-climate-current-001.json`
- `experiments/results/r6_ablation_report/r6-ablation-report-anes-climate-current-001.json`
- `experiments/results/r6_followup_holdout_validation/r6-followup-holdout-validation-current-002.json`
- `experiments/results/r6_evidence_report/r6-evidence-report-current-005.json`

当前新增的 R6 方法验收与迁移协议 addendum：

- `docs/superpowers/specs/2026-06-06-r6-method-gates-transfer-protocol-spec.md`
- 当前路线已从“继续补 public proxy / artifact 细节”切换到“方法定义、acceptance gates、cross-case transfer protocol 和 Product evidence card contract”。
- 后续不再把泛泛增加 proxy 数量作为推进目标；新增数据必须服务于明确 gate，例如 in-condition same-family holdout 或 outcome feedback cross-case transfer。

## 已确认结论

1. 强人口/客户/群体先验不是研究对手，而是仿真底座。
2. 交互仿真的第一价值是发现静态先验盲区和二阶风险。
3. 没有真实 outcome 前，不能宣称交互仿真一定比静态先验更准。
4. 真实 outcome 回来后，系统必须能做误差归因和方法更新。
5. 垂直场景只能作为验证 case，不能成为方法定义。
6. 当前 public proxy evidence 支持继续 R6，但只能作为诊断证据，不能作为 field validation 或跨域准确性结论。
7. same-case outcome feedback update 即使降低误差，也必须保持 `blocked_same_case_only`，不能进入全局默认参数。
8. 双 proxy 结果是 mixed evidence：HTOPS public proxy 上 prior-anchored interaction 优于 no-interaction prior；ANES health heldout proxy 上 prior-anchored interaction 劣于 no-interaction prior。
9. 当前结论不是“R6 稳定正效应成立”，而是“R6 已能发现正向信号和失败边界，值得继续但必须做跨 proxy/holdout 约束”。
10. HTOPS 与 ANES 的 proxy mapping 已形成审计记录，二者都只能作为 bounded reject proxy，不能当作 field outcome 或直接态度真值。
11. ANES health 失败边界已定位为 `interaction_over_amplifies_rejection_risk`：当静态先验已经接近 public proxy 时，rights/rule interaction profile 的 rejection amplification 会过冲。
12. mechanism cap ablation 形成一个诊断候选：当 `static_prior_error <= 0.03` 且目标属于 rights/rule change 时，将 aggregate reject delta 限制到 `0.02`，可以把 ANES heldout proxy 的 prior-anchored error 从 `0.05` 降到 `0.00`，同时不影响 HTOPS proxy 上的正向信号。
13. 上述 cap 仍是 `diagnostic_only`，`global_update_status=blocked_until_follow_up_holdout`；它证明 R6 能做失败归因和候选修复，但还不能宣称机制更新已通过全局验收。
14. Product report 已能展示完整证据链：`pre_release_risk_shift -> public_proxy_failure_boundary -> mechanism_cap_candidate`；其中 mechanism cap 的 `claim_status=diagnostic_candidate_not_runtime_default`，`default_runtime_enabled=false`。
15. Evidence report 已将 Product ingestion 纳入 gate：`product_report_ingests_mechanism_cap=true`；旧的 `needs_product_demo_report_ingestion` 与 `needs_public_proxy_mapping_review` gap 不再保留。
16. follow-up / holdout validation 的当前结论是 `holdout_validation_partial`：mechanism cap 在 ANES source case 上修复失败，并在 HTOPS cross-proxy holdout 上不回归，但缺少同 family 的 rights/rule holdout，因此 `global_update_accepted=false`。
17. outcome feedback update 在两个 public proxy 上都降低了 same-case error，但仍是 `blocked_same_case_only`；当前没有 cross-case transfer protocol，不能进入全局更新。
18. 第三个 public proxy `anes_climate_heldout` 已接入：它是同 ANES public-use、不同政策域的 climate-energy regulation heldout，映射到 `generic-rights-rule-change` 的 bounded reject proxy，`observed_reject_proxy=0.25`。
19. 第三个 proxy 让 holdout 结论更精确：当前不是“没有同 family holdout”，而是“同 family holdout 可用，但不覆盖 cap 触发条件”。在 climate holdout 上 static prior error 为 `0.06`，高于 cap 条件阈值 `0.03`，因此 `mechanism_cap_same_family_cap_condition_covered=false`、`global_update_accepted=false`。
20. 三个 public proxy 的整体证据仍是 mixed evidence：HTOPS 上 prior-anchored interaction 为正向，ANES health 与 ANES climate 上都是 regression；因此 R6 只能继续作为有约束诊断框架推进，不能宣称稳定准确性优势。
21. 当前工作没有偏离 R6 主线，但已到达细节扩张边界；继续堆 proxy 或 JSON 变体收益不足，必须转向方法验收层。
22. 当前 R6 最强主张是：它已经形成能连接强先验、交互风险偏移、结果反馈、失败边界和受约束更新的可审计框架，但尚未证明稳定准确性优势或全局可迁移更新能力。
23. mechanism cap 当前处于 `L3 partial`：source case 修复成立，部分 holdout 不回归，但缺少覆盖 cap 触发条件的独立同 family holdout，不能进入 runtime default。
24. outcome feedback 当前处于 `L2 same-case improvement`：两个 public proxy 上 same-case error 均下降，但缺少 cross-case transfer protocol，不能宣称可迁移优化。

## 可复用资产

- `MCR-Gate` 的 accepted/rejected ledger 和 failure diagnosis。
- `R4` 的 task / population / environment / interaction / gate artifact chain。
- `R5` 的 mechanism state、frame shock、mechanism gate 和 Product audit 经验。
- LCDU / shrinkage prior 作为 no-interaction strong prior 参考。
- Product report contract 中的 claim boundary 和 failure diagnosis 思路。

## 不再作为主线的内容

- DCL-PRS 作为 CCF-A 主算法。
- LCDU/LCDU-LCR-SG 作为唯一主研究路线。
- TextGrad/prompt/persona patch 作为核心优化路径。
- R4/R5 当前 interaction 或 mechanism-state 作为准确性主贡献。
- 单一垂直行业 demo 作为方法本体。

## 当前工作区风险

旧路线未提交文件已于 2026-06-05 移出 active worktree 并归档到 repo 外部：

- `/Users/dm/Documents/cc-社会计算器-worktrees/_archives/research-r2-r5-pre-r6-cleanup-20260605-115514`

当前仍需注意三类风险：

1. 旧 README、ROADMAP、paper 草案仍可能把开发目标拉回 persona / TextGrad / LCDU。
2. `experiments/results` 被 `.gitignore` 的 `results/` 规则忽略，新 R6 证据 JSON 需要显式 `git add -f`。
3. 当前 3 个 case 仍是 fixture-level evidence，不是真实跨域验证。

R6 开发时必须只 stage 本轮明确修改的文件。

## 下一步

1. 实现 `cross-case transfer protocol artifact`，统一记录 source case、candidate update、frozen rule、holdout case、比较结果和 global update 阻断原因。
2. 写出 `in-condition holdout` 搜索标准和数据选择 ledger；不再泛泛找公开数据，而是按 cap 触发条件和 case family 条件筛选。
3. 定义 Product evidence card contract，把 claim status、allowed claim、blocked claim、source artifact、升级条件做成产品可消费结构。
4. 只有当前三项完成后，才继续做有目标的数据接入或 Product demo/API 接线。

## 验收边界

第一阶段验收只确认：

- artifact 合同成立；
- risk shift 相对 no-interaction 可解释；
- outcome 可回填；
- learning report 可做误差归因；
- update registry 阻断未验证更新。

第一阶段不宣称：

- 交互仿真已经比静态先验更准；
- 方法已经具备跨行业真实预测能力；
- LLM agent 交互等价于真实人群行为。
