# VECTOR verified question-to-investigation planning

Implementation from verified clean checkpoint `945c9aa953b10904b454faf331d99d7dfea0febb`.
Implementation checkpoint: `ac4291c2e3809f64a36dca2606d6baec1e69a7f8`.
Status: experimental and opt-in; installed and locally verified. Neural assistance remains unqualified under the tested resource controls.
No general intelligence, autonomous scientific discovery or release qualification is claimed.

## Implementation and reuse

One new core module, `src/vector_core/planner.py`, compiles ordinary questions into
the existing investigation DAG. It reuses reviewed semantic claims/aliases,
relationship traversal, independent source qualification, safe Decimal/SI tools,
typed findings, checked answer composition, original hash/span provenance,
append-only investigation events, portable validation and the qualified model
adapter. No second planner database, schema migration or replacement architecture.

Changed runtime modules: planner (new), investigation, findings, service, projects,
portable, desktop, CLI and inference_worker. Added three planning test modules,
a CLI regression, two frozen fixture packs and two evaluation tools. README,
ARCHITECTURE and PLANNING_SPEC document the contracts. OS security, launcher,
privileged authority and Foundational Laws are unchanged.

Plans expose the objective, constraints, assumptions, available/missing evidence,
methods, dependencies, intermediate findings, verification status, alternatives,
unresolved questions, completion criteria and next actions. Direct explicit
arithmetic needs no model or catalog search. Data-derived aliases and explicit
relationship paths support previously unfamiliar subjects without adding topic
categories. Incomplete applicability, conflicts, missing methods, unknown ideas
and unresolved language are retained instead of silently converted to answers.

The Assistant uses the same ordinary question field with an experimental opt-in
checkbox. Clarify, resume and explore actions share service/CLI pathways. Saved
conversations retain investigation references, not trusted answer caches.
Revisions preserve completed history and suppress stale answers. Pending turn
identities survive a failure before investigation creation. Completed steps are
not repeated after reopening. In-flight uncommitted inference has no exactly-once
computation guarantee; explicit continuation remains necessary.

Historical compiler replay detects changed plan metadata and dependencies.
Independent operation verification checks source hashes/spans, qualified premises,
conflicts, units and numeric results. Replay of a language frontend is not proof
of English entailment. Human-approved alternative plans still use the original
controller; model text cannot dispatch operations or authorize actions.

## Frozen comparisons

A = existing direct/checked behavior at unchanged 945c 9aa.
B = existing investigation routing at that same checkpoint.
C = new opted-in question planning. All comparisons below are model-disabled.
The same frozen objective expectations score values, statuses, units, required
gaps and unsupported definite values. C additionally verifies required source
attribution, operation selection, declared usable dependencies and completed
plan construction. Gold never enters the planner; two explicitly supplied user
controls are passed equally to old/new pathways. A/B lack the new plan metadata,
so their plan-quality field is not applicable, rather than automatically zero.

| External set | A correct result/required gap | B | C | C plan checks |
|---|---:|---:|---:|---:|
| Development, 28 questions | 5/28 | 2/28 | 28/28 | 28/28 |
| Separate transfer, 8 questions | 1/8 | 0/8 | 8/8 | 8/8 |

Development contains 18 positive-finding tasks and 10 requiring explicit unresolved
status; transfer contains 6 and 2 respectively. These scores do not mean 36 factual
questions were answered. No mode produced an unsupported definite value under
this scorer. The separate transfer set introduced new subjects, values and domains
after initial planner design. This is still a small, controlled evaluation, not
a broad natural-language or discovery benchmark.

Examples include a new alias mapping to an 11.7 index; an explicit two-hop source
path supported by three separate originals; power 17 W times duration 23 s yielding
391 J; calculating 40 then using that completed result to obtain 5; disagreement 31
versus 43 Pa kept disputed; Mercury clarified by astronomy; known mass plus unknown
temperature retained as partial; and a novel archive/cooling inquiry left open
with possible evidence requirements. Negative component-to-whole inference,
uninterpreted time modifiers and unrelated source conditions are rejected.

