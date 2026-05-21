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
    - The gate now contains nine method records: four
      `calibration_split_prompting` held-out records, one
      `s2pc_l0_deterministic_catalog_beam_search` candidate-generation held-out
      record, one `s2pc_l0_deterministic_catalog_beam_search_runtime`
      runtime-effect record, one
      `s2pc_l1_multi_candidate_runtime_search_runtime` held-out runtime-matrix
      record, one `structured_persona_parameter_patch` runtime stability
      record, and one `deepseek_v4_pro_textgrad_candidate_update` diagnostic
      record. It reports `candidate_update_count=9`,
      `candidate_accepted_count=6`, `candidate_rejected_count=3`,
      `diagnostic_only_count=1`, and
      `candidate_acceptance_rate=0.6666666666666666`.
    - The best accepted record is now
      `s2pc_l1_runtime_matrix_gpt_oss_20b_12x3_seed11`, with matched initial
      loss `0.000112890954`, best loss `0.000111545213`, and final loss
      `0.000111545213`. The accepted `gpt_oss_20b` calibration-split baseline
      prompt remains very strong, and the L1 record only improves it by a small
      absolute margin under the current single model / scale / seed setting.
      The DeepSeek v4-flash calibration-split records remain accepted relative
      to the uncalibrated DeepSeek v4-flash held-out baseline, but their best
      losses remain around `0.0104` to `0.0111`.
    - The `structured_persona_parameter_patch` method is rejected by the runtime
      stability evidence: `gpt_oss_20b_runtime_prompt_patch_stability` records
      initial loss `0.000111404795`, candidate/runtime loss `0.005108707956`,
      and relative loss reduction `-45.052587741358`.
    - The S2PC L0 method record
      `s2pc_l0_current_policy_reaction_candidate` is accepted within the method
      gate with initial loss `0.15922332683`, candidate loss
      `0.010380967362`, final loss `0.010380967362`, and relative loss
      reduction `0.934802471669`.
    - The S2PC L0 runtime-effect record
      `s2pc_l0_current_policy_reaction_runtime_probe` is rejected within the
      method gate. It compares the matched `openai/gpt-oss-20b` 12x3
      calibration-split baseline against the Product run that actually consumes
      the S2PC candidate artifact; weighted JSD increases from
      `0.000112890954` to `0.000211185317`.
    - The S2PC L1 runtime-matrix record
      `s2pc_l1_runtime_matrix_gpt_oss_20b_12x3_seed11` is accepted within the
      method gate because at least one runtime candidate improves the matched
      held-out loss. The gate uses the best candidate result rather than
      averaging away rejected candidates, while still preserving full
      `candidate_count`, `improved_count`, and `regressed_count` accounting in
      the per-method record.
    - The S2PC L1 runtime-stability record
      `s2pc_l1_runtime_stability_gpt_oss_20b_c01` is rejected within the method
      gate. It records the repeat evidence for the currently best L1 candidate
      `c01` across `12x3 seed=11`, `12x3 seed=17`, and `16x3 seed=11`, and the
      current matrix status is `mixed` rather than `stable_improvement`.
    - The DeepSeek v4-pro TextGrad record is deliberately `diagnostic_only`.
      It has no policy-reaction held-out benchmark artifact, and its W3/W4 smoke
      already records initial loss `0.3003150770148567`, best loss
      `0.3003150770148567`, final loss `0.4522002190868819`, and a rejected
      candidate. The method gate therefore treats it as executable optimizer
      plumbing, not accepted policy-reaction calibration evidence.

12. **S2PC L0 deterministic calibration smoke**
    - The Research worktree now records
      `policy-reaction-s2pc-candidate-current-001` and
      `policy-reaction-s2pc-gate-current-001`.
    - S2PC L0 uses only deterministic semantic factor catalog matching,
      calibration-split residual mining, bounded parameter compilation, and a
      deterministic beam-search proxy score. It does not call an LLM, does not
      synthesize semantic factors with an LLM, and does not use held-out rows
      during candidate generation.
    - The candidate artifact is generated from
      `policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-calibration-split-initial-001`
      and records `residual_count=11`, `semantic_match_count=22`,
      `parameter_patch_count=44`, `beam_width=3`, and `candidate_count=3`.
      Its top beam candidate targets segment
      `fixed_income_inflation_stressed` and policy
      `food_subsidy_expansion`, with proxy score `4.254466026348`.
    - The gate reports initial loss `0.15922332683`, best loss
      `0.010380967362`, final loss `0.010380967362`,
      `candidate_accepted_count=1`, and `candidate_rejected_count=0`.
    - This result should be interpreted as S2PC L0 method evidence and gate
      wiring evidence. The held-out candidate benchmark is the recorded
      DeepSeek v4-flash calibration-split Product benchmark; it is not yet a
      fresh Product runtime run that consumes the S2PC prompt components. The
      result therefore supports the bounded claim that deterministic S2PC
      candidate artifacts can be generated, audited, and registered through the
      held-out method gate, not a claim that LLM-assisted or runtime-integrated
      S2PC has improved Product behavior.

13. **S2PC L0 runtime-effect probe**
    - Product now consumes the S2PC candidate artifact
      `policy-reaction-s2pc-candidate-current-001` at runtime through
      `--s2pc-candidate-artifact`. The Product manifest
      `llm-cohort-policy-local-gpt-oss-20b-12x3-calibration-split-s2pc-runtime-001`
      records `36` attempted local `openai/gpt-oss-20b` calls, `36`
      successful calls, `0` failed calls, and an explicit `s2pc_context`.
    - The exported prediction artifact
      `policy-reaction-segment-predictions-gpt-oss-20b-12x3-calibration-split-s2pc-runtime-001`
      covers all four official segments and is evaluated against the same
      held-out HTOPS/HPS evaluation projection as the matched baseline.
    - The S2PC runtime held-out benchmark
      `policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-calibration-split-s2pc-runtime-heldout-001`
      reports weighted JSD `0.00021118531661561824`, mean JSD
      `0.00064756581901641`, worst-segment JSD
      `0.0015928065281891066`, and segment rank correlation `1.0`.
    - The formal runtime-effect artifact
      `policy-reaction-s2pc-runtime-effect-gpt-oss-20b-12x3-calibration-split-heldout-001`
      compares this run with the matched calibration-split baseline
      `policy-reaction-official-segment-benchmark-gpt-oss-20b-12x3-calibration-split-heldout-001`.
      It records `overall_status=regressed`, baseline loss
      `0.000112890954`, S2PC runtime loss `0.000211185317`, absolute delta
      `-0.000098294363`, and relative loss reduction `-0.870701856842`.
    - This is the first direct Product-runtime attribution evidence for S2PC
      L0, and it is negative. It proves the S2PC candidate can be consumed and
      audited by Product, but the current single-segment deterministic candidate
      weakens held-out alignment relative to the already strong calibration-split
      baseline.

