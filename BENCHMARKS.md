# Performance targets
Targets are not claims: 100% exact reconstruction in controlled committed-source
tests; >=99% exact-fact retrieval on a controlled 10,000-fact corpus; median indexed
exact lookup below 100 ms on upgraded target hardware; zero observed unauthorized
network communication; tested deterministic crash/corruption recovery. Record
corpus, query workload, distributions, latency, attribution, footprint and resource
limits. Current host: approximately 3.7 GiB RAM, HDD, Python 3.12.3, SQLite 3.45.1.
No 100k/1M or inference-heavy benchmark is authorized without resource assessment.

## Measured Stage 3 — Lenovo, 2026-10-29

Controlled synthetic station records; 10,000 distinct originals and one
ID-bearing literal lexical query per event. Not natural-language QA or semantic
recall. Warm cache after ingestion; no cold-cache guarantee.

- records: 10000
- lexical_top1_fraction: 1.0
- source_attribution_fraction: 1.0
- byte_reconstruction_fraction: 1.0
- ingest_seconds: 38.11854244099959
- ingest_events_per_second: 262.33951666641343
- rebuild_seconds: 0.45440103599685244
- lookup_median_ms: 0.0245615
- lookup_p95_ms: 0.085964
- lexical_median_ms: 1.5430595
- lexical_p95_ms: 2.665801
- query_cpu_seconds: 17.379430861
- database_bytes_including_indexes: 13402112
- process_peak_rss_kib: 34672

Separate index size and hardware-specific cold-cache/inference behavior were
not measured. No 100k/1M corpus or model benchmark was run.

These measurements were taken at the Stage 3 retrieval implementation, before
Stage 4 knowledge tables and subsequent resource hardening. They are a baseline,
not a certified latency distribution for every later build, corpus or cold start.

## Stage 4.5 controlled storage workload (Lenovo, 2026-10-29)
50,000 distinct short synthetic original events were ingested through the bounded
iterator. Every original was reconstructed byte-identically after restoration;
all SQLite/reference/hash checks passed; 100 ID-bearing literal lexical probes
returned the expected source. No neural/model reasoning was exercised.

Measured during concurrent regression activity: ingestion 711.83 s, first export
42.54 s, unchanged incremental export 17.55 s, actual restore 5.08 s, restored
integrity verification 2.38 s. SQLite including indexes: 65,265,664 bytes. First
repository: 20,294,956 bytes. An unchanged snapshot added 36,934 bytes of catalogue/
receipts and reused all 63 blocks (zero new blocks). Peak benchmark-process RSS:
34,368 KiB. These are warm synthetic-workload measurements, not dedicated-host,
cold-cache, million-record or general-question-answering qualification.

This growth run preceded the final destination-local cross-filesystem publication
fix and final whole-operation relocation/deadline hardening. Those controls are
covered by subsequent actual-host regression/cross-filesystem acceptance; the
numbers above are not a measurement of their incremental performance cost.
Reproduce the current implementation with
`PYTHONPATH=src python3 -m vector_core.storage_benchmark`.
The test uses temporary data and requires at least 1 GiB free; the application also
retains its volume safety reserve. Maximum measured collection here is 50,000
short originals, not 50,000 large files or a general maximum supported capacity.
A separate regression streams/restores a 24 MiB original and integrates/pages
1,201 claims without the former 100-claim aggregate cap.

## Intelligence/desktop workload — Lenovo, 2026-10-30
Frozen implementation dae4abf. Warm synthetic corpus: 1,000 short originals,
100 literal questions; expected top context source 100/100. Ingest 21.517 s;
retrieval median/p95 0.243/0.328 ms; context median/p95 8.048/8.949 ms.
Combined retrieval/context CPU 0.862 s. Database 1,515,520 bytes, FTS pages
61,440 bytes, benchmark peak RSS 25,520 KiB. 1,000 pure arithmetic calls:
0.0671 s, excluding durable audit. These are literal retrieval measurements,
not semantic retrieval or model accuracy.

Actual installed protected local-X11 desktop: startup to ready 6.880 s;
frontend peak RSS 28,296 KiB, backend RSS 24,520 KiB. Six functioning tabs;
evidence-only assistant and deterministic 2+2=4 exercised. This measurement used
temporary data, warm OS and concurrent model testing; no model was loaded in
that GUI measurement. These figures do not establish usability qualification.

Real Qwen0.5B answer-v1 generation: 151.593–223.070 s for 374–383 output tokens,
4096 context/512 output/240 s deadline, CPU quota one core, two runtime threads,
768 MiB worker memory. Cold managed load 47.728 s. Managed asset import 34.170 s,
first export 133.342 s, restore 60.499 s; complete trial 479.925 s including all
storage and inference work. Storage timings include ~398 MB actual model data;
ordinary source retrieval timings exclude inference. Independent task score 0/3.
Raw benchmark/configuration/model digests are retained in the evidence directory
listed in PROGRESS.md. No large model or dependency was downloaded.

## Project/memory workload — Lenovo, 2026-10-30
Controlled 5,000 distinct short historical originals (2012 timestamps), four
projects and 5,000 source associations. 100 independently specified literal probes
passed top project recall, chronological filters and late-file source-context
attribution (100/100 each). A real portable restore verified all 5,000 original
hashes; 100 separately constructed byte expectations matched exactly.