Development fixture SHA 256:
`85856d4260a5bc395be54842d4a4c787ff06eb15f2e127de950c68040f6e6332`.
Transfer fixture SHA 256:
`f79dc1acf5d11d3a09ff688034859d44296c547b7ec25571ae134528afd959aa`.

## Runtime and memory

Final model-disabled C evaluation:12.262 s development,6.568 s transfer,
median workflow 0.213 s and 0.606 s. Maximum evaluator RSS 32.6 MiB (33,332 KiB),
sampled host used RAM 1,585.2 MiB, host swap 1,280.5 MiB, zero new swap-out and zero
OOM kills. Old A/B development medians 0.044/0.077 s and transfer 0.229/0.472 s;
old processes peaked 28.5/28.0 MiB. Faster retrieval-only baselines often did not
complete the requested operation, so these timings do not establish a speedup.
Host totals include other applications; evaluator RSS is the process measure.

## Actual 0.5B trial

Installed Ollama 0.40.12 independently discovered the 494.03M Q4_K_M model
(digest `4ff64a7f502a08b7616edb8ca0a79eb1853fc363d842b7df4b46915d11a3fb09`).
Exactly one actual generation request used installed `qwen2.5-coder:0.5b`,
context 2048, output 96, timeout 60 s, temperature 0, seed 0, concurrency 1. The full
prompt was 631 bytes; no essential instructions/evidence were truncated. Task:
propose two competing explanations and a distinguishing measurement for an
intermittently vibrating fan, explicitly retaining uncertainty. No gold answer
or simulated text was supplied. The real planner and installed-model adapter
were used in an isolated evaluation database.

The worker independently qualified namespaces, no external routes/network,
read-only model/filesystem restrictions, seccomp, CPU quota 100%, pids 64,
memory 768 MiB and zero worker swap. The host monitor stopped the trial when
swap-out exceeded 32 MiB and full-memory PSI stayed above 10% for 5 s. Observed:

- Whole trial 49.848 s; generation operation 16.634 s before cancellation.
- Peak worker cgroup memory 768.008 MiB; sum sampled worker-process RSS 477.7 MiB.
- Peak host used RAM 1,945.4 MiB; peak swap 1,315.1 MiB.
- Host swap-out 35.641 MiB; peak full-memory PSI avg 10=13.16%.
- Worker swap 0; host/cgroup OOM kills 0.
- Worker terminated and its cgroup disappeared. Available host RAM after cleanup
  2,242.1 MiB versus initial 2,218.3 MiB. Extra host swap allocations remained;
  cleanup does not mean the host swap total returned to baseline.

No complete model response or terminal API metrics were obtained: tokens/second
and load time are unavailable. Zero proposals were accepted. This is an
incomplete neural-quality test, not a reasoning-score failure or success. There
was still available host RAM; the qualified worker allocation reached its
limit. This establishes resource pressure under the tested controls, not that
the 0.5B model is intrinsically incapable or that physical RAM alone caused it.
No limit was raised and no further inference attempted. Prior Stage 6C 12/12
checked answers and 0/12 Qwen commentary remain historical evidence, not new
planner-assisted neural passes.

The optional neural pathway accepts bounded ordinary prose as an explicitly
unverified proposal, avoiding a brittle new model-plan JSON contract. It cannot
replace checked findings, manufacture citations, execute suggested steps or
promote hypotheses to discoveries. Existing answer/claim/notes JSON contracts
remain strict. Actual neural assistance is implemented but not demonstrated as
reliable on this runtime. Leave it unqualified pending a stable resource profile.

## Verification and preservation

Unchanged baseline 204/204 source tests passed in 452.311 s. The first expanded full
suite passed 226/226 in 704.606 s. The final source suite passed **226/226 with zero skips in 575.990 s**,
with all 47 core-module hashes unchanged during the run. The local offline wheel
SHA256 is `cda19c88692417c690d3a36faa402aa090eb0b645e8e54d0ac8de7c55decbcd6`;
all 47 installed modules match. The old installed package is preserved independently.
The installed isolated runtime ran 226 tests in 631.229 s: **225 passed and one
was skipped** because optional `cryptography` is absent. The source-host positive
encryption test passed; encrypted roundtrip remains unverified in the installed
interpreter. No other skip or failure occurred. Post-install preservation follows
only once verified. Actual GUI question entry, saved history, CLI, crash/restart,
portable forgery rejection, missing evidence, ambiguous sense and source
qualification tests are included. The original 52 checked model-disabled cases
are retained unchanged.