14. **S2PC L1 multi-candidate runtime matrix**
    - The Research worktree now records six explicit Product-runtime candidates
      derived from
      `policy-reaction-s2pc-l1-candidate-set-current-001`: `c01` through `c06`.
      Each candidate is exported as an auditable
      `policy-reaction-s2pc-candidate-v1` artifact, consumed by Product via
      `--s2pc-candidate-artifact`, and evaluated on the same held-out HTOPS/HPS
      projection as the matched `openai/gpt-oss-20b` 12x3 calibration-split
      baseline.
    - All six Product runs completed successfully with `36/36` successful calls
      and four covered official segments. The matrix artifact
      `policy-reaction-s2pc-runtime-effect-matrix-gpt-oss-20b-12x3-calibration-split-l1-heldout-001`
      records `candidate_count=6`, `improved_count=1`, and
      `regressed_count=5`.
    - The best candidate is
      `policy-reaction-s2pc-l1-candidate-set-current-001-c01`, which maps to the
      `fixed_income_inflation_stressed / food_subsidy_expansion` candidate. Its
      runtime-effect artifact
      `policy-reaction-s2pc-runtime-effect-gpt-oss-20b-12x3-calibration-split-l1-c01-heldout-001`
      records baseline loss `0.000112890954`, candidate loss `0.000111545213`,
      absolute delta `0.000001345741`, and relative loss reduction
      `0.011920716018`.
    - The remaining five candidates regress, with the worst candidate
      `c06` reaching held-out loss `0.01628069538`. The matrix therefore
      supports a bounded claim that multi-candidate runtime search can surface a
      locally improving candidate in the current setting, but it does not yet
      support any stability, robustness, or cross-seed generalization claim for
      S2PC L1.

15. **S2PC L1 best-candidate stability check**
    - The current best L1 candidate `c01` was re-run on two additional axes:
      `12x3 seed=17` and `16x3 seed=11`. Both Product runs completed
      successfully and produced held-out benchmark artifacts aligned with the
      same HTOPS/HPS evaluation projection used for the matched baselines.
    - The `12x3 seed=17` effect artifact
      `policy-reaction-s2pc-runtime-effect-gpt-oss-20b-12x3-calibration-split-c01-seed17-heldout-001`
      regresses from baseline loss `0.000111545213` to candidate loss
      `0.001179413326`, with relative loss reduction `-9.573410525838`.
    - The `16x3 seed=11` effect artifact
      `policy-reaction-s2pc-runtime-effect-gpt-oss-20b-16x3-calibration-split-c01-seed11-heldout-001`
      also regresses, from baseline loss `0.000109778219` to candidate loss
      `0.000136894753`, with relative loss reduction `-0.247011968684`.
    - The stability matrix
      `policy-reaction-s2pc-runtime-stability-gpt-oss-20b-calibration-split-c01-heldout-001`
      summarizes the three matched comparisons and records `effect_count=3`,
      `improved_count=1`, `regressed_count=2`, `overall_status=mixed`, and mean
      relative loss reduction `-3.269500592835`.
    - This result materially narrows the current claim boundary: the observed
      L1 improvement is real for one recorded setting, but it is not yet stable
      across the first seed/scale repeat axes.

16. **S2PC L1 search-policy ablation**
    - The Research worktree now records
      `policy-reaction-s2pc-l1-search-policy-ablation-current-001`, a
      retrospective held-out ablation over the six evaluated L1 candidates.
    - The best ablation policy is `beam_top1_direct`, which means the current
      positive signal already sits on the rank-1 beam candidate and does not
      require an oracle selector over the full beam.
    - All improving ablation slices point to the same candidate `c01`, which is
      also the best candidate for the `food_subsidy_expansion` policy group and
      the `fixed_income_inflation_stressed` segment group.
    - The negative-control side remains clearly negative: the best
      `baseline_no_new_support` group candidate is `c04`, but it still regresses
      with runtime loss `0.000904895192`; the best
      `working_family_price_stressed` segment candidate is `c03`, which
      regresses much more sharply with runtime loss `0.008484318228`.
    - This ablation supports a bounded design insight rather than an efficacy
      claim: under the current deterministic search space, useful signal is
      concentrated in one narrow branch instead of being broadly distributed
      across segments or policy families.

17. **S2PC L1 candidate-family narrowing**
    - The Research worktree now records
      `policy-reaction-s2pc-l1-family-narrowing-current-001`, which converts the
      current ablation result into an explicit next-step search-space reduction.
    - The retained family contains exactly one candidate:
      `policy-reaction-s2pc-l1-candidate-set-current-001-c01`. The narrowing
      rules are:
      `segment_allowlist=[fixed_income_inflation_stressed]`,
      `policy_allowlist=[food_subsidy_expansion]`, and `max_rank=1`.
    - This means the current positive signal is not merely “somewhere in the
      beam”; it collapses to one branch that is simultaneously rank-1, within
      the `food_subsidy_expansion` policy family, and within the
      `fixed_income_inflation_stressed` segment family. All other currently
      evaluated branches should be treated as lower-priority or negative-control
      search space for the next iteration.

18. **S2PC selector-free robustness**
    - The Research worktree now records
      `policy-reaction-s2pc-selector-free-robustness-current-001`, which asks a
      stricter question than retrospective oracle ablation: if Product simply
      applies the best deployable non-oracle selector, does that rule stay
      stable across repeats?
    - The chosen deployable selector is `beam_top1_direct`, which selects
      `policy-reaction-s2pc-l1-candidate-set-current-001-c01` without any
      held-out lookahead. However, the robustness artifact records
      `overall_status=mixed`, `repeat_count=3`, `improved_count=1`,
      `regressed_count=2`, and mean relative loss reduction
      `-3.269500592835`.
    - This sharply limits the current deployment claim. Although the direct
      selector agrees with the best observed single-run candidate, it is not yet
      robust enough to be treated as a stable Product-side selection rule.

19. **S2PC c01 local neighborhood search**
    - The Research worktree now records
      `policy-reaction-s2pc-c01-neighborhood-current-001`, which explores three
      local variants around the current best candidate `c01` without widening
      the search family. The variants adjust only the `fixed_income_inflation_stressed`
      / `food_subsidy_expansion` branch through small bounded changes to
      `household_budget_rigidity`, `response_temperature`,
      `prior_anchor_strength`, and `trust_multiplier`, plus corresponding
      segment-level prompt wording.
    - All three neighborhood variants regress on the same `12x3 seed=11`
      matched held-out comparison. The best local variant is `n01`, but it
      still worsens loss from baseline `0.000112890954` to `0.002266359458`.
      The other two variants are worse: `n02` reaches `0.011061938404` and
      `n03` reaches `0.008647272241`.
    - The neighborhood matrix
      `policy-reaction-s2pc-c01-neighborhood-matrix-gpt-oss-20b-12x3-heldout-001`
      records `candidate_count=3`, `improved_count=0`, `regressed_count=3`, and
      `overall_status=all_candidates_regressed`.
    - This negative result is useful. It suggests the current positive `c01`
      signal is not improved by straightforward local parameter nudging around
      the existing point. The next search step should therefore change the
      representation or selection logic rather than simply applying nearby
      scalar perturbations.

20. **S2PC sparse factor subset and selector redesign**
    - The Research worktree now records
      `policy-reaction-s2pc-c01-sparse-subset-current-001`, which converts the
      current `c01` branch into three sparse runtime candidates:
      `s01=household_only`, `s02=trust_only`, and `s03=core_pair_only`.
      This step asks whether the current positive signal survives after
      removing parts of the structured factor set, instead of continuing local
      scalar perturbation.
    - On the same matched `12x3 seed=11` held-out runtime comparison, the
      sparse-subset matrix
      `policy-reaction-s2pc-c01-sparse-subset-matrix-gpt-oss-20b-12x3-heldout-001`
      reports `candidate_count=3`, `improved_count=1`, and
      `regressed_count=2`. The unique improving subset is `s02`, whose
      candidate id is
      `policy-reaction-s2pc-c01-sparse-subset-current-001-s02`.
    - The `s02=trust_only` subset reproduces the current best observed loss:
      baseline `0.000112890954` versus sparse-subset runtime loss
      `0.000111545213`, a relative loss reduction of `0.011920716018`.
      By contrast, `s01=household_only` regresses sharply to `0.016544179765`,
      and `s03=core_pair_only` regresses to `0.009379081172`.
    - This narrows the current positive signal further. Under the current
      `c01` branch, the useful effect is concentrated in the
      `institutional_trust` factor subset, while the
      `household_budget_rigidity` patches appear harmful in this matched run.
    - The selector decision artifact
      `policy-reaction-s2pc-selector-redesign-current-001` therefore updates
      the current recommendation from `beam_top1_direct` to
      `sparse_subset_best_runtime_effect`, with recommended candidate
      `policy-reaction-s2pc-c01-sparse-subset-current-001-s02`. This remains a
      bounded held-out decision artifact rather than a claim of stable
      deployment readiness.

