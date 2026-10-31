# Stage 6A adaptive investigation foundation

[FOUNDATIONAL_LAWS.md](FOUNDATIONAL_LAWS.md) remains authoritative and unchanged.
[STAGE6A_RESEARCH.md](STAGE6A_RESEARCH.md) records comparative evidence and decisions.
This is working orchestration, not a qualification of independent discovery.

## Data and execution

`investigation.Investigations` reuses `Memory`, original-verified `build_context`,
replaceable inference adapters and Decimal/SI `tools.compute`. Existing `ask` and
its strict source-answer contract remain available. The new path can generate
hypotheses/solutions/interpretations with empty citation lists; none is promoted
to a fact. Supplied citations still require exact source ID, SHA, span and quote.
Imported/retrieved material and model output never enter the service dispatcher.
The plain-JSON candidate protocol has actual field instructions, no placeholder
source/code example. Invalid raw prefixes, SHA, truncation and repetition markers
remain evidence, not progress. No model tools, arbitrary Python or shell are added.

Transparent routing handles explicit calculations directly, without a model.
Otherwise a source retrieval step precedes direct generation or synthesis for an
explicit exploration request. This is capability/request routing, not a learned
semantic task classifier. User-approved DAG plans can combine retrieval,
reconciliation, generation, synthesis, critique, calculations, finite constraints,
independent numeric verification/selection and interpreted result relationships.
Dependencies and variable bindings support multi-step computations. General
semantic planning, autonomous experimental design and MCTS are not implemented.
Model-proposed plans remain suggestions, not automatically granted execution.

`constraints` enumerates explicitly supplied finite numeric domains with allowlisted
relations and the existing arithmetic evaluator. Its mixed-radix cursor continues
without replaying previous assignments; returned `complete:false` explicitly means
only a search chunk was checked. Limits (8 variables, 32 domain values/constraints,
10,000 assignments and 128 returned solutions per chunk) are operational budgets,
not a universal logical solver or a ceiling on eventual cognitive capability.
The owner can continue with the returned offset. Dimensional or empirical claims
are not established by satisfying numeric premises.

The independently controlled `verify` step computes a numeric expectation from
trusted plan inputs and compares the candidate's answer; candidates cannot choose
or change this criterion. `select` returns only candidates satisfying those checks.
Critique and citation validity alone never certify correctness, semantic entailment,
scientific feasibility or originality. Test-feedback expected values are tool
observations; evaluation of unaided model performance must not supply gold answers
as input. Simulated dependency markers propagate to derived results.

## Persistence and interruption

Two dynamically registered contracts, `investigations` and `investigation_events`,
use the existing append-only record/audit registry. No schema migration or parallel
memory database is added. Existing project IDs associate investigations with the
project/evidence infrastructure. Every plan/control version, started step, result,
failure, rejected alternative and interpreted relationship remains in history.
New record references are checked on append/import; portable validation also
rechecks citation/context quotes from restored originals. Unknown/missing references
and corrupted quotes fail. Small-pilot export/actual restoration is tested; this
is not full-library portable release acceptance.

A finite `Budget` controls steps/model calls/time per invocation (defaults 4/2/30s).
Progress is not globally capped by the old 1–3 answer retry limit or six literal
steps. Explicit continuation can renew budgets and change plans/configuration.
A plan chunk has at most 128 steps; append/replacement chunks retain old history.
Context overflow fails explicitly rather than silently inventing or truncating
citations. Adapter context/output/timeout and worker OS resource bounds remain.
No infinite automatic budget renewal or low-probability idea rejection is added.

The started checkpoint commits before executing a step. Completion appends its
observation and next state atomically. A hard crash preserves `running` and the
started event, never a fabricated result. Explicit user resume/redirection is
required for in-flight/paused/cancelled work. Pure local computations/retrieval or
model calls may be repeated after interruption (at least once); no external action
or exactly-once inference-cost guarantee exists. Historical plans and completed
step IDs cannot be silently repurposed; changed work needs new IDs.