A fresh independent safety checkpoint completed before any production changes:
consistent SQLite snapshot plus 4,587 independently hash-verified object copies,
1,599,438,405 bytes. Initial copy timed out at 1,200 s while competing for I/O;
partial copies were retained, rechecked against unchanged authoritative data and
completed with 1,814 missing copies. Existing backups were not overwritten.
Three monitor setup attempts encountered two causes: thread creation after policy
activation and a descriptor-close race. All failed setup evidence remains; those
attempts made no inference request.
One intermediate suite was deliberately interrupted to avoid concurrent resource
measurements, and is not counted as a passing run. The corrected monitor starts
and waits before policy activation, then samples after descriptor closure and
thread-synchronized filtering; no security-policy change was made.

The installed production demonstration passed in 79.795 s without inference or
fixture imports: “What does hemoglobin bind?” returned source-attributed oxygen;
“Calculate (13 + 7) * 2; then divide the result by 8” returned 40 then 5; the
unfamiliar fan explanation remained unresolved. Reopening reconstructed saved
history and reused the same investigation without repeating completed steps.
Original-event and preference counts did not change.

Final preservation **passed** in 720.717 s, including full portable
validation (459.708 s). All 1,000 literary
editions and 1,288,804 passages, 22 scientific editions and 2,631 text segments
have identical pre/post fingerprints. All 4,587 managed original object hashes
and their independent safety copies match. All 18 prior history prefixes are
unchanged. Schema remains 8; preferences, both model-store inventories, existing
safety backup inventory and Foundational Laws are unchanged. Laws SHA256:
`059fd4e4193c92dbb6860d48a3050bdb66b8b3abaaa6fb4a37854950d808748d`. Full database/source/provenance validation passed.
No source corpus import, default-model change, owner override, authentication
change, training or HELIX modification was performed.

## Durable evidence

Implementation source checkpoint is `ac4291c2e3809f64a36dca2606d6baec1e69a7f8`. The following report-only
Git checkpoint adds this report and its README link; its exact final HEAD and
clean repository/package verification are recorded in [FINAL.json](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-question-planning/FINAL.json).
All 47 installed core modules match the tested source. Detailed local evidence:

- [Final source suite](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-question-planning/final-source-suite-verified.log)
- [Installed suite, including explicit skip](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-question-planning/installed-suite.log)
- [Development comparison](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-question-planning/comparison-final-v2-development.json)
- [Separate transfer comparison](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-question-planning/comparison-final-v2-transfer.json)
- [Sampled deterministic resource measurements](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-question-planning/comparison-final-v2-resources.json)
- [Actual 0.5B attempt and cancellation](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-question-planning/live-small-verified/result.json)
- [Actual production demonstration](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-question-planning/production-demo.json)
- [Full preservation verification](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-question-planning/preservation-after.json)
- [Pre-change independent safety checkpoint](/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-question-planning/before-question-planning.json)


## Limits and next improvement

This is conservative grounded interpretation and explicit arithmetic, not
general natural-language entailment. Catalog/path/objective limits are renewable
resource slices and explicitly incomplete when exceeded or prefixed records are
excluded. Only reviewed semantic interpretations support checked grounding;
unqualified book/science passages remain retrievable evidence, not automatically
established claims. Source-bound arithmetic followed by further arithmetic still
needs an explicit supported quantity binding or a revised method. Creative
proposals are preserved, not independently tested or automatically adopted.

The next highest-leverage improvement is an independently scored
hypothesis→prediction→discriminating-test→observation loop with approved methods,
source/quantity bindings and revision based on actual outcomes. First broaden
unfamiliar paraphrase and counterexample evaluation so language interpretation
is checked independently of compiler replay. Qualify model working-set behavior
on suitable hardware before claiming a neural reasoning gain. Keep planning
opt-in and preserve existing default behavior.
