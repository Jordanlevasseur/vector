# Roadmap
1. Secure foundation: independent runtime, config, migrations, kernel offline
   policy, diagnostics, tests and backup foundations. Host acceptance required.
2. Permanent memory: transactional immutable original bytes, event identity,
   provenance/revisions, hashes, duplicate events, exact reconstruction, verified
   backup/restore and crash tests.
3. Retrieval: incremental FTS5, exact/metadata/temporal/source search, rebuilds,
   provenance and controlled 10,000-fact measurements.
4. Knowledge: source-linked claims, entities/relations, supported scoped conflicts,
   assessments and overrides; never automatic truth or discarded raw input.
4.5. Mandatory portability and scalable storage: registered state, exact offline
   export/restore, managed models/assets, incremental backup, verified crash/full
   disk recovery, larger-volume moves and measured growth beyond 10k. Permanent
   acceptance gate for all later subsystems; see PORTABILITY.md.
5. Reasoning: bounded evidence/context interfaces and separately secured local
   inference. No unsafe connection to an unqualified inference daemon.
6. Deterministic scientific tools with checked units and bounded operation.
7. Desktop: ingestion, sources, search, knowledge, health; no voice work.
8. Qualification: representative reliability/resource/retrieval benchmarks.
9. HELIX integration: prohibited until separately authorized.
Progress and measured acceptance are recorded separately from this plan.

## Current boundary
The supported core through Stage 4.5 is implemented and host-tested within the
explicit PORTABILITY.md bounds. Final source suite: 67/67 passed. Independent
installed suite: 66 passed and one optional encrypted-roundtrip test skipped because
that interpreter has no cryptography; actual host encryption tests passed. Storage
growth is measured at 50,000 short originals; see BENCHMARKS.md for revision/timing
scope. Stage 5A remains gated by a separately qualified inference profile, authorized
managed weights/runtime and independently verified reasoning. Do not connect an
unqualified shared daemon. Stages 6-8 have not passed acceptance; Stage 9 remains
unauthorized. Desktop actions await a tested display/IPC profile.