Execution does not hold the writer lock during inference. Control updates clear
the active token; a late result is retained as discarded and cannot overwrite the
new goal/control state. Cooperative cancellation is checked at safe boundaries,
inside finite constraint chunks and by supported inference transport. Existing
retrieval/SQLite/source reads and individual pure calculations are not instantly
interruptible; over-budget work stops at its next safe boundary. This is not a
hard wall-clock guarantee for blocking host filesystem calls. Desktop termination
is still distinct from durable investigation pause/resume.

`complete` means all steps in the current plan finished, **not** that every
candidate/check passed, a finite search was exhaustive, or a discovery is true.
Inspect each check's `passed`, enumeration `complete`, simulation and epistemic
markers. Incorrect candidates and unsuccessful checks remain visible.

## Authority and integrations

`authority.DecisionAuthority` is the narrow interface for ordinary explicitly
approved control operations and future privileged authentication. Privileged
override always fails closed. Authentication, enrollment, command normalization
and privileged lifecycle remain unspecified; no activation phrase parser exists.
Ordinary `approved:true` flags follow existing trusted service semantics and are
not proof of owner identity. An owner can pause, cancel, resume or redirect a plan,
change its goal and renew a slice without altering underlying evidence. Initial
plan approval delegates its pure reasoning steps; each thought/step does not prompt
again. This does not grant permission to any new external operation.

Shared service operations: `investigation_create/get/history/control/run`.
CLI: `investigation ACTION PARAMETERS_JSON`, optionally using the existing isolated
`--models-directory`/`--managed` adapter and explicit model settings. Model preparation
occurs only after run approval. No new desktop panel is included; the service is
available to future UI work through its existing protected operation boundary.
Existing claim overrides remain scoped assumptions, not privileged owner control.

Example on a NEW pilot data directory, not the real literary library:

```bash
cd /home/mint/VECTOR/vector
PYTHONPATH=src python3 -B -m vector_core --data-dir /absolute/new/pilot investigation create '{"goal":"Compute a pilot product","calculation":{"operation":"arithmetic","parameters":{"expression":"19*31"}},"approved":true}'
PYTHONPATH=src python3 -B -m vector_core --data-dir /absolute/new/pilot investigation run '{"id":"ID_FROM_CREATE","approved":true}'
PYTHONPATH=src python3 -B -m vector_core --data-dir /absolute/new/pilot investigation history '{"id":"ID_FROM_CREATE"}'
```

## Five concerns and remaining qualification

1. Evidence-only restriction: separate proposal path allows unsupported ideas,
   explicitly unverified, without weakening the existing source-answer validator.
2. Fixed budgets: renewable finite slices/chunks, explicit overflow, resumable work;
   old adapter limits and deterministic routing remain current operational limits.
3. Literal planning: dependency DAGs, alternatives, objective checks, feedback and
   redirection work; semantic goal decomposition and automatic strategy learning
   still depend on future model/design qualification.
4. Narrow override: general investigation control plus a fail-closed authority
   interface. No authenticated privileged owner override or identity design yet.
5. Cancellation/resumption: durable checkpoints, retained failures, safe-boundary
   pause/cancel, stale-result discard and crash recovery; no instantaneous all-op
   interruption or reversal of prior external actions is claimed.

Stored investigation feedback and retrieval are persistent experience, not changes
to model weights or proven cumulative cognitive improvement. No training occurred.
Real-model and deterministic test results must be reported separately, including
weak-model/schema failures, invalid/repeated proposals and blocked environments.

History is paginated; current working results are limited to the selected plan
chunk. History correlation still scans a run's records and is not qualified for
very large investigation histories. Code and mathematical premises, not self-rated
confidence, define the currently supported objective checks. A completed workflow
with a failed numeric check must never be advertised as a solved problem.

Reconciliation uses a bounded 8192-byte evidence budget independent of the model
window. Retrieval reserves generation space with a minimum usable source-context
budget; the final generated prompt still must fit the adapter's strict byte limit.
Thus no-model evidence reconciliation is available under default configuration,
while an undersized model window still fails explicitly rather than accepting
truncated/unsupported generation.
