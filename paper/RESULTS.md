# CIRCE Results and Claim Boundaries

This document defines what the current CIRCE evidence chain can support and
what remains outside the claimed result surface. It is intentionally stricter
than the experiment logs: dry-run metrics can validate orchestration and data
contracts, but they do not establish live LLM model-quality improvement.

## Current Evidence Classes

1. Deterministic contract evidence
   - ECE supports soft calibration targets.
   - Choice probability parsing preserves all alternatives.
   - EDM includes macro and trajectory components.
   - Manifest serialization rejects malformed lanes, modes, statuses,
     timestamps, non-JSON payloads, and non-finite metric values.

2. Dry-run calibration plumbing
   - W3/W4 causal calibration executes end to end with mocked LLM responses.
   - W5/W6 emergence calibration executes end to end with mocked LLM responses.
   - The dry-run evidence matrix launches the causal child run plus
     asynchronous and synchronous emergence child runs.
   - Current dry-run manifests record command, configuration, metrics,
     artifact paths, status, and the claim boundary
     `dry-run plumbing evidence only`.
   - Dry-run results validate orchestration, result persistence, and manifest
     shape, not model quality.

3. Local/live calibration evidence
   - A run only enters this class when a manifest has `mode` equal to `local`
     or `live`.
   - Each run must record model, provider, command, configuration, metrics,
     artifacts, status, and notes.
   - Local/live runs may support model-quality claims only for the recorded
     configuration and only after the associated manifest or archived artifact
     is available for review.

4. Acceptance-gated TextGrad evidence
   - Paper-gate v2 achieved matrix coverage but failed as an unrestricted
     improvement claim because a material fraction of candidate updates were
     rejected or negative.
   - Wave 8 evaluates TextGrad as a candidate generator inside an explicit
     accept/reject/revert method, with `initial_loss`, `best_loss`,
     `final_loss`, candidate counts, and update policy recorded in manifests.
   - The current v3 smoke artifact is positive local Gemma evidence for one
     recorded cell, not paper-grade coverage.

5. PopulationBench-lite benchmark gate
   - The benchmark spec defines four reviewer-facing tasks: distributional
     choice fit, counterfactual direction, segment stability, and auditability.
   - The spec is a research gate for reproducible local evidence. It is not
     field validation and cannot by itself support commercial forecasting
     claims.
   - The current smoke artifact computes all three formerly blocked metrics
     from `benchmarks/fixtures/populationbench_lite_smoke_records.json`:
     `choice_distribution_jsd=0.005796652704995218`,
     `ate_direction_accuracy=1.0`, and `segment_rank_correlation=1.0`.
   - These values close the metric-computability gap for the smoke gate only;
     they are synthetic fixture evidence, not paper-grade domain coverage.

6. Policy reaction public-data intake readiness
   - The policy-reaction source catalog identifies HPS/HTOPS public-use data as
     an auditable candidate source for food subsidy, living-cost, and inflation
     pressure reaction benchmarks.
   - The intake manifest records source URL, access mode, unit of analysis,
     candidate policy fields, segment fields, target fields, and claim boundary
     in strict JSON.
   - This is public-data intake readiness only. It is not a model-quality
     result, not validation of a policy-reaction predictor, and not a China
     policy prediction.

7. Policy-reaction benchmark smoke gate
   - The HPS/HTOPS-shaped smoke artifact computes distributional policy-reaction
     fit, counterfactual direction, segment rank stability, and strict JSON
     auditability from `benchmarks/fixtures/policy_reaction_hps_smoke_records.json`.
   - The current smoke metrics are `choice_distribution_jsd=0.001478641375608338`,
     `ate_direction_accuracy=1.0`, and `segment_rank_correlation=1.0` across
     three policy-reaction segments.
   - The public-row converter smoke artifact reads HPS/HTOPS-shaped rows from
     `benchmarks/fixtures/policy_reaction_hps_public_rows_smoke.csv`, converts
     cataloged survey fields into benchmark records, and computes
     `choice_distribution_jsd=0.011460912342538824`,
     `ate_direction_accuracy=1.0`, and `segment_rank_correlation=1.0`.
   - The artifact status is `public_data_smoke`; it is not field validation, not
     paper-grade real-data coverage, and not a calibrated China policy forecast.

