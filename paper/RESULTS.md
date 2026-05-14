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