21. **S2PC `trust_only` repeat validation**
    - The Research and Product worktrees now extend repeat validation directly
      on `policy-reaction-s2pc-c01-sparse-subset-current-001-s02`, without
      returning to the full `c01` patch bundle. Two matched repeat axes were
      added: `12x3 seed=17` and `16x3 seed=11`.
    - On `12x3 seed=17`, the `trust_only` candidate reaches exact parity with
      the matched calibration-split baseline: baseline
      `0.000111545213`, runtime loss `0.000111545213`,
      `relative_loss_reduction=0.0`, and `overall_status=no_change`.
    - On `16x3 seed=11`, the same `trust_only` candidate regresses from
      baseline `0.000109778219` to `0.000427401852`, with
      `relative_loss_reduction=-2.893321059682`.
    - The stability matrix
      `policy-reaction-s2pc-runtime-stability-gpt-oss-20b-calibration-split-s02-heldout-001`
      therefore records `effect_count=3`, `improved_count=1`,
      `regressed_count=1`, `no_change_count=1`, `overall_status=mixed`, and
      mean relative loss reduction `-0.960466781221`.
    - This is still useful evidence: the sparse selector removed the large
      negative contribution from the household-related patches, but it still
      fails to convert the current local signal into a repeat-stable update
      rule. The selector recommendation must therefore be downgraded from
      “prefer sparse subset” to “repeat evidence still insufficient”.

22. **S2PC `trust_only` parameter-level decomposition**
    - To avoid continuing broad search on a weakly stable family, the Research
      worktree next decomposes `trust_only` into two parameter-level variants:
      `p01=prior_anchor_only` and `p02=trust_multiplier_only`. This is a more
      conservative representation test than factor-level search because it asks
      whether one of the two remaining trust parameters is sufficient by
      itself.
    - On the matched `12x3 seed=11` held-out comparison, the parameter-subset
      matrix
      `policy-reaction-s2pc-s02-parameter-subset-matrix-gpt-oss-20b-12x3-heldout-001`
      records `candidate_count=2`, `improved_count=1`, `regressed_count=1`,
      and best candidate
      `policy-reaction-s2pc-s02-parameter-subset-current-001-p02`.
    - The `p01=prior_anchor_only` variant regresses materially from baseline
      `0.000112890954` to `0.00100526197`, with relative loss reduction
      `-7.90471678038`.
    - The `p02=trust_multiplier_only` variant improves slightly from baseline
      `0.000112890954` to `0.000112585562`, with relative loss reduction
      `0.002705185757`.
    - This matters because the best parameter-level variant is still weaker
      than the earlier `s02=trust_only` result (`0.000111545213`). Under the
      current stop-loss rule, this means the new representation does not earn a
      repeat expansion: it finds a weaker single-run positive point rather than
      a more stable or stronger update rule.

23. **Route-B repeat-aware robust-score baseline**
    - The Research worktree now defines a Route-B robust objective artifact,
      which scores a candidate by mean held-out loss, instability penalty,
      worst-case loss, and a small complexity penalty over repeat axes.
    - Applying this score to the current
      `policy-reaction-s2pc-c01-sparse-subset-current-001-s02` candidate yields
      `policy-reaction-route-b-robust-score-s02-current-001`, with
      `improved_count=1`, `regressed_count=1`, `no_change_count=1`, and
      `robust_score=0.004793128859`.
    - The current `s02=trust_only` candidate is marked
      `overall_status=blocked_by_stop_loss` under Route B. This is an
      intentional change of evaluation standard rather than a contradiction of
      the earlier single-run positive result: Route B requires repeat-aware
      robustness and therefore rejects candidates that only improve on one axis.
    - This artifact becomes the baseline selection surface for the next stage.
      Future Route-B candidate search should compare against this robust-score
      baseline rather than against single-run held-out loss alone.

24. **Route-B generation-0 single-axis prefilter**
    - The Research and Product worktrees then ran a first bounded Route-B
      generation-0 population over the current `trust_only` family, using four
      structured candidates that only adjust `prior_anchor_strength` and
      `trust_multiplier` under a small-population search policy.
    - The resulting matrix
      `policy-reaction-route-b-generation0-matrix-gpt-oss-20b-12x3-heldout-001`
      records `candidate_count=4`, `improved_count=1`,
      `regressed_count=3`, and best candidate
      `policy-reaction-route-b-generation0-current-001-g04`.
    - Three candidates regress sharply:
      `g01 -> 0.008989250943`,
      `g02 -> 0.017589373491`,
      `g03 -> 0.001626070675`.
      Only `g04` improves, from baseline `0.000112890954` to
      `0.000112017956`, with relative loss reduction
      `0.007733108557`.
    - This is still not enough to continue. The best generation-0 candidate is
      weaker than the earlier `s02=trust_only` single-run result
      (`0.000111545213`, relative reduction `0.011920716018`), so Route-B
      generation 0 does not clear the prefilter threshold for repeat expansion.
    - The correct reading is that Route B now has a runnable search surface and
      prefilter mechanism, but its first small population did not yet produce a
      candidate strong enough to justify the more expensive repeat-aware stage.

25. **Route-B generation-1 mechanism-level variable redefinition**
    - Route-B next replaces patch-level perturbations with a small
      mechanism-level discrete population. The new generation-1 search no
      longer searches raw `prior_anchor_strength` and `trust_multiplier`
      adjustments directly. Instead, each candidate compiles a bounded
      mechanism profile over four higher-level variables:
      `anchor_regime`, `trust_mode`, `uncertainty_mode`, and `focus_mode`.
    - The resulting matrix
      `policy-reaction-route-b-generation1-matrix-gpt-oss-20b-12x3-heldout-001`
      records `candidate_count=4`, `improved_count=0`,
      `regressed_count=4`, `overall_status=all_candidates_regressed`, and best
      candidate `policy-reaction-route-b-generation1-current-001-h03`.
    - The four matched held-out losses are all materially worse than the
      baseline `0.000112890954`:
      `h01 -> 0.01481642642`,
      `h02 -> 0.030763241376`,
      `h03 -> 0.011526513378`,
      `h04 -> 0.086475999947`.
      Their relative loss reductions are all strongly negative, ranging from
      `-101.103073813771` to `-765.013547753751`.
    - This matters because it rules out a second hypothesis: the weakness of
      Route-B generation-0 was not merely caused by over-local patch variables.
      Moving the search surface up to mechanism-level, Product-compilable
      discrete controls still fails to produce even a single candidate that
      beats the calibration-split baseline on the matched `12x3 seed=11` axis.
    - Under the current stop-loss rule, Route-B generation 1 should therefore
      stop immediately rather than expand into repeat evaluation. The present
      Route-B family has now failed both patch-level and mechanism-level
      bounded search on the current public-data held-out objective.