8. Official HPS/HTOPS public-use ingestion evidence
   - The HTOPS/HPS 2506 CSV zip was downloaded from the Census public-use
     dataset endpoint and hashed as
     `8d14cf52f5c3bc4fab5e74e3136cb753ab1195a06314725f00761035158172d4`.
   - The ingestion artifact reads `HTOPS_HPS_2506_PUF.csv` from the official
     zip, validates required source columns, and reports `puf_row_count=7485`,
     `usable_row_count=7317`, and `skipped_row_count=168`.
   - The resulting segment coverage is `general_population_cost_pressure=4658`,
     `fixed_income_inflation_stressed=1431`,
     `working_family_price_stressed=1105`, and
     `low_income_food_insecure=123`.
   - This is official public-use survey ingestion evidence only. It is not an
     LLM prediction-quality result, not field validation, and not a calibrated
     China policy forecast.

9. Official segment-alignment benchmark contract
   - The official segment benchmark compares the HTOPS/HPS ingestion artifact's
     observed policy-reaction proxy distributions with a separate segment
     prediction artifact.
   - The current smoke artifact uses a fixture prediction artifact to validate
     the benchmark contract and computes weighted JSD
     `0.0012863075023781803`, worst-segment JSD `0.0019366687119405392`,
     and segment rank correlation `1.0` across four matched official segments.
   - This closes the computability gap for official-data alignment metrics. It
     is not yet a Product LLM quality result because the prediction side is a
     fixture, not a committed Product cohort run.

10. Product LLM official segment-alignment smoke result
   - The Product worktree produced a local `openai/gpt-oss-20b` 12-persona,
     3-strategy policy cohort with 36 successful local LLM calls and exported
     `policy-reaction-segment-predictions-v1`.
   - The Research official segment benchmark consumed that Product artifact and
     passed segment coverage across all four HTOPS/HPS-derived official
     segments.
   - The observed alignment metrics are weak: weighted JSD
     `0.18508191023524456`, worst-segment JSD `0.20176098754129515`,
     mean JSD `0.14176641355525532`, segment rank correlation `-0.25`, and
     worst-segment rank correlation `-1.0`.
   - This is a useful negative/diagnostic Product-to-Research evidence chain:
     the workflow is auditable, but the current local LLM cohort is not
     calibrated to the official public-use observed distribution.

11. Acceptance-gated official calibration candidate
   - The Product worktree then ran the same local `openai/gpt-oss-20b` 12x3
     cohort with `calibration_profile=official_htops_2506`, which adds the
     official HTOPS/HPS segment observed distributions as prompt-level
     calibration anchors.
   - The official segment benchmark improved from initial weighted JSD
     `0.18508191023524456` to candidate weighted JSD
     `0.0000014452916659122088`; segment rank correlation improved from
     `-0.25` to `1.0`.
   - The calibration gate accepted the candidate and records
     `initial_loss=0.18508191023524456`,
     `best_loss=0.0000014452916659122088`,
     `final_loss=0.0000014452916659122088`,
     `candidate_accepted_count=1`, and `candidate_rejected_count=0`.
   - This is acceptance-gated local evidence that Research can make Product
     outputs conform to an official public-data benchmark. It is not yet
     generalization evidence because it has one model, one seed, one scale, and
     uses the same official source as the prompt anchor.

12. Leakage-aware official row-split evaluation
   - The official HTOPS/HPS 2506 public-use rows are now deterministically split
     by `sha256(SCRAMID) mod 2` into calibration and evaluation projections.
     The split artifact records `puf_row_count=7485`,
     `calibration_row_count=3845`, `evaluation_row_count=3640`, and
     `unassigned_row_count=0`.
   - The evaluation projection preserves the
     `policy-reaction-public-data-ingestion-v1` schema so the official segment
     benchmark can consume it as a held-out target. The evaluation projection
     reports `usable_row_count=3561` across the same four policy-reaction
     segments.
   - On the held-out evaluation projection, the uncalibrated Product
     `openai/gpt-oss-20b` 12x3 artifact reports weighted JSD
     `0.18814846781521002`, worst-segment JSD `0.20538128218199306`,
     mean JSD `0.1414090526039107`, segment rank correlation `-0.25`, and
     worst-segment rank correlation `-1.0`.
   - On the same held-out projection, the current calibrated Product artifact
     reports weighted JSD `0.000025466162714366303`, worst-segment JSD
     `0.0004027469503724598`, mean JSD `0.00011978496001786317`, segment rank
     correlation `1.0`, and worst-segment rank correlation `1.0`.
   - This improves the evidence chain from same-artifact fitting to row-level
     holdout evaluation. It still does not establish generalization because the
     prompt anchors and evaluation rows come from the same public source and
     release; the next gate is to derive Product calibration priors only from
     the calibration projection, then evaluate only on the held-out projection.

