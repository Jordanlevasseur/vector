# Acceptance requirements
Stage 1: clean local-only installation; mandatory actual kernel denial with a
positive socket control; fail-closed missing-policy startup; independent private
database; migration/restart/log/backup checks. Restricted runner failures are not
host passes. Stage 2: repeated events, original byte reconstruction, revisions,
transaction rollback and process-crash recovery; verified non-overwriting backup
and restore. Stage 3: incremental/rebuilt indexes, source attribution, representative
controlled 10k retrieval/latency measurements. Stage 4: provenance-preserving claim
integration, supported conflicts and explicit override history. Subsequent reasoning,
tools, GUI and release stages require their own measured acceptance. No stage passes
because files or unit tests alone exist. Stage 9 remains unauthorized.

## Measured acceptance through the supported Stage 4 foundation
- Stage 1 checkpoint ac2295e: 10 actual-host tests and clean offline install/startup.
- Stage 2 checkpoint 89a5f68: 21 actual-host tests including crash and recovery.
- Stage 3 checkpoint 1cce94c: 27 tests and controlled 10k measurements (BENCHMARKS.md).
- Final Stage 4/resource-hardening: 43 source and 43 independent installed tests,
  with no skips or expected failures. Kernel positive/denial control is included.
  Dedicated default data is independent from the source tree and HELIX.

This accepts only the documented bounded formats and operations. No general
language extraction, calibrated truth determination, broad scientific reasoning,
embedding retrieval, large-scale corpus qualification, graphical workflow or
inference-service security has passed acceptance. Stage 9 is not authorized.
Upgrade acceptance explicitly covers populated schema-2 originals and a schema-2
backup migrating to schema 4 with unchanged event identity, source bytes and FTS
retrieval. Physical power-loss testing, hostile-host review, inference isolation,
GUI workflows, general NLP and representative multi-source reasoning remain open.

## Mandatory Stage 4.5 gate
PORTABILITY.md defines the new contract. Required acceptance covers complete
populated export/import; exact originals/IDs/duplicate events/revisions/claims/
overrides/registered state/assets; different-location restore and index rebuild;
corrupt/incomplete/unsafe input rejection; real-process interruption recovery;
disk-full rollback; incremental correctness; kernel network denial during transfer;
missing-asset failure; and measured storage growth beyond 10,000 records.
A created archive is not a verified backup. Actual restore verification is required.
Stage 5A cannot rely on unverified portability. GUI/inference/release qualification
remains separate, and skipped optional-dependency tests are never counted as passes.


Final Stage 4.5 source acceptance: 67 passed/no skips; installed acceptance:
66 passed/one explicitly unverified optional-encryption test in .venv. The same
positive encryption test passed on the actual host interpreter. Actual cross-volume
publication, crash/restart, disk-full rollback, unsafe import rejection and transfer
network denial passed. Real schema-4 default data migrated/restored at schema 5
with its original event ID/bytes/hash unchanged. BENCHMARKS.md records the 50k
workload and precise performance-revision boundary. This qualifies the documented
storage operations, not local reasoning, GUI, physical power loss or broad release.


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


## Final Lenovo memory/project acceptance — 2026-10-30
Frozen implementation ee3e692, with earlier batches e3b0c83 and 26d7cb6.
Source: 112 passed, zero skips (224.184 s). Independent installed: 111 passed,
one skipped (243.581 s). The installed skip is the optional authenticated-encryption
roundtrip because cryptography is absent from the isolated .venv; host source
positive encryption passed. All 36 installed modules match source exactly. The
final source includes all earlier tests unchanged and 17 new memory/project cases.
No skipped test is represented as a pass.

Actual GUI acceptance additionally verified multi-source cross-project reuse,
source-switch claim paging, visible forms, durable research items, model-unavailable
operation and error-free protected workflows. Startup 2.106 s; frontend peak RSS
29,564 KiB, backend RSS 24,640 KiB on the warm Lenovo. These are automated native
GUI checks, not a human usability study or a general desktop release qualification.

Final installed controlled corpus: 5,000 originals, four projects, 5,000 associations,
100/100 top recall, chronological, late-file context and independent restored-byte
probes. Full restore integrity checked all 5,000 original hashes. Recall median/p95
1.259/2.804 ms; context 0.934/2.479 ms; max context 703 bytes; peak RSS 40,436 KiB;
SQLite 21,164,032 bytes, FTS 802,816 bytes. Bulk associations 9.576 s versus earlier
single-transaction-per-source 203.711 s. Synchronous FULL and batch crash rollback
remain mandatory. Warm/concurrent workloads are not dedicated-host throughput or
semantic-reasoning measurements. Detailed raw results are retained outside the repo.

Default user data has schema 7, its original event ID/28,715 bytes/SHA-256 unchanged,
and actual restore verification passed before and after the installed upgrade.
No synthetic knowledge was inserted into the default user installation. All new
state participates in registered portable records; complete-state tests compare
all versions/IDs/reference tables exactly after actual restoration. Network, worker,
filesystem, seccomp, source/hash, authorization and recovery tests passed unchanged.
No external network, downloads, shared runtime changes or HELIX modifications.

