# Dual-model runtime investigation from b0e7527

## Current outcome

**The primary objective is not yet achieved.** Real 0.5B inference works, with
serious reasoning/coherence limitations. Three controlled 2B loading trials
were stopped by the unchanged sustained-memory-pressure protection. No accepted
2B response was produced in this investigation. **Complete real Both mode was
NOT RUN**, because successful B-only inference was the explicit prerequisite.
No simulated response was substituted. VECTOR is not release-ready; Priority 4
advanced reasoning/planning remains unqualified.

This follow-up implements bounded CPU loading and better diagnostics/prompt
framing. It does not replace the intelligence architecture, model selection,
independent-response/review/synthesis pipeline, source validation or approval
system. Existing A, B and Both selections remain available. Neither model,
Ollama nor the owner's default/preferences/startup declaration is replaced.

Evidence root:
`/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-dual-runtime-20261102`.
Raw results, stage records, actual runner arguments and resource samples remain
separate from the derived `MEASUREMENTS.json` and semantic assessment below.
The tested B is the existing `vector-qwen35-local:2b-q4_k_m`, a text-only local
GGUF import (SHA-256 `9a3d0aa6c920f096441139b6a254542da855223fdad06855ea00c6c087fd713d`),
not a qualification of the official full multimodal distribution. Both installed
dependency graphs were freshly verified before trials (A: 8 files; B: 5 files).
The private runtime reported installed Ollama 0.40.12; nothing was downloaded.

## What blocked B

The historical `real-service-task-framing` trial in `DUAL_MODEL_REPORT.md` passed
1536 MiB RAM admission, then failed during generation. Its generic OR-condition
error lacked the triggering counters. **Its precise individual trigger cannot
be reconstructed.** Later measurements do not retroactively prove that trigger.

A fresh 1536 MiB request was refused before loading: available RAM did not meet
1536 + 384 = 1920 MiB. This admission rule is conservative and does not model the
actual working set. Reducing the ceiling to 1440 MiB admitted controlled trials,
but did not resolve the runtime failure. The remaining blocker therefore is not
merely that initial estimate, context overflow, response parsing or output budget.

All three actual B trials used context 1024, output budget 128, timeout 300 s,
CPU quota 100%, 64 tasks and zero allowed worker swap. The expected answer was
fixed independently: under the given red/metal/nonfloating premises, K does not
float. No expected answer was placed in the model prompt.

| B loading strategy | Request seconds before stop | Peak sampled scope MiB | Minimum host available MiB | Request host swap-out MiB | Maximum full-memory PSI % |
| --- | ---: | ---: | ---: | ---: | ---: |
| Batch 32, runtime's copying default | 39.52 | 992.27 | 1254.74 | 55.12 | 68.67 |
| Batch 32, explicit mapping | 29.40 | 948.59 | 1852.07 | 42.19 | 50.61 |
| Batch 32, mapping, process-local THP disable | 44.31 | 638.98 | 1897.56 | 103.40 | 73.37 |

In each case the exact stop was **full-memory PSI above 30% continuously for
15 seconds**. No worker swap, worker memory-limit hits, worker OOM or host
OOM-kill counter increase was recorded. Scope cleanup was verified. Loading did
not finish, so completed B load time and generation tokens/s are **not measured**,
not zero or passing. Scope/RSS peaks are sampled lower bounds, not completed-model
capacity requirements. The host has 3,978,833,920 bytes RAM and 4,215,271,424 bytes
swap. Peak total host swap used in the two completely sampled B phases was
1322.96 and 1496.73 MiB; that includes pre-existing/shared-host use.

The scope and every inspected ancestor had no binding `memory.high` or ancestor
`memory.max`. New scope `memory.events.max/oom/oom_kill` stayed zero. Available
RAM alone was thus insufficient to predict loading stability. Allocation/reclaim,
memory compaction and I/O stalls were observed on the shared host. The mapped
trial's whole sampled phase recorded 124 compaction stalls, 121 compaction
failures and 223 allocation stalls; the THP-disabled phase recorded 24 compaction
stalls/failures but 1239 allocation stalls. These phases have different duration
and shared activity, so they are not a controlled causal comparison.
Whole sampled-phase global CPU I/O-wait fractions were 56.33% and 81.05% in the
mapped and THP-disabled trials; non-I/O CPU busy fractions were 24.36% and 11.73%.
This further supports a loading/paging stall diagnosis, rather than a completed
generation simply being slow at computation. It does not identify one storage
or kernel cause uniquely.

This establishes a real pressure/stall blocker under the current host workload,
not that the 2B architecture is unsupported or that 3.7 GiB can never run it.
Earlier actual 1024-context B trials on this same hardware completed, as recorded
under `vector-qwen35-runtime-t420-20261031`. No exact minimum RAM upgrade, or claim
that more RAM fixes reasoning correctness, follows from these observations.