13. Calibration-split anchored held-out Product gate
   - The Product worktree ran a new local `openai/gpt-oss-20b` 12x3 cohort with
     `calibration_profile=official_htops_2506_calibration_split`. The prompt
     priors are loaded only from
     `policy-reaction-htops-2506-calibration-ingestion-001.json`, whose
     `source_split` is `calibration`.
   - The exported Product artifact
     `policy-reaction-segment-predictions-gpt-oss-20b-12x3-calibration-split-001`
     covers all four official segments and is evaluated only against
     `policy-reaction-htops-2506-evaluation-ingestion-001.json`.
   - The held-out evaluation benchmark reports weighted JSD
     `0.00011289095369171064`, worst-segment JSD
     `0.0015928065281891066`, mean JSD `0.00047800531351438507`, segment rank
     correlation `1.0`, and worst-segment rank correlation `1.0`.
   - The held-out calibration gate compares against the uncalibrated held-out
     baseline and accepts the candidate with
     `initial_loss=0.18814846781521002`,
     `best_loss=0.00011289095369171064`,
     `final_loss=0.00011289095369171064`,
     `candidate_accepted_count=1`, and `candidate_rejected_count=0`.
   - This is the first complete Research/Product evidence chain where the
     prompt anchor comes from the calibration projection and the acceptance
     metric comes from the held-out evaluation projection. It remains local,
     same-source, same-release evidence rather than cross-source or
     customer-field validation.

14. Calibration-split prompt/persona patch gate
   - The Research worktree now derives a prompt/persona patch candidate from
     the calibration projection benchmark
     `policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-calibration-split-initial-001`.
     The calibration benchmark compares the uncalibrated Product predictions
     against `policy-reaction-htops-2506-calibration-ingestion-001` and reports
     weighted JSD `0.18230076050456098`, mean JSD
     `0.1423293026128619`, worst-segment JSD `0.19832880119161886`,
     segment rank correlation `-0.25`, and worst-segment rank correlation
     `-1.0`.
   - The derived candidate contains eight structured patches: four segment
     residual patches and four persona-level calibration-anchor parameter
     patches. All candidate patches record `source_split=calibration`.
   - The prompt/persona patch gate
     `policy-reaction-prompt-patch-gate-gpt-oss-20b-12x3-calibration-split-heldout-001`
     evaluates the candidate only through the held-out benchmark
     `policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-calibration-split-heldout-001`.
     It accepts the candidate with
     `initial_loss=0.18814846781521002`,
     `best_loss=0.00011289095369171064`,
     `final_loss=0.00011289095369171064`,
     `candidate_accepted_count=1`, and `candidate_rejected_count=0`.
   - This converts the Product calibration profile into an inspectable
     prompt/persona patch evidence object. The claim remains same-source,
     same-release, local Product evidence; it does not establish field validity
     or cross-source policy-simulation accuracy.

15. Product runtime prompt/persona patch effect
   - Product now consumes the accepted Research prompt/persona patch gate at
     runtime through the `llm-cohort-gate` prompt patch artifact path. The
     resulting Product cohort manifest
     `llm-cohort-policy-local-gpt-oss-20b-12x3-calibration-split-prompt-patch-runtime-001`
     records `36` attempted local `openai/gpt-oss-20b` calls, `36`
     successful calls, `0` failed calls, and the accepted prompt patch context
     with `patch_count=8`.
   - A root-cause check found that the first runtime-effect comparison used the
     older uncalibrated held-out benchmark as its baseline. That comparison
     overstated the runtime patch because the fair baseline for this question
     is the same `official_htops_2506_calibration_split` Product run without
     prompt/persona patch injection.
   - The corrected effect artifact
     `policy-reaction-runtime-patch-effect-gpt-oss-20b-12x3-calibration-split-heldout-001`
     now compares the matched calibration-split baseline
     `policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-calibration-split-heldout-001`
     against the runtime-patch benchmark
     `policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-runtime-patch-heldout-001`.
     Weighted JSD increases from `0.000112890954` to
     `0.004316334859`, so the runtime patch regresses relative to the matched
     calibration-split baseline.
   - Two additional repeat axes were run through Product and evaluated in
     Research: `12x3 seed=17` and `16x3 seed=11`. The explicit repeat effect
     artifacts report regressions in both cases: `12x3 seed=17` increases
     weighted JSD from `0.000111545213` to `0.002550125008`, and `16x3
     seed=11` increases weighted JSD from `0.000109778219` to
     `0.008459664001`.
   - The stability matrix
     `policy-reaction-runtime-patch-stability-gpt-oss-20b-calibration-split-heldout-001`
     summarizes three matched baseline-vs-runtime-patch comparisons. It records
     `effect_count=3`, `improved_count=0`, `regressed_count=3`,
     `overall_status=stable_regression`, and mean relative loss reduction
     `-45.052587741358`.
   - This negative result is important for the Research/Product bridge: the
     accepted prompt/persona patch is runnable and auditable, but direct
     injection weakens held-out segment alignment once the stronger
     calibration-split baseline is used. The patch gate should therefore be
     treated as a candidate-generation and audit component, not as accepted
     runtime evidence until the actual runtime effect gate passes. The claim
     remains local, same-source, same-release, and segment-level; it does not
     establish field validation, causal policy effects, or cross-source
     generalization.

