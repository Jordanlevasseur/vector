# Verified progress

## Stage 1 — secure foundation
Implemented independent package/configuration, private SQLite WAL/FULL migrations,
append-only audit, bounded local logs, consistent unique backups, explicit bounded
file intake, and mandatory kernel seccomp offline policy. No model dependency.

Lenovo: 10/10 tests passed. Actual unfiltered socket creation was the positive
control; VECTOR then denied socket families and inherited socket/process bypasses.
Fresh `--no-index --no-deps --no-build-isolation` installation and installed CLI
startup passed. Restricted runner: 9 tests passed, one positive-control socket
creation error caused by the runner's own restrictions; not reported as a pass.

No inference daemon policy is qualified, and no model communication is enabled.
No broad filesystem sandbox or hostile-host guarantees are claimed. HELIX was
not read as a code dependency or changed. Next: Stage 2 permanent originals/events.

## Stage 2 — permanent memory
Implemented immutable content-addressed bytes, distinct submission events, per-event
filenames/media/metadata, source identity, revision ancestry, extraction statuses,
transactional bounded batches, integrity checking, exact export, unique backups and
checksum-verified restore into a new location only. Failed restores remain blocked
in quarantine. Binary/invalid UTF-8 originals are retained without false extraction.

Lenovo full suite: 21/21 passed, including actual CLI ingest/list/show/export/backup/
restore, before/after-COMMIT process crashes, deduplicated repeated events, failed
batch rollback, corruption detection, append-only controls and all Stage 1 checks.
No hardware power-loss claim or malicious-administrator authenticity is implied.
Next: Stage 3 incremental lexical retrieval and measured controlled 10k workload.

## Stage 3 — deterministic retrieval
Implemented incremental contentless FTS5, source/time/typed metadata filters,
literal query handling, bounded ranked excerpts with original verification, and
atomic rebuild from originals. CLI search/rebuild is integrated.

Lenovo full suite: 27/27 passed. Controlled 10,000-record benchmark reconstructed
100% of originals and returned correct top-1/source attribution for all ID-bearing
lexical queries. Warm-cache median exact lookup 0.0246 ms; lexical 1.5431 ms;
13,402,112 database bytes; peak process RSS 34,672 KiB. Ingest 38.12 s; rebuild
0.454 s. This does not establish general semantic or factual reasoning ability.
Next: Stage 4 source-linked claims, supported scoped conflict detection and explicit
auditable operating overrides; originals remain unchanged.

## Stage 4 — supported knowledge integration
Implemented explicit pipe-format extraction, exact source spans and hashes, typed
unverified claims, case-preserving entities, one-hop relationships, scoped/unit-
matched exclusive disagreement queries, append-only assessments/evidence links and
explicit scoped overrides. Raw originals survive extraction failure. Original
source claims remain visible after overrides. Append order handles clock regression.
Added resource checks for oversized corrupt blobs, restore copying and backup time.

Final actual Lenovo full suite: 43/43 passed. Clean local wheel installed in VECTOR's
own `.venv` with `include-system-site-packages=false`; all 43 tests passed again
against the installed runtime from outside the checkout. Actual CLI tests drive
kernel-guarded learning/conflicts/explicit override, exact archive export and
backup/restore. Kernel positive/denial controls remain included and passing.

This is bounded Stage 4 foundation acceptance, not general language understanding.
Stages 5-8 remain unqualified; Stage 9 remains unauthorized. Local inference is
blocked until a separately secured service and narrowly scoped client policy are
verified. Existing inference daemons were not modified or contacted. There is no
GUI, semantic retrieval, neural learning or scientific reasoning claim.

Final additional acceptance covered data-parent rename protections and upgrade
from a populated schema-2 archive (including its backup) to schema 4 without
changing original bytes, IDs or retrieval provenance. Source and installed suites
both finish at 43 passing tests, no skips or expected failures. Installed modules
were checked byte-for-byte against the source. The user's 28,715-byte master
directive is the first real archived submission in the private default database,
was retrieved through FTS and verified byte-identical, and has a unique local
backup. It was not automatically converted into facts or claimed as model learning.

## Final database guard correction
A host regression reproduced SQLite REPLACE implicitly deleting an original despite
ordinary delete triggers. VECTOR write connections now enable recursive triggers,
so REPLACE is rejected and original bytes remain unchanged. Negative/corrupt schema
versions are also rejected before migration rather than selecting a negative list
index. Both source and clean-installed full suites passed again: 43/43 each.
The deliberate pre-fix failure and restricted-runner ownership errors are retained
separately from the successful host results.


