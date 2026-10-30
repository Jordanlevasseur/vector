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
Stages 1–4.5 remain preserved. Inference/evidence/learning/tool foundations were
checkpointed at 5079048 (81 passing actual-host tests). The desktop integration adds
actual protected workflows, managed-model materialization and indexed history.
Framework and OS-profile acceptance is separate from actual model accuracy; no
simulated test establishes model reasoning. See INTELLIGENCE_SPEC.md,
DESKTOP_SPEC.md and PROGRESS.md for final test/model results. Stage 6 currently
covers a bounded deterministic subset; general scientific reasoning remains open.
Stage 7 has a working local X11 interface, with representative usability/security
qualification still required. Stage 8 remains a release gate. Stage 9 remains
unauthorized. No host-wide security relaxation or shared-service reuse is permitted.
