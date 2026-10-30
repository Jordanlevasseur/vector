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
