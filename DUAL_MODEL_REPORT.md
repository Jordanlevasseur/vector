# Dual local model integration — measured qualification

Baseline: `12a03c5`. This report distinguishes implemented control flow,
explicit simulated tests, real local generation, and unqualified reasoning.

## Outcome

The backend and existing desktop now support model A, model B and structured
sequential collaboration, with persistent selections and recoverable stage
records. **Full real-model collaboration is not qualified and VECTOR is not
release-ready.** The current hardware stopped a 2B trial under its resource
protection. The real 0.5B model restated the logic question rather than solving it.
Neither valid JSON nor two-model agreement certifies an answer.

Final source/installed suite counts, installation checkpoint and final desktop
measurements are recorded below after closing verification.

## Actual local models

- A: `qwen2.5-coder:0.5b`, in `/usr/share/ollama/.ollama/models`.
  Actual runtime manifest digest: `4ff64a7f502a08b7616edb8ca0a79eb1853fc363d842b7df4b46915d11a3fb09`.
- B: `vector-qwen35-local:2b-q4_k_m`, in the existing
  `/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-qwen35-evaluation-20261031/candidate-models` store.
  Manifest digest: `12aa08322906e5b057c85898dfc236f7a11e8fe39a1ea50b7ebbc00193ef6f7a`.
  GGUF SHA-256: `9a3d0aa6c920f096441139b6a254542da855223fdad06855ea00c6c087fd713d`.
- Both complete dependency graphs passed the existing streamed SHA-256 checks.
  The installed private runtime reports Ollama `0.40.12`. No model/runtime was
  downloaded, replaced, updated or substituted. B is the previously imported
  text-only GGUF package; this does not qualify full multimodal capabilities.

## Implementation and reuse

`model_routing.py` is the new orchestration layer over existing adapters,
application operations, context/semantic retrieval, scoped assumptions, source
validation, checked investigation findings and registered portable records.
It does not replace the cognitive controller, memory database, planner or tools.

The Chat selector contains the three requested modes. Settings expose a default
mode, exact role bindings, synthesis role, context/output/timeout limits and
0–2 additional review rounds. Conversation choices override the default and
persist through restart/resumption without erasing history or drafts. The
legacy generation preference remains separate. No production default mode is
chosen by installation or testing.

A/B modes generate only with the selected exact local identifier. Both runs:

1. One immutable task/evidence/history snapshot, identical for both independent calls.
2. A independent proposal, then B independent proposal.
3. A's critique of B's actual output, then B's critique of A's actual output.
4. Synthesis by the configured role, preserving criticisms and uncertainty.
5. Optional bounded additional review/refinement only for unresolved issues;
   unchanged criticisms stop escalation. Agreement never becomes verification.

The task is explicitly separated from untrusted evidence. Full selected sources,
conditions, disagreements, scoped assumptions and complete conversation history
are retained or the request is explicitly refused. Annotated semantic retrieval
and replayed historical findings use existing infrastructure. Historical finding
selection is bounded and explicitly non-exhaustive. Oversize peer handoffs fail
without clipping. Arithmetic and explicit retrieval retain the established
checked calculator/source pathway without unnecessary model calls.

Advanced investigation budgets now reserve and count physical invocation attempts,
not wrapper calls. A five-call collaboration cannot bypass a one-call slice.
Those calls share the original inference time allowance. Insufficient budgets
pause optional generation while retaining checked findings.

Every stage records its exact model/digest, generation configuration, prompt/output
hashes, runtime metrics and OS qualification report. Failures retain completed
work, bounded partials and previous attempts. History/restore replay source
attestations, handoffs and checked finding documents. Exact and question-shaped
partial request copies are rejected as unfulfilled, not displayed as answers.
Resume preserves the original task/configuration/digests and requires explicit
user action. Single-model continuation creates a clearly identified child run;
it never silently claims two-model participation. A closed worker requires fresh
qualification on application restart.

The desktop shows phase status and one final response, with an optional Model
work view of actual outputs and critiques. Hidden runtime thinking fields are
not exposed. Experimental planning remains opt-in. Generated text never invokes
application commands, approves proposals or creates verified source claims.

## Security and resource controls

The existing private Ollama namespace/pipe transport remains mandatory. Multiple
stores are composed from verified files as read-only bind mounts; required v2
manifest metadata is retained. No host Ollama listener or external endpoint is
used. User/network namespaces, nested-userns denial, seccomp, read-only sources,
CPUQuota=100%, TasksMax=64 and MemoryMax remain enforced. MemorySwapMax=0 is now
also independently verified. Runtime models are unloaded between calls and only
one inference request executes at a time.

A private owner-controlled startup declaration contains only authorized model
roots and bounded limits. A 1.5 GiB profile requires the existing 384 MiB host RAM
reserve. If that admission fails, startup can use a stricter 768 MiB ceiling with
an explicit notice; oversized models are refused before loading. This is a
conservative admission rule, not an assertion that disk size equals RAM usage.
Each generation monitors host reserve, swap-out, OOM counters, worker swap and
sustained full-memory pressure; missing monitoring fails closed. New failures
save the exact triggering condition and observed counters.

