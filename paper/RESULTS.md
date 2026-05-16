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
