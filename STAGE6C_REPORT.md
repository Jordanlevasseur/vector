# VECTOR Stage 6C — verified cognitive output and evidence handoff

Implementation checkpoint: `3d0cad8cbfdbaa4c816961f514c6d317c603a318`, continued
from `ede5ce68e40d56c1f9c2b5639689fa9b5b821c00`. This report is the subsequent
measurement/documentation checkpoint. Cancellation-reporting checkpoint `6677e2c6bb4676d8d9bf2d007c34c11b98a16852` adds the 204th source regression without changing installed runtime code. Hardening checkpoint `098af4a05051b223b09dfa6a63146a9a00208771` binds the saved question to its pinned goal and namespaces combined test-fixture identities. The original 12 neural calls used `3d0cad8`; subsequent comparisons use `098af4a`. Neural prompt/generation/security code and all expected outcomes are unchanged by this hardening.

Evidence directory:
`/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6c`.
No external network, downloads, training, HELIX changes, owner override, model
replacement or default-model change is part of this work.

## Findings and architecture

See `STAGE6C_AUDIT.md` for all twelve exact failure mechanisms. All 12 Stage 6B
integrated neural outputs failed the existing strict contract; none was truncated
and all 12 independent source/tool results were correct. Missing citations,
semantic-record/tool-request copying and input/output boundary confusion dominate,
but they are not the whole diagnosis: X1 chose an arbitrary disputed value,
J1/J2 mangled relationships, Q1 misdescribed a formula and N1 conflated electrical
and clinical senses of current. Removing structural checks would conceal these
substantive failures. The original rejected responses remain rejected.

The separate production two-hop guard refusal was 7761 bytes versus 7424 allowed.
Stage 6C does not raise that window or retry repeatedly. Full original provenance
stays independently stored; a compact logical handoff is offered only if complete.

One new core module, `findings.py`, reuses existing versioned investigation
states/events, semantic snapshots, source attestations, Decimal/SI tools and
portable restoration. Schema 8 is unchanged; no parallel knowledge store or model
service was introduced. Typed findings preserve source support, conditional
verified computation, joined inference, dispute, uncertainty, hypotheses, owner
assertions, simulation and dependencies. Replay checks the original recorded
request and proof, not a verification-looking field. Compositional blocks report
these results with visible source handles, units, applicability and provenance.

`compose` persists an answer before optional `explain`. The optional local model
can propose an ordering of all findings and separately labelled unverified notes.
A fixed worker schema and strict parsing/reference checks apply. No output field
can replace checked values/statuses/citations. Notes are not merged into the
answer or treated as facts, commands, permissions or verified novel reasoning.
Failure, timeout or oversize handoff leaves the completed checked answer intact.
Existing core/worker isolation and resource controls are unchanged.

The shared service, CLI `semantic answer`/`investigation answer`, and desktop
**Checked investigation results (no model required)** expose these results.
Historical checkpoints survive restart/restore. Fresh views warn on changed
interpretations/new disagreements without rewriting the old answer. Normal chat,
experimental connected-evidence default and generation preferences are unchanged.
Explicit trusted-user requests remain necessary for new grounded operations.

## Evaluation scope

The original 40 frozen gold cases and 12 new independent cases are scored at the
output block/value/unit/status/source/condition/date level. Expected outcomes live
only in test fixtures/scorers, never production rules or prompts. New cases cover
391 J, 70,000 Pa and 25.4 mm computations, unseen two-hop material lookup, 31/43 Pa
disagreement, polarity, applicability/time negatives, owner belief, hypothesis and
clinical-sense uncertainty. These are explicitly fictional premises, not empirical
science. The original corpus also includes 9 exact excerpts from 6 preserved local
publications with U.S.-only rights/provenance. Full originals and excerpt offsets
are independently rechecked.

Frozen historical neural comparisons are labelled historical, not rerun or
repaired. Fresh neural comparisons use the actual unchanged Qwen 2.5-Coder 0.5B,
8192 context/512 output, temperature 0, seed 0, 300-second timeout, CPU quota 1,
768 MiB cgroup memory, zero worker swap, 64 tasks and qualified offline isolation.
The original 12 new-path calls completed. The planned unseen four paired A/C/D
cases and production-source case have their completion/blocking status reported
separately below. A=direct baseline, C=Stage 6B integrated neural
answer, D=Stage 6C checked answer plus optional unverified model contribution.
Neural protocol acceptance is not an answer-correctness or entailment score.

## Measured results

