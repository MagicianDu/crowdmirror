# CIRCE Theory Notes

## Definitions

Let `x` denote an evaluated social-simulation scenario. A scenario includes the
choice context, intervention or control condition, agent-facing prompt context,
and any domain configuration needed to replay the lane.

Let `a` denote the micro-level action or choice target for `x`. Depending on the
benchmark lane, `a` can be an observed choice, a semi-synthetic choice label, or
a probability target over the choice set.

Let `z` denote the macro-level emergence target for `x`. It can be a trajectory,
an endpoint statistic, or a vector of aggregate dynamics produced by an ABM,
semi-synthetic generator, or archived benchmark reference.

Let `theta` denote the simulator state being calibrated. In CIRCE this includes
the prompt template, model configuration, parser, sampling controls, update
history, and lane-specific calibration settings.

Let `m` denote the evidence manifest for a candidate update. The manifest records
the mode, status, command, configuration, model/provider when applicable, seed,
metrics, artifact paths, and claim boundary. A candidate update has no paper or
Product claim status unless its manifest is complete and inspectable.

## Joint Calibration Objective

CIRCE evaluates accepted candidate updates with the weighted joint objective:

```text
L_joint(theta, m) = w_c L_choice(theta; x, a) + w_e L_emerge(theta; x, z)
```

`L_choice` measures micro-level choice mismatch or causal-choice calibration
error. `L_emerge` measures macro-level emergence distortion against the declared
trajectory or aggregate reference. The weights `w_c >= 0` and `w_e >= 0` are
declared before the run and are not retuned after observing the result.

The manifest term is not a soft penalty in this objective. `L_manifest(m)` is a
hard acceptance constraint: it must be zero, meaning the manifest passes the
required completeness and inspectability checks, before the candidate update can
enter a paper claim, Product evidence card, trust explanation, or customer-facing
claim boundary. If `L_manifest(m) != 0`, or if required manifest fields are
missing, the candidate update is rejected for claim use even when `L_choice` or
`L_emerge` improves. CIRCE therefore does not rely on a small `w_m` weight to
trade away auditability.

For an accepted update from `theta_t` to `theta_{t+1}`, the rule is:

```text
L_manifest(m_{t+1}) = 0
and
L_joint(theta_{t+1}, m_{t+1}) <= L_joint(theta_t, m_t) - epsilon
```

where `epsilon > 0` is fixed before the run. Dry-run manifests can satisfy the
manifest constraint only for deterministic plumbing claims; they do not enter
model-quality paper or Product claims.

The technical contribution is not raw prompt optimization. CIRCE treats
TextGrad-style feedback as a candidate generator inside an acceptance-gated
population calibration loop: an LLM proposes a prompt update, the simulator
evaluates the candidate on declared counterfactual evidence, and the system
accepts the candidate only when the measured population loss improves under the
same benchmark configuration. Rejected candidates are retained as negative
evidence rather than silently applied.

Prompt updates are represented as structured patches over explicit simulator
components, such as `global_instruction`, `segment_prompt`, `persona_prompt`,
`policy_interpretation_prompt`, `calibration_anchor`, and `response_contract`.
The patch generator can be TextGrad, an LLM critic, a residual-rule generator,
or a search procedure, but it is not allowed to directly overwrite the whole
simulator prompt as an uninspected string. Each patch records its target,
operation, source split, reason, expected effect, and supporting residuals. A
patch generated from evaluation targets is inadmissible; evaluation evidence is
used only by the acceptance gate. This makes automated prompt refinement
fine-grained and reversible while preserving the same acceptance rule as other
CIRCE updates.

PopulationBench-lite is the current reviewer-facing benchmark gate for this
claim. It requires distributional choice fit, counterfactual direction,
segment-level stability, and manifest auditability. Passing the gate can support
a bounded local-method claim; it does not establish field validity or
customer-scenario forecasting accuracy.

## Assumptions