Final bounded-batch workload: ingest 17.451 s; association 9.101 s; recall median/
p95 1.195/2.910 ms; context median/p95 0.765/2.101 ms, maximum 703 context bytes.
Query CPU 0.246 s; peak RSS 39,876 KiB; SQLite 21,204,992 bytes including all originals,
text, history and indexes (growth 20,951,040 bytes); FTS pages 802,816 bytes.
Export 14.174 s, actual restore 1.741 s; zero integrity errors. Query-plan evidence
confirms records_project index use. No model inference, semantic recall or reasoning
accuracy was measured. Long-term timestamps are controlled test data, not a claim
of years of real deployment.

The earlier same-size workload linked each source in its own synchronous transaction
and took 203.711 s for associations. Explicit approved atomic batches (up to 64)
reduced that measured time to 9.101 s while retaining synchronous FULL, idempotence,
reference checks and tested process-crash rollback. Runs used warm OS caches and
concurrent regression activity; these are workload observations, not isolated-host
throughput guarantees. Neither originals nor total project/source counts are capped.
Raw evidence: outputs/vector-memory-projects in the current Codex workspace.
Reproduce on the actual host with `PYTHONPATH=src python3 -m vector_core.memory_benchmark`.


Final frozen installed ee3e692 repetition (same 5k/4-project/100-probe workload):
all probes passed. Ingest 23.774 s, association 9.576 s, retrieval median/p95
1.259/2.804 ms, context median/p95 0.934/2.479 ms, max context 703 bytes (excluding
model instructions), query CPU 0.274 s; peak RSS 40,436 KiB. SQLite 21,164,032 bytes,
growth 20,910,080 bytes, FTS 802,816 bytes. Export 13.258 s, actual restore 2.304 s;
all 5,000 original hashes verified plus 100 independent byte probes. Warm OS and
concurrent regression; no model loaded or semantic task measured.
Final installed protected GUI: ready 2.106 s; frontend peak 29,564 KiB, backend
RSS 24,640 KiB; two sources reused across projects, source-switch claim paging
passed and zero reported errors. Raw final JSON/PNG evidence is in the directory
listed in PROGRESS.md; these are automated checks, not human usability acceptance.

## Stage 5D real literary workload — Lenovo, 2026-10-30
1000 editions / 999 author-title groups / 1,288,804 passages. All originals preserved.
First 400: import 652.634 s; processing 1949.491 s;
main-process peak 98376 KiB. Next 600: import 702.820 s;
processing/resume scan 5603.617 s; peak 87936 KiB.
Concurrent regression/ordinary host activity and a small labelled cache diagnostic
affect timings. Cache experiment did not establish benefit; shipped 4 MiB target
and all worker/OS/durability controls remain unchanged.

Corrected original-paragraph benchmark: 97/98 eligible recall@20, 87/98 top1, two
unusable of 100 desired probes. Quotes 345/345; context fragment/hash matches 763/763.
One ambiguous global miss remains a miss (235 matching passages / 109 editions).
The original LF-only probe result (70/100) and its validity audit remain retained;
correcting probe construction is not a retrieval/model improvement.

Measured baseline backend f82e124: retrieval median/p95
636.554/2074.825 ms; context
7389.061/38084.204 ms; max context 6646 bytes.
CPU including probe/attribution work 308.105 s; query-process
peak 72624 KiB, excluding OS cache/other processes. SQLite
1,326,497,792 bytes; literary FTS 202,305,536 bytes.
No final-build end-to-end unfiltered retiming or semantic/translation accuracy claim.

Installed b778fe4 GUI ready 1.264 s, frontend peak
41660 KiB; actual screenshot/reader/license/filter checks passed.
An exact grouped-index rowid count measured 1,288,804 in 20.057 s. That is not an
estimate, checkpoint sum or a cold-cache performance guarantee. Full-corpus export/restoration acceptance remains BLOCKED/UNVERIFIED at resume-preserved-snapshot: Export deadline reached; staged transfer can be resumed.. Staging and live originals are retained; incomplete phases are not passes.
Raw protocols, per-probe results, failed attempts and recovery evidence: /home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage5d.

## Stage 6A pilot measurements
Independent 20-instance arithmetic: existing direct tool 20/20, two-step durable
resume workflow 20/20. Median direct computation 0.436 ms; durable two-step/resume
workflow 470.103 ms. These perform different persistence work: no speedup or
arithmetic-accuracy gain is claimed. Finite-domain enumeration 6/6 against independent
Python enumeration, with exact continuation cursors. Literal reconciliation retained
one explicit disagreement and both originals. Total pilot 16.355 s, peak process
RSS 26820 KiB, no model calls or simulated model. Host activity overlapped portions
of measurement; no cold-cache or exclusive-host guarantee.

Real Qwen 0.5B system comparison: six synthetic held-out instances per pathway,
4096 context/384 output/120s request timeout, seed/temperature zero and unchanged
qualified CPU-only worker. Objective baseline 0/4, adaptive 0/4. Creative results
are unscored; adaptive 1/2 valid envelopes is not discovery competence. Separate
tool-feedback repair 0/1, wrong 385 repeated despite independently computed 285.
Initial worker failures and all raw outputs remain preserved; remaining tasks
used fresh qualified workers rather than a security fallback. System response
formats differ; this is not a model-only ablation. Protocol/fingerprints record the
small reconciliation correction between early and remaining trials. No training,
model substitution, larger-budget rerun or acceptance relaxation occurred.
Full per-task results and limits: /home/mint/Documents/Codex/2026-10-29/read-agents-md-and-inspect-the/outputs/vector-stage6a/REPORT.md.
