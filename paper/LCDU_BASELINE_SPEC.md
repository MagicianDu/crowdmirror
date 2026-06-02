# LCDU Baseline Spec

## 1. 目标

LCDU 要冲 CCF-A，不能只和 TextGrad 或弱 prompt baseline 比。所有 baseline 必须进入统一 candidate schema、统一 split contract、统一 loss/reporting。

## 2. 统一 baseline candidate schema

```json
{
  "schema_version": "lcdu-baseline-candidate-v1",
  "candidate_id": "baseline-family-run-id",
  "method_family": "tpe_search",
  "generator": "optuna_tpe",
  "source_split_contract": {
    "candidate_generation": "calibration",
    "candidate_acceptance": "heldout",
    "final_claim_check": "test"
  },
  "candidate_prompt_components": {
    "segment_prompt": {},
    "calibration_anchor": {},
    "response_contract": "Return strict JSON probabilities."
  },
  "search_space": {},
  "budget": {
    "candidate_count": 0,
    "llm_call_budget": 0,
    "token_budget": 0
  },
  "claim_boundary": "baseline candidate; not accepted evidence until held-out gate passes"
}
```

## 3. Baseline families

### B0: Raw Prompt

作用：无校准下限。

要求：

1. 不使用 calibration residual。
2. 不使用 prompt patch。
3. 记录 provider/model/seed/scale。

### B1: TextGrad

作用：检验自由文本反馈更新是否稳定。

要求：

1. 反馈可来自 calibration split。
2. 候选必须进入 held-out gate。
3. 负向更新必须保留。
4. 不允许直接把 TextGrad 输出当 accepted prompt。

### B2: DSPy

作用：代表 prompt/program optimizer baseline。

要求：

1. 先做小预算 smoke。
2. 输出 prompt/program candidate。
3. 使用同一 held-out acceptance gate。
4. 记录 optimizer metric、train split、validation split。

### B3: Random / Latin Hypercube Search

作用：检验 LCDU 是否只是撞中了一个参数区域。

要求：

1. 搜索空间与 LCDU 参数空间一致。
2. 使用固定随机种子。
3. 至少报告 candidate distribution，不只报告 best。

### B4: Bayesian / TPE Search

作用：强参数优化 baseline。

要求：

1. 可用 Optuna/TPE 或轻量等价实现。
2. calibration split 选择候选。
3. held-out split 接受候选。
4. 报告 search trace 与过拟合风险。

### B5: Genetic / CEM Search

作用：检验启发式群体搜索是否优于 LCDU。

要求：

1. 个体编码必须可还原为 prompt-anchor candidate。
2. mutation/crossover 不得读取 held-out target。
3. 每代输出 best/median/worst。
4. CEM 需要报告 elite fraction。

### B6: LLM-as-Optimizer

作用：检验强 LLM 能否自动生成更好候选。

要求：

1. 推荐先用 DeepSeek v4-flash 做大矩阵，v4-pro 做关键复核。
2. LLM 只能看到 calibration residual 和 schema。
3. 输出必须是结构化 candidate。
4. held-out gate 决定接受。

### B7: S2PC

作用：历史结构化参数搜索路线。

要求：

1. 复用已有 artifacts。
2. 只作为 baseline 和 negative evidence。
3. 不再回到已经 stop-loss 的全量 patch 组合。

### B8: Retrieval-only

作用：检验语义检索本身是否足够。

要求：

1. 只检索相似 persona/segment/prototype。
2. 不施加 numeric constraint。
3. 与 LCDU 对比 semantic retrieval + constraint 的增益。

### B9: Constraint-only

作用：检验数值约束本身是否足够。

要求：

1. 不使用 semantic factor text。
2. 只使用概率上下界或 ranking guard。
3. 与 synchronized LCDU 对比。

## 4. 统一评估指标

每个 baseline 都必须报告：

1. `initial_loss`
2. `candidate_loss`
3. `best_loss`
4. `final_loss`
5. `relative_loss_reduction`
6. `worst_segment_loss_delta`
7. `axis_loss_delta`
8. `candidate_accepted_count`
9. `candidate_rejected_count`
10. `token_cost`
11. `runtime_seconds`

## 5. 统一接受规则

baseline 不能因为是对照组就降低标准：

```text
accepted iff
  held-out loss improves
  and complete segment coverage
  and no forbidden worst-segment regression
  and strict JSON artifact is valid
```

## 6. 主表进入标准

一个 baseline 进入论文主表，必须满足：

1. 有明确 candidate generator；
2. 有固定预算；
3. 有至少 3 seed/repeat；
4. 有 accepted/rejected 记录；
5. 有 failure reason；
6. 有 artifact refs。

只跑一次的 baseline 只能进 appendix 或 diagnostic section。

## 7. 当前第一层 ANES baseline coverage

当前已经生成第一层 ANES strong-baseline family artifact：

1. artifact：`experiments/results/lcdu_baseline_family/lcdu-anes-baseline-family-matrix-anes-current-001.json`
2. status：`baseline_family_matrix_ready`
3. covered families：
   - `population_search`
   - `textgrad_or_prompt_optimizer`

实现边界：

1. `population_search` 是 calibration-derived alpha grid，使用 heldout 选择、test 报告；当前两个 ANES task 均选择 `population_search_alpha_1`，等价于 direct segment anchor。
2. `textgrad_or_prompt_optimizer` 当前是 heldout-selected prompt variant/method grid，不是 TextGrad gradient update proof。
3. 因此该 artifact 可以关闭第一层 missing family gap，但不能替代 DSPy/TPE/GA/CEM/LLM-as-optimizer repeat 主表。