1. The benchmark lane declares `x`, `a`, `z`, metric definitions, weights,
   threshold `tau`, and acceptance tolerance `epsilon` before evaluating a
   candidate update.
2. `L_choice` and `L_emerge` are non-negative and finite for every admissible
   candidate update.
3. The acceptance rule compares a candidate update to the previous accepted
   simulator state under the same lane, mode, metric definitions, and fixed
   weights.
4. The prompt or simulator update operator can change `theta` without changing
   the benchmark target `a` or `z` for the lane being evaluated.
5. Manifest validation is deterministic for a given `m` and checks at least
   mode, status, command, configuration, metrics, artifact paths, model/provider
   context when applicable, and claim boundary.
6. A candidate with an incomplete or non-inspectable manifest is inadmissible for
   paper and Product claims, regardless of the measured choice or emergence
   losses.

## Proposition 1

Suppose the initial accepted state has finite objective value `J_0 =
L_joint(theta_0, m_0)`, the stopping threshold is `tau >= 0`, and every accepted
update in a produced accepted-update sequence satisfies the manifest constraint
plus the `epsilon` acceptance rule:

```text
J_{t+1} <= J_t - epsilon
```

for a fixed `epsilon > 0` whenever `J_t > tau`. For any sequence that continues
to produce accepted updates under this rule, the sequence can contain at most
the following number of accepted updates before its accepted objective is at or
below threshold `tau`:

```text
ceil(max(J_0 - tau, 0) / epsilon)
```

Candidate updates with incomplete manifests are not counted as accepted updates
and cannot extend the accepted sequence.

This proposition does not guarantee that the update operator can always find another accepted candidate.
It also does not guarantee optimizer convergence or objective reachability; it is only an accounting bound on sequences that already satisfy the acceptance rule.

## Proof Sketch

Because `L_choice` and `L_emerge` are non-negative and the weights are
non-negative, every admissible joint objective value is non-negative. The
manifest condition filters the sequence to accepted updates only; it does not
contribute a soft loss that can be traded against metric improvement.

If `J_0 <= tau`, the run already satisfies the threshold and needs no accepted
improvement update. Otherwise, after one accepted update the objective is at most
`J_0 - epsilon`. After `k` accepted updates it is at most `J_0 - k epsilon`.
The first `k` satisfying `J_0 - k epsilon <= tau` is at most
`ceil((J_0 - tau) / epsilon)`. Therefore a sequence that keeps producing
accepted updates under the rule cannot have more than that many above-threshold
accepted updates. The statement is conditional on accepted updates existing; it
does not assert that the candidate generator will find them. Because incomplete
manifests never enter the accepted sequence, they cannot weaken this bound.

## Product Transfer

The formal objects above map directly to Product trust surfaces, but only after
the manifest constraint is satisfied.

`x` becomes the scenario context shown in a report evidence card. `a` becomes the
micro-choice fit or preference-alignment field. `z` becomes the macro-emergence
or aggregate-risk field. `theta` becomes the simulator configuration and update
history that explain why a recommendation differs from prompt-only persona
generation. `m` becomes the evidence card itself: mode, model/provider, command,
metrics, artifacts, and claim boundary.

The joint objective supports a trust explanation: CIRCE evaluates both
individual choice fit and group-level emergence distortion before accepting a
claim-bearing update. The hard manifest constraint supports the Product claim
boundary: if the manifest is incomplete, missing artifacts, dry-run-only for a
model-quality claim, or outside its declared mode, the report must mark the
recommendation as evidence-limited instead of presenting it as customer proof.

## Limits

Proposition 1 is an optimization accounting result over accepted updates. It
does not prove real-world behavioral validity. It does not prove cross-domain
generalization. It does not prove customer forecast accuracy. It does not prove
live-model superiority.

Those claims require separate evidence: validated benchmark manifests, external
or field validation where appropriate, and mode-specific local or live artifacts.
The theory artifact only states how CIRCE defines admissible claim-bearing
updates and why incomplete manifests cannot be repaired by a small soft penalty.