8. **DeepSeek v4-flash Product cohort smoke**
   - The Product worktree connected to the DeepSeek OpenAI-compatible endpoint
     with `model=deepseek-v4-flash` and ran a 12-persona, 3-policy
     policy-reaction cohort under run id
     `llm-cohort-policy-deepseek-v4-flash-12x3-smoke-001`.
   - The completed Product manifest records `36` attempted calls, `36`
     successful calls, `0` failed calls, and exports the segment prediction
     artifact
     `policy-reaction-segment-predictions-deepseek-v4-flash-12x3-smoke-001`.
   - The Research held-out official segment benchmark
     `policy-reaction-official-segment-benchmark-deepseek-v4-flash-12x3-smoke-heldout-001`
     consumes that Product prediction artifact and the HTOPS/HPS evaluation
     split. It reports full segment coverage and weighted choice-distribution
     JSD `0.15922332682959597`.
   - This is a useful provider-integration and benchmarkability result, not a
     calibration improvement result. In this smoke setting, DeepSeek v4-flash
     remains much worse than the matched calibration-split `openai/gpt-oss-20b`
     held-out artifact with weighted JSD `0.00011289095369171064`, while being
     in the same rough range as the uncalibrated `openai/gpt-oss-20b` held-out
     artifact. The immediate implication is that provider strength alone does
     not replace explicit calibration and acceptance gates.

9. **DeepSeek v4-flash calibration-split held-out smoke**
   - The Product worktree then ran `model=deepseek-v4-flash` with the
     `official_htops_2506_calibration_split` profile loaded only from the
     calibration projection artifact. Three Product manifests are now recorded:
     `llm-cohort-policy-deepseek-v4-flash-12x3-calibration-split-001`,
     `llm-cohort-policy-deepseek-v4-flash-12x3-calibration-split-seed17-001`,
     and `llm-cohort-policy-deepseek-v4-flash-16x3-calibration-split-seed11-001`.
   - The first two runs use 12 personas and 3 policies, each with `36` attempted
     calls, `36` successful calls, and `0` failed calls. The third run increases
     the cohort to 16 personas and records `48` attempted calls, `48` successful
     calls, and `0` failed calls.
   - The corresponding held-out Research benchmarks are
     `policy-reaction-official-segment-benchmark-deepseek-v4-flash-12x3-calibration-split-heldout-001`,
     `policy-reaction-official-segment-benchmark-deepseek-v4-flash-12x3-calibration-split-seed17-heldout-001`,
     and
     `policy-reaction-official-segment-benchmark-deepseek-v4-flash-16x3-calibration-split-seed11-heldout-001`.
   - All three held-out artifacts report full segment coverage and segment rank
     correlation `0.75`. Weighted choice-distribution JSD is stable across the
     repeats: `0.01038096736167976`, `0.010887103272666527`, and
     `0.011115634336425139`, with mean `0.010794568323590475`, minimum
     `0.01038096736167976`, maximum `0.011115634336425139`, and population
     standard deviation `0.00030698092073803995`.
   - This is a stable calibration-transfer smoke relative to the uncalibrated
     DeepSeek v4-flash weighted JSD `0.15922332682959597`, but it is still much
     weaker than the matched calibration-split `openai/gpt-oss-20b` held-out
     weighted JSD `0.00011289095369171064`. The safe claim is that explicit
     calibration split prompting improves DeepSeek v4-flash alignment in these
     small runs; it is not a cross-provider superiority claim.