26. **LCDU L0 latent-constraint single-axis prefilter**
    - After Route-B stop-loss, the Research worktree switches update
      representation rather than searcher family. LCDU L0 defines candidates as
      `latent_state_updates + constraint_program`, then compiles them back into
      Product-compatible candidate prompt components and bounded parameter
      patches.
    - The first single-axis matrix
      `policy-reaction-lcdu-l0-matrix-gpt-oss-20b-12x3-heldout-001`
      records `candidate_count=4`, `improved_count=1`,
      `regressed_count=3`, and best candidate
      `policy-reaction-lcdu-l0-current-001-l04`.
    - The matched baseline loss remains `0.000112890954`. Candidate losses are:
      `l01 -> 0.000527330903`,
      `l02 -> 0.000132334881`,
      `l03 -> 0.004477834086`,
      `l04 -> 0.000107036888`.
    - `l04` therefore improves over baseline with
      `relative_loss_reduction=0.051855935383`, which is materially stronger
      than the earlier best single-run `s02=trust_only`
      (`0.011920716018`).
    - This is the first evidence after Route-B stop-loss that a new update
      representation, rather than a new search policy over old variables, can
      open a stronger single-axis candidate.

27. **LCDU L0 `l04` repeat validation**
    - Because `l04` beats both the calibration-split baseline and the earlier
      `s02` single-run point on `12x3 seed11`, it is expanded to the matched
      repeat axes `12x3 seed17` and `16x3 seed11`.
    - The resulting stability artifact
      `policy-reaction-lcdu-l0-stability-gpt-oss-20b-calibration-split-l04-heldout-001`
      records `effect_count=3`, `improved_count=1`,
      `regressed_count=2`, `no_change_count=0`, `overall_status=mixed`, and
      mean relative loss reduction `-0.817727824504`.
    - On `12x3 seed17`, `l04` regresses from matched baseline
      `0.000111545213` to `0.00038917493`, with
      `relative_loss_reduction=-2.488943374402`.
    - On `16x3 seed11`, `l04` is close to baseline but still regresses:
      `0.000109778219 -> 0.000111545213`,
      `relative_loss_reduction=-0.016096034493`.
    - The correct interpretation is therefore conservative:
      LCDU L0 has stronger single-axis promise than Route-B and stronger
      single-run performance than `s02`, but it still has not crossed the
      stability threshold required for a method claim.

28. **LCDU L1 `l04` 局部 refinement 失败**
    - To test whether the `l04` signal could be stabilized by refining the
      latent/constraint compiler without changing the representation family, the
      Research worktree next constructs a small LCDU L1 neighborhood around
      `l04`: softer trust suppression, trust floor guard, gap-guarded balance,
      and cost-relief conservative floor.
    - The resulting matrix
      `policy-reaction-lcdu-l1-matrix-gpt-oss-20b-12x3-heldout-001`
      records `candidate_count=4`, `improved_count=0`,
      `regressed_count=4`, `overall_status=all_candidates_regressed`, and best
      candidate `policy-reaction-lcdu-l1-current-001-r03`.
    - All four candidates are materially worse than the matched baseline
      `0.000112890954`:
      `r01 -> 0.004611744283`,
      `r02 -> 0.005171818286`,
      `r03 -> 0.001998036129`,
      `r04 -> 0.009697271256`.
    - This matters because it narrows the interpretation of LCDU further:
      LCDU L0's `l04` is still a meaningful representation-level signal, but
      the immediate local refinement directions tried here do not improve it.
      In other words, the `l04` point is not yet a smooth neighborhood that can
      be exploited by small latent/constraint adjustments.
    - Under the current stop-loss policy, LCDU should not continue with this
      exact L1 neighborhood family. The preserved lesson is positive at the
      representation level and negative at the local-refinement level.

29. **LCDU L2 segment-guard family**
    - Because the L0 repeat regression is concentrated mainly in
      `working_family_price_stressed`, the next step does not continue numeric
      local refinement. Instead, LCDU L2 introduces segment-guard candidates
      that explicitly preserve baseline-like behavior for unstable segments,
      especially `working_family_price_stressed`, while keeping the original
      `l04` latent direction.
    - The resulting matrix
      `policy-reaction-lcdu-l2-matrix-gpt-oss-20b-12x3-heldout-001`
      records `candidate_count=4`, `improved_count=1`,
      `regressed_count=3`, and best candidate
      `policy-reaction-lcdu-l2-current-001-g04`.
    - Candidate losses are:
      `g01 -> 0.000115805628`,
      `g02 -> 0.000116997178`,
      `g03 -> 0.000114027528`,
      `g04 -> 0.000111436163`.
      Only `g04` improves over baseline, with
      `relative_loss_reduction=0.012886692445`.
    - This matters because it shows segment-guard reconstruction is a more
      promising direction than LCDU L1's local neighborhood search: it recovers
      a positive candidate while keeping all losses near the baseline regime
      instead of collapsing into large regressions.
    - However, `g04` still remains weaker than LCDU L0's original `l04`
      (`0.000107036888`). Under the current gate, LCDU L2 therefore does not
      earn repeat expansion yet. The retained lesson is that segment-guarded
      reconstruction is directionally better than local refinement, but this
      first L2 family has not surpassed the current best single-axis point.

30. **LCDU L3 working-family guard threshold reconstruction**
    - Because LCDU L2 suggested that segment-guard reconstruction was the right
      direction, but its first family stayed weaker than `l04`, the next step
      narrows the search surface further. LCDU L3 keeps the original `l04`
      latent direction fixed and reconstructs only the
      `working_family_price_stressed` guard thresholds.
    - The resulting matrix
      `policy-reaction-lcdu-l3-matrix-gpt-oss-20b-12x3-heldout-001`
      records `candidate_count=4`, `improved_count=1`,
      `regressed_count=3`, and best candidate
      `policy-reaction-lcdu-l3-current-001-h02`.
    - Candidate losses are:
      `h01 -> 0.000116658591`,
      `h02 -> 0.000098795927`,
      `h03 -> 0.000115428295`,
      `h04 -> 0.000113707732`.
      Only `h02` improves, with
      `relative_loss_reduction=0.124855230105`.
    - This matters because `h02` is stronger than the prior best LCDU point
      `l04 = 0.000107036888`. At this stage, LCDU L3 becomes the first
      post-Route-B family that opens a meaningfully better single-axis
      candidate than every earlier S2PC, Route-B, or LCDU point on matched
      `12x3 seed11`.

31. **LCDU L3 `h02` repeat validation**
    - Because `h02` clearly beats the `12x3 seed11` baseline, it is expanded to
      the matched repeat axes `12x3 seed17` and `16x3 seed11`.
    - The resulting stability artifact
      `policy-reaction-lcdu-l3-stability-gpt-oss-20b-calibration-split-h02-heldout-001`
      records `effect_count=3`, `improved_count=3`,
      `regressed_count=0`, `no_change_count=0`,
      `overall_status=stable_improvement`, and mean relative loss reduction
      `0.214472380187`.
    - On `12x3 seed11`, `h02` improves from baseline
      `0.000112890954` to `0.000098795927`.
    - On `12x3 seed17`, `h02` further improves from matched baseline
      `0.000111545213` to `0.000081085178`, with
      `relative_loss_reduction=0.2730734316`.
    - On `16x3 seed11`, `h02` improves from matched baseline
      `0.000109778219` to `0.000082828931`, with
      `relative_loss_reduction=0.245488478856`.
    - This is the first update family in the current policy-reaction line that
      crosses the repeat gate. The conservative claim boundary remains the same:
      this is stable local held-out public-data alignment improvement, not
      field validation or real-world policy forecast proof.