## Corrections and verified settings

- Generation explicitly requests `num_batch=32`, two CPU threads and
  `use_mmap=true`. Actual runner arguments confirmed `-b 32 -ub 32 -t 2`.
  The old `--load-mode none` disappeared with mapping requested; corresponding
  anonymous/file charges changed from approximately 660/329 MiB to 112/834 MiB
  at the respective failure snapshots. Cached file pages can be charged outside
  the worker scope: a smaller scope charge is not the same as lower physical
  model RSS. Read-only files and global host monitoring remain required.
- The private worker sets and verifies `PR_SET_THP_DISABLE(1)` before spawning
  Ollama. Parent qualification rejects failure. Actual daemon/runner samples
  confirmed `THP_enabled: 0`. No global THP, swap, kernel or desktop setting was
  changed. The scoped setting did **not** establish successful B loading.
- Every generation records current/peak resources and bounded `memory.events`
  and `memory.stat` counters; ordinary runtime errors/timeouts retain the last
  snapshot. Monitoring initialization now lies inside fail-closed cleanup.
- The operator tool requires a ten-second quiet baseline and checks complete
  selected model dependency SHA-256 graphs. It never pulls a model or contacts
  a shared daemon. Its sampler is created before the core's thread prohibition,
  waits until the synchronized filter/descriptor sweep finishes, then opens its
  log. The first diagnostic attempt created a thread too late; a subsequent
  early sampler lost its descriptor. These operator-tool defects were repaired.
  The first copying-trial sampler is incomplete; its table values come from the
  independent transport safety monitor, not that broken sampling log.
- Prompt framing permits empty uncertainty/issues only when no specific problem
  remains and distinguishes retrieval notices from task answerability. Final
  framing removes the literal product/version label which A had incorporated
  into a fictional greeting. Exact v1/v2 replay and handoff hashes remain covered;
  complete task, evidence, history, attestations and peer outputs are preserved.

All existing namespace, network, nested-userns, seccomp, filesystem, memory,
CPU, task, SHA-256, citation, human approval and physical-call/time-budget controls
remain in place. No threshold was relaxed to obtain a model result.

## Real 0.5B capability comparison

Final compact-direct and full VECTOR-service tests used the same four tasks,
context 2048, output budget 192, temperature/seed zero, 768 MiB ceiling, mapping
and process-local THP disable. Every response was actual
`qwen2.5-coder:0.5b`, not a fixture. Protocol completion is separate from the
following unchanged objective criteria.

| Task/criterion | Compact direct prompt | Final VECTOR framing |
| --- | --- | --- |
| Conclude K does not float | Repeated “No metal object floats”; did not complete the deduction about K | Copied retrieval notice and claimed task lacked evidence: failed |
| Ideal 18 V / 9 ohm circuit: 2 A and 36 W | Claimed 18 V × 9 ohms = 162 W: incorrect | Copied request; existing unfulfilled-output validator rejected it |
| Unknown sealed-box mass: cannot determine without measurement/data | Restated unknown object; missing mass explanation incomplete | Restated question and irrelevant retrieval notice: unfulfilled |
| One short welcoming sentence | “Welcome to our new project!”: passed | Two sentences plus irrelevant uncertainty: failed requested format/coherence |

Direct calls completed in 11.31–22.92 s; runtime load 1.55–2.02 s and generation
4.57–5.09 tokens/s. Service calls took 29.61–37.28 s; load 1.45–2.56 s and
generation 4.16–5.01 tokens/s, including the subsequently rejected echo. Peak
sampled runner RSS was about 490.8 MiB in both phases; scope peaks were 172.62
and 156.56 MiB because mapped cache charges can belong elsewhere. Worker swap
and measured per-request host swap-out were zero. Minimum host available RAM
remained at least 1995 MiB. Peak total host swap use was 1462.05/1460.63 MiB.
These are actual observations after checksum reads, not controlled cold starts.

The final responses did not exhaust output/context budgets; these failures are
not diagnosed as truncation. The matched comparison demonstrates sensitivity to
context/framing but also direct arithmetic/logic limitations. It does not uniquely
isolate every prompt effect from model capacity or establish reliability from one
greeting. A is presently suitable only for bounded drafts/formatting with external
checking, not trusted arithmetic, engineering, reasoning or an authoritative veto
on B. Existing deterministic verified tools should retain those responsibilities.
The user's independent A selection remains available.

An earlier v2 engineering question containing “Calculate” never reached inference:
the existing language router classified it as unsupported arithmetic and asked for
clarification. The final matched wording instead asked what current/power result;
the physical problem and 2 A/36 W criteria were unchanged. This distinguishes a
routing limitation from a wrong model answer. No router/security check was bypassed.