10. **DeepSeek v4-pro candidate-update smoke**
    - The Research worktree ran W3/W4 causal calibration with
      `model=deepseek-v4-pro`, `eval_size=2`, `max_iter=2`, dataset seed `42`,
      and run id `w3w4-deepseek-v4-pro-eval2-seed42-structured-smoke-001`.
    - The run completed with `13` total LLM calls, initial loss
      `0.3003150770148567`, best loss `0.3003150770148567`, and final loss
      `0.4522002190868819`.
    - Candidate accounting records `candidate_accepted_count=0`,
      `candidate_rejected_count=1`, `candidate_acceptance_rate=0.0`, and
      `textgrad_effect_status=rejected_no_improvement`. Output budget
      saturation was false, so the negative result is not explained by prompt
      truncation in this smoke.
    - This result is useful because it proves the stronger DeepSeek v4-pro
      candidate-generation path is executable and auditable, but it provides no
      evidence that the current TextGrad-style prompt update improves loss.
      DeepSeek v4-pro should therefore be carried forward as a candidate
      generator to compare against structured persona-parameter calibration,
      not reported as an effective optimizer yet.

11. **Policy-reaction update-method gate**
    - The Research worktree now records the method-level comparison artifact
      `policy-reaction-update-method-gate-current-001`. It separates held-out
      candidate evidence from diagnostic-only optimizer evidence under one strict
      update policy:
      `accept_matched_heldout_loss_improvement_with_complete_segment_coverage_else_reject_or_mark_diagnostic`.
    - The gate contains six method records: four `calibration_split_prompting`
      held-out records, one `structured_persona_parameter_patch` runtime
      stability record, and one `deepseek_v4_pro_textgrad_candidate_update`
      diagnostic record. It reports `candidate_update_count=5`,
      `candidate_accepted_count=4`, `candidate_rejected_count=1`,
      `diagnostic_only_count=1`, and `candidate_acceptance_rate=0.8`.
    - The best accepted record is
      `gpt_oss_20b_calibration_split_prompting_12x3_seed11`, with matched
      initial loss `0.188148467815`, best loss `0.000112890954`, and final loss
      `0.000112890954`. The DeepSeek v4-flash calibration-split records are also
      accepted relative to the uncalibrated DeepSeek v4-flash held-out baseline,
      but their best losses remain around `0.0104` to `0.0111`.
    - The `structured_persona_parameter_patch` method is rejected by the runtime
      stability evidence: `gpt_oss_20b_runtime_prompt_patch_stability` records
      initial loss `0.000111404795`, candidate/runtime loss `0.005108707956`,
      and relative loss reduction `-45.052587741358`.
    - The DeepSeek v4-pro TextGrad record is deliberately `diagnostic_only`.
      It has no policy-reaction held-out benchmark artifact, and its W3/W4 smoke
      already records initial loss `0.3003150770148567`, best loss
      `0.3003150770148567`, final loss `0.4522002190868819`, and a rejected
      candidate. The method gate therefore treats it as executable optimizer
      plumbing, not accepted policy-reaction calibration evidence.

## Accepted Claims

- CIRCE has a deterministic validation path for probability contracts,
  causal-loss accounting, EDM accounting, and evidence-manifest validity.
- CIRCE can execute causal and emergence calibration loops without API keys in
  dry-run mode.
- CIRCE can write auditable manifests for W3/W4 causal calibration, W5/W6
  emergence calibration, and dry-run evidence-matrix runs.
- Dry-run matrix evidence can show that child commands exited successfully and
  produced manifests, but only as plumbing evidence.
- Local/live improvement claims require a committed manifest or archived run
  artifact with `mode` equal to `local` or `live`.
- CIRCE can record an offline, strict-JSON public-data intake manifest for the
  HPS/HTOPS food-cost policy-reaction benchmark source.
- CIRCE can compute a strict-JSON HPS/HTOPS-shaped policy-reaction smoke
  benchmark with distributional fit, direction, and segment-stability metrics.
- CIRCE can convert HPS/HTOPS-shaped public rows with cataloged policy and
  segment fields into strict-JSON policy-reaction benchmark records.
- CIRCE can ingest the official HTOPS/HPS 2506 public-use CSV zip and produce
  strict-JSON aggregate evidence for policy-reaction segment coverage.
- CIRCE can compute strict-JSON official-data segment-alignment metrics when
  given a compatible segment prediction artifact.
- CIRCE can evaluate a real Product LLM cohort prediction artifact against the
  official HTOPS/HPS segment benchmark and preserve negative alignment results.