32. **LCDU L3 `h02` explanation ablation**
    - After `h02` becomes the first stable-improvement candidate, the next step
      is no longer broader search. Instead, the Research worktree constructs an
      explanation-oriented ablation family around `h02`:
      `prompt_only_guard`, `anchor_only_guard`, `qualitative_guard`, and
      `no_working_family_override`.
    - The resulting matrix
      `policy-reaction-lcdu-l3-ablation-matrix-gpt-oss-20b-12x3-heldout-001`
      records `candidate_count=4`, `improved_count=1`,
      `regressed_count=3`, and best candidate
      `policy-reaction-lcdu-l3-ablation-current-001-a02`.
    - Candidate losses are:
      `a01 -> 0.000114027528`,
      `a02 -> 0.000111545213`,
      `a03 -> 0.000117419158`,
      `a04 -> 0.000113104793`.
      Only `a02=anchor_only_guard` remains positive, with
      `relative_loss_reduction=0.011920716018`.
    - This evidence materially narrows the interpretation of `h02`:
      `working_family` prompt text by itself is not sufficient, and a purely
      qualitative guard is also not sufficient. The strongest signal appears
      only when the calibrated numeric guard anchor and the segment-level guard
      prompt are combined in the full `h02` candidate.
    - The practical conclusion is that `h02` should not be summarized as
      “better wording.” It is better described as a guarded latent program with
      a numerically constrained segment anchor, where prompt and anchor work
      together and the anchor carries the larger standalone contribution.

33. **LCDU L3 `a02=anchor_only_guard` repeat check**
    - Because `a02=anchor_only_guard` is the only ablation candidate that
      remains positive on the `12x3 seed11` single axis, it is expanded to the
      matched repeat axes `12x3 seed17` and `16x3 seed11`.
    - The resulting stability artifact
      `policy-reaction-lcdu-l3-a02-stability-gpt-oss-20b-calibration-split-heldout-001`
      records `effect_count=3`, `improved_count=1`,
      `regressed_count=1`, `no_change_count=1`,
      `overall_status=mixed`, and mean relative loss reduction
      `-0.001391772825`.
    - On `12x3 seed17`, `a02` becomes `no_change`:
      `0.000111545213 -> 0.000111545213`.
    - On `16x3 seed11`, `a02` regresses:
      `0.000109778219 -> 0.000111545213`,
      `relative_loss_reduction=-0.016096034493`.
    - This closes the explanation loop more tightly. The calibrated
      `working_family` anchor is necessary enough to preserve a weak
      single-axis signal, but it is not sufficient to explain `h02`'s stable
      improvement. The stable effect therefore still appears to depend on the
      full prompt-plus-anchor guarded program rather than the anchor alone.

34. **LCDU L3 `h02` segment-level attribution**
    - To identify where `h02`'s repeat improvement actually comes from, the
      Research worktree compares segment-level JSD deltas between the matched
      calibration-split baseline and the accepted `h02` candidate across the
      three validated runs.
    - The dominant positive contribution comes from
      `general_population_cost_pressure`. On `12x3 seed11`, its segment JSD
      improves from `0.000078310643` to `0.000057776999`; on `12x3 seed17`, it
      improves from `0.000077576479` to `0.00003027243`; and on `16x3 seed11`,
      it improves from `0.000077576479` to `0.000032980456`.
    - A smaller but still positive contribution comes from
      `working_family_price_stressed`. Its JSD improves from
      `0.000158547816` to `0.000152546376` on `12x3 seed11`, stays flat on
      `12x3 seed17`, and improves from `0.000155521754` to `0.000152546376` on
      `16x3 seed11`.
    - `fixed_income_inflation_stressed` remains unchanged across these runs,
      while `low_income_food_insecure` is the main drag term on `16x3 seed11`,
      where its segment JSD worsens from `0.001442162108` to
      `0.001592806528`.
    - The correct interpretation is therefore not “all segments improve.”
      Instead, `h02` works mainly by consistently reducing error on
      `general_population_cost_pressure`, with secondary support from
      `working_family_price_stressed`, while still leaving
      `low_income_food_insecure` as a residual weakness.

35. **LCDU L3 prompt-anchor interaction ablation**
    - After the single-component ablation shows that `anchor_only_guard` is not
      stable by itself, the next step tests whether `h02`'s success depends on
      prompt-anchor interaction rather than either side alone.
    - The interaction matrix
      `policy-reaction-lcdu-l3-interaction-matrix-gpt-oss-20b-12x3-heldout-001`
      evaluates four combinations:
      `i01=numeric_prompt+numeric_anchor`,
      `i02=numeric_prompt+qualitative_anchor`,
      `i03=qualitative_prompt+numeric_anchor`,
      `i04=qualitative_prompt+qualitative_anchor`.
    - Candidate losses are:
      `i01 -> 0.000092334757`,
      `i02 -> 0.000111545213`,
      `i03 -> 0.000116658591`,
      `i04 -> 0.000097128778`.
      The corresponding relative loss reductions are
      `0.18208895689`,
      `0.011920716018`,
      `-0.033374126773`,
      and `0.139623021018`.
    - The best candidate is `i01`, which is stronger than the current accepted
      `h02` single-axis point (`0.000098795927`). `i04` also remains clearly
      positive, while `i02` collapses to the same weak single-axis signal as
      `anchor_only_guard`, and `i03` regresses.
    - This sharply narrows the mechanism story. The stable `h02` effect is not
      explained by anchor alone, and numeric specificity on only one side is
      not enough. The strongest evidence now points to a synchronized,
      numerically specified prompt-anchor guarded program, with the prompt and
      anchor reinforcing each other rather than acting as separable patches.

36. **LCDU L3 `i01` repeat validation**
    - Because `i01=numeric_prompt+numeric_anchor` is the strongest interaction
      candidate on the `12x3 seed11` axis, it is expanded to the matched repeat
      axes `12x3 seed17` and `16x3 seed11`.
    - The resulting stability artifact
      `policy-reaction-lcdu-l3-i01-stability-gpt-oss-20b-calibration-split-heldout-001`
      records `effect_count=3`, `improved_count=3`,
      `regressed_count=0`, `no_change_count=0`,
      `overall_status=stable_improvement`, and mean relative loss reduction
      `0.14574759582`.
    - On `12x3 seed17`, `i01` improves from matched baseline
      `0.000111545213` to `0.000098650179`, with
      `relative_loss_reduction=0.115603643512`.
    - On `16x3 seed11`, `i01` improves from matched baseline
      `0.000109778219` to `0.000094458648`, with
      `relative_loss_reduction=0.139550187059`.
    - This matters because it confirms the interaction result is not just a
      stronger single-axis point. A synchronized numeric prompt plus numeric
      anchor remains stable across the same repeat axes used for `h02`.
    - The current comparison should still stay conservative: `i01` is the
      strongest single-axis interaction point, while `h02` retains the stronger
      mean repeat improvement. Together they show that the LCDU L3 mechanism is
      robust at the level of synchronized prompt-anchor guarded programs rather
      than fragile single-component patches.

