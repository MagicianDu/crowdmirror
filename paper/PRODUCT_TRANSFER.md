# CIRCE Product Transfer

## Transfer Principle

Research outputs are useful to CrowdMirror only when they become explicit,
auditable Product evidence. A CIRCE artifact can support a Product trust surface
only if the artifact records mode, model, command, metrics, artifact paths, and
claim boundary. If any of those fields are missing, the Product report must show
the evidence as missing or unsupported.

The Product LLM choice result is a separate claim surface from the Research
method evidence. A Research manifest may document that CIRCE ran in `local` mode,
but a Product pricing canary using synthetic personas must remain `missing` for
its own LLM choice calibration unless a manifest validates that exact product
scenario, model, metric, and scope.

## Evidence Classes

| Evidence class | Manifest mode | Product use | Claim boundary |
| --- | --- | --- | --- |
| Dry-run plumbing | `dry-run` | Shows that scripts, manifests, and report wiring execute | No model-quality or customer-behavior claim |
| Local model canary | `local` | Shows a local LLM path, model id, metrics, and artifacts under a bounded setup | local-model calibration evidence; not cross-provider evidence |
| Live model run | `live` | May support a provider-specific benchmark claim when metrics and artifacts are committed | live-model evidence; not cross-domain generalization |
| Product scenario calibration | `local` or `live` plus matching product scenario metadata | May support a bounded Product calibration card | Only valid for the recorded scenario, model, and metric |

## Product Surfaces

Research artifacts should map to these Product surfaces:

- Evidence card: manifest schema, run id, lane, mode, status, metrics, artifact references, and claim boundary.
- Claim boundary panel: visible wording that separates method evidence from product-scenario calibration.
- Report export: machine-readable `research_evidence` with unsupported warnings when the manifest scope does not validate the current Product scenario.
- Operator review: warnings that explain when a customer-facing claim is blocked.
- Competitive explanation: bounded method differentiation against prompt-only persona demos, not a broad superiority claim.

## Current Local Gemma Canary

The current committed local Research artifact is
`local-gemma-w3w4-canary-001`.

It records:

- lane: `causal`
- mode: `local`
- model: `google/gemma-4-31b`
- total LLM calls: `4`
- initial loss: `0.4055871739728345`
- best loss: `0.4055871739728345`
- improvement ratio: `0.0`
- claim boundary: `local-model calibration evidence; not cross-provider evidence`

This artifact can support a Product statement that the Research line has a
local-model causal-calibration canary with auditable metrics and artifacts. It
cannot support model superiority, product pricing calibration, or customer
forecast accuracy because the run did not improve the loss and does not validate
the pricing scenario used by CrowdMirror.

When Product attaches this manifest to a pricing LLM canary, the report should
show a `research_evidence` card with `mode=local`, but the Product LLM choice
summary must remain `missing` for calibration evidence until a matching
Product-scenario calibration manifest exists.

## No-Go Claims

- Do not claim CCF-A readiness from the current local canary.
- Do not claim calibrated pricing simulation from the W3/W4 transport-choice
  manifest.
- Do not claim cross-provider evidence from a local Gemma run.
- Current local evidence is not customer-specific forecast accuracy evidence and
  does not replace user research.
- Do not claim improvement when `improvement_ratio` is `0.0`.
- Do not hide the scope mismatch between a Research benchmark lane and a Product
  business scenario.
- Do not use dry-run manifests for model-quality, prediction, or superiority
  claims.