## Verification and preservation

Focused checks passed: final prompt/replay regressions 6/6; process-local memory,
payload and hidden-thinking measurement tests 3/3; existing actual namespace,
process exhaustion, streaming, timeout and cleanup checks 7/7; resource guard
checks 7/7. An earlier interrupted partial collaboration test run is not counted
as a full pass. The complete source suite passed **309/309, zero skips**, in
825.577 seconds. All 50 runtime module hashes match the final real-model trials.
The local wheel was built under kernel network denial and its 50 modules exactly
match the tested source. Simulation tests exercise orchestration only, never
real Qwen acceptance.

The pre-install check matched both model-store inventories, all 12,829 independent
backup entries and archived source-file metadata. It detected a difference from
the older b0e7527 preservation snapshot in `vector.sqlite3` and five preference
records. Those records are dated 00:26–00:30 UTC November 3; the database mtime is
00:31 UTC, before the first current evaluation at 00:41 UTC. They were preserved,
not restored to the older snapshot. A fresh current pre-installation inventory
and all 12 preference records provide the closing comparison baseline. The
initial historical-comparison failure remains retained in `preservation-before.json`.
Foundational laws retain SHA-256
`059fd4e4193c92dbb6860d48a3050bdb66b8b3abaaa6fb4a37854950d808748d`.

Implementation checkpoint: `c2910c4`. The clean production checkout was
fast-forwarded locally and its wheel installed with kernel network denial,
`--isolated --no-index --no-deps --no-compile`. All 50 installed module hashes
match the tested source; the previous installed package and distribution metadata
were separately preserved for rollback. The full installed suite executed
**309 tests: 308 passed, one skipped, zero failures**, in 712.369 seconds. The
skipped authenticated-encryption round-trip requires optional `cryptography`,
absent from this interpreter. It passed in the host source suite; missing-support
fail-closed tests passed. No dependency was downloaded and the skip is not a pass.

`preservation-after.json` passed: active data metadata and all 12 preference
records match the current pre-installation snapshot, schema remains 8, and no
production model-run records were created. Both model-store inventories and all
12,829 independent-backup entries match the older baseline. Model graph hashes
were fully verified before trials (A 8 files; B 5), with unchanged closing metadata;
no additional final weight rehash is claimed. Startup declaration bytes, defaults,
laws and all 50 installed module hashes passed their comparisons. The host
OOM-kill counter remained zero. This is not a fresh full corpus-content rehash,
SQL integrity scan, production restore or broad reasoning qualification.

## Safe next host acceptance

Do not keep repeating a pressure-stopped workload to obtain a pass. Close other
memory-heavy applications, preferably run the evaluation outside the Codex GUI,
or provide additional RAM before another B trial. The current software cannot
promise stable B inference with the present shared workload. More RAM offers
headroom; the tested hardware minimum and a fix for reasoning errors remain
unproven. No default-model switch is recommended.

The following uses the existing stores and current qualified source, writes only
fresh private evaluation directories, and retains all controls. Choose new output
paths if these exist. First establish a complete B-only response and review actual
correctness, then a service response, before attempting Both. Each command exits
nonzero for a blocked/incomplete pipeline; exit zero still requires semantic review.
Never trim task/peer/evidence content if the later context budget is insufficient.

```bash
cd /home/mint/VECTOR/vector
PYTHONPATH=src .venv/bin/python tools/evaluate_runtime_models.py \
  --store /home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-qwen35-evaluation-20261031/candidate-models \
  --output /home/mint/Documents/Codex/vector-b-next-direct \
  --memory-mib 1536 --context 1024 --output-tokens 128 \
  --modes b --tasks logic engineering uncertainty greeting

PYTHONPATH=src .venv/bin/python tools/evaluate_runtime_models.py \
  --store /usr/share/ollama/.ollama/models \
  --store /home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-qwen35-evaluation-20261031/candidate-models \
  --output /home/mint/Documents/Codex/vector-b-next-service \
  --memory-mib 1536 --context 2048 --output-tokens 192 \
  --modes b --tasks logic --service

PYTHONPATH=src .venv/bin/python tools/evaluate_runtime_models.py \
  --store /usr/share/ollama/.ollama/models \
  --store /home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-qwen35-evaluation-20261031/candidate-models \
  --output /home/mint/Documents/Codex/vector-both-next-real \
  --memory-mib 1536 --context 4096 --output-tokens 192 \
  --modes both --tasks logic --service
```

The 4096-context complete real collaboration is **unqualified**, not a promised
working setting. Verify both distinct model digests, five actual stage generations,
full peer handoffs, final output, independent correctness and cleanup. No agreement
or valid JSON alone certifies reasoning.