|Evaluation|Result|Meaning|
|---|---|---|
|Original 40 + unseen 12, model disabled|52/52 checked answers correct|Independent block/value/unit/status/source/applicability checks; no neural inference.|
|Original 12, historical direct baseline|1/12|Frozen real 0.5B evidence, not rerun.|
|Original 12, historical nonsemantic investigation|1/12|Separate older adaptive-controller baseline.|
|Original 12, historical Stage 6B evidence-integrated neural answers|0/12|Correct source/tools did not yield accepted neural answers.|
|Original 12, Stage 6C checked answers with actual neural contribution attempted|12/12 checked; 0/12 neural contributions accepted|All model outputs rejected; the checked answer survives independently.|
|Unseen paired A/C/D neural comparison|Blocked: 0 completed generations; 1 A request cancelled; 11 cells unrun|Resource safety stop; not a 0/12 model score.|
|Production historical scientific join, model disabled|1/1 correct; full scientific provenance retained|2,461 bytes versus unchanged 7,424-byte guard; old package 7,761 bytes.|
|Production scientific join with neural contribution|Not run|Stopped after the unseen workload resource guard.|

The 12 completed model responses all ended normally (`stop`), with 364–817 input
tokens and 68–440 generated tokens; none hit the 512 output budget or 8192 context.
Seven invented/misclassified finding handles and five used prose instead of
source handles. These failures are preserved, not repaired into accepted notes.
There are also substantive errors: X1 invented ratings A/B/C/D and described them
as verified while the checked finding retained a 10/20 W dispute. J1 described the
terminal material instead of explaining the requested density. N1's new raw text
correctly withheld current clinical guidance without the old electrical-current
distractor, but its invalid evidence field still failed the strict contract.
No genuine novel neural reasoning improvement was measured; the model already
received the checked facts, and protocol acceptance would not prove entailment.

Final installed deterministic evaluation: 52/52, 13.275 seconds including fixture
loading and durable workflow writes, process maximum RSS 31,760 KiB (about 31.0 MiB).
Median individual durable workflow time was 0.127 seconds (`deterministic-final/comparison.json`).
These are absolute fixture-process measurements, not an incremental memory cost
for the feature or a claim that the entire 1.3 GB database is resident in 31 MiB.
The real production join completed in 1.319 seconds without a model.

Actual 0.5B original 12 run, Ollama 0.40.12 on the Lenovo i7-2640M/4 logical CPUs,
approximately 3.7 GiB RAM and 3.9 GiB swap:

- Median generation 2.335 tokens/s (range 1.993–2.827), excluding loading/prefill.
- Median load 9.359 seconds; request median 116.115 seconds, range 68.454–211.937.
- Total phase 1487.866 seconds (24.8 minutes), including baseline/unload checks.
- Peak runner RSS 649,965,568 bytes (about 619.9 MiB); cgroup peak 805326848 bytes
  (about 768.02 MiB, including file cache and kernel page-accounting overshoot).
- Worker swap 0; host swap baseline 1450729472 bytes, peak 1470709760 bytes.
  Host swap-out during the phase 22179840 bytes; attribution to other host
  activity is not independently established. New host OOM kills 0.
- Minimum host available memory 1347063808 bytes; full-memory PSI avg10 peak 2.73%.
  Worker exited, descendants cleaned and cgroup removed. After closing, host
  available memory was 2035298304 bytes. No original-run safety guard fired.

The corrected unseen run encountered different host conditions. Its first
baseline A request was cancelled after 17.963 seconds. Host swap-out reached
181.918 MiB (guard 128 MiB), and full-memory PSI avg10 reached 63.35% with the
above 30% condition sustained for 15 seconds. Worker swap remained 0, new OOM kills
were 0, and the worker/cgroup were cleaned up. Minimum host available memory was
1446.734 MiB, so physical RAM exhaustion alone is not established as the cause;
the source of the global pressure was not diagnosed. Worker group usage peaked
at 532459520 bytes, below its 768 MiB limit. Further inference was stopped, including
the production-model call. No thresholds, context, model or acceptance checks
were weakened. A subsequent harness cleanup exception is documented below.

The new unseen cases demonstrate deterministic answer construction only. Their
fresh neural A/C/D comparison and the production neural handoff remain
unverified under a stable host baseline. Original successful isolation and
cleanup measurements do not turn these blocked tests into passes.

The first combined unseen fixture load failed before any model request because
both source packs used the key `hypothesis`. This was a test-harness defect,
not a model failure. Derived fixture identities and gold source references are
now namespaced; expected answers and source text are unchanged. The failed setup
record remains in `live-unseen/result.json` and is excluded from inference scores.
A combined-load regression covers this defect. A separate tampering test failed
before the question-binding guard and passed after it; it is retained in the
full regression suite. Neither fix relaxes a correctness or security check.

When the resource guard cancelled generation, the older live harness also
referenced an uninitialized unload sample and raised `UnboundLocalError`.
The resource stop and final cleanup evidence were retained in the raw report.
The harness now initializes that sample and reports a cancelled per-case unload
verdict as unknown, deferring cleanup certification to the final worker phase.
An explicit no-inference cancellation regression verifies this behavior. This is
a test-harness reporting defect, not evidence that the isolation boundary failed.
Neither a fresh neural response nor a passed unload check was fabricated.

## Preservation and regression qualification

