# DIFFERENTIATION: Calibrated Generative Agents for Computational Social Science

## What Exists vs. What's Missing

| Thread | What Exists | What's Missing |
|--------|-------------|----------------|
| 1. Generative Agents | Believable agents at scale (25→1M); qualitative emergence; broad domain coverage | Closed-loop calibration against empirical data; population-level loss optimization; principled persona search |
| 2. Prompt Optimization | TextGrad/DSPy/ProTeGi/GEPA optimizers for compound LLM systems; proven on NLP benchmarks | Application to distributional/population losses; persona-generator optimization; calibration of behavioral simulators |
| 3. DCM + LLM | LLMs as choice predictors; comparison to MNL/mixed logit; hybrid text-utility models | Systematic calibration of LLM choice probabilities; elasticity validation; counterfactual transfer tests |
| 4. Silicon Samples | Diagnosis of LLM mis-alignment (WEIRD bias, joint collapse, minority under-representation) | Optimization-based fix (not fine-tuning); principled persona→distribution theory; joint-distribution repair |
| 5. Evaluation | Fragmented metrics across communities; OpinionQA/GlobalOpinionQA for marginals | Unified protocol covering marginals + joints + subgroups + counterfactuals + temporal; no optimization target |

## Our Unique Contribution

### Core Innovation: Calibration-as-Optimization for LLM Population Simulators

We are the first to:

1. **Frame LLM social simulation as a calibration problem** — treating persona prompts, agent scaffolds, and decision-policy prompts as parameters of a population-level generative model with an explicit distributional loss.

2. **Apply prompt optimization to population-alignment objectives** — adapting TextGrad/DSPy-style optimizers from accuracy targets to KL/Wasserstein/multicalibration targets over choice distributions.

3. **Propose a unified evaluation protocol** — synthesizing metrics from survey methodology, DCM, NLP calibration, fairness (multicalibration), causal inference, and ABM validation into a single coherent framework.

4. **Bridge generative agents and discrete choice models** — making LLM simulators produce calibrated choice probabilities comparable to mixed-logit outputs, enabling downstream policy analysis (elasticities, welfare, counterfactuals).

5. **Provide a cheap alternative to interview-based persona generation** — where Park 2024 requires 2-hour interviews per agent, we achieve comparable calibration via prompt optimization against aggregate survey data.

### Contribution Map by Thread

```
Thread 1 (Generative Agents)
  └─ We add: calibration loop, population loss, principled evaluation

Thread 2 (Prompt Optimization)
  └─ We add: novel target (distributional loss), novel domain (social simulation)

Thread 3 (DCM + LLM)
  └─ We add: systematic calibration method, head-to-head with mixed logit on proper metrics

Thread 4 (Silicon Samples)
  └─ We add: optimization-based fix for documented mis-alignment, joint-distribution repair

Thread 5 (Evaluation)
  └─ We add: unified protocol that is both evaluation framework AND optimization target
```

## Potential Reviewer Objections & Responses

### Objection 1: "This is just prompt engineering with extra steps"

**Response:** Prompt engineering is manual and targets qualitative believability. We formalize the problem as statistical estimation: the "parameters" are prompt components, the "likelihood" is a population-alignment loss, and the "optimizer" is a principled search algorithm with convergence properties. The distinction is analogous to hand-tuning neural network weights vs. gradient descent — same space, fundamentally different methodology and guarantees.

### Objection 2: "LLMs are not identified — you can't do inference with them"

**Response:** We do not claim the LLM simulator is a structural model with identified parameters in the econometric sense. We claim it is a *calibrated predictive simulator* — analogous to a well-tuned random forest for choice prediction. Its value is in (a) cold-start prediction where no historical data exists for the specific scenario, (b) counterfactual exploration where structural assumptions are too strong, and (c) generating hypotheses for subsequent empirical testing. We explicitly benchmark against identified DCMs and report where each excels.

### Objection 3: "The calibration will overfit to training marginals"