## Stage 4.5 — Portability and scalable storage (2026-10-29)
Implemented registered versioned subsystem state, managed compressed CAS assets and
streamed originals, strict complete-inventory checks, fixed-block incremental
repositories, independently verified new-only restoration, crash resume, capacity
monitoring/reserve, real SQLite-full rollback and cooperative verified relocation.
Optional installed cryptography provides AES-256-GCM/HKDF with separate offline
recovery keys and no plaintext fallback. Models/extensions remain inert. No HELIX
source, shared inference service, firewall or host-wide security setting changed.

Final actual Lenovo source suite: **67 passed, no skips** (228.545 s).
Final independent wheel-installed suite outside the checkout: **66 passed,
1 skipped** (220.464 s). The sole skip is authenticated-encryption roundtrip:
cryptography is absent from the isolated .venv. Actual host Python has that local
dependency and its positive encryption/wrong-key/tamper tests passed. Core .venv
operations remain dependency-free; missing encryption fails closed. All 18 installed
Python modules were compared byte-for-byte with final source. Tests include a real
second-filesystem export/restore, abrupt os._exit recovery, actual SQLITE_FULL,
strict unsafe/missing state rejection and kernel socket denial during transfers.
The removed 100-claim aggregate cap is verified with 1,201 source-linked claims;
the failure-retention fixture now uses an actually invalid subject. Migration
assertions now require the current migration count (5), retaining byte/ID checks.

The 50,000-event synthetic growth workload restored every original byte-identically,
passed all integrity checks and 100 literal retrieval probes. An unchanged backup
reused 63 blocks with zero new blocks. BENCHMARKS.md records timing, overhead and
the fact that final cross-filesystem publication/locking/deadline fixes followed
that growth measurement; their final behavior passed actual-host regression.

Real default data was first backed up by the previous installed runtime, then
migrated to schema 5. Its complete portable export was actually restored in two
independent temporary installations. Existing event eedfd6c445664afa9a2b46a03cee4a5d
and the 28,715-byte original master directive retained SHA-256
`eaaf6cac9a07207a754a46557b0f8e93b79a0dabcd0c015c00317c79571a16e2`.
No real model weights are installed in VECTOR; fake test asset bytes are explicitly
labelled fixtures and never presented as models/inference. Default data stays in
its original location; relocation acceptance used disposable installations.

Known boundaries: Linux/runtime/schema dependencies require separate trusted
installation; optional encryption is unavailable in .venv until provisioned offline;
large-file full-text indexing is deferred above the extraction budget; incomplete
source fragments are retained for review; restore reserve is conservative; no
automatic backup retention deletion or partitioned/distributed store; no physical
power-loss qualification, million-record claim, model reasoning or GUI acceptance.
Stage 5A activation remains blocked by the absence of a qualified dedicated inference
profile/runtime/managed model. The existing deny-all-sockets/process policy remains
mandatory. Portability does not qualify that new security profile or release readiness.

## Stage 5 foundation batch
Preserved b8cdbfc and re-ran all 67 baseline tests successfully. Added replaceable
bounded inference adapters, a separately isolated Ollama broker with verified
namespace/cgroup controls, original-grounded context/ranking, strict source citations,
bounded operational reasoning/uncertainty records, explicitly labelled simulation
for tests, human-approved atomic knowledge proposals and deterministic SI/Decimal
tools. Full actual-host regression: 81 passed, zero skips (150.740 s).
Actual PID exhaustion and worker-descendant cleanup passed. Dedicated Ollama 0.40.12
discovered local qwen2.5-coder:0.5b without loading weights or contacting the shared
service. Actual model generation and desktop workflows remain unqualified at this
checkpoint. All new durable state uses Stage 4.5 registered contracts. See
INTELLIGENCE_SPEC.md. HELIX and other independent repositories were not modified.

## Desktop and shared application integration
Added the actual Tk desktop and independent protected application backend, shared
CLI/service operations, startup/model availability/errors, evidence-only fallback,
clickable originals, claim/override learning workflows, projects/restart history,
deterministic tools and Stage 4.5 backup/restore/relocation controls. New explicit
pipe/local-display profiles retain socket/process denial and synchronize threads.
Migration 6 adds indexes only. Managed model import resolves verified external
obligations; materialization is restricted to the supported Ollama layout. No hidden
persistent side database is used. Menu installer preserves existing customized files.

Actual Lenovo full source suite: 92 passed, zero skips (183.795 s). Independent
wheel-installed suite outside checkout: 91 passed, one skipped (160.682 s). The
installed skip is optional authenticated-encryption roundtrip because cryptography
is absent from .venv; host encryption passed. CPU-only worker qualification, PID
exhaustion/cleanup, actual GUI, remote-display denial, thread synchronization,
application restart, indexed history and portable new-state tests are included.
Startup diagnostics exposed GPU discovery after resolving the installed runner;
GPU backend directories are now hidden and CPU-only settings explicit. The shared
Ollama home is also hidden. No host-wide setting/shared service was changed.