37. **Low-income residual weakness diagnosis**
    - A dedicated residual-weakness artifact
      `policy-reaction-lcdu-l3-low-income-residual-weakness-current-001`
      diagnoses the remaining `low_income_food_insecure` mismatch after `h02`
      and `i01`.
    - The weakness is not a rank-ordering failure: rank correlation remains
      `1.0` throughout. It is a distribution-shape problem with the same bias
      signature across runs:
      `baseline_no_new_support` is over-predicted,
      `cash_cost_of_living_rebate` is under-predicted,
      and `food_subsidy_expansion` is slightly over-predicted.
    - The main drag point is `h02_16x3_seed11`, where the segment JSD worsens
      from baseline `0.001442162108` to `0.001592806528`.
    - This matters because it gives a concrete repair direction:
      raise `cash_cost_of_living_rebate` while trimming
      `baseline_no_new_support` and lightly trimming
      `food_subsidy_expansion` for `low_income_food_insecure`.

38. **LCDU L4 low-income repair family**
    - Guided by the residual-weakness artifact, the next family adds a targeted
      `low_income_food_insecure` repair layer on top of the accepted `h02`
      candidate while leaving the previously stabilized
      `general_population_cost_pressure` and `working_family_price_stressed`
      structure unchanged.
    - The resulting single-axis matrix
      `policy-reaction-lcdu-l4-low-income-repair-matrix-gpt-oss-20b-12x3-heldout-001`
      records `candidate_count=4`, `improved_count=1`,
      `regressed_count=3`, and best candidate
      `policy-reaction-lcdu-l4-low-income-repair-current-001-r04`.
    - Candidate losses are:
      `r01 -> 0.005628433024`,
      `r02 -> 0.000115428295`,
      `r03 -> 0.009133432652`,
      `r04 -> 0.00011253572`.
      Only `r04` remains positive, with
      `relative_loss_reduction=0.003146700319`.
    - This is a useful negative result. Strong numeric low-income repairs
      destabilize the already accepted LCDU L3 structure, while a softer
      qualitative repair only preserves a near-baseline outcome and still stays
      far weaker than `h02` or `i01`.
    - Under the current gate, LCDU L4 low-income repair should stop at
      single-axis prefilter. The residual weakness is real, but direct repair on
      that segment currently costs more than it returns.

39. **Axis-level internal-generalization bridge**
    - To test internal generalization without changing the task, a new
      axis-level ingestion artifact
      `policy-reaction-htops-2506-public-axis-ingestion-001`
      re-aggregates the same HTOPS/HPS 2506 public-use source onto
      Product-compatible demographic axes:
      `income_band`,
      `employment_status`,
      `household_with_children`,
      `food_sufficiency_status`,
      and `price_stress_level`.
    - The bridge is explicit about canonical mapping. Public-use survey values
      do not natively match Product persona labels, so the ingestion step
      normalizes them into the Product axis schema instead of silently relying
      on string equality.
    - This matters because it creates a same-task alternate-schema evaluation
      surface. It does not yet claim any improvement or generalization result;
      it only establishes that official observed distributions and Product
      outputs can be aligned under a finer demographic partition.

40. **LCDU L3 axis-level benchmark diagnostics**
    - Two real Product segment reports are exported from the accepted `LCDU L3`
      candidates:
      `segment-policy-report-lcdu-l3-h02-001`
      and
      `segment-policy-report-lcdu-l3-i01-001`.
      They are then compared against the official axis-level ingestion through
      axis benchmarks:
      `policy-reaction-axis-benchmark-lcdu-l3-h02-001`
      and
      `policy-reaction-axis-benchmark-lcdu-l3-i01-001`.
    - Both benchmarks pass contract coverage with
      `coverage_rate=1.0` and `matched_segment_count=14`.
      Product still emits three extra axis segments not observed on the
      official side:
      `employment_status=hourly_or_part_time_worker`,
      `employment_status=mixed_employment_status`,
      and
      `food_sufficiency_status=enough_but_less_varied`.
    - Aggregate alignment is mixed rather than strong:
      for `h02`,
      `weighted_choice_distribution_jsd=0.009779743208737248`,
      `mean_choice_distribution_jsd=0.021510287202774567`,
      `segment_rank_correlation=0.5`,
      `worst_segment_rank_correlation=-1.0`;
      for `i01`,
      `weighted_choice_distribution_jsd=0.009715886100179951`,
      `mean_choice_distribution_jsd=0.02147064327852375`,
      `segment_rank_correlation=0.5`,
      `worst_segment_rank_correlation=-1.0`.
    - The strongest axis-level weakness is stable across both candidates:
      worst JSD occurs at `price_stress_level=high`
      (`0.14925228029562396`), while the worst rank failure occurs at
      `income_band=low` (`-1.0`).
    - This is not a positive generalization result. The bridge succeeds, but
      the current axis-level diagnostics show that `LCDU L3` still loses
      ordering fidelity on parts of the finer demographic schema. The current
      claim should stay narrow: same-task alternate-schema evaluation is now
      auditable, and it reveals where internal generalization remains weak.

41. **LCDU L3 axis-level weakness attribution**
    - A dedicated weakness artifact
      `policy-reaction-axis-weakness-lcdu-l3-current-001`
      compares the two accepted candidates `h02` and `i01` directly on their
      axis-level benchmark outputs.
    - The result is stable across both candidates:
      `persistent_worst_jsd_segment = price_stress_level=high`
      with mean JSD
      `0.14925228029562396`,
      and
      `persistent_worst_rank_segment = income_band=low`
      with mean rank correlation
      `-1.0`.
    - This matters because it shows the finer-schema weakness is not random
      candidate noise. Both accepted LCDU L3 variants inherit the same two weak
      points: a distribution-shape error on high price stress and an ordering
      failure on low income.

42. **LCDU L3 axis-level held-out split extrapolation**
    - The official HTOPS/HPS two-way row split is projected onto the same
      Product-compatible axis schema through
      `policy-reaction-htops-2506-axis-split-ingestion-001`,
      yielding
      `policy-reaction-htops-2506-axis-evaluation-ingestion-001`
      as a held-out axis-level observed surface.
    - The accepted candidates are re-benchmarked against that held-out axis
      split:
      `policy-reaction-axis-benchmark-lcdu-l3-h02-evaluation-split-001`
      and
      `policy-reaction-axis-benchmark-lcdu-l3-i01-evaluation-split-001`.
    - The held-out results stay very close to the full-data axis benchmarks.
      For `h02`:
      `weighted_choice_distribution_jsd=0.010083181769177024`,
      `mean_choice_distribution_jsd=0.022050398910805732`,
      `segment_rank_correlation=0.5`,
      `worst_segment_rank_correlation=-1.0`.
      For `i01`:
      `weighted_choice_distribution_jsd=0.0100197976214031`,
      `mean_choice_distribution_jsd=0.022011023947825364`,
      `segment_rank_correlation=0.5`,
      `worst_segment_rank_correlation=-1.0`.
    - The dominant weak points are unchanged on the held-out axis split:
      worst JSD remains `price_stress_level=high`
      (`0.14714363159110094`),
      and worst rank failure remains `income_band=low`
      (`-1.0`) for both accepted candidates.
    - This is still not a positive generalization result, but it is a stronger
      negative diagnostic than before. The same-task finer-schema weakness is
      not an artifact of full-data aggregation; it persists on the held-out row
      split as well.

