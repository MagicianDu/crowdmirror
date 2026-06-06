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

1. 把 public proxy mapping review 文档化，分别解释 HTOPS `baseline_no_new_support` 和 ANES `private_insurance_plan` 为什么只能作为 reject proxy。
2. 针对 ANES health 的失败边界诊断 interaction 机制是否过度放大 rejection risk。
3. 将 evidence report 接到 Product report/demo ingestion，但继续保留 claim boundary。
4. 用 follow-up 或 holdout case 验证 outcome feedback update，只有跨 case 不回归时才允许从 `blocked_same_case_only` 升级。

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