Framework/profile/desktop tests do not qualify model answer accuracy. The actual
model qualification utility preserves independently controlled original-quote
expectations and raw/partial-generation evidence. Current real-model requalification
and performance evidence are recorded separately after this implementation batch.
The application remains an experimental build, not release-ready or generally
qualified for multi-source reasoning or scientific engineering decisions.

## Structured output and interaction durability
Added fixed answer-v1/claims-v1 decoder schemas after actual Qwen output copied the
evidence-context object instead of answering. Schemas constrain syntax only; all
source IDs, hashes, spans, quotes, scopes, independent task expectations and human
approval checks remain enforced. No citations or answer values are filled in by the
controller. Raw/partial output evidence remains explicitly marked and bounded.
Questions now commit a pending version before retrieval/inference; a real abrupt-
exit test verifies recovery without any fabricated response. History shows the latest
turn version while preserving all versions. Proposal review displays exact original
quotes before enabling explicit approval, with selection instead of manual ID entry.

Full actual-host source suite: 95 passed/no skips (180.197 s). Frozen offline wheel:
all 33 modules byte-identical to source. Independent installed suite: 94 passed,
1 optional cryptography test skipped (168.665 s); host encryption passed. No running
application was upgraded during final frozen model trials.

Real model accuracy is deliberately separate. Plain-JSON Qwen 0.5B trials returned
copied context objects and failed answer validation. One storage roundtrip passed
but its generation phase was invalidated by an in-flight adapter interface change;
it is not counted as model evidence. A rerun against the frozen installed build
restored all real weights and produced answer-v1 output with valid source citations,
but failed the independent verbatim/completeness task. Final consistency results
and timing are recorded separately. These outcomes are not release qualification.


## Lenovo intelligence qualification — 2026-10-30
Implementation checkpoint: dae4abf (preceded by 5079048 and c42b6f6). Source
regression: 95 passed, zero skips, 180.197 s. Frozen wheel: all 33 modules
byte-identical; independent installed regression: 94 passed, one skipped,
168.665 s. The skip is the positive optional authenticated-encryption test because
cryptography is absent from the isolated .venv; it passed on the host interpreter.
No skipped test is counted as a pass.

Actual isolated Qwen2.5-Coder 0.5B (Q4_K_M), Ollama 0.40.12, answer-v1:
**0/3 independent two-source verbatim-attribution trials passed**. All three
returned structurally valid output with valid original citations and the correct
flow values, but paraphrased instead of quoting and set insufficient=true. They
remain explicitly unverified inferences. Valid attribution is not independent
semantic verification or completion of the requested task. No simulated output
was substituted. Context 4096, output budget 512, temperature 0, seed 0,
timeout 240 s. Model generations took 223.070, 151.593 and 155.426 s; all completed
below budget (383, 374 and 376 output tokens), so these failures are not explained
by response truncation. Deterministic configuration and essentially identical
mistakes provide no evidence that repeating the same request will help.

Two earlier plain-JSON trials copied the evidence-context structure and failed
answer validation. Fixed decoder schemas improved syntax without supplying any
answer values/citations or changing validation. A separate earlier managed trial
passed storage checks but its generation was invalidated by an in-flight adapter
interface change; it is excluded from model scoring. The three final trials used
an immutable installed build. The frozen managed trial imported, exported and
restored real model weights before actual inference; external-only model
selection correctly prevented a falsely self-contained export.

Actual worker checks verified separate route-free network namespace, external
connect denial, nested-userns denial, read-only model blobs, hidden host/shared
model homes, CPU-only backend, memory.max=805306368, pids.max=64 and
cpu.max='100000 100000'. Process exhaustion/cleanup, timeout/cancellation/crash,
source/path/hash rejection, real protected GUI and interaction crash persistence
are covered by actual-host tests. No host-wide policy or shared Ollama service was
changed. Neither HELIX nor separate assistant projects were modified.

Evidence directory (outside the repository):
/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-intelligence/resumed-20261030
See REPORT.md, frozen-*-trial*.json, full regression logs, fingerprints, benchmark
JSON, actual default-data verification and final-interaction-roundtrip.json.
This is an experimental foundation; VECTOR is not release-ready.

Final post-inference managed snapshot e1760c88ffc642d8b41c7fdb1226b5ba
passed actual restoration: 8 files, 7 managed objects, 2 original events, no
integrity errors. Incremental export reused 375 blocks and added 1; original
IDs/bytes preserved. Actual restore verification 62.800 s; export plus verification
162.125 s. Evidence: final-interaction-roundtrip.json. No source changes followed
the frozen 95-test regression or model trials.