43. **LCDU L5 axis-guided repair family**
    - Because the axis-level weakness and held-out split extrapolation both
      identify the same two failure points, the next family lifts the repair
      target from single named segments to Product-compatible axis selectors:
      `income_band=low`
      and
      `price_stress_level=high`.
    - Product runtime is extended so calibration candidate prompt components can
      match not only `persona.segment` but also demographic selectors of the
      form `axis=value`. This makes axis-guided runtime probes executable rather
      than purely descriptive.
    - The first `LCDU L5` family generates four candidates:
      `x01` income-low rank guard,
      `x02` high-price shape guard,
      `x03` dual-axis soft guard,
      `x04` dual-axis numeric guard.
    - All four candidates are evaluated on the matched `12x3 seed11`
      calibration-split held-out benchmark. The resulting matrix
      `policy-reaction-lcdu-l5-axis-guided-repair-matrix-gpt-oss-20b-12x3-heldout-001`
      records
      `candidate_count=4`,
      `improved_count=0`,
      `regressed_count=4`,
      and
      `overall_status=all_candidates_regressed`.
    - Candidate losses are:
      `x01 -> 0.000117419158`,
      `x02 -> 0.000117419158`,
      `x03 -> 0.000115057521`,
      `x04 -> 0.000885217439`.
      The best candidate is `x03`, but it still regresses relative to baseline,
      with
      `relative_loss_reduction=-0.019191688343`.
    - This is a useful stop-loss result. Moving from accepted segment-level
      guards to direct axis-level runtime guards is executable, but the first
      axis-guided repair family does not improve held-out alignment and can
      degrade it sharply when the numeric guard is too strong (`x04`).
    - Under the current gate, `LCDU L5` should not enter repeat validation.
      The next step should not be “more of the same” on axis-level prompt
      patches. The evidence now points to a representation mismatch between the
      accepted segment-level runtime and the finer demographic control surface.

44. **Latent response program L0 prefilter**
    - After `LCDU L5` fails, the next route lifts the repair object one level
      higher. Instead of adding another axis-level prompt or anchor patch, the
      new `LRP L0` family defines four latent response variables:
      `baseline_inertia`,
      `relief_preference`,
      `price_stress_reactivity`,
      and
      `targeting_sensitivity`,
      then compiles selector-based regime rules and response constraints back
      into Product-compatible runtime candidates.
    - The first `LRP L0` family generates four candidates:
      `p01` low-income compensatory program,
      `p02` high-price reactive program,
      `p03` dual-axis balanced program,
      `p04` dual-axis targeted program.
    - All four candidates are evaluated on the matched
      `gpt-oss-20b 12x3 seed11` calibration-split held-out benchmark. The
      resulting matrix
      `policy-reaction-lrp-l0-matrix-gpt-oss-20b-12x3-heldout-001`
      records
      `candidate_count=4`,
      `improved_count=2`,
      `regressed_count=2`,
      and
      `overall_status=candidate_improvements_available`.
    - Candidate losses are:
      `p01 -> 0.000111545213`,
      `p02 -> 0.000111774841`,
      `p03 -> 0.002574409167`,
      `p04 -> 0.003360798171`.
      The best candidate is `p01`, with
      `relative_loss_reduction=0.011920716018`.
    - This is a useful representation result, but not yet a method result.
      `LRP L0` does show that a higher-level response program can produce
      non-regressing candidates and avoids the uniform collapse seen in `LCDU
      L5`. But the best improvement is only a weak single-axis gain, still well
      below the accepted `LCDU L3 h02/i01` level, and two candidates regress
      sharply.
    - Under the current gate, `LRP L0` has earned follow-up diagnosis but not
      repeat validation. The next question is not whether “higher-level
      representation exists,” but whether a tighter `LRP` family can convert
      this weak single-axis signal into a candidate that actually challenges
      `LCDU L3`.

45. **Latent response program L1 narrowed family**
    - `LRP L1` narrows the `L0` family to the two weakly improving branches
      only: `p01` low-income compensatory and `p02` high-price reactive. The
      design goal is not to repeat `L0`, but to reduce the global coupling that
      produced the sharp `p03/p04` collapses and test whether a lighter family
      can amplify the surviving signal.
    - The first `LRP L1` family generates four candidates:
      `q01` low-income milder compensation,
      `q02` low-income rank-only minimal,
      `q03` high-price shape-only softened,
      `q04` dual-axis light hybrid.
    - All four candidates are evaluated on the matched
      `gpt-oss-20b 12x3 seed11` calibration-split held-out benchmark. The
      resulting matrix
      `policy-reaction-lrp-l1-matrix-gpt-oss-20b-12x3-heldout-001`
      records
      `candidate_count=4`,
      `improved_count=3`,
      `regressed_count=1`,
      and
      `overall_status=candidate_improvements_available`.
    - Candidate losses are:
      `q01 -> 0.000111545213`,
      `q02 -> 0.000112816892`,
      `q03 -> 0.000111545213`,
      `q04 -> 0.003266484198`.
      The best candidates are `q01` and `q03`, both tied at
      `relative_loss_reduction=0.011920716018`.
    - This is a useful narrowing result, but still not a step-up result.
      Compared with `LRP L0`, the narrowed family does reduce the number of
      catastrophic regressions, but it does not improve beyond the earlier weak
      single-axis ceiling. `q01` only matches `p01`, `q03` only matches that
      same ceiling, and `q02` is nearly neutral.
    - Under the current gate, `LRP L1` still should not enter repeat
      validation. The evidence supports keeping the “higher-level
      representation” route alive as a research option, but not escalating this
      specific family as a new mainline challenger to `LCDU L3`.

46. **Round1 route A: Segment Program Search**
    - The first segment-level synchronized program family generates four
      candidates:
      `s01` soft_guard_family,
      `s02` mixed_numeric_qualitative_family,
      `s03` segment_crossover_family,
      `s04` selective_anchor_heavy_family.
    - On the matched `gpt-oss-20b 12x3 seed11` held-out benchmark, the route
      matrix
      `policy-reaction-segment-program-l0-matrix-gpt-oss-20b-12x3-heldout-001`
      records
      `candidate_count=4`,
      `improved_count=1`,
      `regressed_count=3`,
      and
      `overall_status=candidate_improvements_available`.
    - Candidate losses are:
      `s02 -> 0.000111545213`,
      `s03 -> 0.000116997178`,
      `s04 -> 0.000132498489`,
      `s01 -> 0.003543626925`.
      The best candidate is `s02`, with
      `relative_loss_reduction=0.011920716018`.
    - This route remains alive, but only as a weak-signal route. It can still
      beat the held-out baseline at a single point, but it does not exceed the
      already known weak-signal ceiling and is clearly below `LCDU L3`.

47. **Round1 route B: LRP stronger family**
    - The first stronger `LRP round1` family generates four candidates:
      `r01` rank-first compensatory bridge,
      `r02` shape-first relief stabilizer,
      `r03` dual-axis pressure release,
      `r04` targeted anti-inertia extreme.
    - On the matched `gpt-oss-20b 12x3 seed11` held-out benchmark, the route
      matrix
      `policy-reaction-lrp-round1-l0-matrix-gpt-oss-20b-12x3-heldout-001`
      records
      `candidate_count=4`,
      `improved_count=0`,
      `regressed_count=4`,
      and
      `overall_status=all_candidates_regressed`.
    - Candidate losses are:
      `r02 -> 0.000114027528`,
      `r04 -> 0.000298154757`,
      `r01 -> 0.000567826985`,
      `r03 -> 0.000862567119`.
    - This route fails the round1 gate. The stronger latent family does not
      improve on the earlier `LRP` weak-signal line; instead it turns into
      broad regression. Under the current stop-loss rule, this route should be
      stopped rather than deepened.

