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