Final source suite:204/204 passed with no skips (`final-harness-suite.log`,
542.345 seconds). The installed runtime suite ran 203 tests:202 passed and one
explicit optional-cryptography round trip was skipped (`installed-final-suite.log`,
457.958 seconds). That positive encryption test passed in the source-host
interpreter; it remains unverified in the deployed interpreter, which lacks the
optional dependency. No skipped test is counted as passed. The additional 204th
source test covers cancellation reporting in the repository evaluation harness;
installed runtime modules did not change after their 203-test qualification.

Actual host tests include namespace/network denial, readonly model/home
restrictions, process exhaustion, timeout/cancellation/cleanup, desktop display
and the new checked-results path, immutable persistence, abrupt crashes,
restart/resume, portable export/restore, scientific attribution and malicious
answer/proof tampering. The final 46 installed Python modules match the local
wheel/source; wheel SHA-256
`1adec207fc32ca84cf997b5f84a0441b33d5a0f1a6aaba9287142edc243aff94`.
No package or model was downloaded. Prior installed packages were preserved.

Preservation passed (`preservation-after.json`), taking 882.370 seconds:

- 1,000 literary editions and 1,288,804 literary passages unchanged.
- 22 scientific editions and 2,631 extracted-text segments unchanged.
- All 4,587 pre-existing managed objects physically rehashed and unchanged;
 4,588 blob records and 4,722 source events passed full integrity checks.
- All 18 checked prior history/table prefixes match the pre-change SQLite
 snapshot, including claims, assessments, overrides, entities, persistence
 records and 135,166 pronunciation rows. New investigation evidence is additive.
- Generation/session/runtime preferences are byte-for-byte unchanged. Both primary
 and candidate model-store inventories and the existing whole-system backup
 inventory are unchanged. Schema 8 is unchanged.
- Full SQLite/FK/original-object/portable-record validation passed in
 622.631 seconds, including replay of persisted checked answers.
- Foundational Laws SHA-256 remains
 `059fd4e4193c92dbb6860d48a3050bdb66b8b3abaaa6fb4a37854950d808748d`.
 Core offline security and worker resource-control source files are unchanged.

Before production work, a consistent SQLite snapshot and independent rehashed
copies of every registered object were preserved:1599438405 bytes total,
708.486 seconds. It is an additional safety checkpoint, not a new claim that a
full production restore was performed. Existing verified whole-system backups
were retained; fixture-level actual restore/recovery was exercised by the tests.

## Remaining host acceptance

No further inference was attempted after the pressure guard. The following are
owner-side commands for a later stable Lenovo session; they keep all guards and
use fresh empty evidence directories. They do not download models or change the
production model preference. A zero process exit is not sufficient: inspect
`result.json` for `error`, `cancelled`, `stop_reasons`, completed generations and
actual answer scores. Blocked/cancelled cases must remain blocked/cancelled.

```sh
cd /home/mint/VECTOR/vector
vector_stage6c_trial_dir=$(mktemp -d /home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6c/lenovo-unseen-XXXXXX)
.venv/bin/python -B tools/evaluate_stage6b_live.py --corpus tests/fixtures/stage6b-corpus.json --directory "$vector_stage6c_trial_dir" --models-directory /usr/share/ollama/.ollama/models --include-unseen --unseen-only --compare-checked
```

The actual production-source neural handoff (still unrun) has a prepared local
acceptance driver. It appends investigation evidence only and imports no fixture,
source or claim into production. Run it only after stable host conditions permit:

```sh
vector_stage6c_prod_dir=$(mktemp -d /home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6c/lenovo-production-XXXXXX)
.venv/bin/python -B /home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6c/production_live.py "$vector_stage6c_prod_dir"
```

These commands have been prepared, not substituted for actual passing results.
No installed encrypted-backup round trip is certified while that interpreter
lacks its optional offline cryptography dependency. No dependency is downloaded
or security fallback enabled to conceal that limitation.

## Limits and next priority

Release readiness is not declared: unseen neural comparisons and the production
neural handoff are blocked by the observed host-resource stop, and installed
encrypted-backup positive acceptance is incomplete. The checked-answer feature
is implemented and verified within the explicit-request scope measured here.

This is a measured improvement in checked result delivery, not evidence that the
0.5B model acquired mathematical, causal or general reasoning ability. Existing
source assertions may be wrong. Decimal computations are conditional on their
premises; joins are terminal-source retrieval, not causal transitivity. Source
interpretation remains explicit/manual, coverage is limited, and there is no
independent checker for arbitrary natural-language entailment. Unchecked future
observation types remain unknown until an appropriate proof adapter exists.

The normal freeform chat route can still fail. New operations remain explicit;
optional neural commentary remains experimental/unverified. No general reasoning,
autonomous action or HELIX release readiness is claimed. Per-operation finding,
prompt and output budgets bound each slice; complete history and further work can
continue independently and these are not permanent intellectual limits.

The next highest-leverage work is a checked natural-language-to-investigation
planner with explicit scope/sense/dependency choices and independent proof checks
for claims beyond curated lookup/arithmetic. It should reuse these finding and
answer contracts, retain hypotheses without certification, and be tested on new
blind tasks before being exposed as default conversation. That next stage has
not been started.