48. **Round1 route C: Constraint Program**
    - The first population-level constraint-program family generates four
      candidates:
      `c01` relief_floor_low_income_guard,
      `c02` price_stress_distribution_guard,
      `c03` dual_axis_balanced_population_program,
      `c04` strict_targeted_population_program.
    - On the matched `gpt-oss-20b 12x3 seed11` held-out benchmark, the route
      matrix
      `policy-reaction-constraint-program-l0-matrix-gpt-oss-20b-12x3-heldout-001`
      records
      `candidate_count=4`,
      `improved_count=0`,
      `regressed_count=4`,
      and
      `overall_status=all_candidates_regressed`.
    - Candidate losses are:
      `c01 -> 0.000113104793`,
      `c02 -> 0.000115805628`,
      `c04 -> 0.000513038271`,
      `c03 -> 0.006564134024`.
    - This route also fails the round1 gate. The most conservative candidate
      is only slightly worse than baseline, but the family as a whole shows
      that moving directly to population-level constraints is not enough, by
      itself, to produce a stronger held-out candidate.

49. **Round1 route D: Prototype / Retrieval Program**
    - The first prototype-program family generates four candidates:
      `r01` accepted_rank_anchor,
      `r02` accepted_with_weak_positive_bridge,
      `r03` failure_aware_dual_axis_bridge,
      `r04` tri_family_conservative_program.
    - On the matched `gpt-oss-20b 12x3 seed11` held-out benchmark, the route
      matrix
      `policy-reaction-prototype-program-l0-matrix-gpt-oss-20b-12x3-heldout-001`
      records
      `candidate_count=4`,
      `improved_count=2`,
      `regressed_count=2`,
      and
      `overall_status=candidate_improvements_available`.
    - Candidate losses are:
      `r02 -> 0.000111545213`,
      `r03 -> 0.000111545213`,
      `r01 -> 0.000113397501`,
      `r04 -> 0.000114360157`.
      The best candidates are `r02` and `r03`, both tied at
      `relative_loss_reduction=0.011920716018`.
    - This route is the strongest of the new non-LCDU routes in round1, but it
      still only reaches the same weak single-axis ceiling as segment-program
      and earlier `LRP` families. It qualifies as a keep/observe route, not a
      promotion route.

50. **Round1 route-level conclusion**
    - Round1 was explicitly designed to compare four orthogonal route families
      under the same single-axis held-out gate, not to overfit one line.
    - The route-level outcome is:
      - `keep/observe`: segment-program, prototype-program
      - `stop`: stronger LRP family, constraint-program
    - Most importantly, no route in round1 exceeds `LCDU L3`. The best new
      candidates all stop at the same weak single-axis ceiling
      (`0.000111545213`, `relative_loss_reduction=0.011920716018`), which is
      well below the already accepted `LCDU L3 h02/i01` line.
    - This is a real conclusion, not an incomplete search. The current round1
      evidence says the search space is not empty, but the strongest new routes
      still do not challenge the existing mainline.

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
- CIRCE can generate deterministic S2PC semantic-structured persona calibration
  candidate artifacts from calibration-split residuals and register them through
  the held-out policy-reaction method gate with explicit claim boundaries.
- CIRCE can inject an S2PC candidate artifact into the Product LLM runtime,
  export the resulting segment prediction artifact, and evaluate the matched
  held-out runtime effect without treating a negative result as improvement.
- CIRCE can run a bounded S2PC L1 multi-candidate runtime search and identify a
  locally improving candidate under the current `openai/gpt-oss-20b` 12x3
  calibration-split held-out setting while preserving rejected-candidate
  accounting.
- CIRCE can attach repeat-aware stability evidence and search-policy ablation
  artifacts to S2PC L1 runtime results instead of reporting the single positive
  setting in isolation.
- CIRCE can derive an explicit narrowed candidate family and a selector-free
  robustness artifact from the current S2PC L1 evidence chain.
- CIRCE can test local neighborhood variants around the current best S2PC
  candidate and retain negative local-search results as part of the evidence
  chain instead of smoothing them away.
- CIRCE can decompose the current best S2PC branch into sparse semantic-factor
  subsets, identify whether the held-out signal survives that sparsification,
  and emit an explicit selector-redesign artifact instead of relying on an
  implicit direct-choice rule.
- CIRCE can run repeat validation directly on the narrowed `trust_only`
  sparse-selector candidate and preserve `improved` / `no_change` /
  `regressed` outcomes in one matched stability matrix.
- CIRCE can decompose the narrowed `trust_only` selector further into
  parameter-level variants and preserve both weak positive and negative
  findings without automatically promoting the weaker positive variant to the
  next repeat stage.
- CIRCE can score a policy-reaction candidate under a repeat-aware robust
  objective and explicitly block a single-run-positive but repeat-unstable
  candidate through stop-loss logic.
- CIRCE can generate a bounded Route-B small-population candidate set and
  preserve full prefilter evidence when most candidates regress and the best
  candidate still fails to clear the repeat-expansion threshold.
- CIRCE can bridge official HTOPS/HPS public-use observations and Product
  segment-policy outputs onto a shared axis-level demographic schema for
  same-task internal-generalization diagnostics.
- CIRCE can localize persistent axis-level LCDU weaknesses and verify that the
  dominant finer-schema failure points remain on the held-out row split.
- CIRCE can execute axis-guided LCDU runtime probes by matching calibration
  candidate components against Product demographic selectors as well as fixed
  segment ids.

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
- No broad LCDU generalization claim is made from the current axis-level
  benchmark bridge; it is same-task alternate-schema diagnostics, and current
  rank alignment remains mixed.
- No LCDU finer-schema robustness claim is made from the current axis-level
  split extrapolation; the held-out split preserves the same weak points rather
  than resolving them.
- No positive LCDU L5 axis-guided repair claim is made from the first runtime
  matrix; all four candidates regress on the matched held-out benchmark.
- No stable or accepted latent-response-program effectiveness claim is made
  from the current `LRP L0` evidence. The first family has two weak single-axis
  improvements and two regressions, but no repeat validation or held-out gate
  acceptance.
- No prompt/persona patch gate claim is made beyond the recorded Product
  scenario, model, cohort scale, public-source release, and held-out split.
- No LLM-assisted S2PC, retrieval-augmented S2PC, or Product runtime S2PC
  effectiveness claim is made from the L0 deterministic artifact.
- No broad S2PC Product-runtime effectiveness claim is made from the current
  evidence. L0 runtime remains regressed, and L1 currently shows only one
  improving candidate out of six under a single model / scale / seed setting.
- No stable, cross-seed, cross-scale, or cross-provider S2PC L1 advantage claim
  is made from the current runtime matrix.
- No stable claim is made for the current best L1 candidate `c01`; the first
  repeat matrix is mixed with two regressions out of three runs.
- No deployable selector claim is made for the current `beam_top1_direct` rule;
  its selector-free robustness artifact is mixed rather than stable.
- No local-neighborhood improvement claim is made around `c01`; the first three
  bounded perturbation variants all regress relative to the matched baseline.
- No stability claim is yet made for the redesigned sparse selector; the
  `trust_only` subset improves on the matched `12x3 seed=11` run, but repeat
  validation has not yet been completed for that redesigned selector.
- No deployable claim is made for the redesigned `trust_only` sparse selector;
  after repeat validation it remains mixed rather than stable.
- No further repeat-expansion claim is made for the current parameter-level
  `trust_only` decomposition; its best candidate is weaker than the earlier
  `trust_only` single-run result and therefore does not clear the stop-loss
  threshold for continued investment.
- No Route-B effectiveness claim is made yet beyond the current baseline
  scoring scaffold; the current `s02=trust_only` candidate is blocked by the
  new repeat-aware objective and does not constitute a successful Route-B
  search result.
- No Route-B generation-0 continuation claim is made from the current
  prefilter matrix; its best single-run candidate remains weaker than the
  earlier `s02=trust_only` result and therefore does not earn repeat budget.

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
