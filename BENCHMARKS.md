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