The synthesis default is role B based on the previously recorded matched Lenovo
trial (2B 3/4, 0.5B 1/4). That small earlier result does not establish general
superiority or successful collaboration, and does not change the active model.

## Real host evidence and failures

All evidence is retained under:
`/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-dual-model`.

- `real-service/result.json`: initial startup failed because the combined-store
  directories were not separate mount points for read-only remounting. This was
  an implementation defect, not a Lenovo namespace limitation. Separate bounded
  tmpfs mount points fixed it; a new actual two-store isolation/cleanup test passes.
- `real-service-repaired/result.json`: the larger profile was resource-blocked,
  so the qualified 768 MiB profile ran A. A returned the full question with an
  ambiguity statement. This is not a correct answer. B was refused before loading;
  Both retained A's output and stopped at the blocked B stage. No B output was
  substituted and no successful collaboration is claimed.
- That trial's two real A calls generated 63 tokens each, at approximately
  3.80 and 3.91 tokens/s. Runtime load times were 2.15 and 5.30 seconds; whole
  application calls were 40.22 and 31.79 seconds. Peak sampled scope memory was
  633,491,456 and 791,654,400 bytes; worker swap was zero. These are scope charges,
  not model-private RSS or controlled cold-start benchmarks.
- `real-service-task-framing/result.json`: available RAM admitted the 1.5 GiB
  worker. A still copied a question-shaped fragment instead of solving the task.
  B started but a resource guard stopped the run after 119.81 seconds, without an
  accepted B response. Both was NOT RUN after worker closure. Full-memory PSI
  avg10 was 38.37% at shutdown; host swap used rose by approximately 187.41 MiB
  between the recorded endpoints. Shared host activity is a confounder.
- That pressure trial predates the precise failure-counter snapshot enhancement;
  its generic resource error does not identify which individual guard fired.
  The observed PSI/swap endpoints are not a reconstruction of the exact trigger.
  This diagnostic limitation is retained honestly; future failures now save
  specific thresholds/counters. The high-load 2B trial is not repeated after the
  protection trip. Worker shutdown and empty-scope cleanup were verified.

The independent logic criterion remains unchanged: under the stated premises
(red implies metal; no metal floats; K is red), K does not float. Restating the
request or calling this implication ambiguous does not pass. The standalone tool's
lexical screen is explicitly preliminary; semantic correctness requires review
of the actual text. No simulated response is used in these real trials.

## Tests and preserved functionality

The first full run executed 283 tests: 281 passed, one failure and one error. Both
were integration defects: adapter refresh overwrote an explicitly supplied
adapter, and an extra asynchronous mode refresh raced the existing history
workflow. Both unchanged regression tests pass after implementation repairs.
An initial new citation fixture also had an incorrect end offset; the unchanged
source validator rejected it and the fixture was corrected. No validation was
weakened to accommodate any model.

The next complete run passed 287 tests with no skips (749.266 seconds). Subsequent
host findings added stage qualification evidence, the actual two-store startup
regression, managed-model preparation, exact resource diagnostics, stronger echo
rejection and an actual process-crash/restart test. The focused final integration
run passed 38 tests, including real namespace/GUI checks and explicitly simulated
model orchestration. Final complete runs are reported below; mocks are not real
Qwen acceptance.

The baseline preservation snapshot records 1000 literary editions, 1,288,804 units,
22 scientific editions, 4,722 original submission events, 2,069 sources and 14 claims,
plus 12,829 entries in the existing independent safety backup. Original sources,
laws, corpus indexes, models, active generation preferences and backups are not
rewritten by model integration/evaluation. Tests and inference use separate
private installations. Preservation verification scope and closing comparisons
are recorded below; no production restore is performed.

## Remaining qualification

The 0.5B model has not demonstrated reliable reasoning for the tested task. The
current shared Lenovo workload resource-stopped B; complete real Both mode and
cross-model quality improvement remain unverified. More RAM can improve resource
headroom but does not establish model correctness. The next step is a measured
B-only and complete Both trial after adequate RAM/stable memory pressure, followed
by held-out factual attribution, logic and engineering tests. Retain independent
validation and uncertainty, regardless of model agreement.

Do not switch the default model or declare release readiness from these results.

## Final source qualification

The final full source suite passed **297/297 tests with no skips** in 691.665
seconds. This includes the actual two-store isolation/cleanup test, actual GUI
mode controls, strict citation/replay validation, actual process-crash recovery,
managed asset materialization and physical model-call/time-budget regressions.
The preceding 294-test pass (721.968 seconds) is retained as provisional evidence
before the budget review. That review found that a collaboration could otherwise
count as one advanced invocation; the final implementation reserves and charges
physical attempts and shares the original time allowance. The new budget tests
pass and existing authorization checks remain intact.

The final wheel contains 50 Python modules and exactly matches the frozen source
and test snapshot. The previous installed 49-module package was independently
compared with the untouched baseline and backed up before replacement.