- CIRCE can accept a Research-informed Product prompt/persona calibration
  candidate only when official-data alignment loss improves under a strict JSON
  calibration gate.
- CIRCE can create deterministic official-data calibration/evaluation row
  splits and evaluate Product segment predictions on a held-out official
  projection while preserving strict JSON evidence contracts.
- CIRCE can connect a Product LLM cohort calibrated only from the official
  calibration projection to a Research acceptance gate evaluated only on the
  official held-out projection.
- CIRCE can derive structured prompt/persona patch candidates from a
  calibration projection and accept them only through a held-out prompt patch
  gate with inspectable residual and parameter patch records.
- CIRCE can route a paid DeepSeek v4-flash Product cohort through the same
  Product-to-Research segment prediction and held-out benchmark artifacts
  without writing provider keys into manifests.
- CIRCE can evaluate DeepSeek v4-flash under both uncalibrated and
  calibration-split Product prompts against the same HTOPS/HPS held-out
  benchmark, preserving provider, model, split, and artifact boundaries.
- CIRCE can execute a DeepSeek v4-pro candidate-update smoke and record
  acceptance-gated negative results without treating rejected prompt updates as
  improvements.
- CIRCE can compare automated prompt/persona update methods in a strict JSON
  policy-reaction method gate that accepts only matched held-out improvements,
  rejects regressed runtime patch evidence, and marks optimizer-only evidence as
  diagnostic when policy-reaction held-out evaluation is missing.

## Not Yet Claimed

- No cross-domain generalization is claimed.
- No cross-provider or production-provider equivalence is claimed from local
  evidence.
- No commercial demand prediction accuracy is claimed.
- No replacement of human user research is claimed.
- No live LLM improvement is claimed from dry-run-only evidence.
- No causal or emergence metric improvement is claimed unless a non-dry-run
  manifest records the initial metric, best metric, command, configuration,
  model/provider context, and artifact path.
- No TextGrad effectiveness claim is made unless the manifest reports
  acceptance-gated candidate accounting with zero pending candidates.
- No DeepSeek v4-pro prompt-update effectiveness claim is made from the current
  W3/W4 smoke because the only evaluated candidate was rejected and final loss
  worsened.
- No TextGrad or DeepSeek v4-pro policy-reaction optimizer effectiveness claim
  is made until a generated policy-reaction candidate is evaluated on the
  held-out HPS/HTOPS benchmark and accepted by the method gate.
- No policy-reaction model-quality result, China policy prediction, or field
  validation claim is made from the public-data intake catalog or manifest.
- No policy-reaction field validation or paper-grade benchmark coverage is made
  from the current `public_data_smoke` fixture artifact.
- No claim is made that the public-row converter smoke fixture is a downloaded
  official HPS/HTOPS public-use file; it is a converter contract for the next
  real-data ingestion step.
- No LLM model-quality, causal policy effect, or field-validation claim is made
  from the official public-use ingestion artifact; it is a data-readiness and
  evidence-chain audit artifact.
- No Product LLM quality claim is made from the current official segment
  benchmark smoke artifact because its prediction side is a fixture contract,
  not an actual Product cohort output.
- No positive Product LLM calibration claim is made from the current
  `openai/gpt-oss-20b` 12x3 official segment benchmark result; the metrics are
  diagnostic evidence of a calibration gap.
- No general policy-simulation accuracy claim is made from the accepted
  `official_htops_2506` calibration candidate until it is repeated across
  seeds, cohort scales, prompts, and model configurations, and until leakage
  boundaries between calibration anchors and evaluation targets are addressed.
- No cross-source or cross-period generalization claim is made from the
  row-split evaluation because the calibration and evaluation projections are
  both derived from HTOPS/HPS 2506.
- No prompt/persona patch gate claim is made beyond the recorded Product
  scenario, model, cohort scale, public-source release, and held-out split.

## Evidence Review Checklist

- [ ] Manifest exists under `experiments/results/manifests/`.
- [ ] Manifest uses schema version `circe-evidence-v1`.
- [ ] Manifest mode is `local` or `live` for any model-quality claim.
- [ ] Initial and best metrics are both recorded.
- [ ] Command and configuration are recorded.
- [ ] Model/provider context is recorded for any local/live claim.
- [ ] Artifact paths point to inspectable run output or an archived artifact.
- [ ] Failure or null-result runs are retained with status and notes.
- [ ] Dry-run manifests are cited only as deterministic or plumbing evidence.