No new real-model answer qualification is claimed. Qwen0.5B's previous independent
0/3 remains historical unqualified evidence, not a score measured on this new
context implementation. Simulated framework outputs are explicitly labelled and
never production fallback. Literal categories, exact entities and user-authored
links are not semantic understanding or neural training. Older project items remain
paged/portable, but context currently checks only the latest 20 items; full-history
project-note/task FTS is the next concrete milestone. Broader mixed-domain reasoning,
reviewed entity aliases, human usability, installed optional encryption and physical
power-loss/hostile-host acceptance remain open. VECTOR is not release-ready.

Evidence directory:
/home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-memory-projects
See REPORT.md, final-full-installed.log, release-candidate-source.log,
final-installed-fingerprint.json, benchmark-final-installed.json,
desktop-installed.json and default-migration-and-restore.json.

## Stage 5D measured checkpoint — 2026-10-30
Implementation b778fe4; all 41 installed modules match source. Source 130
passed, 0 skipped (232.241 s). Independent installed
129 passed, 1 skipped (231.958 s). The skip is
authenticated encryption: optional cryptography is absent in the isolated interpreter;
source-host positive encryption passed. No skip is represented as a pass.

Actual default library: 1,000 verified digital editions, 999 conservative author/title
groups, 550 distinct credited author-name strings, 60 explicitly credited translated
editions, 19 provider language codes, 1,288,804 source-linked passages and 1,000 body
observations. All processing states complete. Raw hashes/provider IDs are unique.
Ariosto's Orlando Furioso has two retained editions. Canonical work identities across
translations/aliases/volumes remain unreviewed; 1,000 distinct underlying works is not
certified. All 1,000 print dates remain unknown. No 10,000-book trial was run.

User selected U.S.-only rights. All 1,000 passed source/RDF hashes, provider identity,
U.S. rights assertions, header-notice and full-license checks. Full originals and
licenses remain available offline; no worldwide clearance is asserted. CMUdict has
135,166 source pronunciation entries and its original license. Full-library live
integrity passed with 2,003 events/2,002 managed objects, zero errors; the original
28,715-byte user event and SHA-256 are unchanged. Full-corpus export/restoration acceptance remains BLOCKED/UNVERIFIED at resume-preserved-snapshot: Export deadline reached; staged transfer can be resumed.. Staging and live originals are retained; incomplete phases are not passes.

The original 70/100 retrieval result is retained: LF-only probe construction against
CRLF text caused clipped words and cross-paragraph probes in all 30 misses. The
pre-registered corrected original-paragraph protocol found the expected source
97/98 eligible times, top1 87/98; two unusable probes are not passes. Exact original
quotations 345/345, context fragment/hash attribution 763/763. One global miss matches
235 passages across 109 editions; six hits exist within its expected source, but
its global miss is retained. Baseline context median/p95 7.389/38.084 s remains poor.
No unfiltered retrieval speedup is claimed for later display/deadline/filter/count fixes.

Actual installed protected GUI on the real library passed under the same 60-second
request wait: clean CRLF display with original quotes untouched, complete license
viewer, language-filtered search, exact counts and IPv4/IPv6/Unix socket denial.
Ready 1.264 s; frontend peak 41660 KiB. Screenshot
visually inspected. Earlier stats timeout retained; exact rowid counting now scans
the existing grouped index. SQL integrity verification has VM deadline interruption
and connection-recovery coverage; no hash/schema checks or 900-second budgets were
relaxed. Existing event indexes are reused for language filtering; no new index.

43 curriculum targets, zero qualified language proficiencies. Actual reviewed
linguistic records/typed links remain zero; body form candidates and dictionary
references are not semantic knowledge or neural training. No new model trial;
previous Qwen 0.5B 0/3 remains historical evidence. No large model was downloaded.

Stage 5D is incomplete; VECTOR is not release-ready. Next: profile actual broad-term
FTS/context and verification I/O with persistent probe evidence; preserve independent
expectations, hashes, bounds and approval. Curate work/edition identities and print
metadata, build scholar-reviewed English/historical-language gold sets and attested
resources, then separately qualify a capable local model. Installed optional
encryption, cold-cache/human/RTL GUI, physical power-loss, hostile-host and actual
cross-computer acceptance remain open. HELIX was not modified.

Full 14-field report and raw evidence: /home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage5d/REPORT.md

Immediate release blocker: the actual 1000-edition export resume timed out after
900.293 seconds under the unchanged budget. Live integrity passed in 636.371 s;
no full-library restoration result exists. Instrument the inner export stages and
resolve this engineering/performance failure before increasing corpus scale. Its
exact internal bottleneck is not established. Do not treat this as an unavailable
dependency, skip validation, or raise deadlines to manufacture acceptance.
Native rerun commands: /home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage5d/HOST_ACCEPTANCE.md