**Response:** We address this via (a) train/test splits on both questions and demographic cells; (b) regularization in the optimizer (early stopping, prompt-complexity penalties); (c) explicit out-of-distribution evaluation (held-out subgroups, counterfactual scenarios, temporal holdout); (d) reporting joint-distribution metrics that are not directly optimized when only marginals are in the loss.

### Objection 4: "Why not just fine-tune the LLM on survey data?"

**Response:** Fine-tuning (a) requires model access (not available for frontier APIs), (b) is expensive and non-portable across model versions, (c) risks catastrophic forgetting of general capabilities, and (d) conflates the persona-generation and decision-policy components. Prompt optimization is model-agnostic, cheap, modular, and interpretable — the optimized prompts can be inspected, transferred, and composed.

### Objection 5: "N=1000 survey respondents can't calibrate a simulator for 300M people"

**Response:** We leverage the same statistical logic as survey methodology: a well-designed sample of 1,000–2,000 respondents, properly weighted, estimates population marginals to ±2–3pp. Our calibration target is the *weighted empirical distribution*, not individual responses. We report effective sample size, calibration uncertainty, and sensitivity to sample composition. Moreover, the LLM's pre-training provides a strong prior; calibration adjusts this prior, not builds from scratch.

### Objection 6: "Evaluation on OpinionQA-style benchmarks is too easy / not realistic"

**Response:** OpinionQA is our *starting point*, not our endpoint. We additionally evaluate on (a) revealed-preference choice data (not just stated opinions), (b) experimental data with known treatment effects (counterfactual recovery), (c) panel data with temporal dynamics, and (d) domain-specific DCM datasets (transportation mode choice, product choice). We propose these harder evaluations as a contribution to the field.

### Objection 7: "The base model will change and invalidate your calibration"

**Response:** This is a real limitation we acknowledge. We mitigate by (a) reporting calibration transfer across 3+ base models (GPT-4o, Claude 3.5, Llama 3), (b) proposing a lightweight re-calibration protocol (10% of original optimization cost), and (c) framing calibration as a recurring process analogous to survey weighting — it must be refreshed, not done once.

### Objection 8: "This doesn't advance social science theory"

**Response:** We position our contribution as *methodological infrastructure* for CSS, not as a substantive social-science finding. Analogously, mixed logit did not discover new preferences — it provided a better tool for measuring them. Our calibrated simulator enables social scientists to (a) pilot experiments cheaply, (b) explore counterfactuals, (c) generate hypotheses, and (d) augment small samples — all with quantified reliability.

## Positioning Statement (for paper introduction)

> Large language models can simulate human social behavior, but uncalibrated simulations are unreliable — they over-represent majority opinions, collapse joint distributions, and produce mis-calibrated choice probabilities. We introduce **[System Name]**, the first framework that treats LLM-based population simulation as a calibration problem: we optimize persona-generation and decision-policy prompts against empirical population distributions using text-gradient methods, evaluate with a unified protocol spanning marginal, joint, subgroup, and counterfactual alignment, and demonstrate that calibrated LLM simulators match or exceed mixed-logit baselines on choice prediction while enabling zero-shot counterfactual exploration. Our framework bridges generative agents (architecture), prompt optimization (method), discrete choice models (evaluation standard), and computational social science (application domain) into a coherent methodology for building trustworthy population behavior simulators.

## Key Differentiators Summary

| Dimension | Prior Work | Our Work |
|-----------|-----------|----------|
| Objective | Believability / accuracy | Population-distribution alignment |
| Optimization | Manual prompt design | Automated text-gradient optimization |
| Evaluation | Marginals only / qualitative | Unified: marginals + joints + subgroups + counterfactuals |
| Baseline comparison | None or naive | Mixed logit, hierarchical Bayes DCM |
| Persona generation | Fixed templates / interviews | Optimized prompt programs |
| Portability | Single model | Cross-model transfer + re-calibration protocol |
| Output | Demonstrations | Calibrated choice probabilities with uncertainty |
| Use case | Exploration / storytelling | Policy analysis / experiment piloting / augmentation |
